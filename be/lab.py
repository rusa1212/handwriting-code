"""알고리즘 실험실 (LEVEL 4): 지도 좌표로 받은 출발/도착을 그래프 탐색 결과로 바꾼다

좌표 → 가장 가까운 노드 → search.py의 알고리즘 → 노드 id를 다시 좌표로
"""

import math
import sys
import time
from functools import cache

from graph import Graph, NodeId, load_osm_graph
from schemas import LatLng, SearchResponse
from search import ALGORITHMS

# 가장 가까운 노드가 이보다 멀면 그래프 영역(구미역 주변 2km) 밖을 고른 것으로 본다
MAX_SNAP_M = 500


class OutOfAreaError(Exception):
    def __init__(self, label: str, distance: float) -> None:
        super().__init__(f"{label}가 구미 실험 영역 밖입니다 (가장 가까운 도로까지 {distance:,.0f}m)")
        self.label = label
        self.distance = distance


@cache
def get_graph() -> Graph:
    """구미 OSM 그래프. 처음 부를 때 한 번만 JSON을 읽고 이후에는 같은 그래프를 돌려준다"""
    return load_osm_graph()


def _snap(graph: Graph, point: LatLng, label: str) -> NodeId:
    node_id, distance = graph.nearest_node(point.lat, point.lng)
    if distance >= MAX_SNAP_M:
        raise OutOfAreaError(label, distance)
    return node_id


def run_search(start: LatLng, end: LatLng, algorithm: str) -> SearchResponse:
    graph = get_graph()
    start_node = _snap(graph, start, "출발지")
    end_node = _snap(graph, end, "도착지")

    # 탐색 함수만 잰다 (노드 맞추기, 좌표 변환은 빼고)
    t0 = time.perf_counter()
    result = ALGORITHMS[algorithm](graph, start_node, end_node)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    return SearchResponse(
        path=[graph.coords[n] for n in result.path],
        visited_order=[graph.coords[n] for n in result.visited_order],
        cost=None if math.isinf(result.cost) else result.cost,
        elapsed_ms=elapsed_ms,
    )


def _check() -> None:
    """3-2 확인: 구미역 → 근처 좌표를 네 알고리즘으로, 영역 밖 좌표는 오류가 나는지"""
    gumi_station = LatLng(lat=36.1283, lng=128.3306)
    nearby = LatLng(lat=36.1220, lng=128.3420)
    outside = LatLng(lat=36.16, lng=128.34)  # 구미역 북쪽 3.5km

    print("[구미역 → 근처 좌표]")
    for name in ALGORITHMS:
        r = run_search(gumi_station, nearby, name)
        print(f"  {name:<8} 비용 {r.cost:>7,.0f}m, 경로 {len(r.path):>3}점, 방문 {len(r.visited_order):>4}개,"
              f" {r.elapsed_ms:.2f}ms")

    r = run_search(gumi_station, gumi_station, "astar")
    print(f"[출발 = 도착] 경로 {len(r.path)}점, 비용 {r.cost}")

    print("[영역 밖]")
    for label, start, end in [("도착이 밖", gumi_station, outside), ("출발이 밖", outside, gumi_station)]:
        try:
            run_search(start, end, "dijkstra")
            print(f"  {label}: 오류가 나지 않음!")
        except OutOfAreaError as e:
            print(f"  {label}: {e}")

    t0 = time.perf_counter()
    get_graph()
    print(f"[그래프 캐시] 두 번째 호출 {(time.perf_counter() - t0) * 1000:.3f}ms")


if __name__ == "__main__":
    # Windows 터미널(cp949)에서 한글이 깨지지 않게 한다
    sys.stdout.reconfigure(encoding="utf-8")
    _check()
