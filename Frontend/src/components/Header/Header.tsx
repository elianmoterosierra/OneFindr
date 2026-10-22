import { useState } from 'react'
import { Brand } from '../Brand/Brand'
import { Icon } from '../Icon/Icon'
import './Header.css'

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="site-header" id="top">
      <Brand />
      <button type="button" className="mobile-menu-button" aria-label="Abrir menú" aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}>
        <span /><span /><span />
      </button>
      <div className={`header-actions ${menuOpen ? 'is-open' : ''}`}>
        <nav className="main-nav" aria-label="Navegación principal">
          <a href="#explorar" className="active">Explorar</a>
          <a href="#alertas">Alertas de precio</a>
          <a href="#guardados">Guardados</a>
        </nav>
        <div className="account-actions">
          <button type="button" className="icon-button secondary" aria-label="Filtros y preferencias"><Icon name="filter" size={17} /></button>
          <button type="button" className="icon-button primary" aria-label="Abrir perfil"><Icon name="user" size={17} /></button>
        </div>
      </div>
    </header>
  )
}
