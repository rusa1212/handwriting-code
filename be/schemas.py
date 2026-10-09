from typing import Literal

from pydantic import BaseModel, Field

# 프론트 ↔ 백엔드 API 약속 (docs/webpagePlan.md 7장)
# 단위는 API 원본 그대로 둔다: 거리 m, 시간 초, 통행료 원. km·분 변환은 화면에서 한다.


class Place(BaseModel):
    name: str
    lat: float
    lng: float


class PlaceCandidate(Place):
    """장소 검색 결과 하나. 사용자가 고르면 Place로 그대로 쓸 수 있다"""

    id: str
    address: str = Field(description="도로명 주소 (없으면 지번 주소)")


class RoutesRequest(BaseModel):
    origin: Place
    destination: Place


class RouteMetrics(BaseModel):
    """점수 계산에 필요한 값만 담은 경로 (좌표 제외)"""

    id: str
    distance: int = Field(description="거리 (m)")
    duration: int = Field(description="소요 시간 (초)")
    toll: int = Field(description="통행료 (원)")


class Route(RouteMetrics):
    path: list[tuple[float, float]] = Field(description="경로 좌표 [[lat, lng], ...]")


class Weights(BaseModel):
    """사용자 선호도. 합이 1이 아니어도 된다 (계산할 때 합으로 나눈다)"""

    time: float = Field(ge=0, description="시간 중요도")
    distance: float = Field(ge=0, description="거리 중요도")
    toll: float = Field(ge=0, description="통행료 중요도")


class RecommendRequest(BaseModel):
    # Route를 그대로 보내도 path는 무시된다 (pydantic은 모르는 필드를 버린다)
    routes: list[RouteMetrics] = Field(min_length=1)
    weights: Weights


class RecommendResponse(BaseModel):
    scores: dict[str, float] = Field(description="경로 id → 점수 (0~100, 높을수록 좋음)")
    best_id: str
    reason: str


# 알고리즘 실험실 (LEVEL 4, docs/algorithmLabPlan.md 3단계)


class LatLng(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class SearchRequest(BaseModel):
    start: LatLng
    end: LatLng
    algorithm: Literal["bfs", "dfs", "dijkstra", "astar"]
    weights: Weights | None = Field(default=None, description="LEVEL 5에서 사용. LEVEL 4에서는 거리만 쓴다")


class SearchResponse(BaseModel):
    path: list[tuple[float, float]] = Field(description="경로 좌표 [[lat, lng], ...] (없으면 빈 목록)")
    visited_order: list[tuple[float, float]] = Field(description="방문(확정)한 노드 좌표, 방문 순서대로")
    # 경로가 없을 때 inf는 JSON으로 보낼 수 없으므로 None(null)으로 보낸다
    cost: float | None = Field(description="경로 거리 (m), 경로가 없으면 null")
    elapsed_ms: float = Field(description="탐색 함수 실행 시간 (ms)")
