from typing import Callable, NamedTuple

from schemas import RecommendResponse, RouteMetrics, Weights

# LEVEL 3: 사용자 가중치로 경로 점수를 계산한다
# 거리(m), 시간(초), 통행료(원)는 단위가 달라 그대로 더할 수 없으므로
# 경로들 사이에서 0(가장 좋음) ~ 1(가장 나쁨)로 정규화한 뒤 가중치를 곱한다
#
# 어떤 요소로 점수를 매길지는 모드마다 다르다 (docs/taxi.md 7-1)
# - 자가용: 시간·거리·통행료
# - 택시: 요금(택시비 + 통행료)·시간. 승객에게 거리는 요금에 이미 들어가 있다

# 한국어는 이어지는 말("빠르고")과 끝나는 말("빠릅니다")의 형태가 달라서 둘 다 둔다
Phrase = tuple[str, str]  # (이어지는 말, 끝나는 말)


def _diff_time(best: RouteMetrics, other: RouteMetrics) -> Phrase | None:
    minutes = round((other.duration - best.duration) / 60)
    if minutes > 0:
        return (f"{minutes}분 빠르고", f"{minutes}분 빠릅니다")
    if minutes < 0:
        return (f"{-minutes}분 느리고", f"{-minutes}분 느립니다")
    return None


def _diff_distance(best: RouteMetrics, other: RouteMetrics) -> Phrase | None:
    km = round((other.distance - best.distance) / 1000, 1)
    if km > 0:
        return (f"{km}km 짧고", f"{km}km 짧습니다")
    if km < 0:
        return (f"{-km}km 길고", f"{-km}km 깁니다")
    return None


def _diff_won(subject: str, get: Callable[[RouteMetrics], int]):
    """금액 차이 문장을 만드는 함수. subject: "통행료가 " 처럼 앞에 붙일 말"""

    def diff(best: RouteMetrics, other: RouteMetrics) -> Phrase | None:
        won = get(other) - get(best)
        if won > 0:
            return (f"{subject}{won:,}원 싸고", f"{subject}{won:,}원 쌉니다")
        if won < 0:
            return (f"{subject}{-won:,}원 비싸고", f"{subject}{-won:,}원 비쌉니다")
        return None

    return diff


class Factor(NamedTuple):
    name: str  # 요소 이름 (목적격 조사 포함): "시간을"
    get: Callable[[RouteMetrics], int]  # 경로에서 꺼낼 값 (작을수록 좋다)
    strength: Phrase  # 추천 경로가 이 요소에서 1등일 때: (이어지는 말, 꾸미는 말)
    diff: Callable[[RouteMetrics, RouteMetrics], Phrase | None]  # 2위와의 차이 (화면 단위로 반올림해 같으면 None)


FACTORS = {
    "time": Factor("시간을", lambda r: r.duration, ("가장 빠르고", "가장 빠른"), _diff_time),
    "distance": Factor("거리를", lambda r: r.distance, ("가장 짧고", "가장 짧은"), _diff_distance),
    "toll": Factor("통행료를", lambda r: r.toll, ("통행료가 가장 싸고", "통행료가 가장 싼"), _diff_won("통행료가 ", lambda r: r.toll)),
    "cost": Factor("요금을", lambda r: r.cost, ("요금이 가장 싸고", "요금이 가장 싼"), _diff_won("요금이 ", lambda r: r.cost)),
}

# 모드마다 쓰는 요소. 순서 = 이유 문장에 나오는 순서
MODE_FACTORS = {
    "car": ("time", "distance", "toll"),
    "taxi": ("cost", "time"),
}

COUNT_WORDS = {2: "두", 3: "세"}


def _normalize(values: list[int]) -> list[float]:
    """min-max 정규화. 모든 값이 같으면 차이가 없으므로 전부 0"""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _effective(weights: Weights, mode: str) -> dict[str, float]:
    """모드에서 쓰는 요소의 가중치만 꺼낸다. 전부 0이면 모든 요소를 똑같이 본다"""
    w = {key: getattr(weights, key) for key in MODE_FACTORS[mode]}
    if sum(w.values()) == 0:
        return dict.fromkeys(w, 1.0)
    return w


def score_routes(routes: list[RouteMetrics], weights: Weights, mode: str = "car") -> dict[str, float]:
    """경로 id → 점수 (0~100, 높을수록 좋음)"""
    w = _effective(weights, mode)
    total = sum(w.values())
    normalized = {key: _normalize([FACTORS[key].get(r) for r in routes]) for key in w}

    scores = {}
    for i, route in enumerate(routes):
        cost = sum(normalized[key][i] * w[key] for key in w) / total  # 0~1, 낮을수록 좋음
        scores[route.id] = round((1 - cost) * 100, 1)
    return scores


# ---- 추천 이유 문장 ----


def _join(phrases: list[Phrase]) -> str:
    """[(이어지는 말, 끝나는 말), ...] → "A고, B고, C습니다" """
    return ", ".join([p[0] for p in phrases[:-1]] + [phrases[-1][1]])


def make_reason(
    routes: list[RouteMetrics], weights: Weights, scores: dict[str, float], best_id: str, mode: str = "car"
) -> str:
    if len(routes) == 1:
        return f"찾은 경로가 하나뿐이라 추천 경로는 {best_id}입니다."

    keys = MODE_FACTORS[mode]

    # 1) 무엇을 중요하게 봤는지: 가중치가 가장 큰 요소 (같으면 함께)
    w = _effective(weights, mode)
    top = [k for k in keys if w[k] == max(w.values())]
    if len(top) == len(keys):
        lead = f"{COUNT_WORDS[len(keys)]} 요소를 똑같이 보면"
    else:
        names = [FACTORS[k].name for k in top]
        # 조사는 마지막 이름에만 붙인다: "시간을", "거리를" → "시간·거리를"
        lead = "·".join(n[:-1] for n in names) + names[-1][-1] + " 가장 중요하게 보면"
    sentences = [f"{lead} 추천 경로는 {best_id}입니다."]

    # 2) 추천 경로가 1등인 요소
    #    사용자가 신경 쓰지 않는 요소(가중치 0)와 모든 경로가 같은 값인 요소는 뺀다
    best = next(r for r in routes if r.id == best_id)
    wins = []
    for key in keys:
        get = FACTORS[key].get
        values = [get(r) for r in routes]
        if w[key] > 0 and get(best) == min(values) and min(values) != max(values):
            wins.append(FACTORS[key].strength)
    if wins:
        sentences.append(f"{_join(wins)} 경로입니다.")

    # 3) 2위와 비교: 무엇을 얻고 무엇을 포기했는지
    runner_up_id = max((i for i in scores if i != best_id), key=scores.get)
    runner_up = next(r for r in routes if r.id == runner_up_id)
    diff = [p for key in keys if (p := FACTORS[key].diff(best, runner_up))]
    if scores[runner_up_id] == scores[best_id]:
        sentences.append(f"{runner_up_id}도 점수가 같아 먼저 찾은 경로를 골랐습니다.")
    elif diff:
        sentences.append(f"2위 {runner_up_id}보다 {_join(diff)}.")
    else:
        sentences.append(f"2위 {runner_up_id}와 거의 차이가 없습니다.")

    return " ".join(sentences)


def recommend(routes: list[RouteMetrics], weights: Weights, mode: str = "car") -> RecommendResponse:
    scores = score_routes(routes, weights, mode)
    best_id = max(scores, key=scores.get)  # 동점이면 앞쪽(카카오가 먼저 준) 경로
    return RecommendResponse(
        scores=scores, best_id=best_id, reason=make_reason(routes, weights, scores, best_id, mode)
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

    # 택시 모드 (docs/taxi.md 7단계): 빠르지만 비싼 길 vs 느리지만 싼 길
    print("\n택시 모드")
    taxi_routes = [
        RouteMetrics(id="A", distance=10600, duration=24 * 60, toll=0, cost=16200),
        RouteMetrics(id="B", distance=9800, duration=29 * 60, toll=0, cost=15000),
        RouteMetrics(id="C", distance=14000, duration=20 * 60, toll=1200, cost=19400),
    ]
    taxi_cases = {
        "요금 중심": Weights(cost=0.8, time=0.2),
        "시간 중심": Weights(cost=0.2, time=0.8),
        "요금=시간": Weights(cost=0.5, time=0.5),
        "전부 0": Weights(),
    }
    for name, w in taxi_cases.items():
        result = recommend(taxi_routes, w, "taxi")
        print(f"[{name}] {result.scores} → 추천 {result.best_id}")
        print(f"  {result.reason}")
