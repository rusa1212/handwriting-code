import { useEffect, useMemo, useRef, useState } from 'react'
import { searchGraph } from '../api/client'
import { LAB_BOUNDS, LAB_CENTER, LAB_COMPARE_LEVEL, LAB_LEVEL } from '../constants'
import MapView from '../components/MapView'

// 클릭할 수 있는 영역 안내. MapView는 rects가 바뀌면 다시 그리므로 렌더마다 새 배열을 만들지 않게 밖에 둔다
const LAB_RECTS = [LAB_BOUNDS]
const NO_DOTS = [] // 결과가 없을 때도 같은 배열을 넘겨 점을 다시 그리지 않게 한다
// 탐색 애니메이션: 프레임마다 보여줄 방문 노드 수 (60fps에서 초당 약 300개)
// 알고리즘과 상관없이 같은 속도라야 A*가 Dijkstra보다 빨리 끝나는 것이 보인다
const STEP = 5
// 재생 속도 배율: 프레임마다 STEP × 배율개를 보여준다 (×0.5는 2.5개라 소수로 쌓고 지도에는 내림한 개수만 보여준다)
const SPEEDS = [0.5, 1, 2, 4]
// 재생 중 방금 방문한 점을 탐색 경계로 강조할 프레임 수 (약 0.1초 분량). 속도를 올려도 경계 두께가 같게 개수는 배율을 곱한다
const DOT_HEAD_FRAMES = 6

// 서버 algorithm 값 → 화면 이름, 고른 알고리즘 아래에 보여줄 한 줄 설명
const ALGORITHMS = [
  { id: 'bfs', label: 'BFS', description: '거치는 노드 수가 가장 적은 경로를 찾습니다. 도로 길이는 보지 않습니다.' },
  { id: 'dfs', label: 'DFS', description: '한 방향으로 끝까지 파고듭니다. 최단 경로를 보장하지 않습니다.' },
  { id: 'dijkstra', label: 'Dijkstra', description: '출발지에서 가까운 노드부터 확정해 최단 경로를 찾습니다.' },
  { id: 'astar', label: 'A*', description: 'Dijkstra + 직선거리로 도착지 쪽부터 탐색합니다. 최단 경로를 보장합니다.' },
]
const ALGORITHM_LABEL = Object.fromEntries(ALGORITHMS.map((a) => [a.id, a.label]))
const ALGORITHM_DESCRIPTION = Object.fromEntries(ALGORITHMS.map((a) => [a.id, a.description]))
const COMPARE_SIDES = ['왼쪽 지도', '오른쪽 지도']

// 지도 한 장: 결과 하나의 방문 노드를 앞에서부터 shown개 보여주고, 자기 결과가 다 나오면 경로를 그린다
// 비교 모드에서는 두 장이 같은 shown을 받으므로 같은 속도로 재생되고, 방문 노드가 적은 쪽이 먼저 끝난다
// label: 지도 위에 띄울 알고리즘 이름 (단일 모드는 사이드바에 결과가 있으므로 넘기지 않는다)
function LabMap({ label = null, result, shown, dotHead, level, markers, onMapClick }) {
  const total = result ? result.visited_order.length : 0
  const done = result !== null && shown >= total

  // 경로 선: 이 지도의 재생이 끝난 뒤, 점이 2개 이상일 때만 그린다 (경로 없음 = 빈 목록, 출발 = 도착 = 점 1개)
  const routes = useMemo(
    () => (done && result.path.length > 1 ? [{ id: 'search', path: result.path }] : []),
    [result, done],
  )

  return (
    <div className="lab-map">
      <MapView
        center={LAB_CENTER}
        level={level}
        rects={LAB_RECTS}
        dots={result ? result.visited_order : NO_DOTS}
        dotCount={shown}
        dotHead={dotHead}
        // 탐색 범위(점)가 경로보다 넓으므로 경로에 맞춰 확대하지 않고 영역 전체 화면을 그대로 둔다
        fitRoutes={false}
        routes={routes}
        markers={markers}
        selectedId="search"
        onMapClick={onMapClick}
      />
      {label && (
        <div className="lab-map-status">
          <strong>{label}</strong>
          {result &&
            (done
              ? ` · ✅ 완료 · 방문 ${total.toLocaleString()}개${result.cost === null ? ' · 경로 없음' : ''}`
              : ` · 방문 ${shown.toLocaleString()} / ${total.toLocaleString()}개`)}
        </div>
      )}
    </div>
  )
}

// 알고리즘 실험실 탭 (LEVEL 4): 직접 구현한 Dijkstra/A* 실행
function AlgorithmLabPage() {
  const [start, setStart] = useState(null) // { lat, lng } 또는 null: 지도에서 찍은 좌표 (주소 변환은 하지 않는다)
  const [end, setEnd] = useState(null)
  const [compare, setCompare] = useState(false) // 비교 모드: 두 알고리즘을 지도 두 장에 나란히 재생
  const [algorithm, setAlgorithm] = useState('astar') // 단일 모드에서 고른 알고리즘
  const [pair, setPair] = useState(['dijkstra', 'astar']) // 비교 모드에서 [왼쪽, 오른쪽] 지도에 고른 알고리즘 (서로 다르게)
  // [{ algorithm, path, visited_order, cost, elapsed_ms }] 또는 null: 단일 모드는 1개, 비교 모드는 [왼쪽, 오른쪽]
  // 알고리즘만 바꿔도 결과는 그대로이므로 실행한 알고리즘을 같이 둔다
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  // 재생 중 지도에 보이는 방문 노드 수 (visited_order 앞에서부터). 비교 모드에서는 두 지도가 같은 값을 쓴다
  // ×0.5 속도에서는 소수가 될 수 있다
  const [shownCount, setShownCount] = useState(0)
  const [paused, setPaused] = useState(false)
  const [speed, setSpeed] = useState(1) // SPEEDS 중 하나. 새로 실행하거나 다시 봐도 그대로 둔다
  const searchIdRef = useRef(0) // 실행 중에 출발/도착을 바꾸거나 다시 실행하면 이전 응답은 버린다

  // 출발/도착 핀. MapView는 markers가 바뀌면 다시 그리므로 좌표가 바뀔 때만 새 배열을 만든다
  const markers = useMemo(
    () => [start && { label: '출발', ...start }, end && { label: '도착', ...end }].filter(Boolean),
    [start, end],
  )

  // 재생은 방문 노드가 가장 많은 결과가 다 나올 때까지 (새 결과가 오면 shownCount는 0부터 시작)
  const total = results ? Math.max(...results.map((r) => r.visited_order.length)) : 0
  const playing = results !== null && shownCount < total
  const shown = Math.floor(shownCount) // 지도와 진행 표시는 정수 개수

  // 재생 중이면 다음 프레임에 방문 노드를 STEP × speed개 더 보여준다. shownCount가 바뀌면 다시 실행되어 한 프레임씩 이어진다
  // 진행 상황은 shownCount 하나뿐이라 건너뛰기(끝까지)·다시 보기(0으로)는 값만 바꾸면 되고,
  // 일시정지는 다음 프레임을 예약하지 않기만 하면 된다 (재개하면 이 effect가 다시 돌아 이어진다)
  // 결과가 지워지거나(출발/도착 변경) 탭을 옮기면 cleanup에서 예약한 프레임을 취소해 멈춘다
  useEffect(() => {
    if (!playing || paused) return
    const frameId = requestAnimationFrame(() => setShownCount((count) => Math.min(count + STEP * speed, total)))
    return () => cancelAnimationFrame(frameId)
  }, [playing, paused, speed, shownCount, total])

  // 같은 결과를 처음부터 다시 재생 (서버를 다시 부르지 않는다)
  function replay() {
    setShownCount(0)
    setPaused(false)
  }

  // 끝까지 바로 보기: 재생이 멈추고 경로가 그려진다
  function skip() {
    setShownCount(total)
    setPaused(false)
  }

  // 출발/도착이 바뀌면 이전 결과는 새 핀과 맞지 않으므로 지운다
  function clearResult() {
    searchIdRef.current++
    setLoading(false)
    setResults(null)
    setError(null)
  }

  // 실험실은 항상 지점 선택 모드: 출발 → 도착 → 다시 클릭하면 새 출발 (도착은 지운다)
  // 비교 모드에서는 어느 지도를 클릭해도 같다
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

  // 모드를 바꾸면 지도 수가 달라지므로 이전 결과는 지운다 (출발/도착은 그대로)
  function handleCompareChange(checked) {
    setCompare(checked)
    clearResult()
  }

  // 비교 모드에서 side(0 = 왼쪽, 1 = 오른쪽) 지도의 알고리즘을 바꾼다. 반대쪽과 같은 것은 라디오에서 막는다
  function handlePairChange(side, id) {
    setPair((prev) => prev.map((a, i) => (i === side ? id : a)))
  }

  async function handleRun() {
    const searchId = ++searchIdRef.current
    const algorithms = compare ? pair : [algorithm]
    setLoading(true)
    setError(null)
    try {
      // 비교 모드는 두 알고리즘을 동시에 요청한다. 하나라도 실패하면 오류만 보여준다
      const found = await Promise.all(algorithms.map((a) => searchGraph(start, end, a)))
      if (searchId !== searchIdRef.current) return
      setShownCount(0) // 재생은 처음부터 (첫 프레임 전에 이전 결과 개수만큼 점이 보이지 않게)
      setPaused(false)
      setResults(found.map((f, i) => ({ algorithm: algorithms[i], ...f })))
    } catch (err) {
      if (searchId !== searchIdRef.current) return
      setResults(null)
      setError(err.message)
    } finally {
      if (searchId === searchIdRef.current) setLoading(false)
    }
  }

  const dotHead = STEP * speed * DOT_HEAD_FRAMES
  const single = !compare && results ? results[0] : null // 단일 모드 결과 (사이드바 요약용)

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
          <label className="compare-toggle">
            <input type="checkbox" checked={compare} onChange={(e) => handleCompareChange(e.target.checked)} />
            비교 모드 (두 알고리즘을 나란히)
          </label>
          {compare ? (
            pair.map((selected, side) => (
              <div key={side}>
                <p className="compare-side">{COMPARE_SIDES[side]}</p>
                <div className="algorithm-options">
                  {ALGORITHMS.map((a) => (
                    <label key={a.id}>
                      <input
                        type="radio"
                        name={`algorithm-${side}`}
                        value={a.id}
                        checked={selected === a.id}
                        disabled={pair[1 - side] === a.id}
                        onChange={() => handlePairChange(side, a.id)}
                      />
                      {a.label}
                    </label>
                  ))}
                </div>
                <p className="algorithm-description">{ALGORITHM_DESCRIPTION[selected]}</p>
              </div>
            ))
          ) : (
            <>
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
              <p className="algorithm-description">{ALGORITHM_DESCRIPTION[algorithm]}</p>
            </>
          )}
          <button type="button" className="primary" onClick={handleRun} disabled={!start || !end || loading}>
            {loading ? '탐색 중...' : '실행'}
          </button>
          {error && <p className="error">{error}</p>}
        </section>
        {results && (
          <section className="panel">
            <h2>결과 · {results.map((r) => ALGORITHM_LABEL[r.algorithm]).join(' vs ')}</h2>
            {/* 비교 모드의 방문 수는 지도마다 다르므로 각 지도 위에 보여준다 */}
            {playing && (
              <p className="hint">
                {paused ? '일시정지' : '탐색 중'}
                {single && ` · 방문 ${shown.toLocaleString()} / ${total.toLocaleString()}개`}
              </p>
            )}
            {/* 재생 중에는 일시정지/재개와 끝까지 바로 보기, 끝난 뒤에는 같은 결과를 처음부터 다시 재생 */}
            <div className="lab-actions">
              {playing ? (
                <>
                  <button type="button" className="secondary" onClick={() => setPaused((p) => !p)}>
                    {paused ? '▶ 재개' : '⏸ 일시정지'}
                  </button>
                  <button type="button" className="secondary" onClick={skip}>
                    건너뛰기
                  </button>
                </>
              ) : (
                <button type="button" className="secondary" onClick={replay}>
                  다시 보기
                </button>
              )}
            </div>
            {/* 속도는 재생 중에 바꿔도 다음 프레임부터 바로 적용된다 */}
            <div className="speed-options">
              속도
              {SPEEDS.map((s) => (
                <label key={s}>
                  <input type="radio" name="speed" checked={speed === s} onChange={() => setSpeed(s)} />×{s}
                </label>
              ))}
            </div>
            {/* 경로를 못 찾았다는 것은 재생이 끝나야 알려준다. 숫자 요약은 서버 응답 그대로라 재생 중에도 보여준다 */}
            {single &&
              (single.cost === null ? (
                !playing && <p className="hint">경로를 찾을 수 없습니다.</p>
              ) : (
                <dl className="lab-result">
                  <dt>경로 거리</dt>
                  {/* 알고리즘끼리 수십 m 차이도 비교할 수 있게 km 대신 m로 보여준다 */}
                  <dd>{Math.round(single.cost).toLocaleString()}m</dd>
                  {/* BFS는 이 값이 가장 작고, Dijkstra/A*는 거리가 가장 짧다 (도로가 꺾이는 점도 노드로 센다) */}
                  <dt>경로 노드</dt>
                  <dd>{single.path.length.toLocaleString()}개</dd>
                  <dt>방문 노드</dt>
                  <dd>{single.visited_order.length.toLocaleString()}개</dd>
                  <dt>탐색 시간</dt>
                  <dd>{single.elapsed_ms.toFixed(2)}ms</dd>
                </dl>
              ))}
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
      {/* 모드를 바꾸면 지도 폭이 달라지므로 key를 바꿔 지도를 새로 만든다 (크기가 바뀐 지도를 다시 맞추지 않아도 된다) */}
      {compare ? (
        <div className="lab-maps">
          {pair.map((selected, side) => (
            <LabMap
              key={`compare-${side}`}
              label={ALGORITHM_LABEL[results ? results[side].algorithm : selected]}
              result={results ? results[side] : null}
              shown={shown}
              dotHead={dotHead}
              level={LAB_COMPARE_LEVEL}
              markers={markers}
              onMapClick={handleMapClick}
            />
          ))}
        </div>
      ) : (
        <LabMap
          key="single"
          result={single}
          shown={shown}
          dotHead={dotHead}
          level={LAB_LEVEL}
          markers={markers}
          onMapClick={handleMapClick}
        />
      )}
    </div>
  )
}

export default AlgorithmLabPage
