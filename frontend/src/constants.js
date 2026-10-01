// 지도 기본 중심: 구미역
export const GUMI_STATION = { lat: 36.1283, lng: 128.3309 }

// /api/geocode가 생기기 전까지 쓰는 장소 목록
// 좌표는 길찾기 API가 경로를 찾을 수 있는 도로 근처로 골랐다 (산 정상 등은 실패한다)
export const PLACES = [
  { name: '구미역', ...GUMI_STATION },
  { name: '구미시청', lat: 36.1195, lng: 128.3443 },
  { name: '금오산 입구', lat: 36.1123, lng: 128.3175 },
  { name: '금오공대', lat: 36.1461, lng: 128.3934 },
  { name: '김천구미역', lat: 36.1135, lng: 128.1806 },
  { name: '대구역', lat: 35.8794, lng: 128.6286 }, // 대안 경로가 2개 나오는 테스트용
]
