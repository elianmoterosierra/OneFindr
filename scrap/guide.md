# Guía de credenciales de plataformas

Las credenciales se guardan localmente en `scrap/.env`. No las publiques ni las
envíes al frontend. Para empezar, copia el ejemplo desde la raíz del proyecto:

```powershell
Copy-Item .\scrap\.env.example .\scrap\.env
```

El servicio carga `scrap/.env` al arrancar y respeta las variables de entorno que
ya estén definidas.

## eBay Browse API

1. Crea una cuenta en [developer.ebay.com](https://developer.ebay.com/).
2. En **Application Keys**, genera un keyset de **Production**.
3. Copia el **App ID (Client ID)** en `EBAY_CLIENT_ID`.
4. Copia el **Cert ID (Client Secret)** en `EBAY_CLIENT_SECRET`.
5. Si buscas en otro marketplace, configura `EBAY_MARKETPLACE_ID` con su ID,
   por ejemplo `EBAY_US`.
6. Guarda `.env` y reinicia el scraper.

No uses las claves de Sandbox para consultar el Browse API de producción.

## MercadoLibre

1. Crea una aplicación en
   [developers.mercadolibre.com](https://developers.mercadolibre.com/).
2. Configura la URL de redirección de OAuth de la aplicación.
3. Completa el flujo OAuth autorizado para obtener un **access token** y asígnalo
   a `MELI_ACCESS_TOKEN`. No uses el client secret como access token.
4. Elige el sitio en `MELI_SITE_ID`: `MLA` para Argentina, `MDO` para República
   Dominicana, `MLM` para México, `MLC` para Chile, entre otros.
5. Guarda `.env` y reinicia el scraper cuando el token se renueve.

La API de búsqueda sin autenticar responde HTTP 403; sin token la fuente aparece
como `not_configured`.

## Amazon

Amazon requiere una cuenta de afiliado y acceso a **Product Advertising API**.
La integración todavía no está implementada, así que Amazon se informa como
`unsupported`; no introduzcas credenciales de Amazon esperando que habiliten la
búsqueda.

## Seguridad y operación

- `.env` está excluido de Git por `scrap/.gitignore`; comparte solo el archivo
  `.env.example`, que no contiene secretos.
- Rota de inmediato una credencial que se haya publicado por accidente.
- `SCRAP_CACHE_TTL_SECONDS` controla la caché de búsqueda (90 segundos por
  defecto); `0` desactiva esa caché.
- Para personalizar CORS, define `SCRAP_CORS_ORIGINS` como una lista de orígenes
  separados por comas.
