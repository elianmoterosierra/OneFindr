from __future__ import annotations

import base64
import copy
import datetime as dt
import email.utils
import json
import logging
import os
import re
import socket
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


SOURCE_NAMES: dict[str, str] = {
    "amazon": "Amazon",
    "ebay": "eBay",
    "wallapop": "Wallapop",
    "fb-marketplace": "Facebook Marketplace",
    "mercadolibre": "MercadoLibre",
}
SOURCE_ORDER = tuple(SOURCE_NAMES)
SOURCE_COLORS: dict[str, str] = {
    "amazon": "#d97706",
    "ebay": "#2563eb",
    "wallapop": "#059669",
    "fb-marketplace": "#4f46e5",
    "mercadolibre": "#eab308",
}
UNAVAILABLE_SOURCES: dict[str, str] = {
    "amazon": "Product Advertising API todavía no está implementada.",
    "wallapop": "Wallapop no ofrece una API pública de búsqueda para este uso.",
    "fb-marketplace": "Facebook Marketplace requiere inicio de sesión y no ofrece una API pública de búsqueda.",
}
MAX_QUERY_LENGTH = 200
MAX_RESULTS_PER_SOURCE = 10
MAX_SOURCE_COUNT = len(SOURCE_ORDER)
TIMEOUT_SECONDS = 12
DEFAULT_CACHE_TTL_SECONDS = 90.0
RETRY_BACKOFF_SECONDS = 0.25
_logger = logging.getLogger("onefindr.scrap")

_cache_lock = threading.Lock()
_search_cache: dict[tuple[str, str, bool], tuple[float, list[dict[str, Any]], list[str]]] = {}
_ebay_token_lock = threading.Lock()
_ebay_token_cache: tuple[str, float] | None = None


class MarketplaceError(Exception):
    """A provider or marketplace response could not be used."""


def _load_dotenv(path: Path | None = None) -> None:
    """Load simple KEY=VALUE pairs without replacing existing environment values."""
    dotenv_path = path or Path(__file__).with_name(".env")
    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].lstrip()
        key, separator, value = stripped.partition("=")
        key = key.strip()
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].rstrip()
        os.environ.setdefault(key, value)


def _source_message(source: str, message: str) -> str:
    """Format all user-visible marketplace messages consistently."""
    name = SOURCE_NAMES[source]
    prefix = f"{name}:"
    clean_message = message.strip()
    if clean_message.casefold().startswith(prefix.casefold()):
        clean_message = clean_message[len(prefix):].strip()
    return f"{prefix} {clean_message}"


def _missing_credentials(source: str) -> list[str]:
    required = {
        "ebay": ("EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"),
        "mercadolibre": ("MELI_ACCESS_TOKEN",),
    }.get(source, ())
    return [name for name in required if not os.environ.get(name, "").strip()]


def _source_status(source: str) -> tuple[str, str]:
    """Return a source's current availability state and explanation."""
    if source in UNAVAILABLE_SOURCES:
        return "unsupported", _source_message(source, UNAVAILABLE_SOURCES[source])
    missing = _missing_credentials(source)
    if missing:
        variables = ", ".join(missing)
        return "not_configured", _source_message(
            source, f"Falta configurar: {variables}."
        )
    return "available", ""


def get_sources() -> list[dict[str, str]]:
    """Describe support and credential state for every marketplace."""
    return [
        {
            "id": source,
            "name": SOURCE_NAMES[source],
            "status": status,
            "reason": reason,
        }
        for source in SOURCE_ORDER
        for status, reason in (_source_status(source),)
    ]


def _sanitize_provider_message(message: Any) -> str:
    """Remove control characters, URLs, and likely credentials from provider text."""
    if not isinstance(message, str):
        return ""
    sanitized = "".join(
        character for character in message if not unicodedata.category(character).startswith("C")
    )
    sanitized = re.sub(r"https?://\S+", "[URL]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(
        r"(?i)\bBearer\s+\S+", "Bearer [redactado]", sanitized
    )
    sanitized = re.sub(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*\b",
        "[token]",
        sanitized,
    )
    for variable in ("MELI_ACCESS_TOKEN", "EBAY_CLIENT_SECRET", "EBAY_CLIENT_ID"):
        secret = os.environ.get(variable, "").strip()
        if secret:
            sanitized = sanitized.replace(secret, "[redactado]")
    return sanitized[:160].strip()


def _retry_after_seconds(value: str | None) -> float | None:
    """Parse Retry-After as either seconds or an HTTP date."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=dt.timezone.utc)
        return max(0.0, (retry_at - dt.datetime.now(dt.timezone.utc)).total_seconds())


def _is_timeout(error: BaseException) -> bool:
    if isinstance(error, (TimeoutError, socket.timeout)):
        return True
    return (
        isinstance(error, urllib.error.URLError)
        and isinstance(error.reason, (TimeoutError, socket.timeout))
    )


def _http_error_message(url: str, error: urllib.error.HTTPError) -> str:
    """Translate provider HTTP errors without exposing response secrets."""
    try:
        payload = json.loads(error.read(8192).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {}
    finally:
        error.close()
    provider_message = (
        payload.get("message") or payload.get("error", "")
        if isinstance(payload, dict)
        else ""
    )
    detail = _sanitize_provider_message(provider_message)
    host = urllib.parse.urlparse(url).hostname or ""
    if host.endswith("ebay.com") and error.code in {401, 403}:
        return (
            f"Credenciales rechazadas (HTTP {error.code}). Verifica "
            "EBAY_CLIENT_ID, EBAY_CLIENT_SECRET y el acceso de la aplicación."
        )
    if host == "api.mercadolibre.com" and error.code in {401, 403}:
        return (
            f"Acceso rechazado (HTTP {error.code}). Verifica que MELI_ACCESS_TOKEN "
            "sea válido y tenga permisos para el sitio configurado."
        )
    suffix = f" ({detail})" if detail else ""
    return f"La plataforma respondió con HTTP {error.code}{suffix}."


def _request_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> dict[str, Any]:
    """Perform a JSON request with one retry for transient server failures."""
    request_headers = {"Accept": "application/json", "User-Agent": "OneFindr/1.0"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers)

    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            retryable = error.code == 429 or 500 <= error.code <= 599
            if retryable and attempt == 0:
                retry_after = error.headers.get("Retry-After") if error.headers else None
                delay = _retry_after_seconds(retry_after)
                error.close()
                time.sleep(delay if delay is not None else RETRY_BACKOFF_SECONDS)
                continue
            raise MarketplaceError(_http_error_message(url, error)) from error
        except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
            if _is_timeout(error) and attempt == 0:
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            if _is_timeout(error):
                raise MarketplaceError("Se agotó el tiempo de espera de la plataforma.") from error
            raise MarketplaceError("No se pudo conectar con la plataforma.") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise MarketplaceError("La plataforma devolvió una respuesta JSON no válida.") from error
        if not isinstance(payload, dict):
            raise MarketplaceError("La plataforma devolvió un formato de respuesta no válido.")
        return payload
    raise MarketplaceError("La plataforma no respondió después de reintentar.")


def _money(value: Any) -> float | None:
    """Convert a non-negative numeric marketplace value to a float."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    return amount if amount >= 0 else None


def _mapping(value: Any) -> dict[str, Any]:
    """Return a mapping or an empty mapping for malformed provider data."""
    return value if isinstance(value, dict) else {}


def _http_image(value: Any) -> str:
    """Allow only absolute HTTP(S) image URLs."""
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
    """Normalize one provider listing into the frontend product shape."""
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
    product_currency = (
        currency.upper()
        if isinstance(currency, str) and re.fullmatch(r"[A-Za-z]{3}", currency)
        else ""
    )
    saving = ""
    if original_amount is not None and original_amount > amount:
        saving = f"Ahorra {original_amount - amount:.2f}"
        if product_currency:
            saving = f"{saving} {product_currency}"
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
        "currency": product_currency,
        "saving": saving,
        "delivery": delivery.strip() if isinstance(delivery, str) and delivery.strip() else "Entrega no especificada",
    }
    if original_amount is not None:
        product["oldPrice"] = original_amount
    return product


def _meli_description(item_id: str, headers: dict[str, str]) -> str:
    """Fetch a listing description independently from its item details."""
    encoded_id = urllib.parse.quote(item_id, safe="")
    payload = _request_json(
        f"https://api.mercadolibre.com/items/{encoded_id}/description",
        headers=headers,
    )
    description = payload.get("plain_text") or payload.get("text") or ""
    return description if isinstance(description, str) else ""


def _meli_summary_needs_detail(summary: dict[str, Any]) -> bool:
    """Detect missing fields needed to render a useful listing card."""
    return not all(
        summary.get(field)
        for field in ("title", "price", "permalink", "thumbnail")
    )


def _fetch_mercadolibre_product(
    summary: dict[str, Any], headers: dict[str, str], detail: bool = False
) -> tuple[dict[str, Any] | None, list[str]]:
    """Map a MercadoLibre summary and optionally enrich it with listing details."""
    item_id = summary.get("id")
    if not isinstance(item_id, str):
        return None, []
    item = summary
    warnings: list[str] = []
    if detail or _meli_summary_needs_detail(summary):
        encoded_id = urllib.parse.quote(item_id, safe="")
        try:
            item = _request_json(
                f"https://api.mercadolibre.com/items/{encoded_id}",
                headers=headers,
            )
        except MarketplaceError as error:
            warnings.append(f"no se pudo recuperar el detalle: {error}")
            item = summary
        try:
            description = _meli_description(item_id, headers)
        except MarketplaceError as error:
            warnings.append(f"no se pudo recuperar la descripción: {error}")
            description = ""
    else:
        description = ""

    pictures = item.get("pictures") or []
    image = ""
    if isinstance(pictures, list) and pictures and isinstance(pictures[0], dict):
        image = pictures[0].get("secure_url") or pictures[0].get("url") or ""
    image = image or item.get("secure_thumbnail") or item.get("thumbnail")
    image = image or summary.get("thumbnail")
    address = _mapping(item.get("seller_address") or summary.get("address"))
    location_parts = [
        _mapping(address.get("city")).get("name"),
        _mapping(address.get("state")).get("name"),
    ]
    shipping = _mapping(item.get("shipping") or summary.get("shipping"))
    delivery = "Envío gratis" if shipping.get("free_shipping") else ""
    return (
        _product(
            source="mercadolibre",
            item_id=item_id,
            title=item.get("title") or summary.get("title"),
            description=description,
            image=image,
            price=item.get("price", summary.get("price")),
            currency=item.get("currency_id") or summary.get("currency_id"),
            url=item.get("permalink") or summary.get("permalink"),
            condition=item.get("condition") or summary.get("condition"),
            location=", ".join(
                part for part in location_parts if isinstance(part, str) and part
            ),
            delivery=delivery,
            old_price=item.get("original_price"),
        ),
        warnings,
    )


def _search_mercadolibre(
    query: str, detail: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    """Search MercadoLibre and optionally enrich its summaries."""
    site_id = os.environ.get("MELI_SITE_ID", "MLA").strip().upper()
    encoded_query = urllib.parse.urlencode({"q": query, "limit": MAX_RESULTS_PER_SOURCE})
    headers = {"Authorization": f"Bearer {os.environ['MELI_ACCESS_TOKEN'].strip()}"}
    response = _request_json(
        f"https://api.mercadolibre.com/sites/{urllib.parse.quote(site_id, safe='')}/search?{encoded_query}",
        headers=headers,
    )
    summaries = response.get("results", [])
    if not isinstance(summaries, list):
        raise MarketplaceError("La plataforma devolvió resultados no válidos.")

    products: list[dict[str, Any]] = []
    warnings: list[str] = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(_fetch_mercadolibre_product, item, headers, detail)
            for item in summaries[:MAX_RESULTS_PER_SOURCE]
            if isinstance(item, dict)
        ]
        for future in futures:
            product, product_warnings = future.result()
            if product:
                products.append(product)
            warnings.extend(product_warnings)
    return products, warnings


def _reset_ebay_token_cache() -> None:
    """Clear the eBay token cache; intended for tests and configuration reloads."""
    global _ebay_token_cache
    with _ebay_token_lock:
        _ebay_token_cache = None


def _ebay_access_token() -> str:
    """Return a cached eBay application token or request a fresh one."""
    global _ebay_token_cache
    with _ebay_token_lock:
        now = time.monotonic()
        if _ebay_token_cache and _ebay_token_cache[1] > now:
            return _ebay_token_cache[0]

        client_id = os.environ["EBAY_CLIENT_ID"].strip()
        client_secret = os.environ["EBAY_CLIENT_SECRET"].strip()
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
        try:
            lifetime = max(0.0, float(token_response.get("expires_in", 0)))
        except (TypeError, ValueError):
            lifetime = 0.0
        _ebay_token_cache = (token, time.monotonic() + max(0.0, lifetime - 60.0))
        return token


def _fetch_ebay_product(
    summary: dict[str, Any],
    token: str,
    marketplace_id: str,
    detail: bool = False,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Map an eBay item summary and optionally fetch full listing details."""
    item_id = summary.get("itemId")
    if not isinstance(item_id, str):
        return None, []
    item = summary
    warnings: list[str] = []
    needs_detail = not all(
        summary.get(field)
        for field in ("title", "price", "itemWebUrl", "image")
    )
    if detail or needs_detail:
        encoded_id = urllib.parse.quote(item_id, safe="")
        try:
            item = _request_json(
                f"https://api.ebay.com/buy/browse/v1/item/{encoded_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
                },
            )
        except MarketplaceError as error:
            warnings.append(f"no se pudo recuperar el detalle: {error}")
            item = summary

    image = _mapping(item.get("image") or summary.get("image")).get("imageUrl")
    shipping_options = item.get("shippingOptions") or summary.get("shippingOptions") or []
    shipping = ""
    if isinstance(shipping_options, list) and shipping_options:
        shipping_cost = _mapping(_mapping(shipping_options[0]).get("shippingCost"))
        if _money(shipping_cost.get("value")) == 0:
            shipping = "Envío gratis"
        elif shipping_cost.get("value"):
            shipping = (
                f"Envío {shipping_cost['value']} "
                f"{shipping_cost.get('currency', '')}"
            ).strip()
    item_location = _mapping(item.get("itemLocation") or summary.get("itemLocation"))
    location = ", ".join(
        value
        for value in (item_location.get("city"), item_location.get("stateOrProvince"))
        if isinstance(value, str) and value
    )
    price = _mapping(item.get("price") or summary.get("price"))
    return (
        _product(
            source="ebay",
            item_id=item_id,
            title=item.get("title") or summary.get("title"),
            description=item.get("shortDescription") or item.get("description") or "",
            image=image,
            price=price.get("value"),
            currency=price.get("currency"),
            url=item.get("itemWebUrl") or summary.get("itemWebUrl"),
            condition=item.get("condition") or summary.get("condition"),
            location=location,
            delivery=shipping,
        ),
        warnings,
    )


def _search_ebay(query: str, detail: bool) -> tuple[list[dict[str, Any]], list[str]]:
    """Search eBay's Browse API and optionally enrich listing summaries."""
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
        raise MarketplaceError("La plataforma devolvió resultados no válidos.")

    products: list[dict[str, Any]] = []
    warnings: list[str] = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(_fetch_ebay_product, item, token, marketplace_id, detail)
            for item in summaries[:MAX_RESULTS_PER_SOURCE]
            if isinstance(item, dict)
        ]
        for future in futures:
            product, product_warnings = future.result()
            if product:
                products.append(product)
            warnings.extend(product_warnings)
    return products, warnings


def _cache_ttl_seconds() -> float:
    """Read the search cache TTL from the environment."""
    try:
        return max(0.0, float(os.environ.get("SCRAP_CACHE_TTL_SECONDS", DEFAULT_CACHE_TTL_SECONDS)))
    except ValueError:
        return DEFAULT_CACHE_TTL_SECONDS


def _clear_search_cache() -> None:
    """Clear search results cache; intended for tests."""
    with _cache_lock:
        _search_cache.clear()


def _search_source_uncached(
    query: str, source: str, detail: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    """Dispatch one marketplace and normalize provider parsing failures."""
    try:
        if source == "mercadolibre":
            return _search_mercadolibre(query, detail)
        if source == "ebay":
            return _search_ebay(query, detail)
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise MarketplaceError("La plataforma devolvió una respuesta no válida.") from error
    raise MarketplaceError("La plataforma solicitada no es compatible.")


def _search_source(
    query: str, source: str, detail: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return cached results when fresh, otherwise query the provider."""
    ttl = _cache_ttl_seconds()
    if ttl <= 0:
        return _search_source_uncached(query, source, detail)
    key = (query, source, detail)
    now = time.monotonic()
    with _cache_lock:
        cached = _search_cache.get(key)
        if cached and cached[0] > now:
            return copy.deepcopy(cached[1]), list(cached[2])
        _search_cache.pop(key, None)

    products, warnings = _search_source_uncached(query, source, detail)
    with _cache_lock:
        if len(_search_cache) >= 512:
            expired_keys = [
                cache_key
                for cache_key, entry in _search_cache.items()
                if entry[0] <= time.monotonic()
            ]
            for cache_key in expired_keys:
                _search_cache.pop(cache_key, None)
            if len(_search_cache) >= 512:
                _search_cache.pop(next(iter(_search_cache)))
        _search_cache[key] = (
            time.monotonic() + ttl,
            copy.deepcopy(products),
            list(warnings),
        )
    return products, warnings


def search_products(
    query: str, sources: list[str], detail: bool = False
) -> dict[str, Any]:
    """Search configured marketplaces concurrently and preserve selected order."""
    products: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    warnings: list[str] = []
    unavailable: dict[str, str] = {}
    not_configured: dict[str, str] = {}
    futures: dict[str, Future[tuple[list[dict[str, Any]], list[str]]]] = {}

    for source in sources:
        status, reason = _source_status(source)
        if status == "unsupported":
            unavailable[source] = reason
        elif status == "not_configured":
            not_configured[source] = reason

    available_sources = [
        source for source in sources if _source_status(source)[0] == "available"
    ]
    if available_sources:
        with ThreadPoolExecutor(max_workers=min(5, len(available_sources))) as executor:
            futures = {
                source: executor.submit(_search_source, query, source, detail)
                for source in available_sources
            }
            for source in available_sources:
                try:
                    source_products, source_warnings = futures[source].result()
                except MarketplaceError as error:
                    errors[source] = _source_message(source, str(error))
                    continue
                products.extend(source_products)
                warnings.extend(_source_message(source, warning) for warning in source_warnings)

    return {
        "products": products,
        "errors": errors,
        "warnings": warnings,
        "unavailable": unavailable,
        "not_configured": not_configured,
    }


def _allowed_origins() -> set[str]:
    """Return the configured browser origins allowed to call the API."""
    return {
        origin.strip()
        for origin in os.environ.get(
            "SCRAP_CORS_ORIGINS",
            "http://localhost:5173,http://localhost:4173,"
            "http://127.0.0.1:5173,http://127.0.0.1:4173",
        ).split(",")
        if origin.strip()
    }


def _cors_headers(origin: str, preflight: bool = False) -> dict[str, str]:
    """Build CORS headers for normal and preflight responses."""
    headers: dict[str, str] = {}
    if origin and origin in _allowed_origins():
        headers["Access-Control-Allow-Origin"] = origin
        headers["Vary"] = "Origin"
    if preflight:
        headers.update(
            {
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Max-Age": "600",
            }
        )
    return headers


class SearchHandler(BaseHTTPRequestHandler):
    """HTTP API handler for search, source status, health, and CORS."""

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in _cors_headers(self.headers.get("Origin", "")).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        for name, value in _cors_headers(
            self.headers.get("Origin", ""), preflight=True
        ).items():
            self.send_header(name, value)
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if parsed_url.path == "/api/sources":
            self._send_json(200, {"sources": get_sources()})
            return
        if parsed_url.path != "/api/search":
            self._send_json(404, {"error": "Ruta no encontrada."})
            return

        params = urllib.parse.parse_qs(parsed_url.query)
        raw_query = params.get("q", [""])[0]
        query = "".join(
            character
            for character in raw_query
            if not unicodedata.category(character).startswith("C")
        ).strip()
        raw_sources = params.get("sources", [""])[0].split(",")
        sources = list(dict.fromkeys(source.strip() for source in raw_sources if source.strip()))
        if not query:
            self._send_json(400, {"error": "El parámetro q debe contener texto."})
            return
        if len(query) > MAX_QUERY_LENGTH:
            self._send_json(
                400,
                {"error": f"La búsqueda no puede superar {MAX_QUERY_LENGTH} caracteres."},
            )
            return
        if len(sources) > MAX_SOURCE_COUNT:
            self._send_json(
                400,
                {"error": f"Selecciona como máximo {MAX_SOURCE_COUNT} plataformas."},
            )
            return
        if not sources or any(source not in SOURCE_NAMES for source in sources):
            self._send_json(400, {"error": "Selecciona al menos una plataforma válida."})
            return
        detail = params.get("detail", ["0"])[0] == "1"
        self._send_json(200, search_products(query, sources, detail))

    def log_message(self, _format: str, *_args: Any) -> None:
        _logger.info(
            "%s %s %s",
            self.address_string(),
            self.command,
            urllib.parse.urlparse(self.path).path,
        )


def main() -> None:
    """Load local configuration and run the development HTTP server."""
    _load_dotenv()
    logging.basicConfig(
        level=os.environ.get("SCRAP_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    host = os.environ.get("SCRAP_HOST", "127.0.0.1")
    port = int(os.environ.get("SCRAP_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), SearchHandler)
    _logger.info("OneFindr scraper disponible en http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _logger.info("Cerrando el scraper")
    finally:
        server.server_close()


_load_dotenv()


if __name__ == "__main__":
    main()
