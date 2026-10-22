import { BrowserRouter as Router, Routes, Route } from 'react-router'
import { Home } from './page/Home/Home'

import { ResultOfSearch } from './page/resultOfSearch/resultOfSearch'
import './App.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/resultados" element={<ResultOfSearch />} />
      </Routes>
    </Router>
  )
}

export default App
