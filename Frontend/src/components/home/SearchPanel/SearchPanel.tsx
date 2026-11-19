import type { FormEvent } from 'react'
import { Icon } from '../../Icon/Icon'
import './SearchPanel.css'
import { PlatformChip } from '../PlatformChip/PlatformChip'
import { useSources } from '../../../store/useSource'
import type { Source } from '../../../types'


type SearchPanelProps = {
  query: string
  onQueryChange: (value: string) => void
  onSubmit: () => void

  error: string
}


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

function SearchChips({ sources }: { sources: Source[] }) {
  return (
    <div className="search-chips">
      {sources.map((source) => (
        <PlatformChip
          key={source.name}
          sourceKey={source.key}
          name={source.name}
          active={source.active}


        />
      ))}
    </div>
  )
}

export function SearchPanel({
  query,
  onQueryChange,
  onSubmit,
  error,
}: SearchPanelProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit()
  }

  const sources = useSources((state) => state.sources)


  return (
    <section className="search-card" aria-label="Buscador de productos">
      <SearchInput value={query} onChange={onQueryChange} onSubmit={handleSubmit} />
      <h3 className="platforms-label" >Plataformas activas</h3>
      <SearchChips sources={sources} />
      {error && <p style={{ color: 'red', justifyContent: 'center' }}>{error}</p>}
    </section>
  )
}
