from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

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
    # 택시 모드에서만 쓴다. 승객이 실제로 내는 돈이라 통행료까지 더한다 (docs/taxi.md 7단계)
    cost: int | None = Field(default=None, description="택시: 예상 택시비 + 통행료 (원)")


class Segment(BaseModel):
    """도로 구간 하나 (카카오 roads[] 한 칸). 택시 요금의 거리·시간 병산에 쓴다 (docs/taxi.md 1단계)"""

    distance: int = Field(description="구간 거리 (m)")
    duration: int = Field(description="구간 소요 시간 (초)")


class Route(RouteMetrics):
    path: list[tuple[float, float]] = Field(description="경로 좌표 [[lat, lng], ...]")
    kakao_taxi: int | None = Field(default=None, description="카카오 예상 택시비 (원). 직접 계산한 값의 검증용")
    labels: list[str] = Field(default=[], description='이 경로를 돌려준 카카오 옵션 ("추천", "최단시간", "최단거리")')
    # 서버 안에서 택시비 계산에만 쓰고 응답 JSON에는 넣지 않는다 (경로 하나에 수백 개라 크다)
    segments: list[Segment] | None = Field(default=None, exclude=True)


# 택시 모드 (docs/taxi.md 5단계)


class TaxiRequest(BaseModel):
    origin: Place
    destination: Place
    # 심야할증을 정하는 출발 시각. 없으면 지금. 시간대가 없으면("2026-11-04T23:15") 한국 시간으로 본다
    depart_at: datetime | None = None


class TaxiFare(BaseModel):
    """택시 요금 내역 (원). base + distance_fare + time_fare + surcharge = total"""

    base: int = Field(description="기본요금")
    distance_fare: int = Field(description="거리 요금")
    time_fare: int = Field(description="시간 요금 (느린 구간)")
    surcharge: int = Field(description="할증 금액 (100원 반올림 차이 포함)")
    total: int = Field(description="예상 택시비 (통행료 제외)")
    night_rate: float = Field(description="적용한 심야할증률 (0.2 = 20%)")
    out_of_area_rate: float = Field(description="적용한 시계외 할증률")


class TaxiRoute(Route):
    fare: TaxiFare


class Weights(BaseModel):
    """사용자 선호도. 합이 1이 아니어도 된다 (계산할 때 합으로 나눈다)
    모드마다 쓰는 요소만 보낸다 (자가용: time·distance·toll, 택시: cost·time). 보내지 않은 요소는 0"""

    time: float = Field(default=0, ge=0, description="시간 중요도")
    distance: float = Field(default=0, ge=0, description="거리 중요도")
    toll: float = Field(default=0, ge=0, description="통행료 중요도")
    cost: float = Field(default=0, ge=0, description="택시 요금(택시비 + 통행료) 중요도")


class RecommendRequest(BaseModel):
    # Route를 그대로 보내도 path는 무시된다 (pydantic은 모르는 필드를 버린다)
    routes: list[RouteMetrics] = Field(min_length=1)
    weights: Weights
    mode: Literal["car", "taxi"] = "car"

    @model_validator(mode="after")
    def _taxi_needs_cost(self):
        if self.mode == "taxi" and any(r.cost is None for r in self.routes):
            raise ValueError("택시 모드는 모든 경로에 cost(택시비 + 통행료)가 있어야 합니다")
        return self


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
    # 탐색 과정 애니메이션용. "단계" = visited_order 번호
    visited_parent: list[int | None] = Field(
        description="visited_order[i]에 처음 도착할 때 거쳐 온 노드의 단계 (출발은 null). 탐색 트리 선을 그린다"
    )
    frontier: list[tuple[float, float, int, int | None]] = Field(
        description="발견한 노드 [lat, lng, 발견한 단계, 방문한 단계 또는 null]. 두 단계 사이에 후보(프런티어)로 보인다"
    )
