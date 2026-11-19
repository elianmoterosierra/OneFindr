import { useEffect, useState } from 'react'
import { Footer } from '../../components/Footer/Footer'
import { Header } from '../../components/Header/Header'
import { ProductCard } from '../../components/resultOfSearch/ProductCard/ProductCard'
import { ResultsControls } from '../../components/resultOfSearch/ResultsControls/ResultsControls'
import { SearchToolbar } from '../../components/resultOfSearch/SearchToolbar/SearchToolbar'
import './resultOfSearch.css'
import { useQueryParam } from '../../hooks/useQueryParams'
import { useFilterProducts } from '../../hooks/useFilterProduct'
import type { Product } from '../../types'

type SearchResponse = {
  products: Product[]
  errors: Record<string, string>
  warnings: string[]
  unavailable: Record<string, string>
  not_configured: Record<string, string>
}

type SearchState = SearchResponse & {
  key: string
  requestError: string
}

export function ResultOfSearch() {
  const { query, setQuery, minPrice, maxPrice, sources } = useQueryParam()
  const selectedSources = sources.split(',').filter(Boolean)
  const searchKey = `${query}\u0000${sources}`
  const [searchState, setSearchState] = useState<SearchState | null>(null)
  const [retryingSources, setRetryingSources] = useState<string[]>([])
  const [retryErrors, setRetryErrors] = useState<Record<string, string>>({})
  const currentSearch = searchState?.key === searchKey ? searchState : null
  const loading = Boolean(query.trim() && selectedSources.length && !currentSearch)
  const sourceNames: Record<string, string> = {
    amazon: 'Amazon',
    ebay: 'eBay',
    wallapop: 'Wallapop',
    'fb-marketplace': 'Facebook Marketplace',
    mercadolibre: 'MercadoLibre',
  }

  useEffect(() => {
    if (!query.trim() || !sources.trim()) return

    const controller = new AbortController()
    const params = new URLSearchParams({ q: query, sources })

    fetch(`/api/search?${params.toString()}`, { signal: controller.signal })
      .then(async (response) => {
        const data = await response.json() as SearchResponse & { error?: string }
        if (!response.ok) throw new Error(data.error || 'No se pudo completar la búsqueda.')
        return data
      })
      .then((data) => {
        setSearchState({ ...data, key: searchKey, requestError: '' })
        setRetryErrors({})
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setSearchState({
          key: searchKey,
          products: [],
          errors: {},
          warnings: [],
          unavailable: {},
          not_configured: {},
          requestError: error instanceof Error ? error.message : 'Error inesperado al buscar productos.',
        })
      })

    return () => controller.abort()
  }, [query, sources, searchKey])

  const retrySource = async (source: string) => {
    setRetryingSources((current) => [...current, source])
    setRetryErrors((current) => {
      const next = { ...current }
      delete next[source]
      return next
    })
    try {
      const params = new URLSearchParams({ q: query, sources: source })
      const response = await fetch(`/api/search?${params.toString()}`)
      const data = await response.json() as SearchResponse & { error?: string }
      if (!response.ok) throw new Error(data.error || 'No se pudo reintentar la búsqueda.')
      setSearchState((current) => {
        if (!current || current.key !== searchKey) return current
        const errors = { ...current.errors }
        const unavailable = { ...current.unavailable }
        const notConfigured = { ...current.not_configured }
        delete errors[source]
        delete unavailable[source]
        delete notConfigured[source]
        Object.assign(errors, data.errors)
        Object.assign(unavailable, data.unavailable)
        Object.assign(notConfigured, data.not_configured)
        const sourceName = sourceNames[source]
        return {
          ...current,
          products: [
            ...current.products.filter((product) => product.source !== source),
            ...data.products,
          ],
          errors,
          unavailable,
          not_configured: notConfigured,
          warnings: [
            ...current.warnings.filter((warning) => !warning.startsWith(`${sourceName}:`)),
            ...data.warnings,
          ],
        }
      })
    } catch (error: unknown) {
      setRetryErrors((current) => ({
        ...current,
        [source]: error instanceof Error ? error.message : 'Error inesperado al reintentar.',
      }))
    } finally {
      setRetryingSources((current) => current.filter((item) => item !== source))
    }
  }

  const filteredProducts = useFilterProducts(
    query,
    selectedSources,
    currentSearch?.products ?? [],
    minPrice,
    maxPrice
  )

  return (
    <div className="results-page">
      <Header />

      <main className="results-main">
        <SearchToolbar
          key={`${query}:${sources}`}
          query={query}
          onClear={() => setQuery('')}
          onSearch={setQuery}
        />
        <ResultsControls />

        {loading && <p className="search-status" role="status">Buscando productos en las plataformas seleccionadas…</p>}
        {currentSearch?.requestError && <p className="search-status search-error" role="alert">{currentSearch.requestError}</p>}
        {Object.entries(currentSearch?.unavailable ?? {}).map(([source, message]) => (
          <p className="search-status search-info" role="status" key={source}>{message}</p>
        ))}
        {Object.entries(currentSearch?.not_configured ?? {}).map(([source, message]) => (
          <p className="search-status search-not-configured" role="status" key={source}>{message}</p>
        ))}
        {Object.entries(currentSearch?.errors ?? {}).map(([source, message]) => (
          <div className="search-status search-error" role="alert" key={source}>
            <span>{message}</span>
            {retryErrors[source] && <span>{retryErrors[source]}</span>}
            <button type="button" disabled={retryingSources.includes(source)} onClick={() => retrySource(source)}>
              {retryingSources.includes(source) ? 'Reintentando…' : `Reintentar ${sourceNames[source] ?? source}`}
            </button>
          </div>
        ))}
        {(currentSearch?.warnings ?? []).map((warning) => <p className="search-status" role="status" key={warning}>{warning}</p>)}
        <section className="products-grid" aria-label="Resultados de búsqueda">
          {filteredProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
          {!loading && !currentSearch?.requestError && filteredProducts.length === 0 && (
            <p className="no-results">No se encontraron productos que coincidan con tu búsqueda.</p>
          )}
        </section>

        {!loading && !currentSearch?.requestError && <p className="results-total">{filteredProducts.length} productos encontrados</p>}
      </main>

      <Footer />
    </div>
  )
}
