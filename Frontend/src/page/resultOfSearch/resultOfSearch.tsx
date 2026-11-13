import { Footer } from '../../components/Footer/Footer'
import { Header } from '../../components/Header/Header'
import { PriceInsight } from '../../components/resultOfSearch/PriceInsight/PriceInsight'
import { ProductCard } from '../../components/resultOfSearch/ProductCard/ProductCard'
import { ResultsControls } from '../../components/resultOfSearch/ResultsControls/ResultsControls'
import { SearchToolbar } from '../../components/resultOfSearch/SearchToolbar/SearchToolbar'
import { products } from './resultOfSearch.data'
import './resultOfSearch.css'
import { useQueryParam } from '../../hooks/useQueryParams'
import { useFilterProducts } from '../../hooks/useFilterProduct'

export function ResultOfSearch() {
  const { query, setQuery, minPrice, maxPrice, sources } = useQueryParam()

  const filteredProducts = useFilterProducts(
    query,
    sources ? sources.split(',') : [],
    products,
    minPrice,
    maxPrice
  )
  const TOTAL_RESULTS = products.length

  return (
    <div className="results-page">
      <Header />

      <main className="results-main">
        <SearchToolbar
          source={sources ? sources.split(',') : []}
          query={query}
          products={products}
          onClear={() => setQuery('')}
          onSearch={setQuery}
        />
        <ResultsControls />

        <section className="products-grid" aria-label="Resultados de búsqueda">
          {filteredProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
          {filteredProducts.length === 0 && (
            <p className="no-results">No se encontraron productos que coincidan con tu búsqueda.</p>
          )}
        </section>

        <PriceInsight />
        <LoadMoreResults totalCount={TOTAL_RESULTS} />
      </main>

      <Footer />
    </div>
  )
}

type LoadMoreResultsProps = {
  totalCount: number
}

function LoadMoreResults({ totalCount }: LoadMoreResultsProps) {
  return (
    <section className="load-more">
      <button type="button" disabled>Cargar más resultados <span>⌄</span></button>
      <p>Mostrando {products.length} de {totalCount} productos disponibles en tiempo real</p>
    </section>
  )
}
