"""OSM 도로망 내려받기 (LEVEL 4, 1-3단계)

Overpass API로 구미역 주변 도로를 받아 data/gumi_roads.json에 저장한다
서버는 이 파일만 읽으므로 영역을 바꿀 때만 다시 실행하면 된다:  python fetch_osm.py

데이터 출처: © OpenStreetMap contributors (ODbL) — 화면에 표시할 때 출처를 적어야 한다
"""

import json
import math
import time
from pathlib import Path

import httpx

from graph import EARTH_RADIUS_M

# 공용 서버는 자원봉사로 운영된다. 혼잡하면(429/504) 다음 서버로 넘어간다
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
RETRY_WAITS_S = [0, 5, 15, 30, 60]  # 시도마다 기다리는 시간 (첫 시도는 바로)

CENTER = (36.1283, 128.3306)  # 구미역
HALF_SIZE_M = 1000  # 중심에서 사방 1km → 2km × 2km

# 자동차가 다니는 도로만 받는다 (인도·자전거길·계단·주차장 통로 등은 뺀다)
CAR_HIGHWAYS = [
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
    "living_street",
]

# 그래프를 만들 때 쓸 태그만 남긴다
KEEP_TAGS = ["highway", "oneway", "maxspeed", "name", "junction"]

OUT_PATH = Path(__file__).parent / "data" / "gumi_roads.json"


def bbox(center: tuple[float, float], half_size_m: float) -> tuple[float, float, float, float]:
    """중심 좌표에서 사방 half_size_m만큼의 영역 → (남, 서, 북, 동)"""
    lat, lng = center
    d_lat = math.degrees(half_size_m / EARTH_RADIUS_M)
    # 경도 1도의 길이는 위도가 높을수록 짧아진다
    d_lng = math.degrees(half_size_m / (EARTH_RADIUS_M * math.cos(math.radians(lat))))
    return (lat - d_lat, lng - d_lng, lat + d_lat, lng + d_lng)


def build_query(box: tuple[float, float, float, float]) -> str:
    south, west, north, east = box
    highways = "|".join(CAR_HIGHWAYS)
    # 도로(way)를 받고, 그 도로가 지나는 점(node)의 좌표도 같이 받는다
    return f"""
[out:json][timeout:60];
way["highway"~"^({highways})$"]({south},{west},{north},{east});
(._;>;);
out body;
"""


def fetch(query: str) -> dict:
    """서버가 바쁘면(504 등) 잠시 기다렸다가 서버를 바꿔 가며 다시 시도한다"""
    last_error = None
    for attempt, wait_s in enumerate(RETRY_WAITS_S):
        if wait_s:
            print(f"  {wait_s}초 뒤 다시 시도합니다")
            time.sleep(wait_s)
        url = OVERPASS_URLS[attempt % len(OVERPASS_URLS)]
        try:
            res = httpx.post(
                url,
                data={"data": query},
                # 기본 User-Agent(python-httpx)는 406으로 거절된다
                headers={"User-Agent": "handwriting-code-route-lab/0.1 (study project)"},
                timeout=90,
            )
            res.raise_for_status()
            return res.json()
        except httpx.HTTPError as e:
            print(f"  {url} 실패: {e}")
            last_error = e
    raise RuntimeError(f"모든 Overpass 서버 호출 실패: {last_error}")


def simplify(raw: dict, box: tuple[float, float, float, float]) -> dict:
    """Overpass 응답에서 그래프에 필요한 것만 남긴다

    nodes: { id: [lat, lng] }
    ways:  [{ id, nodes: [node_id, ...], tags: {...} }]
    """
    nodes = {}
    ways = []
    for el in raw["elements"]:
        if el["type"] == "node":
            nodes[el["id"]] = [el["lat"], el["lon"]]
        elif el["type"] == "way":
            tags = {k: v for k, v in el.get("tags", {}).items() if k in KEEP_TAGS}
            ways.append({"id": el["id"], "nodes": el["nodes"], "tags": tags})
    return {
        "attribution": "© OpenStreetMap contributors (ODbL)",
        "bbox": box,
        "nodes": nodes,
        "ways": ways,
    }


if __name__ == "__main__":
    box = bbox(CENTER, HALF_SIZE_M)
    print(f"영역 (남, 서, 북, 동): {tuple(round(v, 5) for v in box)}")

    data = simplify(fetch(build_query(box)), box)

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    print(f"저장: {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")
    print(f"도로(way) {len(data['ways'])}개, 점(node) {len(data['nodes'])}개")

    by_type: dict[str, int] = {}
    for way in data["ways"]:
        by_type[way["tags"]["highway"]] = by_type.get(way["tags"]["highway"], 0) + 1
    for highway, count in sorted(by_type.items(), key=lambda item: -item[1]):
        print(f"  {highway}: {count}")
    print(f"일방통행 도로: {sum(1 for w in data['ways'] if w['tags'].get('oneway') == 'yes')}개")
