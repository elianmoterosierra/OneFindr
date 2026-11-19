# Scraper de OneFindr

Este servicio Python entrega resultados reales a la aplicación React mediante `GET /api/search?q=...&sources=...`. Normaliza título, descripción, precio, moneda, imagen, estado, ubicación, envío y enlace de oferta.

## Inicio local

Desde la raíz del repositorio:

```powershell
python .\scrap\server.py
```

En otra terminal, desde `Frontend`:

```powershell
npm run dev
```

Vite reenvía `/api` al servicio en `http://127.0.0.1:8000`.

## Fuentes

- **MercadoLibre:** usa su API oficial y requiere un token OAuth en `MELI_ACCESS_TOKEN`; la búsqueda pública sin autenticar responde HTTP 403. El sitio predeterminado es `MLA`; puede cambiarse con `MELI_SITE_ID` (por ejemplo, `MLM` o `MLC`).
- **eBay:** usa Browse API. Configura `EBAY_CLIENT_ID` y `EBAY_CLIENT_SECRET` con credenciales de aplicación de eBay. El marketplace predeterminado es `EBAY_US`; puede cambiarse con `EBAY_MARKETPLACE_ID`.
- **Amazon, Wallapop y Facebook Marketplace:** no se extrae contenido sin acceso oficial disponible. El API devuelve el motivo por fuente; no usa sesiones privadas, endpoints no documentados ni técnicas para evadir controles de acceso.

El servicio no almacena búsquedas ni credenciales. Limita la búsqueda a 200 caracteres y 10 resultados por plataforma. Variables opcionales: `SCRAP_HOST`, `SCRAP_PORT` y `SCRAP_CORS_ORIGINS`.

## Pruebas

```powershell
python .\scrap\test_server.py
```
