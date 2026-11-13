import { Icon } from '../../Icon/Icon'
import './ResultsControls.css'
import { useState } from 'react'
import { FilterModal } from '../FilterModal/FilterModal'
import { useQueryParam } from '../../../hooks/useQueryParams'

const SORT_OPTIONS = ['Mejor precio', 'Relevancia', 'Más reciente']

export function ResultsControls() {
  const { minPrice, maxPrice } = useQueryParam()
  const priceMin = Number(minPrice) || 0
  const priceMax = Number(maxPrice) || 0
  const [open, setOpen] = useState(false)
  const toggleModal = () => setOpen(prev => !prev)
  return (
    <section className="results-controls">
      <div className="controls-left">
        <button type="button" className="filters-button" onClick={toggleModal} ><Icon name="tune" size={18} /><span>Filtros</span><b>3</b></button>
        <div className="filter-summary"><span>Todos los estados</span><span>${priceMin || '0'} - ${priceMax || '0'}</span><span>Envío &amp; Recogida</span></div>
      </div>

      <div className="sort-controls">
        <span>Ordenar por:</span>

        <div className="sort-options">
          {SORT_OPTIONS.map((option, index) => <button type="button" className={index === 0 ? 'selected' : ''} key={option}>{option}</button>)}
        </div>

      </div>
      <FilterModal open={open} onClose={() => setOpen(false)} />
    </section>
  )
}
