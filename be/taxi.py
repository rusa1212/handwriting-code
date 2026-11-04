"""택시 요금 계산 (docs/taxi.md 2단계)

택시 미터기는 거리·시간 병산제다.
- 기본요금으로 기본거리(서울 1.6km)까지 간다
- 그 뒤로는 빠르게 달리면 거리(131m)마다, 느리게 달리면 시간(30초)마다 100원씩 오른다

카카오 경로의 도로 구간(roads[])을 차례로 미터기에 흘려보내 요금을 계산한다.
경로 탐색과 무관한 순수 함수라 숫자만 넣어 터미널에서 검증할 수 있다: python taxi.py
"""

from typing import NamedTuple

from schemas import Segment


class FareTable(NamedTuple):
    base_fare: int  # 기본요금 (원)
    base_distance: int  # 기본거리 (m)
    distance_unit: int  # 이 거리(m)마다 unit_fare가 오른다
    time_unit: int  # 느릴 때 이 시간(초)마다 unit_fare가 오른다
    unit_fare: int  # 한 번 오를 때의 금액 (원)

    @property
    def slow_speed(self) -> float:
        """시간 요금으로 바뀌는 속도 (m/s). 이 속도로 달리면 거리 요금과 시간 요금이 같은 빠르기로 오른다
        서울: 131m ÷ 30초 = 4.37m/s = 15.72km/h"""
        return self.distance_unit / self.time_unit


# ⚠ 서울 2023-02 개편 기준 (중형). 공식 공지로 숫자를 다시 확인할 것
TAXI_TABLES = {
    "seoul": FareTable(base_fare=4800, base_distance=1600, distance_unit=131, time_unit=30, unit_fare=100),
}


class FareBreakdown(NamedTuple):
    """화면에 내역을 보여 주려고 합계만이 아니라 항목별로 돌려준다 (원)"""

    base: int
    distance_fare: int
    time_fare: int
    surcharge: int  # 할증 (3단계에서 계산, 지금은 0)
    total: int


def is_slow(seg: Segment, table: FareTable) -> bool:
    """구간 평균 속도가 기준 이하이면 시간 요금. 시간이 0인 구간은 속도를 알 수 없으므로 거리 요금으로 센다"""
    if seg.duration == 0:
        return False
    return seg.distance / seg.duration <= table.slow_speed


def taxi_fare(segments: list[Segment], table: FareTable = TAXI_TABLES["seoul"]) -> FareBreakdown:
    """구간 목록 → 택시 요금 내역

    미터기 흉내: "남은 기본거리", "쌓인 거리", "쌓인 시간" 카운터를 두고 구간을 차례로 흘려보낸다.
    카운터는 구간이 바뀌어도 이어진다 (100m + 100m 구간이면 두 번째 구간에서 131m를 넘어 100원).
    총거리 ÷ 131m로 한 번에 나누면 느린 구간이 섞인 경로에서 값이 달라진다.
    """
    base_left = table.base_distance  # 기본요금에 포함된 남은 거리 (m)
    dist_acc = 0.0  # 거리 요금 카운터 (m)
    time_acc = 0.0  # 시간 요금 카운터 (초)
    dist_units = time_units = 0

    for seg in segments:
        distance, duration = seg.distance, seg.duration

        # 1) 기본거리를 먼저 쓴다. 느린 구간도 거리는 달렸으므로 기본거리를 깎는다
        #    구간 중간에서 기본거리가 끝나면 남은 비율만큼만 요금 대상이다
        #    (가정: 기본거리 안에서는 느려도 시간 요금이 붙지 않는다. 4단계 오차를 보고 다시 판단)
        if base_left > 0:
            used = min(base_left, distance)
            base_left -= used
            if distance == 0:
                continue
            ratio = (distance - used) / distance
            distance, duration = distance * ratio, duration * ratio
            if distance == 0:
                continue

        # 2) 남은 부분을 빠르기에 따라 거리 카운터 또는 시간 카운터에 쌓는다
        if is_slow(seg, table):  # 속도는 원래 구간 값으로 판단한다 (비율을 곱해도 같다)
            time_acc += duration
            while time_acc >= table.time_unit:
                time_acc -= table.time_unit
                time_units += 1
        else:
            dist_acc += distance
            while dist_acc >= table.distance_unit:
                dist_acc -= table.distance_unit
                dist_units += 1

    base = table.base_fare
    distance_fare = dist_units * table.unit_fare
    time_fare = time_units * table.unit_fare
    surcharge = 0
    # 100원 단위 반올림은 맨 마지막에 한 번만 (할증 배수를 곱하면 100원 단위가 깨지므로 3단계에서 필요해진다)
    total = round((base + distance_fare + time_fare + surcharge) / 100) * 100
    return FareBreakdown(base, distance_fare, time_fare, surcharge, total)


def _check_examples() -> None:
    """손으로 계산할 수 있는 작은 예제 (서울 요금표)"""
    seoul = TAXI_TABLES["seoul"]
    fast = lambda m: Segment(distance=m, duration=round(m / 10))  # 10m/s = 36km/h  # noqa: E731
    slow = lambda m, s: Segment(distance=m, duration=s)  # noqa: E731

    cases = [
        # (설명, 구간, 거리 요금, 시간 요금)
        ("기본거리 이내 1km", [fast(1000)], 0, 0),
        ("딱 기본거리 1.6km", [fast(1600)], 0, 0),
        # 1600 + 131×10 = 2910m → 거리 10번
        ("빠르게 2,910m", [fast(2910)], 1000, 0),
        ("빠르게 2,909m (131m 못 채움)", [fast(2909)], 900, 0),
        # 카운터가 구간을 넘어 이어진다: 기본거리 뒤 100m + 100m = 200m → 1번 (남은 69m)
        ("구간 넘어 이어지는 카운터", [fast(1600), fast(100), fast(100)], 100, 0),
        # 기본거리 뒤에 느린 구간 300m를 300초(1m/s) → 시간 10번, 거리는 0
        ("느린 구간 300초", [fast(1600), slow(300, 300)], 0, 1000),
        # 느린 구간이 기본거리에 걸침: 2000m 중 400m(20%)만 요금 대상 → 2000초 × 0.2 = 400초 → 13번
        ("기본거리에 걸친 느린 구간", [slow(2000, 2000)], 0, 1300),
        # 경계 속도: 131m를 30초 = 정확히 기준 속도 → 느린 것으로 본다 → 시간 1번
        ("기준 속도와 같음", [fast(1600), slow(131, 30)], 0, 100),
        ("시간 0인 구간은 거리 요금", [fast(1600), Segment(distance=262, duration=0)], 200, 0),
    ]
    for name, segs, want_dist, want_time in cases:
        fare = taxi_fare(segs, seoul)
        ok = fare.distance_fare == want_dist and fare.time_fare == want_time
        print(f"  {'OK ' if ok else 'XX '} {name}: 거리 {fare.distance_fare:,}원, 시간 {fare.time_fare:,}원, 합계 {fare.total:,}원")
        assert ok, f"{name}: 기대 거리 {want_dist}, 시간 {want_time}"
        assert fare.total == seoul.base_fare + want_dist + want_time


def _preview_samples() -> None:
    """저장한 카카오 응답으로 미리보기 (본격 비교는 4단계). 할증이 아직 없으므로 낮 시간 기준"""
    from map_api import parse_routes
    from taxi_sample import load_samples

    for name, raw in load_samples().items():
        for route in parse_routes(raw, with_segments=True):
            fare = taxi_fare(route.segments)
            diff = fare.total - route.kakao_taxi
            print(
                f"  [{name} {route.id}] 직접 {fare.total:,}원 "
                f"(기본 {fare.base:,} + 거리 {fare.distance_fare:,} + 시간 {fare.time_fare:,}) | "
                f"카카오 {route.kakao_taxi:,}원 | 차이 {diff:+,}원 ({diff / route.kakao_taxi:+.1%})"
            )


if __name__ == "__main__":
    print("손 계산 예제")
    _check_examples()
    print("\n저장한 샘플 미리보기 (서울 요금표를 모든 지역에 적용)")
    _preview_samples()
