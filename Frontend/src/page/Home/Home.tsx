import { useState } from 'react'
import { Footer } from '../../components/Footer/Footer'
import { Header } from '../../components/Header/Header'
import { SearchPanel } from '../../components/home/SearchPanel/SearchPanel'
import '../../App.css'
import { useQueryParam } from '../../hooks/useQueryParams'
import { useNavigate } from 'react-router'


export function Home() {

    const navigate = useNavigate()
    const { query: queryParam, setQuery } = useQueryParam()
    const [query, setQueryInput] = useState(queryParam)

    const [activePlatforms, setActivePlatforms] = useState([
        'Amazon',
        'FB Marketplace',
        'eBay',
    ])


    const [hasSearched, setHasSearched] = useState(false);

    const togglePlatform = (platform: string) => {
        setActivePlatforms((current) => {
            if (current.includes(platform)) {
                return current.filter((item) => item !== platform)
            }

            return [...current, platform]
        })
    }

    const submitSearch = () => {
        const cleanQuery = query.trim()

        if (!cleanQuery) return


        setHasSearched(true)
        setQuery(cleanQuery)
        navigate(`/resultados?q=${encodeURIComponent(cleanQuery)}`)
    }



    const chooseTrend = (trend: string) => {
        setQuery(trend)
        setHasSearched(false)
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
                    activePlatforms={activePlatforms}
                    hasSearched={hasSearched}
                    onQueryChange={setQueryInput}
                    onTogglePlatform={togglePlatform}
                    onSubmit={submitSearch}
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

