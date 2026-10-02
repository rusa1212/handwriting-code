import { formatDistance, formatDuration, formatToll } from '../lib/format'

// 경로 하나의 요약 카드
// score: 추천 점수 (추천을 받기 전에는 undefined), best: 추천 경로이면 ★ 표시
function RouteCard({ route, selected, score, best, onClick }) {
  return (
    <li>
      <button
        type="button"
        className={selected ? 'route-card selected' : 'route-card'}
        aria-pressed={selected}
        onClick={onClick}
      >
        <span className="route-id">{route.id}</span>
        <span className="route-duration">
          {formatDuration(route.duration)}
          {best && <span className="route-best"> ★ 추천</span>}
        </span>
        {score !== undefined && <span className="route-score">{Math.round(score)}점</span>}
        <span className="route-meta">
          {formatDistance(route.distance)} · 통행료 {formatToll(route.toll)}
        </span>
      </button>
    </li>
  )
}

export default RouteCard
