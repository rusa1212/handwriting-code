# handwriting-code
'최대한' 손코딩으로 진행하는 경로 추천 알고리즘

## 한 일
지도 API로 경로를 받아 사용자 선호도로 추천하는 것에서 시작해, 도로망 그래프 위에서 탐색 알고리즘을 직접 구현하고 그 과정을 지도에 시각화함.

### 1. 경로 추천 탭 
- 출발지/목적지를 장소 검색, 지도 클릭, 현재 위치로 고를 수 있게 함
- 여러 경로를 카드로 비교하고, 카드를 고르면 지도에서 해당 경로를 강조함
- 거리·시간·통행료 중요도 슬라이더를 두고, 값을 경로끼리 0~1로 정규화한 뒤 가중합으로 점수를 매겨 추천 경로와 추천 이유 문장을 보여줌

### 2. 알고리즘 실험실 탭
- 전남대 용봉캠퍼스 주변 2km × 2km의 자동차 도로와 캠퍼스 안 차량 통행로를 OSM에서 받아 방향 그래프로 만듦 (일방통행 반영, 노드 2,609개)
  - 서로 오갈 수 있는 가장 큰 덩어리만 남겨 어떤 두 지점을 골라도 경로가 있게 함
- **BFS, DFS, Dijkstra, A\***(직선거리 휴리스틱)를 라이브러리 없이 직접 구현하고, 예제 그래프와 무작위 200쌍으로 터미널에서 검증함
- 탐색 과정을 애니메이션으로 보여줌
  - 방문 순서 색 그라데이션, 방금 확정한 노드 강조
  - 후보(프런티어): 발견했지만 아직 확정하지 않은 노드
  - 탐색 트리: 각 노드에 처음 도착할 때 거쳐 온 노드와 잇는 선
  - 일시정지, 속도 조절, 건너뛰기, 다시 보기
- **비교 모드**: 두 알고리즘을 지도 두 장에 같은 속도로 재생하고, 방문 노드·거리·시간을 비교 표로 보여줌

### 기술 스택
- 프론트엔드: React + Vite, 카카오맵 JS SDK
- 백엔드: FastAPI (Python), 카카오 모빌리티·로컬 REST API, OSM Overpass API

## 실행 방법

터미널 두 개를 열어 백엔드와 프론트엔드를 각각 실행합니다.
프론트엔드의 `/api/*` 요청은 Vite 프록시를 통해 백엔드로 전달되므로 백엔드를 먼저 실행

### 백엔드 (FastAPI, 포트 8000)

```powershell
cd be
.\venv\Scripts\Activate.ps1      # 가상환경 활성화
pip install -r requirements.txt  # 최초 1회
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload        # http://127.0.0.1:8000
```

- 동작 확인: http://127.0.0.1:8000/api/health → `{"status":"ok"}`
- PowerShell에서 스크립트 실행이 차단되면 먼저 실행: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 프론트엔드 (React + Vite, 포트 5173)

`frontend/.env.local` 파일에 카카오맵 JavaScript 키를 설정해야 합니다.

```
VITE_KAKAO_MAP_KEY=발급받은_키
```

```powershell
cd frontend
npm install    # 최초 1회
npm run dev    # http://localhost:5173
```
