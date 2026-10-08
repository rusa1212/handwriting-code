"""그래프 탐색 알고리즘 (LEVEL 4)

BFS → DFS → Dijkstra → A* 를 직접 구현한다
모든 알고리즘은 search(graph, start, end) -> SearchResult 형태로 맞춘다

    path          출발 → 도착 노드 id 목록. 경로가 없으면 []
    visited_order 방문한(확정한) 노드 id를 순서대로. 탐색 애니메이션에 쓴다
    cost          path의 실제 도로 거리 합(m). 경로가 없으면 math.inf
"""

import heapq
import math
import random
import sys
import time
from collections import deque
from typing import NamedTuple

from graph import Graph, NodeId, load_osm_graph, sample_graph


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


def bfs(graph: Graph, start: NodeId, end: NodeId) -> SearchResult:
    """너비 우선 탐색: 출발에서 가까운(간선 수가 적은) 노드부터 차례로 방문한다

    가중치를 보지 않으므로 **간선 개수가 가장 적은** 경로를 찾는다. 거리가 가장 짧다는 보장은 없다
    visited_order = 큐에서 꺼낸 순서. 도착 노드를 꺼내면 멈춘다 (Dijkstra의 "확정"과 같은 시점)
    """
    parent: dict[NodeId, NodeId | None] = {start: None}  # 큐에 넣은(발견한) 노드는 여기에 있다
    queue = deque([start])
    visited_order = []
    while queue:
        u = queue.popleft()
        visited_order.append(u)
        if u == end:
            break
        for v, _ in graph.neighbors(u):
            # 처음 발견했을 때 parent를 정한다. 먼저 발견한 쪽이 간선 수가 적은 길이다
            if v not in parent:
                parent[v] = u
                queue.append(v)
    return make_result(graph, parent, visited_order, start, end)


def dfs(graph: Graph, start: NodeId, end: NodeId) -> SearchResult:
    """깊이 우선 탐색: 한 길로 끝까지 들어가 보고, 막히면 돌아와 다른 길로 간다

    경로는 찾지만 **최단 경로라는 보장이 없다** (어떤 길로 먼저 들어가느냐에 따라 결과가 바뀐다)
    재귀 대신 스택을 쓴다. 노드가 수천 개면 재귀 깊이 제한(기본 1000)에 걸릴 수 있다
    visited_order = 스택에서 꺼내 처음 방문한 순서. 도착 노드를 방문하면 멈춘다
    """
    parent: dict[NodeId, NodeId | None] = {}  # 방문한 노드만 여기에 있다
    stack: list[tuple[NodeId, NodeId | None]] = [(start, None)]  # (노드, 거쳐 온 노드)
    visited_order = []
    while stack:
        u, came_from = stack.pop()
        # 같은 노드가 여러 경로로 스택에 들어갈 수 있다. 처음 꺼낸 것만 방문한다
        if u in parent:
            continue
        parent[u] = came_from
        visited_order.append(u)
        if u == end:
            break
        # 거꾸로 넣어야 첫 번째 이웃이 스택 맨 위에 와서 먼저 방문된다 (재귀 DFS와 같은 순서)
        for v, _ in reversed(graph.neighbors(u)):
            if v not in parent:
                stack.append((v, u))
    return make_result(graph, parent, visited_order, start, end)


def dijkstra(graph: Graph, start: NodeId, end: NodeId) -> SearchResult:
    """다익스트라: 지금까지 알려진 거리가 가장 짧은 노드부터 하나씩 확정한다

    가중치(도로 거리)가 음수가 아니면 **거리가 가장 짧은** 경로를 보장한다
    우선순위 큐(heapq)에서 꺼낸 노드는 더 짧은 길이 나올 수 없으므로 그 순간 거리가 확정된다
    visited_order = 확정한 순서. 도착 노드를 확정하면 멈춘다
    """
    dist: dict[NodeId, float] = {start: 0}  # 지금까지 찾은 가장 짧은 거리 (아직 확정 전일 수 있다)
    parent: dict[NodeId, NodeId | None] = {start: None}
    done: set[NodeId] = set()
    heap: list[tuple[float, NodeId]] = [(0, start)]
    visited_order = []
    while heap:
        d, u = heapq.heappop(heap)
        # 더 짧은 거리를 찾을 때마다 새로 넣고 옛 항목은 지우지 않는다. 꺼낼 때 이미 확정됐으면 버린다
        if u in done:
            continue
        done.add(u)
        visited_order.append(u)
        if u == end:
            break
        for v, w in graph.neighbors(u):
            new_dist = d + w
            if v not in done and new_dist < dist.get(v, math.inf):
                dist[v] = new_dist
                parent[v] = u
                heapq.heappush(heap, (new_dist, v))
    return make_result(graph, parent, visited_order, start, end)


def astar(graph: Graph, start: NodeId, end: NodeId) -> SearchResult:
    """A*: 다익스트라와 같지만 "지금까지 거리 + 도착까지 남은 직선거리"가 가장 작은 노드부터 확정한다

    g = 출발 → 노드까지 찾은 거리, h = 노드 → 도착 직선거리(하버사인), f = g + h
    도로 거리는 직선거리보다 짧을 수 없으므로 h가 남은 거리를 부풀리지 않는다 → 다익스트라와 같은 최단 경로
    도착 반대쪽 노드는 f가 커서 뒤로 밀리므로 다익스트라보다 적게 방문한다
    visited_order = 확정한 순서. 도착 노드를 확정하면 멈춘다
    """
    g: dict[NodeId, float] = {start: 0}
    parent: dict[NodeId, NodeId | None] = {start: None}
    done: set[NodeId] = set()
    heap: list[tuple[float, NodeId]] = [(graph.distance(start, end), start)]
    visited_order = []
    while heap:
        _, u = heapq.heappop(heap)
        # 다익스트라와 같은 방식으로 옛 항목을 버린다
        # 간선마다 "도로 거리 ≥ 직선거리"이면 한 번 확정한 노드에 더 짧은 길이 나오지 않으므로 다시 열 필요가 없다
        if u in done:
            continue
        done.add(u)
        visited_order.append(u)
        if u == end:
            break
        for v, w in graph.neighbors(u):
            new_g = g[u] + w
            if v not in done and new_g < g.get(v, math.inf):
                g[v] = new_g
                parent[v] = u
                heapq.heappush(heap, (new_g + graph.distance(v, end), v))
    return make_result(graph, parent, visited_order, start, end)


ALGORITHMS = {
    "bfs": bfs,
    "dfs": dfs,
    "dijkstra": dijkstra,
    "astar": astar,
}


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


# 예제 그래프 기대값: (출발, 도착) → (경로, 비용 m). 알고리즘마다 하나씩 늘린다
EXPECTED = {
    "bfs": {
        ("B", "G"): (["B", "E", "G"], 470),  # 간선 2개. 거리로는 B-A-D-E-G(440m)가 더 짧다
        ("A", "F"): (["A", "B", "C", "F"], 370),  # A-D-E-F(320m)와 간선 수가 같으면 먼저 발견한 쪽
    },
    "dfs": {
        ("B", "G"): (["B", "A", "D", "E", "G"], 440),  # A로 먼저 들어간 덕에 우연히 최단 경로
        ("G", "A"): (["G", "E", "B", "A"], 570),  # E에서 B로 먼저 들어가 돌아간다. 최단은 G-E-D-A(340m)
    },
    "dijkstra": {
        ("B", "G"): (["B", "A", "D", "E", "G"], 440),  # B-E-G(470m)보다 간선은 많지만 짧다
        ("G", "A"): (["G", "E", "D", "A"], 340),
        ("A", "F"): (["A", "D", "E", "F"], 320),  # BFS는 같은 간선 수의 A-B-C-F(370m)를 골랐다
    },
    # 경로·비용은 다익스트라와 같아야 한다. 방문 수는 _check_algorithms에서 따로 비교한다
    "astar": {
        ("B", "G"): (["B", "A", "D", "E", "G"], 440),
        ("G", "A"): (["G", "E", "D", "A"], 340),
        ("A", "F"): (["A", "D", "E", "F"], 320),
    },
}


def _check_algorithms() -> None:
    g = sample_graph()
    # 다른 노드와 이어지지 않은 노드: 경로가 없을 때를 확인한다
    g.add_node("H", 36.126, 128.333)
    for name, search in ALGORITHMS.items():
        print(f"  [{name}]")
        cases = [(start, end, *want) for (start, end), want in EXPECTED.get(name, {}).items()]
        cases += [("G", "G", ["G"], 0), ("B", "H", [], math.inf)]
        for start, end, want_path, want_cost in cases:
            result = search(g, start, end)
            ok = result.path == want_path and result.cost == want_cost and result.visited_order[0] == start
            print(f"    {start} → {end}: {_format(result)}  {'OK' if ok else f'기대값 {want_path} {want_cost}m와 다름!'}")

    # A*는 다익스트라보다 방문 노드가 많으면 안 된다
    print("  [dijkstra vs astar 방문 수]")
    for start, end in EXPECTED["astar"]:
        d, a = len(dijkstra(g, start, end).visited_order), len(astar(g, start, end).visited_order)
        print(f"    {start} → {end}: {d}개 vs {a}개  {'OK' if a <= d else 'A*가 더 많이 방문함!'}")


def _check_osm(pairs: int = 200, seed: int = 0) -> None:
    """2-6 확인: 구미 OSM 그래프에서 무작위 출발/도착 쌍으로 네 알고리즘을 비교한다

    - 경로가 모두 있어야 한다 (가장 큰 덩어리만 남겼으므로 어떤 두 노드도 이어져 있다)
    - 다익스트라와 A*의 비용이 같고, A*의 방문 수가 다익스트라보다 많지 않아야 한다
    - BFS/DFS 비용은 다익스트라보다 짧을 수 없다
    """
    g = load_osm_graph()
    ids = list(g.coords)
    rng = random.Random(seed)  # 실행할 때마다 같은 쌍이 나오게 한다
    samples = [tuple(rng.sample(ids, 2)) for _ in range(pairs)]

    total_visited = dict.fromkeys(ALGORITHMS, 0)
    total_cost = dict.fromkeys(ALGORITHMS, 0.0)
    total_ms = dict.fromkeys(ALGORITHMS, 0.0)
    problems = []
    for start, end in samples:
        results = {}
        for name, search in ALGORITHMS.items():
            t0 = time.perf_counter()
            results[name] = search(g, start, end)
            total_ms[name] += (time.perf_counter() - t0) * 1000
            total_visited[name] += len(results[name].visited_order)
            total_cost[name] += results[name].cost

        best = results["dijkstra"].cost
        if any(not r.path or r.path[0] != start or r.path[-1] != end for r in results.values()):
            problems.append((start, end, "경로 없음 또는 출발/도착이 다름"))
        if not math.isclose(results["astar"].cost, best):
            problems.append((start, end, f"A* 비용 {results['astar'].cost:.1f}m ≠ 다익스트라 {best:.1f}m"))
        if len(results["astar"].visited_order) > len(results["dijkstra"].visited_order):
            problems.append((start, end, "A*가 다익스트라보다 많이 방문"))
        for name in ("bfs", "dfs"):
            if results[name].cost < best - 1e-6:
                problems.append((start, end, f"{name} 비용이 다익스트라보다 짧음"))

    print(f"  노드 {g.node_count()}개, 무작위 {pairs}쌍 (seed={seed})")
    print(f"  {'알고리즘':<8} {'평균 비용':>10} {'평균 방문':>9} {'평균 시간':>9}")
    for name in ALGORITHMS:
        print(f"  {name:<10} {total_cost[name] / pairs:>9,.0f}m {total_visited[name] / pairs:>9.0f}개"
              f" {total_ms[name] / pairs:>7.2f}ms")
    ratio = total_visited["astar"] / total_visited["dijkstra"] * 100
    print(f"  A* 방문 수 = 다익스트라의 {ratio:.0f}%")
    print(f"  문제 {len(problems)}건  {'OK' if not problems else ''}")
    for start, end, message in problems[:10]:
        print(f"    {start} → {end}: {message}")

    # 예외 상황
    print("  [예외 상황]")
    node = ids[0]
    for name, search in ALGORITHMS.items():
        result = search(g, node, node)
        ok = result.path == [node] and result.cost == 0
        print(f"    {name:<8} 출발 = 도착: 경로 {len(result.path)}개, 비용 {result.cost:g}m  {'OK' if ok else '다름!'}")
    # 그래프 영역 밖 클릭: 가장 가까운 노드가 멀다. 3단계 API에서 이 거리로 오류를 낸다 (예: 500m 이상)
    for label, lat, lng in [("구미역", 36.1283, 128.3306), ("영역 밖(구미역 북쪽 3.5km)", 36.16, 128.34)]:
        node_id, dist = g.nearest_node(lat, lng)
        print(f"    {label} ({lat}, {lng}) → 가장 가까운 노드 {node_id}, {dist:,.0f}m")


if __name__ == "__main__":
    # Windows 터미널(cp949)에서 한글이 깨지지 않게 한다
    sys.stdout.reconfigure(encoding="utf-8")
    print("[공통 틀 확인]")
    _check_common()
    print("\n[예제 그래프 알고리즘 확인]")
    _check_algorithms()
    print("\n[구미 OSM 그래프 확인]")
    _check_osm()
