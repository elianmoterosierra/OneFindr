import { Icon } from '../../Icon/Icon'
import './PriceInsight.css'

export function PriceInsight() {
  return (
    <section className="price-insight">
      <div className="insight-copy"><span className="insight-label"><Icon name="insights" size={14} />Inteligencia de Metabúsqueda</span><h2>Dispersión de precios detectada</h2><p>Comprar en plataformas locales de segunda mano ofrece hasta un <strong>22% de ahorro</strong> frente al precio medio minorista nuevo.</p></div>
      <div className="price-chart"><div className="chart-labels"><span>Mínimo: $1,390 (eBay)</span><strong>Mediana: $1,520</strong><span>Máximo: $1,999 (Amazon)</span></div><div className="chart-bar"><i /><i /><i /></div><div className="chart-legend"><span><i />Segunda mano</span><span><i />Reacondicionado certificado</span><span><i />Nuevo retail</span></div></div>
    </section>
  )
}
