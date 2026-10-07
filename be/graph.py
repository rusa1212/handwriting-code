"""도로망 그래프 자료구조 (LEVEL 4)

교차로 = Node (id, 좌표), 도로 = Edge (도착 노드, 가중치)
인접 리스트를 딕셔너리로 들고 있는다: { node_id: [(neighbor_id, weight), ...] }
"""

import math

# OSM 노드 id는 정수, 터미널 검증용 예제 그래프는 "A" 같은 문자열을 쓴다
NodeId = int | str

EARTH_RADIUS_M = 6_371_000


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


if __name__ == "__main__":
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
