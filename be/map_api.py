import httpx

from config import KAKAO_REST_API_KEY
from schemas import Place, Route

DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"


class MapApiError(Exception):
    pass


def _to_path(sections: list[dict]) -> list[tuple[float, float]]:
    # vertexes는 [x1, y1, x2, y2, ...] 형태 (x=경도, y=위도) → [(lat, lng), ...]로 바꾼다
    path = []
    for section in sections:
        for road in section["roads"]:
            v = road["vertexes"]
            for i in range(0, len(v), 2):
                path.append((v[i + 1], v[i]))
    return path


def get_routes(origin: Place, destination: Place) -> list[Route]:
    """카카오 모빌리티 길찾기로 대안 경로까지 받아 Route 목록으로 변환한다."""
    try:
        res = httpx.get(
            DIRECTIONS_URL,
            headers={"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"},
            params={
                # 카카오는 "경도,위도" 순서
                "origin": f"{origin.lng},{origin.lat}",
                "destination": f"{destination.lng},{destination.lat}",
                "alternatives": "true",
            },
            timeout=10,
        )
        res.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise MapApiError(f"길찾기 API 오류 {e.response.status_code}: {e.response.text}") from e
    except httpx.HTTPError as e:
        raise MapApiError(f"길찾기 API 호출 실패: {e}") from e

    routes = []
    for item in res.json()["routes"]:
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
            )
        )

    if not routes:
        msg = res.json()["routes"][0].get("result_msg", "경로 없음")
        raise MapApiError(f"경로를 찾지 못했습니다: {msg}")
    return routes
