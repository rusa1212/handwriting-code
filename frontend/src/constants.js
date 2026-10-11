// 지도 첫 화면: 남한 전체가 보이도록 국토 중앙 부근을 중심으로 크게 축소
export const KOREA_CENTER = { lat: 36.35, lng: 127.85 }
export const KOREA_LEVEL = 13

// 알고리즘 실험실: 광주 전남대 주변 2km × 2km 도로망 그래프 (be/data/gwangju_roads.json)
export const LAB_CENTER = { lat: 35.1769, lng: 126.9069 } // 전남대 용봉캠퍼스
export const LAB_LEVEL = 5 // 실험 영역이 한 화면에 들어오는 확대 수준
// gwangju_roads.json의 bbox: 클릭할 수 있는 영역을 지도에 안내할 때 쓴다 (실제 판단은 서버의 500m 규칙)
export const LAB_BOUNDS = { south: 35.16791, west: 126.8959, north: 35.18589, east: 126.9179 }
