import { LAB_CENTER, LAB_LEVEL } from '../constants'
import MapView from '../components/MapView'

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
      <MapView center={LAB_CENTER} level={LAB_LEVEL} />
    </div>
  )
}

export default AlgorithmLabPage
