type submitSearch = {
    query: string
    activePlatforms: []
}

export const submitSearch = ({ query, activePlatforms }: submitSearch) => {
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