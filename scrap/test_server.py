import json
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

from server import (
    MarketplaceError,
    SearchHandler,
    _fetch_ebay_product,
    _fetch_mercadolibre_product,
    _product,
    search_products,
)


class ProductMappingTests(unittest.TestCase):
    def test_product_contains_full_display_fields_and_safe_links(self):
        product = _product(
            source="mercadolibre",
            item_id="MLA123",
            title="  Cámara  ",
            description="Descripción completa",
            image="https://example.test/image.jpg",
            price="42.50",
            currency="ARS",
            url="https://example.test/item",
            condition="Nuevo",
            location="Buenos Aires",
            delivery="Envío gratis",
        )

        self.assertIsNotNone(product)
        self.assertEqual(product["id"], "mercadolibre:MLA123")
        self.assertEqual(product["title"], "Cámara")
        self.assertEqual(product["description"], "Descripción completa")
        self.assertEqual(product["image"], "https://example.test/image.jpg")
        self.assertEqual(product["price"], 42.5)
        self.assertEqual(product["currency"], "ARS")
        self.assertEqual(product["url"], "https://example.test/item")
        self.assertNotIn("oldPrice", product)

    def test_product_rejects_non_http_image_and_offer_urls(self):
        product = _product(
            source="ebay",
            item_id="item-1",
            title="Item",
            description="",
            image="javascript:alert(1)",
            price=10,
            currency="USD",
            url="javascript:alert(1)",
        )

        self.assertEqual(product["image"], "")
        self.assertEqual(product["url"], "")

    def test_product_without_valid_price_or_title_is_skipped(self):
        common = {
            "source": "ebay",
            "item_id": "item-1",
            "description": "",
            "image": "",
            "price": "not-a-price",
            "currency": "USD",
            "url": "",
        }
        self.assertIsNone(_product(title="Item", **common))
        common["price"] = 10
        self.assertIsNone(_product(title="  ", **common))


class SearchSourceTests(unittest.TestCase):
    def test_unavailable_platforms_are_reported_without_fake_results(self):
        result = search_products("laptop", ["amazon", "wallapop", "fb-marketplace"])

        self.assertEqual(result["products"], [])
        self.assertEqual(set(result["errors"]), {"amazon", "wallapop", "fb-marketplace"})
        self.assertEqual(result["warnings"], [])

    @patch("server.search_mercadolibre")
    def test_live_provider_results_and_warnings_are_combined(self, search_mercadolibre):
        product = {"id": "mercadolibre:MLA123"}
        search_mercadolibre.return_value = ([product], ["detalle parcial"])

        result = search_products("cámara", ["mercadolibre"])

        self.assertEqual(result["products"], [product])
        self.assertEqual(result["warnings"], ["detalle parcial"])
        self.assertEqual(result["errors"], {})

    @patch("server.search_ebay", side_effect=MarketplaceError("sin conexión"))
    def test_provider_errors_are_visible(self, _search_ebay):
        result = search_products("camera", ["ebay"])

        self.assertEqual(result["products"], [])
        self.assertEqual(result["errors"], {"ebay": "eBay: sin conexión"})

    @patch("server._request_json")
    def test_mercadolibre_mapping_includes_description_image_and_listing_url(self, request_json):
        request_json.side_effect = [
            {
                "title": "Cámara",
                "price": 120,
                "currency_id": "MXN",
                "permalink": "https://example.test/mercadolibre",
                "pictures": [{"secure_url": "https://example.test/camera.jpg"}],
                "condition": "new",
                "seller_address": {"city": {"name": "Ciudad de México"}},
                "shipping": {"free_shipping": True},
            },
            {"plain_text": "Descripción del vendedor"},
        ]

        product, incomplete = _fetch_mercadolibre_product(
            {"id": "MLM-123", "title": "Cámara"}, {}
        )

        self.assertFalse(incomplete)
        self.assertEqual(product["description"], "Descripción del vendedor")
        self.assertEqual(product["image"], "https://example.test/camera.jpg")
        self.assertEqual(product["url"], "https://example.test/mercadolibre")
        self.assertEqual(product["currency"], "MXN")

    @patch("server._request_json")
    def test_ebay_mapping_includes_description_image_and_offer_url(self, request_json):
        request_json.return_value = {
            "title": "Camera",
            "description": "Full listing description",
            "image": {"imageUrl": "https://example.test/camera.jpg"},
            "price": {"value": "89.99", "currency": "USD"},
            "itemWebUrl": "https://example.test/ebay",
            "condition": "Used",
            "itemLocation": {"city": "Austin", "stateOrProvince": "TX"},
            "shippingOptions": [{"shippingCost": {"value": "0.0"}}],
        }

        product, incomplete = _fetch_ebay_product(
            {"itemId": "v1|123", "title": "Camera"}, "token", "EBAY_US"
        )

        self.assertFalse(incomplete)
        self.assertEqual(product["description"], "Full listing description")
        self.assertEqual(product["image"], "https://example.test/camera.jpg")
        self.assertEqual(product["url"], "https://example.test/ebay")
        self.assertEqual(product["delivery"], "Envío gratis")


class SearchHandlerTests(unittest.TestCase):
    def test_api_validates_queries_and_reports_unavailable_sources(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), SearchHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}/api/search"
        try:
            with self.assertRaises(HTTPError) as response:
                urlopen(base_url + "?sources=ebay")
            self.assertEqual(response.exception.code, 400)
            response.exception.close()

            with urlopen(base_url + "?q=phone&sources=amazon") as response:
                payload = json.loads(response.read())
            self.assertEqual(payload["products"], [])
            self.assertIn("amazon", payload["errors"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
