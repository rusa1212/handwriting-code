import { useMemo, useRef, useState } from 'react'
import { searchGraph } from '../api/client'
import { LAB_BOUNDS, LAB_CENTER, LAB_LEVEL } from '../constants'
import MapView from '../components/MapView'

// 클릭할 수 있는 영역 안내. MapView는 rects가 바뀌면 다시 그리므로 렌더마다 새 배열을 만들지 않게 밖에 둔다
const LAB_RECTS = [LAB_BOUNDS]

// 서버 algorithm 값 → 화면 이름, 고른 알고리즘 아래에 보여줄 한 줄 설명
const ALGORITHMS = [
  { id: 'bfs', label: 'BFS', description: '거치는 노드 수가 가장 적은 경로를 찾습니다. 도로 길이는 보지 않습니다.' },
  { id: 'dfs', label: 'DFS', description: '한 방향으로 끝까지 파고듭니다. 최단 경로를 보장하지 않습니다.' },
  { id: 'dijkstra', label: 'Dijkstra', description: '출발지에서 가까운 노드부터 확정해 최단 경로를 찾습니다.' },
  { id: 'astar', label: 'A*', description: 'Dijkstra + 직선거리로 도착지 쪽부터 탐색합니다. 최단 경로를 보장합니다.' },
]
const ALGORITHM_LABEL = Object.fromEntries(ALGORITHMS.map((a) => [a.id, a.label]))

// 알고리즘 실험실 탭 (LEVEL 4): 직접 구현한 Dijkstra/A* 실행
function AlgorithmLabPage() {
  const [start, setStart] = useState(null) // { lat, lng } 또는 null: 지도에서 찍은 좌표 (주소 변환은 하지 않는다)
  const [end, setEnd] = useState(null)
  const [algorithm, setAlgorithm] = useState('astar')
  // { algorithm, path, visited_order, cost, elapsed_ms }: 알고리즘만 바꿔도 결과는 그대로이므로 실행한 알고리즘을 같이 둔다
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const searchIdRef = useRef(0) // 실행 중에 출발/도착을 바꾸거나 다시 실행하면 이전 응답은 버린다

  // 출발/도착 핀. MapView는 markers가 바뀌면 다시 그리므로 좌표가 바뀔 때만 새 배열을 만든다
  const markers = useMemo(
    () => [start && { label: '출발', ...start }, end && { label: '도착', ...end }].filter(Boolean),
    [start, end],
  )

  // 경로 선: 점이 2개 이상일 때만 그린다 (경로 없음 = 빈 목록, 출발 = 도착 = 점 1개)
  const routes = useMemo(
    () => (result?.path.length > 1 ? [{ id: 'search', path: result.path }] : []),
    [result],
  )

  // 출발/도착이 바뀌면 이전 결과는 새 핀과 맞지 않으므로 지운다
  function clearResult() {
    searchIdRef.current++
    setLoading(false)
    setResult(null)
    setError(null)
  }

  // 실험실은 항상 지점 선택 모드: 출발 → 도착 → 다시 클릭하면 새 출발 (도착은 지운다)
  function handleMapClick(latLng) {
    if (!start || end) {
      setStart(latLng)
      setEnd(null)
    } else {
      setEnd(latLng)
    }
    clearResult()
  }

  function handleReset() {
    setStart(null)
    setEnd(null)
    clearResult()
  }

  async function handleRun() {
    const searchId = ++searchIdRef.current
    setLoading(true)
    setError(null)
    try {
      const found = await searchGraph(start, end, algorithm)
      if (searchId !== searchIdRef.current) return
      setResult({ algorithm, ...found })
    } catch (err) {
      if (searchId !== searchIdRef.current) return
      setResult(null)
      setError(err.message)
    } finally {
      if (searchId === searchIdRef.current) setLoading(false)
    }
  }

  return (
    <div className="page">
      <aside className="sidebar">
        <section className="panel">
          <h2>알고리즘 실험실</h2>
          <p className="hint">
            {!start
              ? '점선 영역 안에서 출발지를 클릭하세요.'
              : !end
                ? '도착지를 클릭하세요.'
                : '다시 클릭하면 새 출발지를 고릅니다.'}
          </p>
          <button type="button" className="secondary" onClick={handleReset} disabled={!start}>
            초기화
          </button>
        </section>
        <section className="panel">
          <h2>알고리즘</h2>
          <div className="algorithm-options">
            {ALGORITHMS.map((a) => (
              <label key={a.id}>
                <input
                  type="radio"
                  name="algorithm"
                  value={a.id}
                  checked={algorithm === a.id}
                  onChange={() => setAlgorithm(a.id)}
                />
                {a.label}
              </label>
            ))}
          </div>
          <p className="algorithm-description">{ALGORITHMS.find((a) => a.id === algorithm).description}</p>
          <button type="button" className="primary" onClick={handleRun} disabled={!start || !end || loading}>
            {loading ? '탐색 중...' : '실행'}
          </button>
          {error && <p className="error">{error}</p>}
        </section>
        {result && (
          <section className="panel">
            <h2>결과 · {ALGORITHM_LABEL[result.algorithm]}</h2>
            {result.cost === null ? (
              <p className="hint">경로를 찾을 수 없습니다.</p>
            ) : (
              <dl className="lab-result">
                <dt>경로 거리</dt>
                {/* 알고리즘끼리 수십 m 차이도 비교할 수 있게 km 대신 m로 보여준다 */}
                <dd>{Math.round(result.cost).toLocaleString()}m</dd>
                <dt>방문 노드</dt>
                <dd>{result.visited_order.length.toLocaleString()}개</dd>
                <dt>탐색 시간</dt>
                <dd>{result.elapsed_ms.toFixed(2)}ms</dd>
              </dl>
            )}
          </section>
        )}
        {/* 도로망은 OSM 데이터(ODbL)라 출처를 화면에 적어야 한다 */}
        <p className="attribution">
          도로 데이터{' '}
          <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
            © OpenStreetMap contributors
          </a>
        </p>
      </aside>
      <MapView
        center={LAB_CENTER}
        level={LAB_LEVEL}
        rects={LAB_RECTS}
        routes={routes}
        markers={markers}
        selectedId="search"
        onMapClick={handleMapClick}
      />
    </div>
  )
}

export default AlgorithmLabPage
