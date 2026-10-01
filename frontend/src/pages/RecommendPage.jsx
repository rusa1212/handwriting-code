import { GUMI_STATION } from '../constants'
import MapView from '../components/MapView'
import PreferencePanel from '../components/PreferencePanel'
import RecommendReason from '../components/RecommendReason'
import RouteList from '../components/RouteList'
import SearchPanel from '../components/SearchPanel'

// 경로 추천 탭 (LEVEL 1~3, 5)
function RecommendPage() {
  return (
    <div className="page">
      <aside className="sidebar">
        <SearchPanel />
        <PreferencePanel />
        <RouteList />
        <RecommendReason />
      </aside>
      <MapView center={GUMI_STATION} />
    </div>
  )
}

export default RecommendPage
