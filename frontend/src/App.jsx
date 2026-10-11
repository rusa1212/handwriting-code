import { useState } from 'react'
import AlgorithmLabPage from './pages/AlgorithmLabPage'
import RecommendPage from './pages/RecommendPage'
import './App.css'

const TABS = [
  { id: 'recommend', label: '경로 추천' },
  { id: 'lab', label: '알고리즘 실험실' },
]

function App() {
  const [tab, setTab] = useState('recommend')

  return (
    <main className="app">
      <header className="app-header">
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={t.id === tab ? 'tab active' : 'tab'}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      {tab === 'recommend' ? <RecommendPage /> : <AlgorithmLabPage />}
    </main>
  )
}

export default App
