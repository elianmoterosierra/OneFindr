
import { useSearchParams } from "react-router";

export function useQueryParam() {
    const [searchParams, setSearchParams] = useSearchParams();
    const query = searchParams.get('q') ?? ''

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
    return {
        query,
        getParam,
        setParam,
        setQuery,

    }


}
