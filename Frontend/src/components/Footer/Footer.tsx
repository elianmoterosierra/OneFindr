import { useState } from 'react'
import { Modal } from '../Modal/Modal'
import './Footer.css'

type LegalDocument = 'privacy' | 'terms' | null

export function Footer() {
  const [openDocument, setOpenDocument] = useState<LegalDocument>(null)

  return (
    <>
      <footer className="site-footer">
        <div className="footer-description"><span>Busca y encuentra</span><b>•</b><span>Metabuscador simultáneo de marketplaces</span></div>
        <nav className="footer-nav" aria-label="Enlaces del pie de página">
          <button type="button" onClick={() => setOpenDocument('privacy')}>Privacidad</button>
          <button type="button" onClick={() => setOpenDocument('terms')}>Términos</button>
          <a href="#soporte">Soporte</a>
        </nav>
      </footer>

      {openDocument === 'privacy' && (
        <Modal title="Política de privacidad" onClose={() => setOpenDocument(null)}>
          <h3>Información que recopilamos</h3>
          <p>OneFindr puede recopilar las búsquedas que realizas y las preferencias que seleccionas para mejorar la experiencia del metabuscador.</p>
          <h3>Uso de la información</h3>
          <p>Utilizamos esta información para mostrar resultados relevantes, mantener el servicio y mejorar sus funcionalidades.</p>
          <h3>Tus derechos</h3>
          <p>Puedes solicitar acceso, corrección o eliminación de tus datos personales escribiéndonos a soporte@onefindr.com.</p>
        </Modal>
      )}

      {openDocument === 'terms' && (
        <Modal title="Términos y condiciones" onClose={() => setOpenDocument(null)}>
          <h3>Uso del servicio</h3>
          <p>OneFindr es una herramienta de comparación que facilita la búsqueda de productos publicados en distintos marketplaces.</p>
          <h3>Resultados y precios</h3>
          <p>Los precios, existencias y condiciones pertenecen a cada plataforma de origen y pueden cambiar sin previo aviso.</p>
          <h3>Responsabilidad</h3>
          <p>Antes de realizar una compra, verifica siempre la información directamente con el vendedor o marketplace correspondiente.</p>
        </Modal>
      )}
    </>
  )
}
