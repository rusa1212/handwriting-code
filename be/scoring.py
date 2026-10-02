from schemas import RecommendResponse, RouteMetrics, Weights

# LEVEL 3: 사용자 가중치로 경로 점수를 계산한다
# 거리(m), 시간(초), 통행료(원)는 단위가 달라 그대로 더할 수 없으므로
# 경로들 사이에서 0(가장 좋음) ~ 1(가장 나쁨)로 정규화한 뒤 가중치를 곱한다


def _normalize(values: list[int]) -> list[float]:
    """min-max 정규화. 모든 값이 같으면 차이가 없으므로 전부 0"""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _effective(weights: Weights) -> Weights:
    # 슬라이더를 전부 0으로 두면 세 요소를 똑같이 본다
    if weights.time + weights.distance + weights.toll == 0:
        return Weights(time=1, distance=1, toll=1)
    return weights


def score_routes(routes: list[RouteMetrics], weights: Weights) -> dict[str, float]:
    """경로 id → 점수 (0~100, 높을수록 좋음)"""
    weights = _effective(weights)
    total = weights.time + weights.distance + weights.toll

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


# ---- 추천 이유 문장 ----
# 한국어는 이어지는 말("빠르고")과 끝나는 말("빠릅니다")의 형태가 달라서 둘 다 둔다

# 요소 이름 (목적격 조사 포함), 경로에서 꺼낼 값
FACTORS = {
    "time": ("시간을", lambda r: r.duration),
    "distance": ("거리를", lambda r: r.distance),
    "toll": ("통행료를", lambda r: r.toll),
}

# 추천 경로가 그 요소에서 1등일 때: (이어지는 말, 꾸미는 말)
STRENGTHS = {
    "time": ("가장 빠르고", "가장 빠른"),
    "distance": ("가장 짧고", "가장 짧은"),
    "toll": ("통행료가 가장 싸고", "통행료가 가장 싼"),
}


def _join(phrases: list[tuple[str, str]]) -> str:
    """[(이어지는 말, 끝나는 말), ...] → "A고, B고, C습니다" """
    return ", ".join([p[0] for p in phrases[:-1]] + [phrases[-1][1]])


def _compare(best: RouteMetrics, other: RouteMetrics) -> list[tuple[str, str]]:
    """2위 경로와 비교한 차이. 화면에 보이는 단위로 반올림해서 차이가 없으면 뺀다"""
    phrases = []

    minutes = round((other.duration - best.duration) / 60)
    if minutes > 0:
        phrases.append((f"{minutes}분 빠르고", f"{minutes}분 빠릅니다"))
    elif minutes < 0:
        phrases.append((f"{-minutes}분 느리고", f"{-minutes}분 느립니다"))

    km = round((other.distance - best.distance) / 1000, 1)
    if km > 0:
        phrases.append((f"{km}km 짧고", f"{km}km 짧습니다"))
    elif km < 0:
        phrases.append((f"{-km}km 길고", f"{-km}km 깁니다"))

    won = other.toll - best.toll
    if won > 0:
        phrases.append((f"통행료가 {won:,}원 싸고", f"통행료가 {won:,}원 쌉니다"))
    elif won < 0:
        phrases.append((f"통행료가 {-won:,}원 비싸고", f"통행료가 {-won:,}원 비쌉니다"))

    return phrases


def make_reason(
    routes: list[RouteMetrics], weights: Weights, scores: dict[str, float], best_id: str
) -> str:
    if len(routes) == 1:
        return f"찾은 경로가 하나뿐이라 추천 경로는 {best_id}입니다."

    # 1) 무엇을 중요하게 봤는지: 가중치가 가장 큰 요소 (같으면 함께)
    w = _effective(weights).model_dump()
    top = [k for k in FACTORS if w[k] == max(w.values())]
    if len(top) == len(FACTORS):
        lead = "세 요소를 똑같이 보면"
    else:
        names = [FACTORS[k][0] for k in top]
        # 조사는 마지막 이름에만 붙인다: "시간을", "거리를" → "시간·거리를"
        lead = "·".join(n[:-1] for n in names) + names[-1][-1] + " 가장 중요하게 보면"
    sentences = [f"{lead} 추천 경로는 {best_id}입니다."]

    # 2) 추천 경로가 1등인 요소
    #    사용자가 신경 쓰지 않는 요소(가중치 0)와 모든 경로가 같은 값인 요소는 뺀다
    best = next(r for r in routes if r.id == best_id)
    wins = []
    for key, (_, get) in FACTORS.items():
        values = [get(r) for r in routes]
        if w[key] > 0 and get(best) == min(values) and min(values) != max(values):
            wins.append(STRENGTHS[key])
    if wins:
        sentences.append(f"{_join(wins)} 경로입니다.")

    # 3) 2위와 비교: 무엇을 얻고 무엇을 포기했는지
    runner_up_id = max((i for i in scores if i != best_id), key=scores.get)
    runner_up = next(r for r in routes if r.id == runner_up_id)
    diff = _compare(best, runner_up)
    if scores[runner_up_id] == scores[best_id]:
        sentences.append(f"{runner_up_id}도 점수가 같아 먼저 찾은 경로를 골랐습니다.")
    elif diff:
        sentences.append(f"2위 {runner_up_id}보다 {_join(diff)}.")
    else:
        sentences.append(f"2위 {runner_up_id}와 거의 차이가 없습니다.")

    return " ".join(sentences)


def recommend(routes: list[RouteMetrics], weights: Weights) -> RecommendResponse:
    scores = score_routes(routes, weights)
    best_id = max(scores, key=scores.get)  # 동점이면 앞쪽(카카오가 먼저 준) 경로
    return RecommendResponse(
        scores=scores, best_id=best_id, reason=make_reason(routes, weights, scores, best_id)
    )


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
        "시간=거리": Weights(time=0.5, distance=0.5, toll=0),
        "전부 0": Weights(time=0, distance=0, toll=0),
    }
    for name, w in cases.items():
        result = recommend(routes, w)
        print(f"[{name}] {result.scores} → 추천 {result.best_id}")
        print(f"  {result.reason}")

    print("[경로 1개]", recommend(routes[:1], cases["시간 중심"]).reason)
