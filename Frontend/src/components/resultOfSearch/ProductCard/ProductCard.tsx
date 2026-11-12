import { Icon } from '../../Icon/Icon'
import './ProductCard.css'
import type { Product } from '../../../types'

type ProductCardProps = { product: Product }


export function ProductCard({ product }: ProductCardProps) {
  return (
    <article className="product-card">
      <div className="product-image-wrap">
        <img src={product.image} alt={product.title} className="product-image" />
        <span className="store-badge" style={{ backgroundColor: product.storeColor }}><Icon name={product.storeIcon} size={13} />{product.store}</span>
        {product.badge && <span className="product-badge">{product.badge}</span>}
        <button type="button" className="favorite-button" aria-label={`Guardar ${product.title}`}><Icon name="favorite" size={16} /></button>
      </div>
      <div className="product-body">
        <div className="product-details">
          <div className="product-meta"><span><i />{product.state}</span><small>{product.distance}</small></div>
          <h3>{product.title}</h3>
          <p>{product.description}</p>
        </div>
        <div className="product-footer">
          <div className="price-row"><div><strong>{product.price}</strong>{product.oldPrice && <del>{product.oldPrice}</del>}</div><span>{product.saving}</span></div>
          <div className="delivery-row"><span><Icon name="person-pin" size={13} />{product.delivery}</span><a href="#oferta">Ver oferta <Icon name="arrow-outward" size={14} /></a></div>
        </div>
      </div>
    </article>
  )
}
