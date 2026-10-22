import './Brand.css'
import { Link } from 'react-router'

export function Brand() {
  return (
    <Link to="/" className="brand" aria-label="OneFindr, inicio">
      <span className="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" strokeWidth="2.2" />
          <path d="m15.5 15.5 4.5 4.5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
          <circle cx="10.5" cy="10.5" r="2.5" fill="currentColor" opacity=".35" />
        </svg>
      </span>
      <span className="brand-text">
        <span className="brand-name"><span>One</span>Findr</span>
        <span className="brand-tagline">Metabuscador</span>
      </span>
    </Link>
  )
}
