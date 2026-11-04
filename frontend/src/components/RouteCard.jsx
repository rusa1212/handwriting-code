import { formatDistance, formatDuration, formatToll, formatWon } from '../lib/format'

// 경로 하나의 요약 카드
// score: 추천 점수 (추천을 받기 전에는 undefined), best: 추천 경로이면 ★ 표시
// 택시 경로(route.fare가 있음)는 예상 택시비를 크게, 시간은 옆에 작게 보여 준다
function RouteCard({ route, selected, score, best, onClick }) {
  const fare = route.fare

  return (
    <li>
      <button
        type="button"
        className={selected ? 'route-card selected' : 'route-card'}
        aria-pressed={selected}
        onClick={onClick}
      >
        <span className="route-id">{route.id}</span>
        {fare ? (
          <span className="route-duration">
            {formatWon(fare.total)}
            <span className="route-sub"> · {formatDuration(route.duration)}</span>
            {best && <span className="route-best"> ★ 추천</span>}
          </span>
        ) : (
          <span className="route-duration">
            {formatDuration(route.duration)}
            {best && <span className="route-best"> ★ 추천</span>}
          </span>
        )}
        {score !== undefined && <span className="route-score">{Math.round(score)}점</span>}
        <span className="route-meta">
          {formatDistance(route.distance)} · 통행료 {formatToll(route.toll)}
          {/* 통행료는 승객이 따로 내므로 있을 때만 합계를 보여 준다 */}
          {fare && route.toll > 0 && ` · 합계 ${formatWon(fare.total + route.toll)}`}
        </span>
      </button>
    </li>
  )
}

export default RouteCard
