import { useEffect, useRef, useState } from 'react'
import { loadKakaoMap } from '../lib/loadKakaoMap'

const ROUTE_STYLE = { strokeWeight: 6, strokeColor: '#7a7a7a', strokeOpacity: 0.8 }

// 지도는 props로 받은 데이터를 그리기만 한다 (상태는 부모가 가진다)
// routes: [{ id, path: [[lat, lng], ...] }]
// markers: [{ label, lat, lng }]
function MapView({ center, level = 4, routes = [], markers = [] }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const [ready, setReady] = useState(false)
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
        setReady(true)
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

  // 경로 선과 마커를 그린다. routes/markers가 바뀌면 이전 것을 지우고 다시 그린다
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    const { kakao } = window

    const overlays = []
    const bounds = new kakao.maps.LatLngBounds()

    for (const route of routes) {
      const path = route.path.map(([lat, lng]) => new kakao.maps.LatLng(lat, lng))
      path.forEach((p) => bounds.extend(p))
      overlays.push(new kakao.maps.Polyline({ map, path, ...ROUTE_STYLE }))
    }

    for (const m of markers) {
      const position = new kakao.maps.LatLng(m.lat, m.lng)
      bounds.extend(position)
      overlays.push(new kakao.maps.Marker({ map, position, title: m.label }))
      overlays.push(
        new kakao.maps.CustomOverlay({
          map,
          position,
          content: `<div class="map-label">${m.label}</div>`,
          yAnchor: 2.8, // 마커 머리 위에 표시
        }),
      )
    }

    // 그린 것이 있으면 전부 화면에 들어오도록 범위를 맞춘다
    if (routes.length > 0 || markers.length > 0) map.setBounds(bounds)

    return () => overlays.forEach((o) => o.setMap(null))
  }, [ready, routes, markers])

  return (
    <div className="map-wrapper">
      <div ref={containerRef} className="map" />
      {error && <p className="map-error">{error}</p>}
    </div>
  )
}

export default MapView
