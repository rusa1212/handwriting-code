"""그래프 탐색 알고리즘 (LEVEL 4)

BFS → DFS → Dijkstra → A* 를 직접 구현한다
모든 알고리즘은 search(graph, start, end) -> SearchResult 형태로 맞춘다

    path          출발 → 도착 노드 id 목록. 경로가 없으면 []
    visited_order 방문한(확정한) 노드 id를 순서대로. 탐색 애니메이션에 쓴다
    cost          path의 실제 도로 거리 합(m). 경로가 없으면 math.inf
"""

import math
import sys
from typing import NamedTuple

from graph import Graph, NodeId, sample_graph


class SearchResult(NamedTuple):
    path: list[NodeId]
    visited_order: list[NodeId]
    cost: float


def reconstruct_path(parent: dict[NodeId, NodeId | None], start: NodeId, end: NodeId) -> list[NodeId]:
    """parent(노드 → 그 노드에 처음 도착할 때 거쳐 온 노드)를 도착에서 거꾸로 따라가 경로를 만든다

    탐색은 출발 노드를 parent[start] = None으로 넣고 시작한다
    end가 parent에 없으면 한 번도 도착하지 못한 것이므로 경로가 없다
    """
    if end not in parent:
        return []
    path = []
    node: NodeId | None = end
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    if path[0] != start:
        raise ValueError(f"parent를 따라가도 출발 노드에 닿지 않습니다: {path}")
    return path


def path_cost(graph: Graph, path: list[NodeId]) -> float:
    """경로의 실제 도로 거리 합(m). 빈 경로는 inf, 노드 하나짜리(출발 = 도착)는 0

    BFS/DFS는 가중치를 보지 않고 경로를 찾으므로, 비용은 찾은 뒤에 이 함수로 따로 계산한다
    """
    if not path:
        return math.inf
    total = 0.0
    for u, v in zip(path, path[1:]):
        # 같은 두 노드 사이에 도로가 여러 개일 수 있으므로 가장 짧은 것을 쓴다
        weights = [w for neighbor, w in graph.neighbors(u) if neighbor == v]
        if not weights:
            raise ValueError(f"경로에 없는 도로가 있습니다: {u} → {v}")
        total += min(weights)
    return total


def make_result(graph: Graph, parent: dict[NodeId, NodeId | None], visited_order: list[NodeId],
                start: NodeId, end: NodeId) -> SearchResult:
    """탐색이 끝난 뒤 parent와 방문 순서로 공통 결과를 만든다"""
    path = reconstruct_path(parent, start, end)
    return SearchResult(path, visited_order, path_cost(graph, path))


# 2-2부터 하나씩 채운다: { "bfs": bfs, "dfs": dfs, ... }
ALGORITHMS: dict = {}


def _format(result: SearchResult) -> str:
    path = "-".join(map(str, result.path)) or "(경로 없음)"
    visited = " ".join(map(str, result.visited_order))
    cost = "없음" if math.isinf(result.cost) else f"{result.cost:g}m"
    return f"경로 {path}, 비용 {cost}, 방문 {len(result.visited_order)}개 [{visited}]"


def _check_common() -> None:
    """2-1 확인: 손으로 만든 parent로 경로 복원과 비용 계산이 맞는지"""
    g = sample_graph()
    # B에서 출발해 B → A → D → E → G로 도착했다고 가정한 parent
    parent = {"B": None, "A": "B", "C": "B", "D": "A", "E": "D", "G": "E"}
    visited = ["B", "A", "C", "D", "E", "G"]

    cases = [
        ("B → G", "B", "G", ["B", "A", "D", "E", "G"], 440),
        ("B → B (출발 = 도착)", "B", "B", ["B"], 0),
        ("B → F (도착 못 함)", "B", "F", [], math.inf),
    ]
    for label, start, end, want_path, want_cost in cases:
        result = make_result(g, parent, visited, start, end)
        ok = result.path == want_path and result.cost == want_cost
        print(f"  {label}: {_format(result)}  {'OK' if ok else f'기대값 {want_path} {want_cost}m와 다름!'}")


def _run_sample() -> None:
    g = sample_graph()
    if not ALGORITHMS:
        print("  (아직 구현한 알고리즘이 없습니다)")
    for name, search in ALGORITHMS.items():
        print(f"  {name:>8}: {_format(search(g, 'B', 'G'))}")


if __name__ == "__main__":
    # Windows 터미널(cp949)에서 한글이 깨지지 않게 한다
    sys.stdout.reconfigure(encoding="utf-8")
    print("[공통 틀 확인]")
    _check_common()
    print("\n[예제 그래프 B → G]")
    _run_sample()
