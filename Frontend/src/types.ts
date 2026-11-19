export type Product = {
    id: string;
    source: string;
    image: string;
    store: string;
    storeIcon: 'storefront' | 'notification' | 'arrow';
    storeColor: string;
    url: string;
    badge?: string;
    state: string;
    distance: string;
    title: string;
    description: string;
    price: number;
    currency: string;
    oldPrice?: number;
    saving?: string;
    delivery: string
}




export type Source = {
    key: string
    name: string
    count: number
    active: boolean
}

export type SourceStore = {
    sources: Source[]
    toggleSource: (name: string) => void
    getSources(): Source[]
    getActiveSources: () => Source[]
}