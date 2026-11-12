import { useState } from 'react'
import { Icon } from '../../Icon/Icon'
import { useQueryParam } from '../../../hooks/useQueryParams'
import { useSources } from '../../../store/useSource'
import './FilterModal.css'

type FilterModalProps = {
  open: boolean
  onClose: () => void
}

const PRODUCT_STATES = [
  'Todos',
  'Nuevo en caja',
  'Reacondicionado',
  'Segunda mano',
]

const INITIAL_STATE = 'Todos'
const INITIAL_MIN_PRICE = '1200'
const INITIAL_MAX_PRICE = '1900'

export function FilterModal({ open, onClose }: FilterModalProps) {

  const sourcesList = useSources((state) => state.sources)
  const toggleSource = useSources((state) => state.toggleSource)
  const { sources, setSources } = useQueryParam()


  const [state, setState] = useState(INITIAL_STATE)
  const [minPrice, setMinPrice] = useState(INITIAL_MIN_PRICE)
  const [maxPrice, setMaxPrice] = useState(INITIAL_MAX_PRICE)
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(
    sources ? sources.split(',') : []
  )

  if (!open) return null

  const clearFilters = () => {
    setState(INITIAL_STATE)
    setMinPrice(INITIAL_MIN_PRICE)
    setMaxPrice(INITIAL_MAX_PRICE)
  }
  const handleToggle = (key: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key]
    )
    toggleSource(key)
  }
  const handleApply = () => {
    setSources(selectedPlatforms) // Actualiza la URL (?sources=...) y refresca los resultados
    onClose()
  }

  return (
    <div
      className="advanced-filter-backdrop"
      role="presentation"
      onMouseDown={onClose}
    >
      <section
        className="advanced-filter-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="filter-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="advanced-filter-header">
          <div>
            <span className="filter-icon">
              <Icon name="tune" size={18} />
            </span>

            <div>
              <h2 id="filter-title">Filtros avanzados</h2>
              <p>Ajusta los parámetros para refinar resultados</p>
            </div>
          </div>

          <div>
            <button
              type="button"
              className="clear-filter-button"
              onClick={clearFilters}
            >
              Limpiar todo
            </button>

            <button
              type="button"
              className="close-filter-button"
              onClick={onClose}
              aria-label="Cerrar filtros"
            >
              <Icon name="close" size={20} />
            </button>
          </div>
        </header>

        <div className="advanced-filter-content">
          <fieldset>
            <legend>Estado del producto</legend>

            <div className="state-options">
              {PRODUCT_STATES.map((option) => (
                <button
                  key={option}
                  type="button"
                  className={state === option ? 'selected' : ''}
                  onClick={() => setState(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend>Rango de precio</legend>

            <div className="price-inputs">
              <label>
                Mínimo
                <input
                  type="number"
                  value={minPrice}
                  onChange={(event) => setMinPrice(event.target.value)}
                />
              </label>

              <label>
                Máximo
                <input
                  type="number"
                  value={maxPrice}
                  onChange={(event) => setMaxPrice(event.target.value)}
                />
              </label>
            </div>

            <input
              className="range-input"
              type="range"
              min="800"
              max="2500"
              value={maxPrice}
              onChange={(event) => setMaxPrice(event.target.value)}
            />

            <div className="range-labels">
              <span>$800</span>
              <strong>
                ${minPrice} – ${maxPrice}
              </strong>
              <span>$2,500+</span>
            </div>
          </fieldset>

          <fieldset>
            <legend>Plataformas activas</legend>

            <div className="marketplace-options">
              {sourcesList.map((source) => (
                <label key={source.key}>
                  <input type="checkbox" defaultChecked={source.active}
                    onChange={() => handleToggle(source.key)}

                  />
                  <span>{source.name}</span>
                  <small>{source.count}</small>


                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend>Ubicación y entrega</legend>

            <div className="delivery-options">
              <label>
                <input type="checkbox" defaultChecked />
                Envíos nacionales
              </label>

              <label>
                <input type="checkbox" defaultChecked />
                Trato en mano / Recogida local
              </label>
            </div>
          </fieldset>
        </div>

        <footer className="advanced-filter-footer">
          <button type="button" onClick={onClose}>
            Cancelar
          </button>

          <button
            type="button"
            className="apply-filter-button"
            onClick={handleApply}

          >
            Aplicar filtros
            <Icon name="check" size={16} />
          </button>
        </footer>
      </section>
    </div>
  )
}
