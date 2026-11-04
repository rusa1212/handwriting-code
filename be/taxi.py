"""택시 요금 계산 (docs/taxi.md 2단계)

택시 미터기는 거리·시간 병산제다.
- 기본요금으로 기본거리(서울 1.6km)까지 간다
- 그 뒤로는 빠르게 달리면 거리(131m)마다, 느리게 달리면 시간(30초)마다 100원씩 오른다

카카오 경로의 도로 구간(roads[])을 차례로 미터기에 흘려보내 요금을 계산한다.
경로 탐색과 무관한 순수 함수라 숫자만 넣어 터미널에서 검증할 수 있다: python taxi.py
"""

from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from schemas import Segment

# 한국 시간. 서머타임이 없어 고정 오프셋이면 충분하다
# (zoneinfo의 "Asia/Seoul"은 Windows에서 tzdata 패키지가 없으면 동작하지 않는다)
KST = timezone(timedelta(hours=9), "KST")


class NightRate(NamedTuple):
    start_hour: int  # 이 시각부터 (포함)
    end_hour: int  # 이 시각 전까지 (미포함)
    rate: float  # 할증률 (0.2 = 20%)


class FareTable(NamedTuple):
    base_fare: int  # 기본요금 (원)
    base_distance: int  # 기본거리 (m)
    distance_unit: int  # 이 거리(m)마다 unit_fare가 오른다
    time_unit: int  # 느릴 때 이 시간(초)마다 unit_fare가 오른다
    unit_fare: int  # 한 번 오를 때의 금액 (원)
    night_rates: tuple[NightRate, ...]  # 심야할증 시간대 (자정을 넘는 구간은 둘로 나눠 적는다)
    out_of_area_rate: float  # 시계외 할증률: 사업 구역 밖으로 나갈 때
    area_bbox: tuple[float, float, float, float]  # 사업 구역 (남, 서, 북, 동). 대략적인 사각형

    @property
    def slow_speed(self) -> float:
        """시간 요금으로 바뀌는 속도 (m/s). 이 속도로 달리면 거리 요금과 시간 요금이 같은 빠르기로 오른다
        서울: 131m ÷ 30초 = 4.37m/s = 15.72km/h"""
        return self.distance_unit / self.time_unit


# ⚠ 서울 2023-02 개편 기준 (중형). 공식 공지로 숫자를 다시 확인할 것
TAXI_TABLES = {
    "seoul": FareTable(
        base_fare=4800,
        base_distance=1600,
        distance_unit=131,
        time_unit=30,
        unit_fare=100,
        # 22~23시 20%, 23~02시 40%, 02~04시 20%
        night_rates=(NightRate(22, 23, 0.2), NightRate(23, 24, 0.4), NightRate(0, 2, 0.4), NightRate(2, 4, 0.2)),
        out_of_area_rate=0.2,
        # 서울 행정구역을 감싸는 사각형. 경계 근처(광명·부천·과천 일부)는 서울로 잘못 볼 수 있다
        area_bbox=(37.413, 126.734, 37.715, 127.270),
    ),
}


class FareBreakdown(NamedTuple):
    """화면에 내역을 보여 주려고 합계만이 아니라 항목별로 돌려준다 (금액은 원)
    base + distance_fare + time_fare + surcharge = total 이 항상 맞는다"""

    base: int
    distance_fare: int
    time_fare: int
    surcharge: int  # 할증 금액 (100원 반올림 차이도 여기에 들어간다)
    total: int
    night_rate: float = 0.0  # 적용한 심야할증률
    out_of_area_rate: float = 0.0  # 적용한 시계외 할증률


def night_rate(depart_at: datetime, table: FareTable) -> float:
    """출발 시각 → 심야할증률. 시간대 정보가 없는 시각은 한국 시간으로 본다
    (가정: 출발 시각 하나로 정한다. 운행 중에 할증 시간대가 바뀌는 것은 반영하지 않는다)"""
    if depart_at.tzinfo is None:
        depart_at = depart_at.replace(tzinfo=KST)
    hour = depart_at.astimezone(KST).hour
    for night in table.night_rates:
        if night.start_hour <= hour < night.end_hour:
            return night.rate
    return 0.0


def in_area(lat: float, lng: float, table: FareTable) -> bool:
    south, west, north, east = table.area_bbox
    return south <= lat <= north and west <= lng <= east


def out_of_area_rate(origin, destination, table: FareTable) -> float:
    """구역 안에서 출발해 구역 밖으로 나가면 시계외 할증. origin, destination: lat·lng가 있는 것 (Place)"""
    if in_area(origin.lat, origin.lng, table) and not in_area(destination.lat, destination.lng, table):
        return table.out_of_area_rate
    return 0.0


def _round_100(won: float) -> int:
    """100원 단위 반올림 (50원 이상 올림). round()는 0.5를 짝수 쪽으로 보내므로 쓰지 않는다"""
    return int((won + 50) // 100) * 100


def is_slow(seg: Segment, table: FareTable) -> bool:
    """구간 평균 속도가 기준 이하이면 시간 요금. 시간이 0인 구간은 속도를 알 수 없으므로 거리 요금으로 센다"""
    if seg.duration == 0:
        return False
    return seg.distance / seg.duration <= table.slow_speed


def taxi_fare(
    segments: list[Segment],
    table: FareTable = TAXI_TABLES["seoul"],
    *,
    night: float = 0.0,
    out_of_area: float = 0.0,
) -> FareBreakdown:
    """구간 목록 → 택시 요금 내역. 할증률 night, out_of_area는 night_rate(), out_of_area_rate()로 구해 넘긴다

    할증: 미터기 요금 × (1 + 심야할증률 + 시계외 할증률) → 100원 단위 반올림
    (가정: 두 할증은 곱하지 않고 더한다. 공식 규정 확인 필요)

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
    meter = base + distance_fare + time_fare
    # 100원 단위 반올림은 할증까지 곱한 뒤 맨 마지막에 한 번만 한다
    total = _round_100(meter * (1 + night + out_of_area))
    surcharge = total - meter
    return FareBreakdown(base, distance_fare, time_fare, surcharge, total, night, out_of_area)


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


def _check_surcharges() -> None:
    """할증 (3단계)"""
    from schemas import Place

    seoul = TAXI_TABLES["seoul"]

    # 시간대 경계: 시작 포함, 끝 미포함
    at = lambda h, m=0: datetime(2026, 11, 4, h, m, tzinfo=KST)  # noqa: E731
    hours = [
        (at(21, 59), 0.0), (at(22), 0.2), (at(22, 59), 0.2), (at(23), 0.4),
        (at(0), 0.4), (at(1, 59), 0.4), (at(2), 0.2), (at(3, 59), 0.2), (at(4), 0.0), (at(14), 0.0),
    ]
    for t, want in hours:
        assert night_rate(t, seoul) == want, f"{t:%H:%M}: {night_rate(t, seoul)} != {want}"
    # 다른 시간대로 들어와도 한국 시간으로 바꿔 본다: UTC 14:15 = KST 23:15
    assert night_rate(datetime(2026, 11, 4, 14, 15, tzinfo=timezone.utc), seoul) == 0.4
    # 시간대 정보가 없으면 한국 시간으로 본다
    assert night_rate(datetime(2026, 11, 4, 23, 15), seoul) == 0.4
    print("  OK  심야할증 시간대 경계 12개")

    # 기본요금만 나오는 거리: 서울시가 발표한 심야 기본요금(5,800원 / 6,700원)과 같아야 한다
    short = [Segment(distance=1000, duration=100)]
    cases = [
        ("낮 기본요금", 0.0, 0.0, 4800),
        ("심야 20% 기본요금 (5,760 → 5,800)", 0.2, 0.0, 5800),
        ("심야 40% 기본요금 (6,720 → 6,700)", 0.4, 0.0, 6700),
        ("시계외 20%", 0.0, 0.2, 5800),
        ("심야 40% + 시계외 20% = 60% (7,680 → 7,700)", 0.4, 0.2, 7700),
    ]
    for name, night, out, want in cases:
        fare = taxi_fare(short, seoul, night=night, out_of_area=out)
        assert fare.total == want, f"{name}: {fare.total} != {want}"
        assert fare.base + fare.distance_fare + fare.time_fare + fare.surcharge == fare.total
        print(f"  OK  {name}: {fare.total:,}원 (할증 {fare.surcharge:+,}원)")

    # 시계외: 서울 안 → 밖만 할증
    seoul_st = Place(name="서울역", lat=37.5547, lng=126.9707)
    gangnam = Place(name="강남역", lat=37.4979, lng=127.0276)
    airport = Place(name="인천공항", lat=37.4492, lng=126.4510)
    assert out_of_area_rate(seoul_st, gangnam, seoul) == 0.0
    assert out_of_area_rate(seoul_st, airport, seoul) == 0.2
    assert out_of_area_rate(airport, seoul_st, seoul) == 0.0  # 밖에서 서울로 들어오는 것은 할증 없음
    print("  OK  시계외 판단 3개 (서울역→강남역 없음, 서울역→인천공항 20%, 인천공항→서울역 없음)")


def _preview_samples() -> None:
    """저장한 카카오 응답으로 미리보기 (본격 비교는 4단계). 샘플을 받은 시각으로 심야할증을 넣는다"""
    from map_api import parse_routes
    from taxi_sample import SAMPLES, load_sample_sets

    seoul = TAXI_TABLES["seoul"]
    for sample_set in load_sample_sets():
        night = night_rate(sample_set.fetched_at, seoul)
        print(f"  == {sample_set.file.name}: 받은 시각 {sample_set.fetched_at:%Y-%m-%d %H:%M} → 심야할증 {night:.0%}")

        for name, raw in sample_set.routes.items():
            origin, destination = SAMPLES[name]
            out = out_of_area_rate(origin, destination, seoul)
            for route in parse_routes(raw, with_segments=True):
                kakao = route.kakao_taxi
                fare = taxi_fare(route.segments, seoul, night=night, out_of_area=out)
                line = (
                    f"  [{name} {route.id}] 직접 {fare.total:,}원 "
                    f"(기본 {fare.base:,} + 거리 {fare.distance_fare:,} + 시간 {fare.time_fare:,} + 할증 {fare.surcharge:,}) | "
                    f"카카오 {kakao:,}원 | 차이 {fare.total - kakao:+,}원 ({(fare.total - kakao) / kakao:+.1%})"
                )
                if out:  # 카카오는 시계외를 넣지 않는 것 같아서 (2단계) 빼고 계산한 값도 보여 준다
                    no_out = taxi_fare(route.segments, seoul, night=night).total
                    line += f" | 시계외 빼면 {no_out:,}원 ({(no_out - kakao) / kakao:+.1%})"
                print(line)


if __name__ == "__main__":
    print("손 계산 예제")
    _check_examples()
    print("\n할증")
    _check_surcharges()
    print("\n저장한 샘플 미리보기 (서울 요금표를 모든 지역에 적용)")
    _preview_samples()
