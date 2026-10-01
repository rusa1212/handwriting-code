import { useEffect, useState } from 'react'
import { getHealth } from './api/client'
import AlgorithmLabPage from './pages/AlgorithmLabPage'
import RecommendPage from './pages/RecommendPage'
import './App.css'

const TABS = [
  { id: 'recommend', label: '경로 추천' },
  { id: 'lab', label: '알고리즘 실험실' },
]

function App() {
  const [tab, setTab] = useState('recommend')
  const [backendStatus, setBackendStatus] = useState('확인 중...')

  useEffect(() => {
    getHealth()
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus('연결 실패'))
  }, [])

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
        <p>
          Backend: <code>{backendStatus}</code>
        </p>
      </header>
      {tab === 'recommend' ? <RecommendPage /> : <AlgorithmLabPage />}
    </main>
  )
}

export default App
