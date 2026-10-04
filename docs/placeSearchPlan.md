# 출발지 / 목적지 자유 입력 작업 계획

> 목표: `constants.js`의 고정 장소(`PLACES`) 대신 **사용자가 원하는 위치**를 출발지·목적지로 쓴다.
> `/api/routes`는 이미 `{ name, lat, lng }`만 받으면 동작하므로, 바꿀 것은 **좌표를 얻는 방법**뿐이다.

---

## 진행 현황

| 단계 | 내용 | 구분 | 상태 |
|---|---|---|---|
| 1 | 백엔드 `GET /api/places` (카카오 키워드 검색) | 필수 | ✅ 완료 |
| 2 | `client.js`에 `searchPlaces` 추가 | 필수 | ✅ 완료 |
| 3 | `PlaceSearchInput`으로 드롭다운 대체 | 필수 | ✅ 완료 |
| 4 | 좌표로 `samePlace` 비교, ⇅ 바꾸기, 미리보기 핀 | 필수 | ✅ 완료 |
| 5 | 지도 클릭으로 지점 선택 + `/api/places/reverse` | 선택 | ✅ 완료 |
| 6 | 현재 위치 버튼 | 선택 | ✅ 완료 |

3단계까지 끝나면 "아무 장소나 검색해서 경로 찾기"가 동작한다.

---

## API 약속

| 엔드포인트 | 요청 | 응답 | 상태 |
|---|---|---|---|
| `GET /api/places?q=구미역&lat=..&lng=..` | 검색어 + (선택) 기준 좌표 | `[{ id, name, address, lat, lng }]` (최대 15개) | ✅ |
| `GET /api/places/reverse?lat=..&lng=..` | 좌표 | `{ name, lat, lng }` (name은 주소) | ✅ |

- `webpagePlan.md`의 `GET /api/geocode`(결과 1개)는 쓰지 않는다. "스타벅스", "시청"처럼 같은 이름이 여러 곳이면 첫 결과가 엉뚱할 수 있으므로 **후보 목록을 주고 사용자가 고른다.**
- `lat`, `lng`에 지도 중심을 넘기면 가까운 장소가 위로 온다.
- 검색 결과가 없으면 오류가 아니라 `[]`. 빈 검색어는 422.

---

## 1단계 ✅ 백엔드 `/api/places`

- `map_api.py`: `_kakao_get(url, params, name)` 공통 호출 함수, `search_places(query, lat, lng)`
- `schemas.py`: `PlaceCandidate(Place)` — `id`, `address` 추가
- `main.py`: `GET /api/places`

확인 결과: "금오산" 15개, "스타벅스"+구미역 좌표 → 구미 지점이 먼저, 없는 장소 → `[]`

---

## 2단계 ✅ `client.js`에 `searchPlaces`

```js
// center: { lat, lng } (선택) → 그 근처 장소가 먼저 나온다
// 반환: [{ id, name, address, lat, lng }]
export function searchPlaces(q, center) { ... }
```

- 쿼리스트링은 `URLSearchParams`로 만든다 (한글 검색어 인코딩).
- `center`가 없으면 `lat`, `lng`를 빼고 보낸다.

---

## 3단계 ✅ `PlaceSearchInput`

`SearchPanel`의 `PlaceSelect`를 대체한다.

```text
SearchPanel
├─ PlaceSearchInput (출발지)
├─ PlaceSearchInput (목적지)
└─ [경로 검색]
```

- props: `label`, `value`(선택된 Place 또는 `null`), `onChange`, `center`
- 내부 상태: `query`, `candidates`, `loading`, `error`, `open`
- 흐름: Enter 또는 🔍 → `searchPlaces(query, center)` → 후보 목록 → 클릭 시 `onChange(place)`, `query = place.name`, 목록 닫기
- 선택 후 글자를 고치면 `onChange(null)` → "글자는 바뀌었는데 좌표는 예전 것" 상태를 막는다.
- 후보에는 `name`과 `address`를 같이 보여준다 (같은 이름 구분용).
- 기존 `PLACES`는 지우지 않고 "빠른 선택" 버튼으로 남겨도 된다.
- 자동완성(입력 중 검색)은 나중에. 붙인다면 `RecommendPage`의 **300ms debounce + `ignore` 플래그** 패턴을 재사용한다.

주의: "금오산" 첫 결과는 산 정상(`남통동 산 33`)이라 길찾기가 실패한다. 기존 에러 표시로 보이므로 정상 동작이다.

---

## 4단계 ✅ 정리

- `RecommendPage`의 `samePlace`를 **이름이 아니라 좌표로** 비교한다.
- 검색 버튼 비활성화: `!origin || !destination || samePlace || loading`
- ⇅ 버튼: 출발지와 목적지를 맞바꾼다.
- 미리보기 핀: 장소를 고르면 검색 전에도 지도에 핀을 보여준다. (지금 `markers`는 검색 후에만 생긴다)

구현 메모
- `markers`는 상태가 아니라 `origin`/`destination`에서 `useMemo`로 만든다.
- 장소를 바꾸거나 ⇅ 하면 이전 경로·추천은 새 핀과 맞지 않으므로 지운다 (`clearResults`).
- 경로 검색 중에 장소를 바꾸면 그 응답은 버린다 (`searchIdRef`).
- 구미 기본값을 없앴다: `PLACES`·`GUMI_STATION` 삭제, 출발지/목적지는 빈 상태로 시작, 지도는 전국(`KOREA_CENTER`, level 13)으로 시작, 검색은 기준 좌표 없이 전국 대상.
- 장소를 고르면 지도를 그 장소로 확대한다 (`focus` 상태 → `MapView`의 `center`, `level=4`). `setBounds`는 경로가 있을 때만 쓴다.

---

## 5단계 ✅ (선택) 지도 클릭으로 지점 선택

- 백엔드: `reverse_geocode(lat, lng)`
  - `GET https://dapi.kakao.com/v2/local/geo/coord2address.json?x=경도&y=위도`
  - `documents[0].road_address`(없으면 `null`) → 없으면 `documents[0].address.address_name`
- `MapView`에 `onMapClick` prop 추가

  ```js
  kakao.maps.event.addListener(map, 'click', (e) =>
    onMapClick({ lat: e.latLng.getLat(), lng: e.latLng.getLng() }),
  )
  ```

  effect 정리 함수에서 `kakao.maps.event.removeListener`로 해제한다.
- "지도에서 출발지 선택" 버튼으로 모드를 켜고, 클릭 → `reverseGeocode` → `setOrigin`

구현 메모
- 입력칸마다 📍 버튼. 누르면 `pickTarget`('origin' | 'destination')이 켜지고, 다시 누르면 취소.
- `pickTarget`이 있을 때만 `MapView`에 `onMapClick`을 넘긴다 → 그때만 클릭 리스너 등록 + 십자 커서.
- 클릭 → `reverseGeocode` → 기존 `handleOriginChange`/`handleDestinationChange`로 넣는다 (핀, 확대, 결과 초기화가 그대로 동작).
- 주소가 없는 지점(바다, 해변 등)은 오류 대신 이름을 "지도에서 고른 위치"로 둔다.
- 주소를 받는 중에 다시 찍거나 취소하면 이전 응답은 버린다 (`pickIdRef`).

---

## 6단계 ✅ (선택) 현재 위치

- `navigator.geolocation.getCurrentPosition`으로 좌표를 받아 출발지로 쓴다.
- 이름은 `reverseGeocode`로 얻거나 "현재 위치"로 둔다.
- 권한 거부·실패 시 에러 메시지를 보여준다. (`localhost`는 https가 아니어도 동작한다)

구현 메모
- `lib/geolocation.js`: `getCurrentPosition()`을 Promise로 감싸고, 오류 코드(권한 거부·위치 없음·시간 초과)별 한국어 메시지로 바꾼다. timeout 10초, 1분 이내 위치는 재사용.
- 출발지 입력 아래 "◎ 현재 위치를 출발지로" 버튼 → 좌표 → `reverseGeocode` → `handleOriginChange` (핀, 확대, 결과 초기화가 그대로 동작).
- 주소 변환만 실패하면 이름을 "현재 위치"로 두고 좌표는 그대로 쓴다.
- 지도에서 고르기와 `pickIdRef`를 같이 쓴다: 나중에 시작한 쪽만 반영되고, 현재 위치를 누르면 지도 선택 모드는 꺼진다.
- 데스크톱은 GPS 없이 Wi-Fi/IP로 위치를 잡아 실제 위치와 수백 m 이상 차이 날 수 있다. 주소를 그대로 보여주므로 사용자가 확인할 수 있다.

---

## 예외 상황

| 상황 | 처리 |
|---|---|
| 검색 결과 0개 | "검색 결과가 없습니다" |
| 산속·바다 위 지점 | 길찾기 실패 → 기존 에러 메시지 |
| 출발지와 도착지가 너무 가까움 | 카카오 `result_code ≠ 0` → 기존 처리 |
| 검색 응답이 순서가 뒤바뀌어 도착 | `ignore` 플래그로 이전 응답을 버린다 |
| 카카오 콘솔에서 로컬 API가 꺼져 있음 | 403 → 502로 전달된다 |
