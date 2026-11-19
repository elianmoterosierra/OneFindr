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
  const currentSearch = searchState?.key === searchKey ? searchState : null
  const loading = Boolean(query.trim() && selectedSources.length && !currentSearch)

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
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setSearchState({
          key: searchKey,
          products: [],
          errors: {},
          warnings: [],
          requestError: error instanceof Error ? error.message : 'Error inesperado al buscar productos.',
        })
      })

    return () => controller.abort()
  }, [query, sources, searchKey])

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
        {Object.entries(currentSearch?.errors ?? {}).map(([source, message]) => (
          <p className="search-status search-error" role="status" key={source}>{message}</p>
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
