import { useState } from 'react'
import { Icon } from '../../Icon/Icon'
import './SearchToolbar.css'

type Source = {
  name: string
  count: number
  active: boolean
}

type SearchToolbarProps = {
  query: string
  sources: Source[]
  onClear: () => void
  onSearch: (query: string) => void
}

export function SearchToolbar({ query, sources, onClear, onSearch }: SearchToolbarProps) {
  const [searchValue, setSearchValue] = useState(query)

  const handleSearch = () => {
    onSearch(searchValue)
  }

  const handleClear = () => {
    setSearchValue('')
    onClear()
  }

  return (
    <section className="results-search-toolbar">
      <div className="results-search-form">
        <Icon name="search" size={18} />
        <input
          value={searchValue}
          onChange={(event) => setSearchValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              handleSearch()
            }
          }}
          aria-label="Búsqueda actual"
        />
        <button type="button" className="clear-search" onClick={handleClear} aria-label="Borrar búsqueda">
          <Icon name="close" size={16} />
        </button>
        <button type="button" className="results-search-button" onClick={handleSearch}>Buscar</button>
      </div>

      <div className="source-summary">
        <div className="source-pills">
          <span className="source-label">Fuentes:</span>
          {sources.map((source) => (
            <span className={`source-pill ${source.active ? 'active' : ''}`} key={source.name}>
              <i />{source.name}<small>{source.count}</small>
            </span>
          ))}
        </div>

        <div className="results-count"><strong>84 resultados</strong><span>en 4 plataformas</span><b>•</b><span className="updated"><i />Actualizado hace 2m</span></div>
      </div>
    </section>
  )
}
