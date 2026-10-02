// 추천 결과의 이유 문장. result: { scores, best_id, reason } (백엔드 /api/recommend)
function RecommendReason({ result, error }) {
  return (
    <section className="panel">
      <h2>④ 추천 이유</h2>
      {error ? (
        <p className="error">{error}</p>
      ) : result ? (
        <p className="reason">
          <span className="reason-best">★ {result.best_id}</span>
          {result.reason}
        </p>
      ) : (
        <p className="placeholder">경로를 검색하면 선호도에 맞는 경로를 추천합니다.</p>
      )}
    </section>
  )
}

export default RecommendReason
