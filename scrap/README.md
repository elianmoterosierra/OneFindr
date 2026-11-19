# Scraper de OneFindr

Este servicio Python entrega resultados reales a la aplicación React mediante `GET /api/search?q=...&sources=...`. Normaliza título, descripción, precio, moneda, imagen, estado, ubicación, envío y enlace de oferta.

## Inicio local

Desde la raíz del repositorio:

```powershell
Copy-Item .\scrap\.env.example .\scrap\.env
# Completa scrap/.env con las credenciales necesarias (ver guide.md).
python .\scrap\server.py
```

En otra terminal, desde `Frontend`:

```powershell
npm run dev
```

Vite reenvía `/api` al servicio en `http://127.0.0.1:8000`.

## Credenciales

Consulta la [guía de creación y configuración de credenciales](./guide.md).
El parser `.env` usa solo la biblioteca estándar y no sobrescribe variables de
entorno ya definidas.

## Fuentes

- **MercadoLibre:** API oficial con token OAuth en `MELI_ACCESS_TOKEN`; el sitio predeterminado es `MLA` y puede cambiarse con `MELI_SITE_ID` (por ejemplo `MDO` para República Dominicana).
- **eBay:** Browse API con `EBAY_CLIENT_ID` y `EBAY_CLIENT_SECRET`; marketplace predeterminado `EBAY_US`, configurable con `EBAY_MARKETPLACE_ID`.
- **Amazon, Wallapop y Facebook Marketplace:** se informan como no disponibles; no se usan sesiones privadas ni endpoints no documentados.

El servicio devuelve `products`, `errors` y `warnings`, además de `unavailable` y
`not_configured` para separar fuentes no soportadas y credenciales ausentes.
`GET /api/sources` muestra los estados de las cinco plataformas; `GET /health`
comprueba la disponibilidad. `GET /api/search` limita la consulta a 200
caracteres y 10 resultados por plataforma; `detail=1` solicita información
completa además del resumen, solo para esa búsqueda. Los resúmenes se
cachean 90 segundos por defecto (`SCRAP_CACHE_TTL_SECONDS`).

## Pruebas

```powershell
python -m unittest
```

## Despliegue

`ThreadingHTTPServer` es solo para desarrollo y pruebas: no incluye TLS,
gestión de procesos ni límites de recursos adecuados para producción. La
aplicación usa `BaseHTTPRequestHandler`, no es directamente una app WSGI o ASGI;
Gunicorn o Uvicorn necesitan un adaptador WSGI/ASGI explícito. Sin añadir
dependencias, deja el servicio escuchando solo en `127.0.0.1:8000` y colócalo
detrás de un proxy inverso que gestione TLS, límites y procesos. Por ejemplo,
una ubicación Nginx puede reenviar `/api/` y `/health` a ese upstream:

```powershell
$env:SCRAP_HOST = "127.0.0.1"
$env:SCRAP_PORT = "8000"
python .\scrap\server.py
```

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

location = /health {
    proxy_pass http://127.0.0.1:8000/health;
}
```
