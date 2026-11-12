import { useState } from 'react'
import { Footer } from '../../components/Footer/Footer'
import { Header } from '../../components/Header/Header'
import { SearchPanel } from '../../components/home/SearchPanel/SearchPanel'
import '../../App.css'
import { useQueryParam } from '../../hooks/useQueryParams'
import { useSources } from '../../store/useSource'
import { useNavigate } from 'react-router'


export function Home() {



    const navigate = useNavigate()
    const { query: queryParam, setQuery } = useQueryParam()
    const sources = useSources((state) => state.sources)
    const activePlatforms = sources
        .filter((source) => source.active)
        .map((source) => source.key)
    const [query, setQueryInput] = useState(queryParam)
    const [error, setError] = useState<string>('')



    const submitSearch = () => {
        const cleanQuery = query.trim()
        if (!cleanQuery) return

        if (activePlatforms.length === 0) {
            setError('Por favor selecciona al menos una plataforma')
            return
        }
        else {
            setError('') // Limpia el error si todo es correcto
            setQuery(cleanQuery)
            navigate(`/resultados?q=${encodeURIComponent(cleanQuery)}&sources=${encodeURIComponent(activePlatforms.join(','))}`)
        }
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
                    onSubmit={submitSearch}
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

