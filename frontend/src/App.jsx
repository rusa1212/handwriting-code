import { useEffect, useState } from 'react'
import MapView from './components/MapView'
import './App.css'

// 구미역 좌표
const GUMI_STATION = { lat: 36.1283, lng: 128.3309 }

function App() {
  const [backendStatus, setBackendStatus] = useState('확인 중...')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => {
        if (!res.ok) throw new Error(res.status)
        return res.json()
      })
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus('연결 실패'))
  }, [])

  return (
    <main className="app">
      <header className="app-header">
        <h1>경로 추천</h1>
        <p>
          Backend: <code>{backendStatus}</code>
        </p>
      </header>
      <MapView center={GUMI_STATION} />
    </main>
  )
}

export default App
