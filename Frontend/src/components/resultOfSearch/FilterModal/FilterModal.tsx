import { useState } from 'react'
import { Icon } from '../../Icon/Icon'
import './FilterModal.css'

type FilterModalProps = { open: boolean; onClose: () => void }

export function FilterModal({ open, onClose }: FilterModalProps) {
  const [state, setState] = useState('Todos')
  const [minPrice, setMinPrice] = useState('1200')
  const [maxPrice, setMaxPrice] = useState('1900')

  if (!open) return null

  const clearFilters = () => { setState('Todos'); setMinPrice('1200'); setMaxPrice('1900') }

  return (
    <div className="advanced-filter-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="advanced-filter-modal" role="dialog" aria-modal="true" aria-labelledby="filter-title" onMouseDown={(event) => event.stopPropagation()}>
        <header className="advanced-filter-header"><div><span className="filter-icon"><Icon name="tune" size={18} /></span><div><h2 id="filter-title">Filtros avanzados</h2><p>Ajusta los parámetros para refinar resultados</p></div></div><div><button type="button" className="clear-filter-button" onClick={clearFilters}>Limpiar todo</button><button type="button" className="close-filter-button" onClick={onClose} aria-label="Cerrar filtros"><Icon name="close" size={20} /></button></div></header>
        <div className="advanced-filter-content">
          <fieldset><legend>Estado del producto</legend><div className="state-options">{['Todos', 'Nuevo en caja', 'Reacondicionado', 'Segunda mano'].map((option) => <button key={option} type="button" className={state === option ? 'selected' : ''} onClick={() => setState(option)}>{option}</button>)}</div></fieldset>
          <fieldset><legend>Rango de precio</legend><div className="price-inputs"><label>Mínimo<input type="number" value={minPrice} onChange={(event) => setMinPrice(event.target.value)} /></label><label>Máximo<input type="number" value={maxPrice} onChange={(event) => setMaxPrice(event.target.value)} /></label></div><input className="range-input" type="range" min="800" max="2500" value={maxPrice} onChange={(event) => setMaxPrice(event.target.value)} /><div className="range-labels"><span>$800</span><strong>${minPrice} – ${maxPrice}</strong><span>$2,500+</span></div></fieldset>
          <fieldset><legend>Plataformas activas</legend><div className="marketplace-options">{[['Amazon Prime', '32 disp.'], ['eBay', '21 disp.'], ['Wallapop', '19 disp.'], ['FB Marketplace', '12 disp.'], ['MercadoLibre', '0 disp.']].map(([name, count], index) => <label key={name}><input type="checkbox" defaultChecked={index < 4} /><span>{name}</span><small>{count}</small></label>)}</div></fieldset>
          <fieldset><legend>Ubicación y entrega</legend><div className="delivery-options"><label><input type="checkbox" defaultChecked />Envíos nacionales</label><label><input type="checkbox" defaultChecked />Trato en mano / Recogida local</label></div></fieldset>
        </div>
        <footer className="advanced-filter-footer"><button type="button" onClick={onClose}>Cancelar</button><button type="button" className="apply-filter-button" onClick={onClose}>Aplicar filtros (84 resultados)<Icon name="check" size={16} /></button></footer>
      </section>
    </div>
  )
}
