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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSearch() {
    setLoading(true)
    setError(null)
    try {
      setRoutes(await getRoutes(origin, destination))
    } catch (err) {
      setRoutes([])
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
        <PreferencePanel />
        <RouteList />
        <RecommendReason />
      </aside>
      <MapView center={GUMI_STATION} />
    </div>
  )
}

export default RecommendPage
