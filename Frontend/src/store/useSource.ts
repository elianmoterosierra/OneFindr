import { create } from "zustand";
import type { ApiSource, Source, SourceStore, SourceStatus } from "../types";

const INITIAL_SOURCE_STATUS: Source['status'] = 'loading'

function isSourceStatus(value: string): value is SourceStatus {
    return value === 'available' || value === 'not_configured' || value === 'unsupported'
}

export const useSources = create<SourceStore>((set, get) => ({
    sources: [
        { key: 'amazon', name: 'Amazon', count: 0, active: false, status: INITIAL_SOURCE_STATUS, reason: 'Consultando disponibilidad…' },
        { key: 'ebay', name: 'eBay', count: 0, active: false, status: INITIAL_SOURCE_STATUS, reason: 'Consultando disponibilidad…' },
        { key: 'wallapop', name: 'Wallapop', count: 0, active: false, status: INITIAL_SOURCE_STATUS, reason: 'Consultando disponibilidad…' },
        { key: 'fb-marketplace', name: 'Facebook Marketplace', count: 0, active: false, status: INITIAL_SOURCE_STATUS, reason: 'Consultando disponibilidad…' },
        { key: 'mercadolibre', name: 'MercadoLibre', count: 0, active: false, status: INITIAL_SOURCE_STATUS, reason: 'Consultando disponibilidad…' },
    ],

    loadSources: async () => {
        const response = await fetch('/api/sources')
        const payload = await response.json() as { sources?: ApiSource[]; error?: string }
        if (!response.ok) {
            throw new Error(payload.error || 'No se pudo consultar la disponibilidad de las plataformas.')
        }
        if (!Array.isArray(payload.sources)) {
            throw new Error('La respuesta de disponibilidad de plataformas no es válida.')
        }
        const apiSources = new Map(payload.sources.map((source) => [source.id, source]))
        for (const source of payload.sources) {
            if (!isSourceStatus(source.status)) {
                throw new Error('La respuesta contiene un estado de plataforma no válido.')
            }
        }
        set((state) => ({
            sources: state.sources.map((source) => {
                const apiSource = apiSources.get(source.key)
                if (!apiSource) return source
                return {
                    ...source,
                    name: apiSource.name,
                    status: apiSource.status,
                    reason: apiSource.reason,
                    active: apiSource.status === 'available' && source.active,
                }
            }),
        }))
    },

    getSources: (): Source[] => {
        return get().sources
    },
    getActiveSources: (): Source[] => {
        return get().sources.filter((source) => source.active)
    },
    toggleSource: (key: string) => {
        set((state) => ({
            sources: state.sources.map((source) =>
                source.key === key && source.status === 'available'
                    ? { ...source, active: !source.active }
                    : source
            ),
        }))
    },

}))