"""택시 모드 1단계 확인용 (docs/taxi.md 1-4)

python taxi_sample.py            저장한 응답 전부 확인 (하나도 없으면 API를 불러 저장)
python taxi_sample.py --refresh  API를 새로 불러 새 파일로 저장한 뒤 전부 확인

- 길찾기 원본 응답을 data/taxi_samples/directions_YYYYMMDD_HHMM.json에 저장해 2~4단계(요금 계산 검증)에서 API 없이 다시 쓴다
- 받을 때마다 받은 시각을 이름으로 한 새 파일을 만든다. 이전 파일은 덮어쓰지 않는다
  (카카오 fare.taxi는 요청 시각의 심야할증이 들어간 값이라 낮·심야 샘플을 둘 다 남겨 비교한다)
- 구간(roads[]) 거리·시간의 합이 경로 전체(summary)와 맞는지 본다
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from map_api import fetch_directions, parse_routes
from schemas import Place
from taxi import KST

SAMPLE_DIR = Path(__file__).parent / "data" / "taxi_samples"

# 짧은 시내, 긴 시내, 통행료·시계외가 있는 경로를 섞는다
SAMPLES = {
    "구미역→금오산": (Place(name="구미역", lat=36.1283, lng=128.3311), Place(name="금오산", lat=36.1094, lng=128.3166)),
    "전남대→광주송정역": (Place(name="전남대", lat=35.1769, lng=126.9069), Place(name="광주송정역", lat=35.1374, lng=126.7907)),
    "서울역→강남역": (Place(name="서울역", lat=37.5547, lng=126.9707), Place(name="강남역", lat=37.4979, lng=127.0276)),
    "서울역→인천공항": (Place(name="서울역", lat=37.5547, lng=126.9707), Place(name="인천공항 T1", lat=37.4492, lng=126.4510)),
}


class SampleSet(NamedTuple):
    """한 번에 받은 샘플 묶음"""

    file: Path
    fetched_at: datetime  # 받은 시각 (한국 시간)
    routes: dict[str, dict]  # 샘플 이름 → 길찾기 원본 응답


def fetch_samples() -> SampleSet:
    """API를 불러 받은 시각 이름의 새 파일로 저장한다. 같은 분에 이미 받은 파일이 있으면 덮어쓰지 않고 멈춘다"""
    fetched_at = datetime.now(KST).replace(microsecond=0)
    file = SAMPLE_DIR / f"directions_{fetched_at:%Y%m%d_%H%M}.json"
    if file.exists():
        raise FileExistsError(f"{file.name}이 이미 있습니다. 1분 뒤에 다시 받으세요.")

    routes = {name: fetch_directions(o, d) for name, (o, d) in SAMPLES.items()}
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"fetched_at": fetched_at.isoformat(), "routes": routes}, ensure_ascii=False), encoding="utf-8")
    print(f"저장: {file.name} ({file.stat().st_size / 1024:.0f}KB)\n")
    return SampleSet(file, fetched_at, routes)


def load_sample_sets() -> list[SampleSet]:
    """저장한 샘플 묶음 전부, 받은 시각 순. 하나도 없으면 API를 불러 하나 만든다"""
    files = sorted(SAMPLE_DIR.glob("directions_*.json"))
    if not files:
        return [fetch_samples()]
    sets = []
    for file in files:
        saved = json.loads(file.read_text(encoding="utf-8"))
        sets.append(SampleSet(file, datetime.fromisoformat(saved["fetched_at"]), saved["routes"]))
    return sets


def check(name: str, raw: dict) -> None:
    for route in parse_routes(raw, with_segments=True):
        segs = route.segments
        dist_sum = sum(s.distance for s in segs)
        time_sum = sum(s.duration for s in segs)
        zero_time = sum(1 for s in segs if s.duration == 0)
        print(
            f"[{name} {route.id}] 구간 {len(segs)}개 | "
            f"거리 {route.distance}m (구간 합 {dist_sum}, 차이 {dist_sum - route.distance:+}) | "
            f"시간 {route.duration}초 (구간 합 {time_sum}, 차이 {time_sum - route.duration:+}) | "
            f"시간 0인 구간 {zero_time}개 | 통행료 {route.toll:,}원 | 카카오 택시비 {route.kakao_taxi:,}원"
        )
        # 거리는 정확히 같아야 한다. 시간은 카카오가 구간마다 반올림하므로 조금 다를 수 있다
        assert dist_sum == route.distance, "구간 거리 합이 경로 거리와 다르다"
        assert abs(time_sum - route.duration) <= max(60, route.duration * 0.05), "구간 시간 합이 너무 다르다"
        # 응답 JSON에는 구간 목록이 빠져야 한다 (exclude=True)
        assert "segments" not in route.model_dump()


if __name__ == "__main__":
    if "--refresh" in sys.argv:
        fetch_samples()
    for sample_set in load_sample_sets():
        print(f"== {sample_set.file.name} (받은 시각 {sample_set.fetched_at:%Y-%m-%d %H:%M})")
        for name, raw in sample_set.routes.items():
            check(name, raw)
        print()
    print("확인 완료")
