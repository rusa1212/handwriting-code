import { useEffect, useState } from 'react'
import { getRoutes, recommend } from '../api/client'
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
  const [result, setResult] = useState(null) // { scores, best_id, reason }
  const [recommendError, setRecommendError] = useState(null)
  const [selectedId, setSelectedId] = useState(null) // 지도에서 강조할 경로
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 경로나 가중치가 바뀌면 추천을 다시 받는다
  // 슬라이더를 끄는 동안 요청이 쏟아지지 않도록 마지막 변경 후 300ms 기다렸다 보낸다 (debounce)
  useEffect(() => {
    if (routes.length === 0) return // 결과 초기화는 검색할 때(handleSearch) 한다
    let ignore = false // 늦게 도착한 이전 요청의 응답은 버린다
    const timer = setTimeout(() => {
      recommend(routes, weights)
        .then((data) => {
          if (ignore) return
          setResult(data)
          setRecommendError(null)
          setSelectedId(data.best_id) // 추천 경로를 지도에서 강조
        })
        .catch((err) => {
          if (ignore) return
          setResult(null)
          setRecommendError(err.message)
        })
    }, 300)
    return () => {
      ignore = true
      clearTimeout(timer)
    }
  }, [routes, weights])

  async function handleSearch() {
    setLoading(true)
    setError(null)
    // 이전 경로의 추천 결과는 새 경로와 id가 맞지 않으므로 지운다 (새 추천은 위 effect가 받는다)
    setResult(null)
    setRecommendError(null)
    try {
      const found = await getRoutes(origin, destination)
      setRoutes(found)
      setSelectedId(found[0].id) // 추천이 도착하기 전까지는 첫 번째 경로를 선택
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
        <RouteList routes={routes} selectedId={selectedId} result={result} onSelect={setSelectedId} />
        <RecommendReason result={result} error={recommendError} />
      </aside>
      <MapView center={GUMI_STATION} routes={routes} markers={markers} selectedId={selectedId} />
    </div>
  )
}

export default RecommendPage
