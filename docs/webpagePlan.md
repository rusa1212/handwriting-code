# 지도 경로 추천 웹페이지 구성 계획

> 기술 스택: **React (프론트) + FastAPI (백엔드)**
> 기반 문서: `mapping.md` (지도 API 기반 경로 추천 알고리즘 프로젝트)

---

## 0. 전체 구조

```text
[브라우저: React]  ←→  [FastAPI 서버]  ←→  [지도 API / 도로 데이터]
  지도 표시, 입력 폼      알고리즘 직접 구현       경로·좌표·도로망
```

웹페이지는 **알고리즘 결과를 보여주는 화면**이다. 한 번에 크게 만들지 않고, LEVEL마다 화면이 하나씩 자라도록 진행한다.

---

## 1. API 키 관리

| 키 종류 | 위치 | 이유 |
|---|---|---|
| 지도 표시용 **JavaScript 키** (카카오맵 JS 키 등) | 프론트 `.env.local` | 브라우저용으로 만든 키. 콘솔에서 허용 도메인(`localhost:5173` 등)을 등록해 보호한다 |
| 길찾기·주소검색용 **REST 키** | 백엔드 `.env` | 프론트에 두면 개발자도구에서 그대로 노출된다 |

- Vite: 환경변수 이름이 `VITE_`로 시작해야 프론트에서 읽힌다.
- Next.js: `NEXT_PUBLIC_`으로 시작해야 한다.
- `.env`, `.env.local`은 `.gitignore`에 추가한다.

---

## 2. 데이터 출처 (중요한 함정)

카카오·네이버 길찾기 API는 **완성된 경로**만 돌려준다. LEVEL 4에서 Dijkstra를 직접 실행하려면 교차로(Node)와 도로(Edge)로 된 **도로망 원본**이 필요하므로 출처를 나눈다.

| 용도 | 데이터 출처 |
|---|---|
| LEVEL 1~3: 경로 비교, 가중치 | 길찾기 API (대안 경로, 시간, 거리, 통행료) |
| LEVEL 4~5: 직접 경로 탐색 | OpenStreetMap 도로 데이터 (구미시 일부 지역만 받아 그래프로 변환) |
| 지도 표시 | 지도 JS SDK (카카오맵 등) |

---

## 3. 화면 레이아웃

```text
┌──────────────────────────────────────────────────────┐
│  헤더:  [경로 추천]  [알고리즘 실험실]  ← 탭 2개          │
├─────────────────┬────────────────────────────────────┤
│ 사이드바          │                                    │
│                 │                                    │
│ ① 출발지 / 목적지 │                                    │
│   [검색]         │              지도                   │
│                 │       (경로 선, 출발/도착 마커)          │
│ ② 선호도 슬라이더  │                                    │
│   시간 ███████░░ │                                    │
│   거리 ████░░░░░ │                                    │
│   비용 ██░░░░░░░ │                                    │
│                 │                                    │
│ ③ 경로 카드 목록   │                                    │
│   ★ A 24분 14km  │                                    │
│     B 30분 12km  │                                    │
│                 │                                    │
│ ④ 추천 이유       │                                    │
└─────────────────┴────────────────────────────────────┘
```

- **경로 추천 탭:** LEVEL 1~3, 5 (API 경로를 받아 비교하고 추천)
- **알고리즘 실험실 탭:** LEVEL 4 (도로망 그래프 위에서 직접 구현한 Dijkstra/A* 실행, 탐색 과정 애니메이션)

탭을 나누면 알고리즘 부분을 따로 실험할 수 있어 코드가 꼬이지 않는다.

---

## 4. 프론트엔드 컴포넌트 구조

```text
src/
├─ App.jsx                  # 탭 전환, 전체 상태 보관
├─ api/
│  └─ client.js             # FastAPI 호출 함수 모음 (fetch는 여기서만)
├─ components/
│  ├─ MapView.jsx           # 지도 + 경로 선 + 마커 (공통)
│  ├─ SearchPanel.jsx       # 출발지/목적지 입력
│  ├─ PreferencePanel.jsx   # 슬라이더 3개
│  ├─ RouteList.jsx         # 경로 카드 목록
│  ├─ RouteCard.jsx
│  └─ RecommendReason.jsx
└─ pages/
   ├─ RecommendPage.jsx     # 경로 추천 탭
   └─ AlgorithmLabPage.jsx  # 알고리즘 실험실 탭
```

`MapView`는 데이터를 **props로 받아서 그리기만** 하도록 만든다. 그러면 두 탭에서 함께 쓸 수 있다.

---

## 5. 상태 설계 (RecommendPage 기준)

```js
const [origin, setOrigin] = useState(null);         // { name, lat, lng }
const [destination, setDestination] = useState(null);
const [routes, setRoutes] = useState([]);           // API에서 받은 경로들
const [weights, setWeights] = useState({ time: 0.5, distance: 0.3, toll: 0.2 });
const [result, setResult] = useState(null);         // 점수 + 추천 경로 + 이유
const [selectedId, setSelectedId] = useState(null); // 지도에서 강조할 경로
```

데이터 흐름:

```text
검색 클릭      → /api/routes    → routes 저장 → 지도에 모든 경로를 회색 선으로
슬라이더 변경  → /api/recommend → result 저장 → 추천 경로만 진한 색으로 강조
```

---

## 6. 백엔드 구조 (FastAPI)

```text
server/
├─ main.py          # FastAPI 앱, 라우트, CORS 설정
├─ schemas.py       # Pydantic 요청/응답 모델
├─ map_api.py       # 지도 API 호출 (REST 키 사용)
├─ scoring.py       # LEVEL 3 가중치 점수 계산
├─ graph.py         # 그래프 자료구조
├─ search.py        # BFS, DFS, Dijkstra, A* 직접 구현
└─ .env             # REST API 키
```

- 요청과 응답은 **Pydantic 모델**로 정의한다. `/docs`에서 바로 테스트할 수 있어 프론트 없이도 백엔드를 먼저 검증할 수 있다.
- `CORSMiddleware`로 프론트 주소(예: `http://localhost:5173`)를 허용해야 요청이 막히지 않는다.

---

## 7. 프론트 ↔ 백엔드 API 약속

화면을 만들기 전에 먼저 정해두면 양쪽을 따로 개발할 수 있다.

| 엔드포인트 | 요청 | 응답 | LEVEL |
|---|---|---|---|
| `GET /api/geocode?q=구미역` | 장소명 | `{ name, lat, lng }` | 1 |
| `POST /api/routes` | `{ origin, destination }` | `[{ id, distance, duration, toll, path: [[lat, lng], ...] }]` | 1~2 |
| `POST /api/recommend` | `{ routes, weights }` | `{ scores, best_id, reason }` | 3 |
| `POST /api/search` | `{ start, end, algorithm, weights }` | `{ path, visited_order, cost }` | 4~5 |

참고:

- 점수 계산은 프론트에서도 가능하지만, 알고리즘을 Python으로 직접 구현하는 것이 목적이므로 **백엔드에 둔다**.
- 슬라이더를 움직일 때 요청이 과도하게 가지 않도록 **300ms 정도 debounce**를 건다.
- 거리(km), 시간(분), 통행료(원)는 단위가 다르므로 그냥 더하지 말고 **정규화**한 뒤 가중치를 곱한다.

---

## 8. 단계별 개발 순서

| 순서 | 작업 | 완료 기준 | LEVEL |
|---|---|---|---|
| 1 | `MapView`: 지도만 띄우기 | 화면에 지도가 보인다 (연결한 키 확인) | 0 |
| 2 | 백엔드 `/api/routes` | `/docs`에서 구미역 → 금오산 응답 확인 | 1 |
| 3 | `SearchPanel` + 지도에 경로 선 그리기 | 검색하면 지도에 경로가 그려진다 | 1 |
| 4 | `RouteList`: 여러 경로를 카드로 비교 | 카드를 클릭하면 지도에서 해당 경로가 강조된다 | 2 |
| 5 | `PreferencePanel` + `/api/recommend` + `RecommendReason` | 슬라이더에 따라 추천 경로와 이유가 바뀐다 | 3 |
| 6 | `AlgorithmLabPage`: 그래프 표시 → Dijkstra → 탐색 애니메이션 → A* 비교 | 방문한 노드가 퍼져나가는 모습이 보이고, A*가 더 적게 탐색하는 것을 확인 | 4 |
| 7 | 실험실의 탐색 결과를 추천 탭에 통합 | 사용자 가중치로 직접 구현한 알고리즘이 경로를 추천한다 | 5 |

---

## 9. 진행 팁

- **한 단계를 끝내고 다음으로 넘어간다.** "버튼을 누르면 결과가 뜬다"까지 동작하면 그 단계는 완료.
- 알고리즘은 웹에 붙이기 전에 **터미널에서 작은 그래프(A~G 노드)로 먼저 검증**한다. 웹에서 디버깅하면 원인이 화면 쪽인지 알고리즘 쪽인지 구분하기 어렵다.
- **탐색 과정 시각화**(`visited_order` 애니메이션)는 꼭 넣는다. Dijkstra와 A*의 차이를 눈으로 확인할 수 있어 이해도를 높이는 데 가장 효과적이다.
- 단계마다 "이번에 이해한 것 / 막혔던 오류"를 짧게 기록한다.