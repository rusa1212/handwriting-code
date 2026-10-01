import { formatDistance, formatDuration, formatToll } from '../lib/format'

// 경로 하나의 요약 카드
function RouteCard({ route, selected, onClick }) {
  return (
    <li>
      <button
        type="button"
        className={selected ? 'route-card selected' : 'route-card'}
        aria-pressed={selected}
        onClick={onClick}
      >
        <span className="route-id">{route.id}</span>
        <span className="route-duration">{formatDuration(route.duration)}</span>
        <span className="route-meta">
          {formatDistance(route.distance)} · 통행료 {formatToll(route.toll)}
        </span>
      </button>
    </li>
  )
}

export default RouteCard
