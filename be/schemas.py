from pydantic import BaseModel, Field

# 프론트 ↔ 백엔드 API 약속 (docs/webpagePlan.md 7장)
# 단위는 API 원본 그대로 둔다: 거리 m, 시간 초, 통행료 원. km·분 변환은 화면에서 한다.


class Place(BaseModel):
    name: str
    lat: float
    lng: float


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
