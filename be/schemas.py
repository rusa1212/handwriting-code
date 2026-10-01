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


class Route(BaseModel):
    id: str
    distance: int = Field(description="거리 (m)")
    duration: int = Field(description="소요 시간 (초)")
    toll: int = Field(description="통행료 (원)")
    path: list[tuple[float, float]] = Field(description="경로 좌표 [[lat, lng], ...]")
