# handwriting-code
'최대한' 손코딩으로 진행하는 경로 추천 알고리즘

## 실행 방법

터미널 두 개를 열어 백엔드와 프론트엔드를 각각 실행합니다.
프론트엔드의 `/api/*` 요청은 Vite 프록시를 통해 백엔드로 전달되므로 백엔드를 먼저 실행하세요.

### 백엔드 (FastAPI, 포트 8000)

```powershell
cd be
.\venv\Scripts\Activate.ps1      # 가상환경 활성화
pip install -r requirements.txt  # 최초 1회
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
