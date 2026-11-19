import { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router'
import { Home } from './page/Home/Home'

import { ResultOfSearch } from './page/resultOfSearch/resultOfSearch'
import './App.css'
import { useSources } from './store/useSource'

function App() {
  const loadSources = useSources((state) => state.loadSources)
  const [sourcesError, setSourcesError] = useState('')

  useEffect(() => {
    let active = true
    loadSources().catch((error: unknown) => {
      if (active) {
        setSourcesError(error instanceof Error ? error.message : 'No se pudo consultar las plataformas.')
      }
    })
    return () => {
      active = false
    }
  }, [loadSources])

  return (
    <Router>
      {sourcesError && <p className="sources-load-error" role="alert">{sourcesError}</p>}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/resultados" element={<ResultOfSearch />} />
      </Routes>
    </Router>
  )
}

export default App
