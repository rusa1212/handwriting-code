import { useEffect, useRef, useState } from 'react'
import { loadKakaoMap } from '../lib/loadKakaoMap'

function KakaoMap({ center, level = 4 }) {
  const containerRef = useRef(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    loadKakaoMap()
      .then((kakao) => {
        if (cancelled) return
        const position = new kakao.maps.LatLng(center.lat, center.lng)
        const map = new kakao.maps.Map(containerRef.current, { center: position, level })
        new kakao.maps.Marker({ map, position })
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })

    return () => {
      cancelled = true
    }
  }, [center.lat, center.lng, level])

  return (
    <div className="map-wrapper">
      <div ref={containerRef} className="map" />
      {error && <p className="map-error">{error}</p>}
    </div>
  )
}

export default KakaoMap
