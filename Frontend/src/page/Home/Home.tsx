import { useState } from 'react'
import { Footer } from '../../components/Footer/Footer'
import { Header } from '../../components/Header/Header'
import { SearchPanel } from '../../components/home/SearchPanel/SearchPanel'
import '../../App.css'
import { useQueryParam } from '../../hooks/useQueryParams'
import { useSources } from '../../store/useSource'
import { useSubmitSearch } from '../../hooks/useSubmitSearch'

export function Home() {
    const { query: queryParam } = useQueryParam()
    const sources = useSources((state) => state.sources)
    const activePlatforms = sources
        .filter((source) => source.active)
        .map((source) => source.key)
    const [query, setQueryInput] = useState(queryParam)

    const { submitSearch, error } = useSubmitSearch()

    const handleSubmit = () => {
        submitSearch(query, activePlatforms)
    }

    const chooseTrend = (trend: string) => {
        setQueryInput(trend)
    }

    return (
        <div className="app-shell">
            <Header />
            <main className="hero-section">
                <div className="hero-copy">
                    <p className="eyebrow">Una búsqueda, todos los marketplaces</p>
                    <h1>
                        Busca y <em>encuentra</em>
                    </h1>
                    <p className="hero-description">
                        Compara precios, descubre oportunidades y ahorra tiempo buscando en un solo lugar.
                    </p>
                </div>
                <SearchPanel
                    query={query}
                    onQueryChange={setQueryInput}
                    onSubmit={handleSubmit}
                    error={error}
                />
                <div className="trends" aria-label="Tendencias de búsqueda">
                    <span className="trends-label">Tendencias hoy:</span>
                    {['MacBook Air M2', 'Sony WH-1000XM5', 'iPad Mini 6'].map((trend) => (
                        <button
                            key={trend}
                            type="button"
                            className="trend"
                            onClick={() => chooseTrend(trend)}
                        >
                            {trend}
                        </button>
                    ))}
                </div>
            </main>
            <Footer />
        </div>
    )
}
