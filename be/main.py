from fastapi import FastAPI, HTTPException

from map_api import MapApiError, get_routes
from schemas import Route, RoutesRequest

app = FastAPI()


# 프론트엔드는 Vite 프록시를 통해 /api/* 요청을 이 서버로 보낸다
@app.get("/api/health")
def health():
    return {"status": "ok"}


# LEVEL 1~2: 출발지 → 목적지 경로 목록 (대안 경로 포함)
@app.post("/api/routes")
def routes(req: RoutesRequest) -> list[Route]:
    try:
        return get_routes(req.origin, req.destination)
    except MapApiError as e:
        # 외부 API 쪽 문제이므로 502 (Bad Gateway)
        raise HTTPException(status_code=502, detail=str(e)) from e
