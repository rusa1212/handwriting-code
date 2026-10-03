from fastapi import FastAPI, HTTPException, Query

from map_api import MapApiError, get_routes, search_places
from schemas import PlaceCandidate, RecommendRequest, RecommendResponse, Route, RoutesRequest
from scoring import recommend

app = FastAPI()


# 프론트엔드는 Vite 프록시를 통해 /api/* 요청을 이 서버로 보낸다
@app.get("/api/health")
def health():
    return {"status": "ok"}


# 장소명/주소로 출발지·목적지 후보를 찾는다. lat, lng를 주면 그 근처가 먼저 나온다
@app.get("/api/places")
def places(
    q: str = Query(min_length=1),
    lat: float | None = None,
    lng: float | None = None,
) -> list[PlaceCandidate]:
    try:
        return search_places(q, lat, lng)
    except MapApiError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


# LEVEL 1~2: 출발지 → 목적지 경로 목록 (대안 경로 포함)
@app.post("/api/routes")
def routes(req: RoutesRequest) -> list[Route]:
    try:
        return get_routes(req.origin, req.destination)
    except MapApiError as e:
        # 외부 API 쪽 문제이므로 502 (Bad Gateway)
        raise HTTPException(status_code=502, detail=str(e)) from e


# LEVEL 3: 받은 경로들에 사용자 가중치를 적용해 점수·추천 경로·이유를 돌려준다
@app.post("/api/recommend")
def recommend_route(req: RecommendRequest) -> RecommendResponse:
    return recommend(req.routes, req.weights)
