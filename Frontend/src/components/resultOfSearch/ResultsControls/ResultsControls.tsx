import { Icon } from '../../Icon/Icon'
import './ResultsControls.css'

const SORT_OPTIONS = ['Mejor precio', 'Relevancia', 'Más reciente']

export function ResultsControls() {
  return (
    <section className="results-controls">
      <div className="controls-left">
        <button type="button" className="filters-button"><Icon name="tune" size={18} /><span>Filtros</span><b>3</b></button>
        <div className="filter-summary"><span>Todos los estados</span><span>$1,200 – $1,900</span><span>Envío &amp; Recogida</span></div>
      </div>

      <div className="sort-controls">
        <span>Ordenar por:</span>
        <div className="sort-options">
          {SORT_OPTIONS.map((option, index) => <button type="button" className={index === 0 ? 'selected' : ''} key={option}>{option}</button>)}
        </div>
      </div>
    </section>
  )
}
