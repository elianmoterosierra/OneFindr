import { useState } from 'react'
import { Icon } from '../../Icon/Icon'
import './SearchToolbar.css'
import { useFilterProducts } from '../../../hooks/useFilterProduct'

import { useSources } from '../../../store/useSource'
import type { Product } from '../../../types'
import { useQueryParam } from '../../../hooks/useQueryParams'


type SearchToolbarProps = {
  source: string[]
  query: string
  products: Product[]
  onClear: () => void
  onSearch: (query: string) => void
}

export function SearchToolbar({ query, onClear, onSearch }: SearchToolbarProps) {
  const [searchValue, setSearchValue] = useState(query)
  const { sources } = useQueryParam()



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
          {sources.split(',').map((source: string) => (
            <span className={`source-pill active`} key={source}>
              <i />{source}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
