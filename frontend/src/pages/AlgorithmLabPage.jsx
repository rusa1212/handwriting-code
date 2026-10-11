import { useEffect, useMemo, useRef, useState } from 'react'
import { searchGraph } from '../api/client'
import { LAB_BOUNDS, LAB_CENTER, LAB_LEVEL } from '../constants'
import MapView from '../components/MapView'

// 클릭할 수 있는 영역 안내. MapView는 rects가 바뀌면 다시 그리므로 렌더마다 새 배열을 만들지 않게 밖에 둔다
const LAB_RECTS = [LAB_BOUNDS]
const NO_DOTS = [] // 결과가 없을 때도 같은 배열을 넘겨 점을 다시 그리지 않게 한다
// 탐색 애니메이션: 프레임마다 보여줄 방문 노드 수 (60fps에서 초당 약 300개)
// 알고리즘과 상관없이 같은 속도라야 A*가 Dijkstra보다 빨리 끝나는 것이 보인다
const STEP = 5

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
  const [shownCount, setShownCount] = useState(0) // 재생 중 지도에 보이는 방문 노드 수 (visited_order 앞에서부터)
  const searchIdRef = useRef(0) // 실행 중에 출발/도착을 바꾸거나 다시 실행하면 이전 응답은 버린다

  // 출발/도착 핀. MapView는 markers가 바뀌면 다시 그리므로 좌표가 바뀔 때만 새 배열을 만든다
  const markers = useMemo(
    () => [start && { label: '출발', ...start }, end && { label: '도착', ...end }].filter(Boolean),
    [start, end],
  )

  // 재생 중: 방문 노드가 아직 다 나오지 않았다 (새 결과가 오면 shownCount는 0부터 시작)
  const playing = result !== null && shownCount < result.visited_order.length

  // 경로 선: 재생이 끝난 뒤, 점이 2개 이상일 때만 그린다 (경로 없음 = 빈 목록, 출발 = 도착 = 점 1개)
  // 그전에 그리면 MapView가 경로에 맞춰 지도를 옮겨 퍼져 나가는 점이 화면 밖으로 밀려난다
  const routes = useMemo(
    () => (!playing && result?.path.length > 1 ? [{ id: 'search', path: result.path }] : []),
    [result, playing],
  )

  // 방문한 노드: 탐색 순서대로 앞에서부터 shownCount개만 보여준다
  const dots = result ? result.visited_order : NO_DOTS

  // 새 결과가 오면 방문 노드를 프레임마다 STEP개씩 늘려 재생한다
  // 결과가 바뀌거나 지워지면(출발/도착 변경, 다시 실행) 또는 탭을 옮기면 cleanup에서 재생을 멈춘다
  useEffect(() => {
    if (!result) return
    const total = result.visited_order.length
    let count = 0
    let frameId

    function tick() {
      count = Math.min(count + STEP, total)
      setShownCount(count)
      if (count < total) frameId = requestAnimationFrame(tick)
    }
    frameId = requestAnimationFrame(tick)

    return () => cancelAnimationFrame(frameId)
  }, [result])

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

  // 일방통행이 있어 방향을 바꾸면 경로가 달라질 수 있다. 이전 결과는 반대 방향이므로 지운다
  function handleSwap() {
    setStart(end)
    setEnd(start)
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
      setShownCount(0) // 재생은 처음부터 (첫 프레임 전에 이전 결과 개수만큼 점이 보이지 않게)
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
          <div className="lab-actions">
            <button
              type="button"
              className="secondary"
              onClick={handleSwap}
              disabled={!start || !end}
              title="출발지와 도착지 바꾸기"
            >
              ⇅ 방향 바꾸기
            </button>
            <button type="button" className="secondary" onClick={handleReset} disabled={!start}>
              초기화
            </button>
          </div>
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
            {playing && (
              <p className="hint">
                탐색 중 · 방문 {shownCount.toLocaleString()} / {result.visited_order.length.toLocaleString()}개
              </p>
            )}
            {/* 경로를 못 찾았다는 것은 재생이 끝나야 알려준다. 숫자 요약은 서버 응답 그대로라 재생 중에도 보여준다 */}
            {result.cost === null ? (
              !playing && <p className="hint">경로를 찾을 수 없습니다.</p>
            ) : (
              <dl className="lab-result">
                <dt>경로 거리</dt>
                {/* 알고리즘끼리 수십 m 차이도 비교할 수 있게 km 대신 m로 보여준다 */}
                <dd>{Math.round(result.cost).toLocaleString()}m</dd>
                {/* BFS는 이 값이 가장 작고, Dijkstra/A*는 거리가 가장 짧다 (도로가 꺾이는 점도 노드로 센다) */}
                <dt>경로 노드</dt>
                <dd>{result.path.length.toLocaleString()}개</dd>
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
        dots={dots}
        dotCount={shownCount}
        routes={routes}
        markers={markers}
        selectedId="search"
        onMapClick={handleMapClick}
      />
    </div>
  )
}

export default AlgorithmLabPage
