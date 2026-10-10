import { LAB_BOUNDS, LAB_CENTER, LAB_LEVEL } from '../constants'
import MapView from '../components/MapView'

// 클릭할 수 있는 영역 안내. MapView는 rects가 바뀌면 다시 그리므로 렌더마다 새 배열을 만들지 않게 밖에 둔다
const LAB_RECTS = [LAB_BOUNDS]

// 알고리즘 실험실 탭 (LEVEL 4): 직접 구현한 Dijkstra/A* 실행
function AlgorithmLabPage() {
  return (
    <div className="page">
      <aside className="sidebar">
        <section className="panel">
          <h2>알고리즘 실험실</h2>
          <p className="placeholder">준비 중</p>
        </section>
      </aside>
      <MapView center={LAB_CENTER} level={LAB_LEVEL} rects={LAB_RECTS} />
    </div>
  )
}

export default AlgorithmLabPage
