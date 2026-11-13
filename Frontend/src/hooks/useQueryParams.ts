import { useSearchParams } from "react-router";

export function useQueryParam() {
    const [searchParams, setSearchParams] = useSearchParams();
    const query = searchParams.get('q') ?? ''
    const sources = searchParams.get('sources') ?? ''

    const minParam = searchParams.get('min')
    const maxParam = searchParams.get('max')
    const minPrice = minParam ? parseFloat(minParam) : undefined
    const maxPrice = maxParam ? parseFloat(maxParam) : undefined

    const getParam = (name: string) => {
        return searchParams.get(name) ?? ''
    }

    const setParam = (name: string, value: string) => {
        setSearchParams((currentParams) => {
            const params = new URLSearchParams(currentParams)

            if (value) {
                params.set(name, value.trim())
            } else {
                params.delete(name)
            }

            return params
        })
    }

    const setQuery = (value: string) => {
        setParam('q', value)
    }

    const setSources = (value: string[]) => {
        setParam('sources', value.join(','))
    }

    const setMinPrice = (value?: number) => {
        setParam('min', value !== undefined ? String(value) : '')
    }

    const setMaxPrice = (value?: number) => {
        setParam('max', value !== undefined ? String(value) : '')
    }

    return {
        query,
        sources,
        minPrice,
        maxPrice,
        getParam,
        setParam,
        setQuery,
        setSources,
        setMaxPrice,
        setMinPrice,
    }
}
