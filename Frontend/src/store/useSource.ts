import { create } from "zustand";
import type { Source, SourceStore } from "../types";

export const useSources = create<SourceStore>((set, get) => ({
    sources: [
        { key: 'amazon', name: 'Amazon', count: 32, active: false },
        { key: 'ebay', name: 'eBay', count: 21, active: false },
        { key: 'wallapop', name: 'Wallapop', count: 19, active: false },
        { key: 'fb-marketplace', name: 'FB Marketplace', count: 12, active: false },
        { key: 'mercadolibre', name: 'MercadoLibre', count: 0, active: false },
    ],

    getSources: (): Source[] => {
        return get().sources
    },
    getActiveSources: (): Source[] => {
        return get().sources.filter((source) => source.active)
    },
    toggleSource: (key: string) => {
        set((state) => ({
            sources: state.sources.map((source) =>
                source.key === key
                    ? { ...source, active: !source.active }
                    : source
            ),
        }))
    },

}))