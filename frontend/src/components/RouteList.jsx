import RouteCard from './RouteCard'

// 검색한 경로들을 카드로 나열해 비교한다
function RouteList({ routes }) {
  return (
    <section className="panel">
      <h2>③ 경로 목록</h2>
      {routes.length === 0 ? (
        <p className="placeholder">경로를 검색하면 여기에 표시됩니다.</p>
      ) : (
        <ul className="route-list">
          {routes.map((route) => (
            <RouteCard key={route.id} route={route} />
          ))}
        </ul>
      )}
    </section>
  )
}

export default RouteList
