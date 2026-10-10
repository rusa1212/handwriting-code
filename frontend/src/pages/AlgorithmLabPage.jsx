import { useMemo, useState } from 'react'
import { LAB_BOUNDS, LAB_CENTER, LAB_LEVEL } from '../constants'
import MapView from '../components/MapView'

// 클릭할 수 있는 영역 안내. MapView는 rects가 바뀌면 다시 그리므로 렌더마다 새 배열을 만들지 않게 밖에 둔다
const LAB_RECTS = [LAB_BOUNDS]

// 알고리즘 실험실 탭 (LEVEL 4): 직접 구현한 Dijkstra/A* 실행
function AlgorithmLabPage() {
  const [start, setStart] = useState(null) // { lat, lng } 또는 null: 지도에서 찍은 좌표 (주소 변환은 하지 않는다)
  const [end, setEnd] = useState(null)

  // 출발/도착 핀. MapView는 markers가 바뀌면 다시 그리므로 좌표가 바뀔 때만 새 배열을 만든다
  const markers = useMemo(
    () => [start && { label: '출발', ...start }, end && { label: '도착', ...end }].filter(Boolean),
    [start, end],
  )

  // 실험실은 항상 지점 선택 모드: 출발 → 도착 → 다시 클릭하면 새 출발 (도착은 지운다)
  function handleMapClick(latLng) {
    if (!start || end) {
      setStart(latLng)
      setEnd(null)
    } else {
      setEnd(latLng)
    }
  }

  function handleReset() {
    setStart(null)
    setEnd(null)
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
      </aside>
      <MapView center={LAB_CENTER} level={LAB_LEVEL} rects={LAB_RECTS} markers={markers} onMapClick={handleMapClick} />
    </div>
  )
}

export default AlgorithmLabPage
