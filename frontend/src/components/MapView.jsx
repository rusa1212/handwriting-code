import { useEffect, useRef, useState } from 'react'
import { loadKakaoMap } from '../lib/loadKakaoMap'

// 지도는 props로 받은 데이터를 그리기만 한다 (상태는 부모가 가진다)
function MapView({ center, level = 4 }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const [error, setError] = useState(null)

  // 지도 객체는 처음 한 번만 만든다
  useEffect(() => {
    let cancelled = false

    loadKakaoMap()
      .then((kakao) => {
        if (cancelled || mapRef.current) return
        mapRef.current = new kakao.maps.Map(containerRef.current, {
          center: new kakao.maps.LatLng(center.lat, center.lng),
          level,
        })
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })

    return () => {
      cancelled = true
    }
    // 처음 만들 때의 center/level만 쓰고, 이후 변경은 아래 effect가 처리한다
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // center, level이 바뀌면 지도를 새로 만들지 않고 이동만 한다
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    map.setCenter(new window.kakao.maps.LatLng(center.lat, center.lng))
    map.setLevel(level)
  }, [center.lat, center.lng, level])

  return (
    <div className="map-wrapper">
      <div ref={containerRef} className="map" />
      {error && <p className="map-error">{error}</p>}
    </div>
  )
}

export default MapView
