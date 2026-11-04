// 지도 첫 화면: 남한 전체가 보이도록 국토 중앙 부근을 중심으로 크게 축소
export const KOREA_CENTER = { lat: 36.35, lng: 127.85 }
export const KOREA_LEVEL = 13

// 선호도 슬라이더: 모드마다 쓰는 요소와 이름. key는 백엔드 Weights 필드와 같다
export const CAR_FACTORS = [
  { key: 'time', label: '시간' },
  { key: 'distance', label: '거리' },
  { key: 'toll', label: '통행료' },
]
// 택시: 승객에게 거리는 요금에 이미 들어가 있으므로 요금(택시비 + 통행료)과 시간만 본다 (docs/taxi.md 7단계)
export const TAXI_FACTORS = [
  { key: 'cost', label: '요금' },
  { key: 'time', label: '시간' },
]

// 알고리즘 실험실:광주 전남대 주변 2km × 2km 도로망 그래프 (be/data/gwangju_roads.json)
export const LAB_CENTER = { lat: 35.1769, lng: 126.9069 } // 전남대 용봉캠퍼스
export const LAB_LEVEL = 5 // 실험 영역이 한 화면에 들어오는 확대 수준
// 비교 모드: 지도 하나의 폭이 절반이라 한 단계 축소해야 영역 가로 2km가 들어온다
export const LAB_COMPARE_LEVEL = LAB_LEVEL + 1
// gwangju_roads.json의 bbox: 클릭할 수 있는 영역을 지도에 안내할 때 쓴다 (실제 판단은 서버의 500m 규칙)
export const LAB_BOUNDS = { south: 35.16791, west: 126.8959, north: 35.18589, east: 126.9179 }
