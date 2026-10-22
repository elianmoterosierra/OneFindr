import { Footer } from '../../components/Footer/Footer'
import { Header } from '../../components/Header/Header'
import { PriceInsight } from '../../components/resultOfSearch/PriceInsight/PriceInsight'
import { ProductCard } from '../../components/resultOfSearch/ProductCard/ProductCard'
import { ResultsControls } from '../../components/resultOfSearch/ResultsControls/ResultsControls'
import { SearchToolbar } from '../../components/resultOfSearch/SearchToolbar/SearchToolbar'
import { products, sources } from './resultOfSearch.data'
import './resultOfSearch.css'
import { useQueryParam } from '../../hooks/useQueryParams'




export function ResultOfSearch() {

  const { query, setQuery } = useQueryParam();
  const TOTAL_RESULTS = 84

  return (
    <div className="results-page">
      <Header />

      <main className="results-main">
        <SearchToolbar query={query} sources={sources} onClear={() => setQuery('')} onSearch={setQuery} />
        <ResultsControls />

        <section className="products-grid" aria-label="Resultados de búsqueda">
          {products.map((product) => <ProductCard key={product.id} product={product} />)}
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
