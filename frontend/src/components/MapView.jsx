import { useEffect, useRef, useState } from 'react'
import { loadKakaoMap } from '../lib/loadKakaoMap'

const ROUTE_STYLE = { strokeWeight: 6, strokeColor: '#7a7a7a', strokeOpacity: 0.8, zIndex: 1 }
// 선택된 경로: 진하고 굵게, 다른 선보다 위에 그린다
const SELECTED_STYLE = { strokeWeight: 8, strokeColor: '#aa3bff', strokeOpacity: 0.95, zIndex: 2 }
// 영역 안내 사각형: 지도를 가리지 않게 옅게 채우고 점선 테두리, 경로보다 아래에 그린다
const RECT_STYLE = {
  strokeWeight: 2,
  strokeColor: '#aa3bff',
  strokeOpacity: 0.8,
  strokeStyle: 'dash',
  fillColor: '#aa3bff',
  fillOpacity: 0.06,
  zIndex: 0,
}

// 지점 선택용 커서: 기본 crosshair는 얇은 검은 선이라 지도에 묻힌다
// 흰 외곽선 위에 굵은 색 선을 겹쳐 어떤 배경에서도 보이게 한다 (중심 16,16이 클릭 지점)
const PICK_CURSOR_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <g stroke="#fff" stroke-width="5" stroke-linecap="round">
    <path d="M16 3v8M16 21v8M3 16h8M21 16h8"/>
  </g>
  <g stroke="#aa3bff" stroke-width="2.5" stroke-linecap="round">
    <path d="M16 3v8M16 21v8M3 16h8M21 16h8"/>
  </g>
  <circle cx="16" cy="16" r="3" fill="#aa3bff" stroke="#fff" stroke-width="1.5"/>
</svg>`
const PICK_CURSOR = `url("data:image/svg+xml,${encodeURIComponent(PICK_CURSOR_SVG)}") 16 16, crosshair`

// 지도는 props로 받은 데이터를 그리기만 한다 (상태는 부모가 가진다)
// routes: [{ id, path: [[lat, lng], ...] }]
// markers: [{ label, lat, lng }]
// rects: [{ south, west, north, east }] 영역 표시용 사각형 (지도 범위 맞추기에는 넣지 않는다)
// selectedId: 강조할 경로 id
// onMapClick: ({ lat, lng }) => void, 넘기면 지도 클릭으로 지점을 고를 수 있다
function MapView({ center, level = 4, routes = [], markers = [], selectedId = null, onMapClick = null, rects = [] }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const polylinesRef = useRef(new Map()) // 경로 id → Polyline (선택 변경 시 다시 그리지 않고 스타일만 바꾼다)
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
    const polylines = polylinesRef.current
    const bounds = new kakao.maps.LatLngBounds()

    for (const route of routes) {
      const path = route.path.map(([lat, lng]) => new kakao.maps.LatLng(lat, lng))
      path.forEach((p) => bounds.extend(p))
      const polyline = new kakao.maps.Polyline({ map, path, ...ROUTE_STYLE })
      polylines.set(route.id, polyline)
      overlays.push(polyline)
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

    // 경로가 있으면 경로와 핀이 전부 화면에 들어오도록 범위를 맞춘다
    // (경로 없이 핀만 있을 때는 부모가 center/level로 위치를 정한다)
    if (routes.length > 0) map.setBounds(bounds)

    return () => {
      overlays.forEach((o) => o.setMap(null))
      polylines.clear()
    }
  }, [ready, routes, markers])

  // 영역 사각형은 경로·핀과 따로 그린다 (핀을 찍을 때마다 다시 그리지 않고, 경로에 맞춘 지도 범위에도 영향이 없다)
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    const { kakao } = window

    const rectangles = rects.map(
      ({ south, west, north, east }) =>
        new kakao.maps.Rectangle({
          map,
          bounds: new kakao.maps.LatLngBounds(
            new kakao.maps.LatLng(south, west), // 남서쪽 모서리
            new kakao.maps.LatLng(north, east), // 북동쪽 모서리
          ),
          ...RECT_STYLE,
        }),
    )

    return () => rectangles.forEach((r) => r.setMap(null))
  }, [ready, rects])

  // onMapClick이 있을 때만 지도 클릭을 받는다 (지점 선택 모드). 커서도 눈에 띄는 십자 모양으로 바꾼다
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map || !onMapClick) return
    const { kakao } = window

    const handleClick = (e) => onMapClick({ lat: e.latLng.getLat(), lng: e.latLng.getLng() })
    kakao.maps.event.addListener(map, 'click', handleClick)
    map.setCursor(PICK_CURSOR)

    return () => {
      kakao.maps.event.removeListener(map, 'click', handleClick)
      map.setCursor('')
    }
  }, [ready, onMapClick])

  // 선택한 경로만 강조한다. 지도 범위는 그대로 둔다
  // (routes가 바뀌면 위 effect가 선을 새로 만든 뒤 이 effect도 다시 실행된다)
  useEffect(() => {
    for (const [id, polyline] of polylinesRef.current) {
      polyline.setOptions(id === selectedId ? SELECTED_STYLE : ROUTE_STYLE)
    }
  }, [ready, routes, selectedId])

  return (
    <div className="map-wrapper">
      <div ref={containerRef} className="map" />
      {error && <p className="map-error">{error}</p>}
    </div>
  )
}

export default MapView
