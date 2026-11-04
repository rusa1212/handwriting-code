import { formatToll, formatWon } from '../lib/format'

// 할증 줄 이름: "할증 (심야 40% + 시계외 20%)"
function surchargeLabel(fare) {
  const parts = []
  if (fare.night_rate) parts.push(`심야 ${Math.round(fare.night_rate * 100)}%`)
  if (fare.out_of_area_rate) parts.push(`시계외 ${Math.round(fare.out_of_area_rate * 100)}%`)
  return parts.length ? `할증 (${parts.join(' + ')})` : '할증'
}

// 선택한 택시 경로의 요금 내역 (백엔드 /api/taxi의 fare)
// 기본 + 거리 + 시간 + 할증 = 예상 택시비, 여기에 통행료를 더하면 총 예상 비용
// title: 패널 제목 (선택한 경로 이름은 뒤에 붙는다)
function FareDetail({ route, title = '③ 요금 내역' }) {
  if (!route?.fare) {
    return (
      <section className="panel">
        <h2>{title}</h2>
        <p className="placeholder">출발지와 목적지를 고르면 예상 택시비를 계산합니다.</p>
      </section>
    )
  }

  const { fare, toll, kakao_taxi: kakao } = route
  const rows = [
    ['기본요금', fare.base],
    ['거리 요금', fare.distance_fare],
    ['시간 요금 (느린 구간)', fare.time_fare],
  ]
  if (fare.surcharge) rows.push([surchargeLabel(fare), fare.surcharge])

  return (
    <section className="panel">
      <h2>
        {title} · {route.id}
      </h2>
      <table className="fare-table">
        <tbody>
          {rows.map(([label, won]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              <td>{formatWon(won)}</td>
            </tr>
          ))}
          <tr className="fare-total">
            <th scope="row">예상 택시비</th>
            <td>{formatWon(fare.total)}</td>
          </tr>
          <tr>
            <th scope="row">통행료 (별도)</th>
            <td>{formatToll(toll)}</td>
          </tr>
          {toll > 0 && (
            <tr className="fare-total">
              <th scope="row">총 예상 비용</th>
              <td>{formatWon(fare.total + toll)}</td>
            </tr>
          )}
        </tbody>
      </table>
      {kakao != null && (
        <p className="hint">
          카카오 예상 택시비 {formatWon(kakao)} (직접 계산과 {fare.total - kakao >= 0 ? '+' : ''}
          {formatWon(fare.total - kakao)} 차이)
        </p>
      )}
      <p className="hint">
        지금 출발 기준, 서울 중형택시 요금표로 계산했습니다. 실제 요금은 교통 상황과 경로에 따라 달라집니다.
      </p>
    </section>
  )
}

export default FareDetail
