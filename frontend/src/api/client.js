// FastAPI 호출 함수 모음: fetch는 이 파일에서만 쓴다
// 경로는 /api/... 로 보내고, Vite 프록시가 FastAPI(127.0.0.1:8000)로 전달한다

async function request(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  const data = await res.json().catch(() => null)

  if (!res.ok) {
    // FastAPI 오류는 { detail: ... } 형태 (422 검증 오류는 detail이 배열)
    const detail = typeof data?.detail === 'string' ? data.detail : `요청 실패 (${res.status})`
    throw new Error(detail)
  }
  return data
}

export function getHealth() {
  return request('/api/health')
}

// origin, destination: { name, lat, lng }
// 반환: [{ id, distance(m), duration(초), toll(원), path: [[lat, lng], ...] }]
export function getRoutes(origin, destination) {
  return request('/api/routes', {
    method: 'POST',
    body: JSON.stringify({ origin, destination }),
  })
}

// routes: getRoutes 결과, weights: { time, distance, toll }
// 반환: { scores: { [id]: 0~100 }, best_id, reason }
export function recommend(routes, weights) {
  // 점수 계산에 좌표는 필요 없으므로 빼고 보낸다 (경로 하나에 좌표가 수천 개)
  const metrics = routes.map(({ id, distance, duration, toll }) => ({ id, distance, duration, toll }))
  return request('/api/recommend', {
    method: 'POST',
    body: JSON.stringify({ routes: metrics, weights }),
  })
}
