import type { FormEvent } from 'react'
import { Icon } from '../../Icon/Icon'
import { PlatformChip } from '../PlatformChip/PlatformChip'
import './SearchPanel.css'

type SearchPanelProps = {
  query: string
  activePlatforms: string[]
  hasSearched: boolean
  onQueryChange: (value: string) => void
  onTogglePlatform: (platform: string) => void
  onSubmit: () => void
}

const PLATFORMS = [
  'Amazon',
  'FB Marketplace',
  'eBay',
  'MercadoLibre',
  'Wallapop',
]

const SEARCH_PLACEHOLDER = 'Ej. MacBook Pro M3, iPhone 15, zapatillas vintage...'

type SearchInputProps = {
  value: string
  onChange: (value: string) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

function SearchInput({ value, onChange, onSubmit }: SearchInputProps) {
  return (
    <form onSubmit={onSubmit} className="search-form">
      <div className="search-input-wrap">
        <Icon name="magnifying-glass" size={18} />
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={SEARCH_PLACEHOLDER}

          autoFocus
        />
        <button type="submit" className="enter-hint" aria-label="Buscar">
          <span>↵</span> Enter
        </button>
      </div>
    </form>
  )
}

type PlatformSelectorProps = {
  activePlatforms: string[]
  onToggle: (platform: string) => void
}

function PlatformSelector({ activePlatforms, onToggle }: PlatformSelectorProps) {
  const activeCount = activePlatforms.length

  return (
    <div className="platforms-section">
      <div className="platforms-heading">
        <span>Plataformas activas</span>
        <span className="active-status">
          <i /> {activeCount} activas
        </span>
      </div>

      <div className="platform-list">
        {PLATFORMS.map((platform) => (
          <PlatformChip
            key={platform}
            name={platform}
            checked={activePlatforms.includes(platform)}
            onChange={() => onToggle(platform)}
          />
        ))}
      </div>
    </div>
  )
}

type SearchFeedbackProps = {
  query: string
  activePlatformCount: number
}

function SearchFeedback({ query, activePlatformCount }: SearchFeedbackProps) {
  const platformLabel = activePlatformCount === 1 ? 'plataforma' : 'plataformas'
  const platformCount = activePlatformCount || 'ninguna'

  return (
    <p className="search-feedback">
      Buscando <strong>“{query.trim()}”</strong> en {platformCount} {platformLabel}...
    </p>
  )
}

export function SearchPanel({
  query,
  activePlatforms,
  hasSearched,
  onQueryChange,
  onTogglePlatform,
  onSubmit,
}: SearchPanelProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit()
  }

  return (
    <section className="search-card" aria-label="Buscador de productos">
      <SearchInput value={query} onChange={onQueryChange} onSubmit={handleSubmit} />
      <PlatformSelector activePlatforms={activePlatforms} onToggle={onTogglePlatform} />
      {hasSearched && (
        <SearchFeedback query={query} activePlatformCount={activePlatforms.length} />
      )}
    </section>
  )
}
