// 지도 첫 화면: 남한 전체가 보이도록 국토 중앙 부근을 중심으로 크게 축소
export const KOREA_CENTER = { lat: 36.35, lng: 127.85 }
export const KOREA_LEVEL = 13

// 알고리즘 실험실: 구미역 주변 2km × 2km 도로망 그래프 (be/data/gumi_roads.json)
export const LAB_CENTER = { lat: 36.1283, lng: 128.3306 } // 구미역
export const LAB_LEVEL = 5 // 실험 영역이 한 화면에 들어오는 확대 수준
// gumi_roads.json의 bbox: 클릭할 수 있는 영역을 지도에 안내할 때 쓴다 (실제 판단은 서버의 500m 규칙)
export const LAB_BOUNDS = { south: 36.11931, west: 128.31947, north: 36.13729, east: 128.34173 }
