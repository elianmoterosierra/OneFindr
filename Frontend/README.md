# OneFindr

OneFindr es una landing de búsqueda de productos desarrollada con React y TypeScript. Permite introducir una búsqueda, navegar a la página de resultados y filtrar productos por título y plataforma.

## Tecnologías

- React 19
- TypeScript
- Vite
- React Router
- CSS por componente
- Iconos personalizados mediante el componente `Icon`

## Requisitos

- Node.js
- npm

## Instalación

Desde la carpeta `Frontend`:

```bash
npm install
```

Para obtener resultados reales, inicia también el servicio Python descrito en [`../scrap/README.md`](../scrap/README.md). El servidor de desarrollo reenvía las peticiones `/api` a ese servicio.

## Comandos disponibles

```bash
# Inicia el servidor de desarrollo
npm run dev

# Comprueba los tipos y crea la versión de producción
npm run build

# Ejecuta ESLint
npm run lint

# Sirve localmente la versión compilada
npm run preview
```

## Funcionalidades

- Búsqueda de productos desde la página principal.
- Resultados en vivo de MercadoLibre y eBay mediante sus APIs oficiales.
- Mensajes claros cuando una plataforma no está disponible o necesita credenciales.
- Navegación a resultados mediante el parámetro `q` de la URL.
- Filtrado por título ignorando mayúsculas, minúsculas y acentos.
- Filtrado por plataformas activas.
- Componentes reutilizables para tarjetas, controles, buscadores y modales.
- Diseño responsive para diferentes tamaños de pantalla.

## Estructura del proyecto

```text
src/
├── assets/       # Recursos estáticos
├── components/   # Componentes reutilizables y sus estilos
├── hooks/        # Hooks personalizados
├── page/         # Vistas principales de la aplicación
├── utils/        # Funciones auxiliares, como los filtros
├── App.tsx       # Configuración de rutas
└── types.ts      # Tipos compartidos
```

## Rutas principales

- `/` — Página de inicio y buscador.
- `/resultados?q=...` — Resultados de la búsqueda.

## Organización de componentes

Cada componente se encuentra en su propia carpeta junto con su archivo CSS cuando necesita estilos específicos. La lógica de filtrado se mantiene separada en `utils` y los hooks personalizados en `hooks` para facilitar su reutilización y mantenimiento.

