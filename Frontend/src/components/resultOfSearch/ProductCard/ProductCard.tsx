import { useState } from 'react'
import { Icon } from '../../Icon/Icon'
import './ProductCard.css'
import type { Product } from '../../../types'

type ProductCardProps = { product: Product }

function formatPrice(value: number, currency: string) {
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value)
  } catch {
    return `${currency} ${value}`
  }
}

export function ProductCard({ product }: ProductCardProps) {
  const [imageFailed, setImageFailed] = useState(false)

  return (
    <article className="product-card">
      <div className="product-image-wrap">
        {product.image && !imageFailed
          ? <img src={product.image} alt={product.title} className="product-image" loading="lazy" onError={() => setImageFailed(true)} />
          : <div className="product-image-placeholder" role="img" aria-label="Imagen no disponible">Imagen no disponible</div>}
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
          <div className="price-row"><div><strong>{formatPrice(product.price, product.currency)}</strong>{product.oldPrice && <del>{formatPrice(product.oldPrice, product.currency)}</del>}</div>{product.saving && <span>{product.saving}</span>}</div>
          <div className="delivery-row"><span><Icon name="person-pin" size={13} />{product.delivery}</span>{product.url && <a href={product.url} target="_blank" rel="noreferrer">Ver oferta <Icon name="arrow-outward" size={14} /></a>}</div>
        </div>
      </div>
    </article>
  )
}
