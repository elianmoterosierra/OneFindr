from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


SOURCE_NAMES = {
    "amazon": "Amazon",
    "ebay": "eBay",
    "wallapop": "Wallapop",
    "fb-marketplace": "Facebook Marketplace",
    "mercadolibre": "MercadoLibre",
}
SOURCE_COLORS = {
    "amazon": "#d97706",
    "ebay": "#2563eb",
    "wallapop": "#059669",
    "fb-marketplace": "#4f46e5",
    "mercadolibre": "#eab308",
}
UNAVAILABLE_SOURCES = {
    "amazon": "Amazon requiere acceso a Product Advertising API y credenciales de afiliado.",
    "wallapop": "Wallapop no ofrece una API pública de búsqueda para este uso.",
    "fb-marketplace": "Facebook Marketplace requiere inicio de sesión y no ofrece una API pública de búsqueda.",
}
MAX_QUERY_LENGTH = 200
MAX_RESULTS_PER_SOURCE = 10
TIMEOUT_SECONDS = 12


class MarketplaceError(Exception):
    pass


def _request_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> dict[str, Any]:
    request_headers = {"Accept": "application/json", "User-Agent": "OneFindr/1.0"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        response_body = error.read(8192)
        try:
            error_payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            error_payload = {}
        provider_message = ""
        if isinstance(error_payload, dict):
            provider_message = error_payload.get("message") or error_payload.get("error") or ""
        provider_message = (
            provider_message[:160]
            if isinstance(provider_message, str)
            else ""
        )
        if urllib.parse.urlparse(url).hostname == "api.mercadolibre.com" and error.code == 403:
            message = (
                "MercadoLibre rechazó el acceso (HTTP 403). Verifica que "
                "MELI_ACCESS_TOKEN sea un token OAuth válido y tenga permisos "
                "para el sitio configurado."
            )
        else:
            detail = f" ({provider_message})" if provider_message else ""
            message = f"La plataforma respondió con HTTP {error.code}{detail}."
        raise MarketplaceError(message) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise MarketplaceError("No se pudo conectar con la plataforma.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MarketplaceError("La plataforma devolvió una respuesta no válida.") from error
    if not isinstance(payload, dict):
        raise MarketplaceError("La plataforma devolvió un formato de respuesta no válido.")
    return payload


def _marketplace_headers() -> dict[str, str]:
    token = os.environ.get("MELI_ACCESS_TOKEN", "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


def _money(value: Any) -> float | None:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    return amount if amount >= 0 else None


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _http_image(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        return ""
    return value if parsed.scheme in {"http", "https"} else ""


def _product(
    *,
    source: str,
    item_id: str,
    title: Any,
    description: Any,
    image: Any,
    price: Any,
    currency: Any,
    url: Any,
    condition: Any = "",
    location: Any = "",
    delivery: Any = "",
    old_price: Any = None,
) -> dict[str, Any] | None:
    amount = _money(price)
    product_url = url if isinstance(url, str) else ""
    if amount is None or not isinstance(title, str) or not title.strip():
        return None
    try:
        url_scheme = urllib.parse.urlparse(product_url).scheme
    except ValueError:
        url_scheme = ""
    if url_scheme not in {"http", "https"}:
        product_url = ""
    original_amount = _money(old_price)
    saving = ""
    if original_amount is not None and original_amount > amount:
        saving = f"Ahorra {original_amount - amount:.2f}"
    product = {
        "id": f"{source}:{item_id}",
        "source": source,
        "image": _http_image(image),
        "store": SOURCE_NAMES[source],
        "storeIcon": "storefront",
        "storeColor": SOURCE_COLORS[source],
        "url": product_url,
        "badge": "",
        "state": condition.strip() if isinstance(condition, str) and condition.strip() else "Estado no indicado",
        "distance": location.strip() if isinstance(location, str) and location.strip() else "Ubicación no indicada",
        "title": title.strip(),
        "description": description.strip() if isinstance(description, str) and description.strip() else "El vendedor no publicó una descripción.",
        "price": amount,
        "currency": currency if isinstance(currency, str) and len(currency) == 3 else "USD",
        "saving": saving,
        "delivery": delivery.strip() if isinstance(delivery, str) and delivery.strip() else "Entrega no especificada",
    }
    if original_amount is not None:
        product["oldPrice"] = original_amount
    return product


def _fetch_mercadolibre_product(
    summary: dict[str, Any], headers: dict[str, str]
) -> tuple[dict[str, Any] | None, bool]:
    item_id = summary.get("id")
    if not isinstance(item_id, str):
        return None, False
    encoded_id = urllib.parse.quote(item_id, safe="")
    detail: dict[str, Any] = {}
    description = ""
    incomplete = False
    try:
        detail = _request_json(
            f"https://api.mercadolibre.com/items/{encoded_id}",
            headers=headers,
        )
        description_data = _request_json(
            f"https://api.mercadolibre.com/items/{encoded_id}/description",
            headers=headers,
        )
        description = description_data.get("plain_text") or description_data.get("text") or ""
    except MarketplaceError:
        incomplete = True

    pictures = detail.get("pictures") or []
    image = ""
    if isinstance(pictures, list) and pictures and isinstance(pictures[0], dict):
        image = pictures[0].get("secure_url") or pictures[0].get("url") or ""
    image = image or detail.get("secure_thumbnail") or detail.get("thumbnail") or summary.get("thumbnail")
    address = _mapping(detail.get("seller_address") or summary.get("address"))
    location_parts = [
        _mapping(address.get("city")).get("name"),
        _mapping(address.get("state")).get("name"),
    ]
    shipping = _mapping(detail.get("shipping") or summary.get("shipping"))
    delivery = "Envío gratis" if shipping.get("free_shipping") else ""
    return (
        _product(
            source="mercadolibre",
            item_id=item_id,
            title=detail.get("title") or summary.get("title"),
            description=description,
            image=image,
            price=detail.get("price", summary.get("price")),
            currency=detail.get("currency_id") or summary.get("currency_id"),
            url=detail.get("permalink") or summary.get("permalink"),
            condition=detail.get("condition") or summary.get("condition"),
            location=", ".join(
                part for part in location_parts if isinstance(part, str) and part
            ),
            delivery=delivery,
            old_price=detail.get("original_price"),
        ),
        incomplete,
    )


def search_mercadolibre(query: str) -> tuple[list[dict[str, Any]], list[str]]:
    if not os.environ.get("MELI_ACCESS_TOKEN", "").strip():
        raise MarketplaceError(
            "MercadoLibre requiere un token OAuth. Configura MELI_ACCESS_TOKEN; "
            "la búsqueda pública responde HTTP 403."
        )
    site_id = os.environ.get("MELI_SITE_ID", "MLA").strip().upper()
    encoded_query = urllib.parse.urlencode(
        {"q": query, "limit": MAX_RESULTS_PER_SOURCE}
    )
    headers = _marketplace_headers()
    response = _request_json(
        f"https://api.mercadolibre.com/sites/{urllib.parse.quote(site_id, safe='')}/search?{encoded_query}",
        headers=headers,
    )
    summaries = response.get("results", [])
    if not isinstance(summaries, list):
        raise MarketplaceError("MercadoLibre devolvió resultados no válidos.")

    products: list[dict[str, Any]] = []
    incomplete_count = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(_fetch_mercadolibre_product, item, headers)
            for item in summaries[:MAX_RESULTS_PER_SOURCE]
            if isinstance(item, dict)
        ]
        for future in futures:
            product, incomplete = future.result()
            if product:
                products.append(product)
            incomplete_count += int(incomplete)
    warnings = []
    if incomplete_count:
        warnings.append(
            f"MercadoLibre: no se pudo recuperar el detalle completo de "
            f"{incomplete_count} producto(s)."
        )
    return products, warnings


def _ebay_access_token() -> str:
    client_id = os.environ.get("EBAY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("EBAY_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise MarketplaceError(
            "eBay necesita EBAY_CLIENT_ID y EBAY_CLIENT_SECRET de su API oficial."
        )
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    payload = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }
    ).encode()
    token_response = _request_json(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=payload,
    )
    token = token_response.get("access_token")
    if not isinstance(token, str) or not token:
        raise MarketplaceError("eBay no devolvió un token de acceso válido.")
    return token


def _fetch_ebay_product(
    summary: dict[str, Any], token: str, marketplace_id: str
) -> tuple[dict[str, Any] | None, bool]:
    item_id = summary.get("itemId")
    if not isinstance(item_id, str):
        return None, False
    encoded_id = urllib.parse.quote(item_id, safe="")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
    }
    incomplete = False
    detail = {}
    try:
        detail = _request_json(
            f"https://api.ebay.com/buy/browse/v1/item/{encoded_id}",
            headers=headers,
        )
    except MarketplaceError:
        incomplete = True
    image_data = detail.get("image") or summary.get("image") or {}
    shipping_options = detail.get("shippingOptions") or summary.get("shippingOptions") or []
    shipping = ""
    if isinstance(shipping_options, list) and shipping_options and isinstance(shipping_options[0], dict):
        shipping_cost = _mapping(shipping_options[0].get("shippingCost"))
        if _money(shipping_cost.get("value")) == 0:
            shipping = "Envío gratis"
        elif shipping_cost.get("value"):
            shipping = f"Envío {shipping_cost['value']} {shipping_cost.get('currency', '')}".strip()
    item_location = _mapping(detail.get("itemLocation") or summary.get("itemLocation"))
    location = ", ".join(
        value
        for value in (item_location.get("city"), item_location.get("stateOrProvince"))
        if isinstance(value, str) and value
    )
    price = _mapping(detail.get("price") or summary.get("price"))
    return (
        _product(
            source="ebay",
            item_id=item_id,
            title=detail.get("title") or summary.get("title"),
            description=detail.get("shortDescription") or detail.get("description") or "",
            image=image_data.get("imageUrl") if isinstance(image_data, dict) else "",
            price=price.get("value"),
            currency=price.get("currency"),
            url=detail.get("itemWebUrl") or summary.get("itemWebUrl"),
            condition=detail.get("condition") or summary.get("condition"),
            location=location,
            delivery=shipping,
        ),
        incomplete,
    )


def search_ebay(query: str) -> tuple[list[dict[str, Any]], list[str]]:
    token = _ebay_access_token()
    marketplace_id = os.environ.get("EBAY_MARKETPLACE_ID", "EBAY_US").strip().upper()
    search_url = "https://api.ebay.com/buy/browse/v1/item_summary/search?" + urllib.parse.urlencode(
        {"q": query, "limit": MAX_RESULTS_PER_SOURCE}
    )
    response = _request_json(
        search_url,
        headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
        },
    )
    summaries = response.get("itemSummaries", [])
    if not isinstance(summaries, list):
        raise MarketplaceError("eBay devolvió resultados no válidos.")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(_fetch_ebay_product, item, token, marketplace_id)
            for item in summaries[:MAX_RESULTS_PER_SOURCE]
            if isinstance(item, dict)
        ]
        fetched = [future.result() for future in futures]
    products = [product for product, _ in fetched if product]
    incomplete_count = sum(int(incomplete) for _, incomplete in fetched)
    warnings = []
    if incomplete_count:
        warnings.append(
            f"eBay: no se pudo recuperar el detalle completo de "
            f"{incomplete_count} producto(s)."
        )
    return products, warnings


def search_products(query: str, sources: list[str]) -> dict[str, Any]:
    products: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    warnings: list[str] = []
    for source in sources:
        if source in UNAVAILABLE_SOURCES:
            errors[source] = UNAVAILABLE_SOURCES[source]
            continue
        try:
            if source == "mercadolibre":
                source_products, source_warnings = search_mercadolibre(query)
            elif source == "ebay":
                source_products, source_warnings = search_ebay(query)
            else:
                errors[source] = "La plataforma solicitada no es compatible."
                continue
            products.extend(source_products)
            warnings.extend(source_warnings)
        except MarketplaceError as error:
            errors[source] = f"{SOURCE_NAMES[source]}: {error}"
    return {"products": products, "errors": errors, "warnings": warnings}


class SearchHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        allowed_origins = {
            origin.strip()
            for origin in os.environ.get(
                "SCRAP_CORS_ORIGINS", "http://localhost:5173,http://localhost:4173"
            ).split(",")
            if origin.strip()
        }
        origin = self.headers.get("Origin", "")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path != "/api/search":
            self._send_json(404, {"error": "Ruta no encontrada."})
            return
        params = urllib.parse.parse_qs(parsed_url.query)
        query = params.get("q", [""])[0].strip()
        sources = list(dict.fromkeys(params.get("sources", [""])[0].split(",")))
        sources = [source for source in sources if source]
        if not query:
            self._send_json(400, {"error": "El parámetro q es obligatorio."})
            return
        if len(query) > MAX_QUERY_LENGTH:
            self._send_json(400, {"error": f"La búsqueda no puede superar {MAX_QUERY_LENGTH} caracteres."})
            return
        if not sources or any(source not in SOURCE_NAMES for source in sources):
            self._send_json(400, {"error": "Selecciona al menos una plataforma válida."})
            return
        self._send_json(200, search_products(query, sources))

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    host = os.environ.get("SCRAP_HOST", "127.0.0.1")
    port = int(os.environ.get("SCRAP_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), SearchHandler)
    print(f"OneFindr scraper disponible en http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando el scraper...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
