import httpx

from config import KAKAO_REST_API_KEY
from schemas import Place, PlaceCandidate, Route, Segment

DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"
KEYWORD_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
COORD_TO_ADDRESS_URL = "https://dapi.kakao.com/v2/local/geo/coord2address.json"


class MapApiError(Exception):
    pass


def _kakao_get(url: str, params: dict, name: str) -> dict:
    """카카오 REST API 공통 호출. 실패하면 MapApiError로 바꿔 던진다."""
    try:
        res = httpx.get(
            url,
            headers={"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"},
            params=params,
            timeout=10,
        )
        res.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise MapApiError(f"{name} API 오류 {e.response.status_code}: {e.response.text}") from e
    except httpx.HTTPError as e:
        raise MapApiError(f"{name} API 호출 실패: {e}") from e
    return res.json()


def _to_path(sections: list[dict]) -> list[tuple[float, float]]:
    # vertexes는 [x1, y1, x2, y2, ...] 형태 (x=경도, y=위도) → [(lat, lng), ...]로 바꾼다
    path = []
    for section in sections:
        for road in section["roads"]:
            v = road["vertexes"]
            for i in range(0, len(v), 2):
                path.append((v[i + 1], v[i]))
    return path


def _to_segments(sections: list[dict]) -> list[Segment]:
    # 택시 요금은 구간마다 빠른지(거리 요금) 느린지(시간 요금)로 달라지므로 summary 합계가 아니라 roads[]를 쓴다
    return [
        Segment(distance=road["distance"], duration=road["duration"])
        for section in sections
        for road in section["roads"]
    ]


def fetch_directions(origin: Place, destination: Place) -> dict:
    """길찾기 API 원본 응답(JSON). 파싱은 parse_routes()가 한다 (저장한 응답으로 오프라인 검증하려고 나눴다)"""
    return _kakao_get(
        DIRECTIONS_URL,
        {
            # 카카오는 "경도,위도" 순서
            "origin": f"{origin.lng},{origin.lat}",
            "destination": f"{destination.lng},{destination.lat}",
            "alternatives": "true",
        },
        "길찾기",
    )


def parse_routes(data: dict, with_segments: bool = False) -> list[Route]:
    """길찾기 원본 응답 → Route 목록. with_segments=True면 택시비 계산용 구간 목록도 담는다"""
    routes = []
    for item in data["routes"]:
        # result_code가 0이 아니면 길을 못 찾은 경로 (summary가 없다)
        if item["result_code"] != 0:
            continue
        summary = item["summary"]
        routes.append(
            Route(
                id=chr(ord("A") + len(routes)),  # 카드에 보여줄 이름: A, B, C ...
                distance=summary["distance"],
                duration=summary["duration"],
                toll=summary["fare"]["toll"],
                path=_to_path(item["sections"]),
                kakao_taxi=summary["fare"].get("taxi"),
                segments=_to_segments(item["sections"]) if with_segments else None,
            )
        )

    if not routes:
        msg = data["routes"][0].get("result_msg", "경로 없음")
        raise MapApiError(f"경로를 찾지 못했습니다: {msg}")
    return routes


def get_routes(origin: Place, destination: Place, with_segments: bool = False) -> list[Route]:
    """카카오 모빌리티 길찾기로 대안 경로까지 받아 Route 목록으로 변환한다."""
    return parse_routes(fetch_directions(origin, destination), with_segments)


def search_places(query: str, lat: float | None = None, lng: float | None = None) -> list[PlaceCandidate]:
    """카카오 로컬 키워드 검색. 기준 좌표를 주면 가까운 장소가 위로 온다."""
    params = {"query": query, "size": 15}
    if lat is not None and lng is not None:
        params["x"] = lng  # 카카오는 x=경도, y=위도
        params["y"] = lat

    data = _kakao_get(KEYWORD_SEARCH_URL, params, "장소 검색")

    # 결과가 없으면 오류가 아니라 빈 목록. 좌표(x, y)는 문자열로 온다
    return [
        PlaceCandidate(
            id=doc["id"],
            name=doc["place_name"],
            address=doc["road_address_name"] or doc["address_name"],
            lat=float(doc["y"]),
            lng=float(doc["x"]),
        )
        for doc in data["documents"]
    ]


def reverse_geocode(lat: float, lng: float) -> Place:
    """좌표 → 주소. 지도에서 찍은 지점의 이름으로 도로명 주소(없으면 지번 주소)를 쓴다."""
    data = _kakao_get(COORD_TO_ADDRESS_URL, {"x": lng, "y": lat}, "주소 변환")

    # 바다 위처럼 주소가 없는 지점이면 documents가 비어 있다. 좌표는 그대로 쓸 수 있으므로 오류로 보지 않는다
    name = "지도에서 고른 위치"
    if data["documents"]:
        doc = data["documents"][0]
        road, jibun = doc.get("road_address"), doc.get("address")
        if road:
            name = road["address_name"]
        elif jibun:
            name = jibun["address_name"]
    return Place(name=name, lat=lat, lng=lng)
