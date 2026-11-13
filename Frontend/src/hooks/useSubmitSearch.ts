import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useQueryParam } from './useQueryParams'

export function useSubmitSearch() {
    const navigate = useNavigate()
    const { setQuery, setMinPrice, setMaxPrice } = useQueryParam()
    const [error, setError] = useState<string>('')

    const submitSearch = (query: string, activePlatforms: string[] = [], min?: number, max?: number) => {
        const cleanQuery = query.trim()
        if (!cleanQuery) return false

        if (activePlatforms.length === 0) {
            setError('Por favor selecciona al menos una plataforma')
            return false
        }

        setError('')
        setQuery(cleanQuery)
        if (min !== undefined) setMinPrice(min)
        if (max !== undefined) setMaxPrice(max)

        const minPart = min !== undefined ? `&min=${min}` : ''
        const maxPart = max !== undefined ? `&max=${max}` : ''

        navigate(`/resultados?q=${encodeURIComponent(cleanQuery)}&sources=${encodeURIComponent(activePlatforms.join(','))}${minPart}${maxPart}`)
        return true
    }

    return { submitSearch, error, setError }
}
