import { useState } from 'react'
import { getRoutes } from '../api/client'
import { GUMI_STATION, PLACES } from '../constants'
import MapView from '../components/MapView'
import PreferencePanel from '../components/PreferencePanel'
import RecommendReason from '../components/RecommendReason'
import RouteList from '../components/RouteList'
import SearchPanel from '../components/SearchPanel'

// 경로 추천 탭 (LEVEL 1~3, 5)
function RecommendPage() {
  const [origin, setOrigin] = useState(PLACES[0]) // { name, lat, lng }
  const [destination, setDestination] = useState(PLACES.at(-1))
  const [routes, setRoutes] = useState([]) // API에서 받은 경로들
  const [markers, setMarkers] = useState([]) // 검색한 출발/도착 지점 (드롭다운을 바꿔도 다음 검색 전까지 유지)
  const [weights, setWeights] = useState({ time: 0.5, distance: 0.3, toll: 0.2 }) // 선호도 슬라이더
  const [selectedId, setSelectedId] = useState(null) // 지도에서 강조할 경로
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSearch() {
    setLoading(true)
    setError(null)
    try {
      const found = await getRoutes(origin, destination)
      setRoutes(found)
      setSelectedId(found[0].id) // 새로 검색하면 첫 번째 경로를 선택
      setMarkers([
        { label: `출발 · ${origin.name}`, lat: origin.lat, lng: origin.lng },
        { label: `도착 · ${destination.name}`, lat: destination.lat, lng: destination.lng },
      ])
    } catch (err) {
      setRoutes([])
      setSelectedId(null)
      setMarkers([])
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <aside className="sidebar">
        <SearchPanel
          origin={origin}
          destination={destination}
          onOriginChange={setOrigin}
          onDestinationChange={setDestination}
          onSearch={handleSearch}
          loading={loading}
          error={error}
          routeCount={routes.length}
        />
        <PreferencePanel weights={weights} onChange={setWeights} />
        <RouteList routes={routes} selectedId={selectedId} onSelect={setSelectedId} />
        <RecommendReason />
      </aside>
      <MapView center={GUMI_STATION} routes={routes} markers={markers} selectedId={selectedId} />
    </div>
  )
}

export default RecommendPage
