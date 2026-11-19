from __future__ import annotations

import io
import json
import os
import threading
import time
import unittest
import urllib.error
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.request import Request, urlopen

from scrap import server


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class ProductMappingTests(unittest.TestCase):
    def test_product_normalizes_fields_without_assuming_a_currency(self) -> None:
        product = server._product(
            source="mercadolibre",
            item_id="MLA123",
            title="  Cámara  ",
            description="Descripción completa",
            image="https://example.test/image.jpg",
            price="42.50",
            currency=None,
            url="https://example.test/item",
            condition="Nuevo",
            old_price="50",
        )

        self.assertIsNotNone(product)
        assert product is not None
        self.assertEqual(product["id"], "mercadolibre:MLA123")
        self.assertEqual(product["title"], "Cámara")
        self.assertEqual(product["currency"], "")
        self.assertEqual(product["saving"], "Ahorra 7.50")
        self.assertEqual(product["image"], "https://example.test/image.jpg")

    def test_product_sanitizes_unsafe_urls_and_formats_savings_with_currency(self) -> None:
        product = server._product(
            source="ebay",
            item_id="item-1",
            title="Item",
            description="",
            image="javascript:alert(1)",
            price=10,
            currency="usd",
            url="javascript:alert(1)",
            old_price=12,
        )

        self.assertIsNotNone(product)
        assert product is not None
        self.assertEqual(product["image"], "")
        self.assertEqual(product["url"], "")
        self.assertEqual(product["currency"], "USD")
        self.assertEqual(product["saving"], "Ahorra 2.00 USD")

    def test_product_rejects_missing_title_or_invalid_price(self) -> None:
        fields = {
            "source": "ebay",
            "item_id": "item-1",
            "description": "",
            "image": "",
            "currency": "USD",
            "url": "",
        }
        self.assertIsNone(server._product(title="Item", price="nope", **fields))
        self.assertIsNone(server._product(title="  ", price=10, **fields))


class DotEnvTests(unittest.TestCase):
    def test_dotenv_loads_values_and_preserves_existing_environment(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "EBAY_CLIENT_ID='from-file'\nMELI_SITE_ID=MDO # comment\n# skip\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"EBAY_CLIENT_ID": "existing"}, clear=True):
                server._load_dotenv(path)
                self.assertEqual(os.environ["EBAY_CLIENT_ID"], "existing")
                self.assertEqual(os.environ["MELI_SITE_ID"], "MDO")


class SearchProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        server._clear_search_cache()
        server._reset_ebay_token_cache()

    def test_unavailable_and_not_configured_sources_are_separated(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            result = server.search_products(
                "laptop", ["amazon", "ebay", "wallapop", "fb-marketplace", "mercadolibre"]
            )

        self.assertEqual(result["products"], [])
        self.assertEqual(result["errors"], {})
        self.assertEqual(
            set(result["unavailable"]), {"amazon", "wallapop", "fb-marketplace"}
        )
        self.assertEqual(set(result["not_configured"]), {"ebay", "mercadolibre"})
        self.assertIn("Amazon:", result["unavailable"]["amazon"])
        self.assertIn("EBAY_CLIENT_ID", result["not_configured"]["ebay"])
        self.assertIn("MELI_ACCESS_TOKEN", result["not_configured"]["mercadolibre"])

    def test_partial_provider_failure_keeps_success_and_selected_order(self) -> None:
        barrier = threading.Barrier(2)
        ebay_product = {"id": "ebay:item"}
        meli_product = {"id": "mercadolibre:item"}

        def search_ebay(_: str, _detail: bool) -> tuple[list[dict[str, str]], list[str]]:
            barrier.wait(timeout=2)
            time.sleep(0.02)
            return [ebay_product], []

        def search_meli(_: str, _detail: bool) -> tuple[list[dict[str, str]], list[str]]:
            barrier.wait(timeout=2)
            return [meli_product], []

        with (
            patch.dict(
                os.environ,
                {
                    "EBAY_CLIENT_ID": "id",
                    "EBAY_CLIENT_SECRET": "secret",
                    "MELI_ACCESS_TOKEN": "token",
                    "SCRAP_CACHE_TTL_SECONDS": "0",
                },
                clear=True,
            ),
            patch.object(server, "_search_ebay", side_effect=search_ebay),
            patch.object(server, "_search_mercadolibre", side_effect=search_meli),
        ):
            result = server.search_products("phone", ["ebay", "mercadolibre"])

        self.assertEqual(result["products"], [ebay_product, meli_product])
        self.assertEqual(result["errors"], {})
        self.assertEqual(result["unavailable"], {})
        self.assertEqual(result["not_configured"], {})

    def test_only_mercadolibre_configured_returns_products_and_informational_states(self) -> None:
        product = {"id": "mercadolibre:item"}
        with (
            patch.dict(
                os.environ,
                {
                    "MELI_ACCESS_TOKEN": "token",
                    "SCRAP_CACHE_TTL_SECONDS": "0",
                },
                clear=True,
            ),
            patch.object(
                server,
                "_search_mercadolibre",
                return_value=([product], []),
            ),
        ):
            result = server.search_products("phone", list(server.SOURCE_ORDER))

        self.assertEqual(result["products"], [product])
        self.assertEqual(result["errors"], {})
        self.assertEqual(
            set(result["unavailable"]), {"amazon", "wallapop", "fb-marketplace"}
        )
        self.assertEqual(set(result["not_configured"]), {"ebay"})

    def test_real_provider_errors_are_prefixed_once(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"EBAY_CLIENT_ID": "id", "EBAY_CLIENT_SECRET": "secret"},
                clear=True,
            ),
            patch.object(
                server,
                "_search_ebay",
                side_effect=server.MarketplaceError("eBay: No se pudo conectar."),
            ),
        ):
            result = server.search_products("phone", ["ebay"])

        self.assertEqual(
            result["errors"], {"ebay": "eBay: No se pudo conectar."}
        )

    def test_ebay_token_is_cached_until_expiration_margin(self) -> None:
        clock = [100.0]
        with (
            patch.dict(
                os.environ,
                {"EBAY_CLIENT_ID": "id", "EBAY_CLIENT_SECRET": "secret"},
                clear=True,
            ),
            patch.object(server.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(
                server,
                "_request_json",
                side_effect=[
                    {"access_token": "token-1", "expires_in": 3600},
                    {"access_token": "token-2", "expires_in": 3600},
                ],
            ) as request_json,
        ):
            self.assertEqual(server._ebay_access_token(), "token-1")
            self.assertEqual(server._ebay_access_token(), "token-1")
            clock[0] = 3641
            self.assertEqual(server._ebay_access_token(), "token-2")

        self.assertEqual(request_json.call_count, 2)
        first_request_body = request_json.call_args_list[0].kwargs["data"].decode()
        self.assertIn("https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope", first_request_body)

    def test_search_cache_hits_and_expires_by_ttl(self) -> None:
        clock = [100.0]
        product = {"id": "ebay:item"}
        with (
            patch.dict(
                os.environ, {"SCRAP_CACHE_TTL_SECONDS": "10"}, clear=True
            ),
            patch.object(server.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(
                server,
                "_search_source_uncached",
                return_value=([product], []),
            ) as search,
        ):
            server._search_source("phone", "ebay", False)
            server._search_source("phone", "ebay", False)
            clock[0] = 111
            server._search_source("phone", "ebay", False)

        self.assertEqual(search.call_count, 2)

    def test_summary_does_not_fetch_detail_and_description_failure_is_separate(self) -> None:
        summary = {
            "id": "MLA-1",
            "title": "Cámara",
            "price": 10,
            "currency_id": "ARS",
            "permalink": "https://example.test/item",
            "thumbnail": "https://example.test/image.jpg",
        }
        with patch.object(server, "_request_json") as request_json:
            product, warnings = server._fetch_mercadolibre_product(summary, {}, False)
        self.assertIsNotNone(product)
        self.assertEqual(warnings, [])
        request_json.assert_not_called()

        with (
            patch.object(
                server,
                "_request_json",
                return_value={"title": "Cámara", "price": 10, "currency_id": "ARS"},
            ),
            patch.object(server, "_meli_description", side_effect=server.MarketplaceError("falló")),
        ):
            product, warnings = server._fetch_mercadolibre_product(
                summary, {}, True
            )
        self.assertIsNotNone(product)
        self.assertEqual(len(warnings), 1)
        self.assertIn("descripción", warnings[0])

    def test_missing_critical_summary_fields_trigger_detail_fetch(self) -> None:
        summary = {"id": "MLA-2", "title": "Cámara", "thumbnail": "https://example.test/a.jpg"}
        detail = {
            "title": "Cámara",
            "price": 25,
            "currency_id": "ARS",
            "permalink": "https://example.test/item",
        }
        with patch.object(server, "_request_json", return_value=detail) as request_json:
            product, warnings = server._fetch_mercadolibre_product(summary, {}, False)

        self.assertIsNotNone(product)
        self.assertEqual(warnings, [])
        self.assertEqual(request_json.call_count, 2)


class RequestTests(unittest.TestCase):
    def test_retries_http_429_and_respects_retry_after(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.example.test/search",
            429,
            "Too Many Requests",
            {"Retry-After": "0"},
            io.BytesIO(b""),
        )
        with (
            patch.object(server.urllib.request, "urlopen", side_effect=[error, FakeResponse(b'{"ok":true}')]),
            patch.object(server.time, "sleep") as sleep,
        ):
            self.assertEqual(server._request_json("https://api.example.test/search"), {"ok": True})
        sleep.assert_called_once_with(0.0)

    def test_ebay_auth_http_errors_have_actionable_message(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.ebay.com/buy/browse/v1/item_summary/search",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"error":"invalid_token"}'),
        )
        with patch.object(server.urllib.request, "urlopen", side_effect=error):
            with self.assertRaisesRegex(server.MarketplaceError, "EBAY_CLIENT_SECRET"):
                server._request_json("https://api.ebay.com/buy/browse/v1/search")

    def test_mercadolibre_auth_http_errors_have_actionable_message(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.mercadolibre.com/sites/MLA/search",
            403,
            "Forbidden",
            {},
            io.BytesIO(b'{"message":"forbidden"}'),
        )
        with patch.object(server.urllib.request, "urlopen", side_effect=error):
            with self.assertRaisesRegex(server.MarketplaceError, "MELI_ACCESS_TOKEN"):
                server._request_json("https://api.mercadolibre.com/sites/MLA/search")

    def test_timeout_is_retried_once(self) -> None:
        with (
            patch.object(
                server.urllib.request,
                "urlopen",
                side_effect=[TimeoutError(), TimeoutError()],
            ) as request_json,
            patch.object(server.time, "sleep"),
        ):
            with self.assertRaisesRegex(server.MarketplaceError, "tiempo de espera"):
                server._request_json("https://api.example.test/search")

        self.assertEqual(request_json.call_count, 2)

    def test_provider_message_removes_urls_controls_and_credentials(self) -> None:
        with patch.dict(os.environ, {"MELI_ACCESS_TOKEN": "private-token"}):
            sanitized = server._sanitize_provider_message(
                "bad\nhttps://internal.test/path Bearer private-token"
            )

        self.assertNotIn("\n", sanitized)
        self.assertNotIn("internal.test", sanitized)
        self.assertNotIn("private-token", sanitized)


class ApiHandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.http_server = ThreadingHTTPServer(("127.0.0.1", 0), server.SearchHandler)
        cls.thread = threading.Thread(target=cls.http_server.serve_forever)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.http_server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.http_server.shutdown()
        cls.http_server.server_close()
        cls.thread.join()

    def request(self, path: str, *, method: str = "GET", headers: dict[str, str] | None = None):
        request = Request(f"{self.base_url}{path}", method=method, headers=headers or {})
        return urlopen(request)

    def test_health_and_sources_endpoints(self) -> None:
        with self.request("/health") as response:
            self.assertEqual(json.loads(response.read()), {"status": "ok"})
        with patch.dict(os.environ, {}, clear=True):
            with self.request("/api/sources") as response:
                payload = json.loads(response.read())

        self.assertEqual(len(payload["sources"]), 5)
        self.assertEqual(
            {source["id"]: source["status"] for source in payload["sources"]}["amazon"],
            "unsupported",
        )

    def test_search_returns_http_200_with_only_unavailable_sources(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.request("/api/search?q=phone&sources=amazon,ebay,wallapop,fb-marketplace,mercadolibre") as response:
                payload = json.loads(response.read())

        self.assertEqual(payload["products"], [])
        self.assertEqual(payload["errors"], {})
        self.assertEqual(len(payload["unavailable"]), 3)
        self.assertEqual(len(payload["not_configured"]), 2)

    def test_preflight_returns_cors_headers_for_allowed_origin(self) -> None:
        with self.request(
            "/api/search",
            method="OPTIONS",
            headers={"Origin": "http://localhost:5173"},
        ) as response:
            headers = response.headers

        self.assertEqual(headers["Access-Control-Allow-Origin"], "http://localhost:5173")
        self.assertEqual(headers["Access-Control-Allow-Methods"], "GET, OPTIONS")
        self.assertEqual(headers["Access-Control-Allow-Headers"], "Content-Type")
        self.assertEqual(headers["Access-Control-Max-Age"], "600")

    def test_search_rejects_empty_control_query_and_too_many_sources(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as empty:
            self.request("/api/search?q=%00%09&sources=ebay")
        self.assertEqual(empty.exception.code, 400)
        empty.exception.close()

        with patch.object(server, "MAX_SOURCE_COUNT", 1):
            with self.assertRaises(urllib.error.HTTPError) as too_many:
                self.request("/api/search?q=phone&sources=ebay,mercadolibre")
        self.assertEqual(too_many.exception.code, 400)
        too_many.exception.close()


if __name__ == "__main__":
    unittest.main()
