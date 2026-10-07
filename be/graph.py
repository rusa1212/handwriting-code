"""도로망 그래프 자료구조 (LEVEL 4)

교차로 = Node (id, 좌표), 도로 = Edge (도착 노드, 가중치)
인접 리스트를 딕셔너리로 들고 있는다: { node_id: [(neighbor_id, weight), ...] }
"""

import json
import math
from pathlib import Path

# OSM 노드 id는 정수, 터미널 검증용 예제 그래프는 "A" 같은 문자열을 쓴다
NodeId = int | str

EARTH_RADIUS_M = 6_371_000

OSM_PATH = Path(__file__).parent / "data" / "gumi_roads.json"  # fetch_osm.py가 만든 파일


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 사이의 직선(대원) 거리(m). 지구를 구로 보고 계산한다

    A* 휴리스틱으로도 쓴다: 실제 도로 거리는 직선거리보다 짧을 수 없으므로 최단 경로를 보장한다
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


class Graph:
    def __init__(self) -> None:
        self.coords: dict[NodeId, tuple[float, float]] = {}  # node_id → (lat, lng)
        self.adj: dict[NodeId, list[tuple[NodeId, float]]] = {}  # node_id → [(neighbor_id, weight)]

    def add_node(self, node_id: NodeId, lat: float, lng: float) -> None:
        self.coords[node_id] = (lat, lng)
        self.adj.setdefault(node_id, [])

    def add_edge(self, u: NodeId, v: NodeId, weight: float, oneway: bool = False) -> None:
        """u → v 도로를 추가한다. 일방통행이 아니면 v → u도 같이 넣는다."""
        if u not in self.coords or v not in self.coords:
            raise KeyError(f"없는 노드로 도로를 만들 수 없습니다: {u} → {v}")
        self.adj[u].append((v, weight))
        if not oneway:
            self.adj[v].append((u, weight))

    def neighbors(self, node_id: NodeId) -> list[tuple[NodeId, float]]:
        return self.adj[node_id]

    def distance(self, u: NodeId, v: NodeId) -> float:
        """두 노드 사이의 직선거리(m)"""
        return haversine(*self.coords[u], *self.coords[v])

    def nearest_node(self, lat: float, lng: float) -> tuple[NodeId, float]:
        """좌표에서 가장 가까운 노드와 그 거리(m)

        지도를 클릭한 지점은 교차로와 정확히 겹치지 않으므로 가장 가까운 노드로 맞춘다
        노드 수천 개 정도는 전부 비교해도 충분히 빠르다. 너무 먼지(그래프 영역 밖인지)는 호출하는 쪽이 판단한다
        """
        if not self.coords:
            raise ValueError("노드가 없는 그래프입니다")
        return min(
            ((node_id, haversine(lat, lng, n_lat, n_lng)) for node_id, (n_lat, n_lng) in self.coords.items()),
            key=lambda item: item[1],
        )

    def node_count(self) -> int:
        return len(self.coords)

    def edge_count(self) -> int:
        # 방향 간선 수 (양방향 도로는 2개로 센다)
        return sum(len(edges) for edges in self.adj.values())


def sample_graph() -> Graph:
    """알고리즘을 웹에 붙이기 전에 터미널에서 검증할 작은 그래프

    A ─ B ─ C
    │   │   │
    D ─ E ─ F
        │
        G

    좌표는 구미역 근처 격자, 가중치(m)는 직선거리보다 작지 않게 정했다 (A* 휴리스틱 검증용)
    B ─ E는 일부러 돌아가는 길(300m)로 두어 B → G 최단 경로가 B-A-D-E-G가 되게 했다
    """
    g = Graph()
    base_lat, base_lng = 36.128, 128.330
    grid = {
        "A": (0, 0), "B": (0, 1), "C": (0, 2),
        "D": (1, 0), "E": (1, 1), "F": (1, 2),
        "G": (2, 1),
    }
    for node_id, (row, col) in grid.items():
        g.add_node(node_id, base_lat - row * 0.001, base_lng + col * 0.001)

    for u, v, w in [
        ("A", "B", 100), ("B", "C", 150),
        ("A", "D", 120), ("B", "E", 300), ("C", "F", 120),
        ("D", "E", 100), ("E", "F", 100),
        ("E", "G", 120),
    ]:
        g.add_edge(u, v, w)
    return g


def _direction(tags: dict) -> int:
    """도로의 통행 방향: 1 = 점 순서대로만, -1 = 반대로만, 0 = 양방향"""
    oneway = tags.get("oneway")
    if oneway in ("yes", "true", "1"):
        return 1
    if oneway == "-1":
        return -1
    if oneway == "no":
        return 0
    # 태그가 없어도 OSM 규칙상 고속도로와 회전교차로는 일방통행이다
    if tags.get("highway") == "motorway" or tags.get("junction") in ("roundabout", "circular"):
        return 1
    return 0


def load_osm_graph(path: Path = OSM_PATH) -> Graph:
    """fetch_osm.py가 저장한 도로 JSON → Graph

    도로(way)는 점(node) 목록이다. 이웃한 두 점마다 간선을 만들고 가중치는 두 점 사이 거리(m)로 한다
    도로가 꺾이는 지점도 노드가 되므로 노드 수가 교차로 수보다 많다 (탐색 애니메이션이 촘촘해지는 장점도 있다)
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    g = Graph()
    # JSON 객체의 키는 문자열이므로 OSM id를 정수로 되돌린다
    coords = {int(node_id): latlng for node_id, latlng in data["nodes"].items()}

    for way in data["ways"]:
        direction = _direction(way["tags"])
        for u, v in zip(way["nodes"], way["nodes"][1:]):
            for node_id in (u, v):
                if node_id not in g.coords:
                    g.add_node(node_id, *coords[node_id])
            weight = g.distance(u, v)
            if direction == -1:
                g.add_edge(v, u, weight, oneway=True)
            else:
                g.add_edge(u, v, weight, oneway=direction == 1)
    return g


def _print_sample() -> None:
    g = sample_graph()
    print(f"노드 {g.node_count()}개, 방향 간선 {g.edge_count()}개")
    for node_id in g.coords:
        edges = ", ".join(f"{v}({w}m)" for v, w in g.neighbors(node_id))
        print(f"  {node_id} → {edges}")

    # 가중치가 직선거리보다 작으면 A* 휴리스틱이 최단 경로를 보장하지 못한다
    print("\n도로 가중치 vs 직선거리")
    for u, edges in g.adj.items():
        for v, w in edges:
            if str(u) < str(v):
                straight = g.distance(u, v)
                mark = "OK" if w >= straight else "가중치가 직선거리보다 작음!"
                print(f"  {u}-{v}: {w}m / 직선 {straight:.1f}m  {mark}")

    print("\n가장 가까운 노드")
    for lat, lng in [(36.128, 128.330), (36.1272, 128.3312), (36.126, 128.3315), (36.140, 128.330)]:
        node_id, dist = g.nearest_node(lat, lng)
        print(f"  ({lat}, {lng}) → {node_id} ({dist:.1f}m)")


def _print_osm() -> None:
    g = load_osm_graph()
    print(f"노드 {g.node_count()}개, 방향 간선 {g.edge_count()}개")

    weights = [w for edges in g.adj.values() for _, w in edges]
    print(f"간선 길이: 최소 {min(weights):.1f}m, 평균 {sum(weights) / len(weights):.1f}m, 최대 {max(weights):.1f}m")

    # 나가는 길이 없는 노드: 영역 밖에서 잘린 도로 끝이나 일방통행 끝. 탐색이 여기서 멈춘다
    dead_ends = [n for n, edges in g.adj.items() if not edges]
    print(f"나가는 간선이 없는 노드: {len(dead_ends)}개")

    lats = [lat for lat, _ in g.coords.values()]
    lngs = [lng for _, lng in g.coords.values()]
    print(f"좌표 범위: 위도 {min(lats):.5f} ~ {max(lats):.5f}, 경도 {min(lngs):.5f} ~ {max(lngs):.5f}")

    node_id, dist = g.nearest_node(36.1283, 128.3306)
    print(f"구미역에서 가장 가까운 노드: {node_id} ({dist:.1f}m), 이웃 {len(g.neighbors(node_id))}개")


if __name__ == "__main__":
    print("[예제 그래프 A~G]")
    _print_sample()
    print("\n[구미 OSM 그래프]")
    _print_osm()
