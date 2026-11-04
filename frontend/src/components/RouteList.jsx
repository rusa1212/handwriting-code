import RouteCard from './RouteCard'

// 검색한 경로들을 카드로 나열해 비교한다. 카드를 누르면 onSelect(id)
// result: 추천 결과 { scores, best_id } (없으면 점수와 ★를 표시하지 않는다)
// title: 모드마다 패널 번호가 달라서 받는다
function RouteList({ routes, selectedId, result, onSelect, title = '③ 경로 목록' }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {routes.length === 0 ? (
        <p className="placeholder">경로를 검색하면 여기에 표시됩니다.</p>
      ) : (
        <ul className="route-list">
          {routes.map((route) => (
            <RouteCard
              key={route.id}
              route={route}
              selected={route.id === selectedId}
              score={result?.scores[route.id]}
              best={route.id === result?.best_id}
              onClick={() => onSelect(route.id)}
            />
          ))}
        </ul>
      )}
    </section>
  )
}

export default RouteList
