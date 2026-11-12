import { useMemo } from 'react'
import type { Product } from '../types'
import { filterInput } from '../utils/filterProducts'


export function useFilterProducts(query: string, sources: string[], products: Product[]) {
    return useMemo(() => filterInput(query, sources, products), [query, sources, products])

}