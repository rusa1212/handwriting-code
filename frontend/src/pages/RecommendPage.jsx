import { useEffect, useMemo, useRef, useState } from 'react'
import { getRoutes, recommend, reverseGeocode } from '../api/client'
import { KOREA_CENTER, KOREA_LEVEL } from '../constants'
import { getCurrentPosition } from '../lib/geolocation'
import MapView from '../components/MapView'
import PreferencePanel from '../components/PreferencePanel'
import RecommendReason from '../components/RecommendReason'
import RouteList from '../components/RouteList'
import SearchPanel from '../components/SearchPanel'

// 경로 추천 탭 (LEVEL 1~3, 5)
function RecommendPage() {
  const [origin, setOrigin] = useState(null) // { name, lat, lng } 또는 null (검색해서 고르기 전)
  const [destination, setDestination] = useState(null)
  const [focus, setFocus] = useState(null) // 마지막으로 고른 장소: 지도를 그곳으로 확대한다
  const [routes, setRoutes] = useState([]) // API에서 받은 경로들
  const [weights, setWeights] = useState({ time: 0.5, distance: 0.3, toll: 0.2 }) // 선호도 슬라이더
  const [result, setResult] = useState(null) // { scores, best_id, reason }
  const [recommendError, setRecommendError] = useState(null)
  const [selectedId, setSelectedId] = useState(null) // 지도에서 강조할 경로
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const searchIdRef = useRef(0) // 검색 중에 장소를 바꾸면 그 검색의 응답은 버린다
  const [pickTarget, setPickTarget] = useState(null) // 지도 클릭으로 고르는 중인 칸: 'origin' | 'destination' | null
  const [pickLoading, setPickLoading] = useState(false) // 찍은 지점의 주소를 받아오는 중
  const [locating, setLocating] = useState(false) // 현재 위치를 확인하는 중
  // 주소를 받는 중에 다시 찍거나 취소하면 이전 응답은 버린다 (현재 위치 확인과 같이 쓴다: 나중에 시작한 쪽만 반영)
  const pickIdRef = useRef(0)

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

  // 출발/도착 핀: 고르는 즉시(경로 검색 전에도) 지도에 보여준다
  // MapView는 markers가 바뀌면 다시 그리므로 장소가 바뀔 때만 새 배열을 만든다
  const markers = useMemo(
    () =>
      [
        origin && { label: `출발 · ${origin.name}`, lat: origin.lat, lng: origin.lng },
        destination && { label: `도착 · ${destination.name}`, lat: destination.lat, lng: destination.lng },
      ].filter(Boolean),
    [origin, destination],
  )

  // 장소가 바뀌면 이전 경로는 새 핀과 맞지 않으므로 지운다
  function clearResults() {
    searchIdRef.current++
    setLoading(false)
    setRoutes([])
    setResult(null)
    setRecommendError(null)
    setSelectedId(null)
    setError(null)
  }

  function handleOriginChange(place) {
    setOrigin(place)
    if (place) setFocus(place)
    clearResults()
  }

  function handleDestinationChange(place) {
    setDestination(place)
    if (place) setFocus(place)
    clearResults()
  }

  function handlePickTargetChange(target) {
    pickIdRef.current++
    setPickLoading(false)
    setLocating(false)
    setPickTarget(target)
  }

  // 지점 선택 모드에서 지도를 클릭하면 좌표 → 주소로 바꿔 해당 칸에 넣는다
  async function handleMapClick(latLng) {
    const pickId = ++pickIdRef.current
    const target = pickTarget
    setPickLoading(true)
    try {
      const place = await reverseGeocode(latLng)
      if (pickId !== pickIdRef.current) return
      if (target === 'origin') handleOriginChange(place)
      else handleDestinationChange(place)
      setPickTarget(null)
    } catch (err) {
      if (pickId !== pickIdRef.current) return
      setError(err.message)
    } finally {
      if (pickId === pickIdRef.current) setPickLoading(false)
    }
  }

  // 현재 위치 → 주소로 바꿔 출발지에 넣는다
  async function handleLocate() {
    const pickId = ++pickIdRef.current
    setPickTarget(null) // 지도에서 고르는 중이었다면 끈다
    setPickLoading(false)
    setLocating(true)
    setError(null)
    try {
      const latLng = await getCurrentPosition()
      if (pickId !== pickIdRef.current) return
      // 주소 변환이 실패해도 좌표는 쓸 수 있으므로 이름만 "현재 위치"로 둔다
      const place = await reverseGeocode(latLng).catch(() => ({ name: '현재 위치', ...latLng }))
      if (pickId !== pickIdRef.current) return
      handleOriginChange(place)
    } catch (err) {
      if (pickId !== pickIdRef.current) return
      setError(err.message)
    } finally {
      if (pickId === pickIdRef.current) setLocating(false)
    }
  }

  function handleSwap() {
    setOrigin(destination)
    setDestination(origin)
    clearResults()
  }

  async function handleSearch() {
    const searchId = ++searchIdRef.current
    setLoading(true)
    setError(null)
    // 이전 경로의 추천 결과는 새 경로와 id가 맞지 않으므로 지운다 (새 추천은 위 effect가 받는다)
    setResult(null)
    setRecommendError(null)
    try {
      const found = await getRoutes(origin, destination)
      if (searchId !== searchIdRef.current) return
      setRoutes(found)
      setSelectedId(found[0].id) // 추천이 도착하기 전까지는 첫 번째 경로를 선택
    } catch (err) {
      if (searchId !== searchIdRef.current) return
      setRoutes([])
      setSelectedId(null)
      setError(err.message)
    } finally {
      if (searchId === searchIdRef.current) setLoading(false)
    }
  }

  return (
    <div className="page">
      <aside className="sidebar">
        <SearchPanel
          origin={origin}
          destination={destination}
          onOriginChange={handleOriginChange}
          onDestinationChange={handleDestinationChange}
          onSwap={handleSwap}
          pickTarget={pickTarget}
          onPickTargetChange={handlePickTargetChange}
          pickLoading={pickLoading}
          onLocate={handleLocate}
          locating={locating}
          onSearch={handleSearch}
          loading={loading}
          error={error}
          routeCount={routes.length}
        />
        <PreferencePanel weights={weights} onChange={setWeights} />
        <RouteList routes={routes} selectedId={selectedId} result={result} onSelect={setSelectedId} />
        <RecommendReason result={result} error={recommendError} />
      </aside>
      <MapView
        center={focus ?? KOREA_CENTER}
        level={focus ? 4 : KOREA_LEVEL}
        routes={routes}
        markers={markers}
        selectedId={selectedId}
        onMapClick={pickTarget ? handleMapClick : null}
      />
    </div>
  )
}

export default RecommendPage
