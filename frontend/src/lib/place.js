// 이름이 달라도 좌표가 같으면 같은 장소로 본다 (검색 결과마다 이름 표기가 다를 수 있다)
export function isSamePlace(a, b) {
  return Boolean(a && b) && Math.abs(a.lat - b.lat) < 1e-6 && Math.abs(a.lng - b.lng) < 1e-6
}
