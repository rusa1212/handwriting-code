from schemas import RouteMetrics, Weights

# LEVEL 3: 사용자 가중치로 경로 점수를 계산한다
# 거리(m), 시간(초), 통행료(원)는 단위가 달라 그대로 더할 수 없으므로
# 경로들 사이에서 0(가장 좋음) ~ 1(가장 나쁨)로 정규화한 뒤 가중치를 곱한다


def _normalize(values: list[int]) -> list[float]:
    """min-max 정규화. 모든 값이 같으면 차이가 없으므로 전부 0"""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def score_routes(routes: list[RouteMetrics], weights: Weights) -> dict[str, float]:
    """경로 id → 점수 (0~100, 높을수록 좋음)"""
    total = weights.time + weights.distance + weights.toll
    if total == 0:
        # 슬라이더를 전부 0으로 두면 세 요소를 똑같이 본다
        weights = Weights(time=1, distance=1, toll=1)
        total = 3

    times = _normalize([r.duration for r in routes])
    distances = _normalize([r.distance for r in routes])
    tolls = _normalize([r.toll for r in routes])

    scores = {}
    for i, route in enumerate(routes):
        cost = (
            times[i] * weights.time
            + distances[i] * weights.distance
            + tolls[i] * weights.toll
        ) / total  # 0~1, 낮을수록 좋음
        scores[route.id] = round((1 - cost) * 100, 1)
    return scores


if __name__ == "__main__":
    # docs/mapping.md LEVEL 2 예시로 확인: python scoring.py
    routes = [
        RouteMetrics(id="A", distance=15000, duration=25 * 60, toll=0),
        RouteMetrics(id="B", distance=12000, duration=30 * 60, toll=1000),
        RouteMetrics(id="C", distance=18000, duration=20 * 60, toll=2000),
    ]
    cases = {
        "시간 중심": Weights(time=0.7, distance=0.2, toll=0.1),
        "비용 중심": Weights(time=0.2, distance=0.3, toll=0.5),
        "거리 중심": Weights(time=0.1, distance=0.8, toll=0.1),
        "전부 0": Weights(time=0, distance=0, toll=0),
    }
    for name, w in cases.items():
        scores = score_routes(routes, w)
        best = max(scores, key=scores.get)
        print(f"{name}: {scores} → 추천 {best}")
