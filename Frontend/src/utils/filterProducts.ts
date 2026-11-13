import type { Product } from "../types"

function normalizeText(text: string) {
    return text
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim()
}

export function filterInput(
    query: string,
    sources: string[],
    products: Product[],
    minPrice?: number,
    maxPrice?: number
) {
    const normalizedQuery = normalizeText(query)
    const words = normalizedQuery.split(/\s+/).filter(Boolean)
    const sourcesFilter = sources.map((source) => normalizeText(source).replace(/-/g, ' '))

    return products.filter((product) => {
        const normalizedStore = normalizeText(product.store).replace(/-/g, ' ')
        const normalizedTitle = normalizeText(product.title)

        const matchQuery = words.length === 0 || words.every((word) => normalizedTitle.includes(word))
        const matchSource = sources.length === 0 || sourcesFilter.some((src) =>
            normalizedStore.includes(src) || src.includes(normalizedStore)
        )

        const matchMin = minPrice !== undefined && !isNaN(minPrice) ? product.price >= minPrice : true
        const matchMax = maxPrice !== undefined && !isNaN(maxPrice) ? product.price <= maxPrice : true
        const matchPrice = matchMin && matchMax

        return matchQuery && matchSource && matchPrice
    })
}
