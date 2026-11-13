import { useMemo } from 'react'
import type { Product } from '../types'
import { filterInput } from '../utils/filterProducts'


export function useFilterProducts(query: string, sources: string[], products: Product[], minPrice?: number, maxPrice?: number) {
    return useMemo(() => filterInput(query, sources, products, minPrice, maxPrice), [query, sources, products, minPrice, maxPrice])

}