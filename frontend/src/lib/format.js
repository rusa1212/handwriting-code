// 백엔드는 원본 단위(m, 초, 원)로 보내고, 화면에 보여줄 때만 변환한다

// 51240 → "51.2km"
export function formatDistance(meters) {
  return `${(meters / 1000).toFixed(1)}km`
}

// 544 → "9분", 3900 → "1시간 5분"
export function formatDuration(seconds) {
  const minutes = Math.max(1, Math.round(seconds / 60)) // 1분 미만도 "1분"으로
  if (minutes < 60) return `${minutes}분`
  const rest = minutes % 60
  return rest ? `${Math.floor(minutes / 60)}시간 ${rest}분` : `${minutes / 60}시간`
}

// 2900 → "2,900원", 0 → "무료"
export function formatToll(won) {
  return won ? `${won.toLocaleString()}원` : '무료'
}
