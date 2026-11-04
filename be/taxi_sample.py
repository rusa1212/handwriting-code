"""택시 모드 1단계 확인용 (docs/taxi.md 1-4)

python taxi_sample.py            저장한 응답으로 확인 (없으면 API를 불러 저장)
python taxi_sample.py --refresh  API를 다시 불러 저장한 뒤 확인

- 길찾기 원본 응답을 data/sample_directions.json에 저장해 2~4단계(요금 계산 검증)에서 API 없이 다시 쓴다
- 구간(roads[]) 거리·시간의 합이 경로 전체(summary)와 맞는지 본다
"""

import json
import sys
from pathlib import Path

from map_api import fetch_directions, parse_routes
from schemas import Place

SAMPLE_FILE = Path(__file__).parent / "data" / "sample_directions.json"

# 짧은 시내, 긴 시내, 통행료·시계외가 있는 경로를 섞는다
SAMPLES = {
    "구미역→금오산": (Place(name="구미역", lat=36.1283, lng=128.3311), Place(name="금오산", lat=36.1094, lng=128.3166)),
    "전남대→광주송정역": (Place(name="전남대", lat=35.1769, lng=126.9069), Place(name="광주송정역", lat=35.1374, lng=126.7907)),
    "서울역→강남역": (Place(name="서울역", lat=37.5547, lng=126.9707), Place(name="강남역", lat=37.4979, lng=127.0276)),
    "서울역→인천공항": (Place(name="서울역", lat=37.5547, lng=126.9707), Place(name="인천공항 T1", lat=37.4492, lng=126.4510)),
}


def load_samples(refresh: bool = False) -> dict[str, dict]:
    """이름 → 길찾기 원본 응답. 파일이 없거나 refresh면 API를 불러 저장한다"""
    if SAMPLE_FILE.exists() and not refresh:
        return json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))

    data = {name: fetch_directions(o, d) for name, (o, d) in SAMPLES.items()}
    SAMPLE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"저장: {SAMPLE_FILE.name} ({SAMPLE_FILE.stat().st_size / 1024:.0f}KB)\n")
    return data


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
    samples = load_samples(refresh="--refresh" in sys.argv)
    for name, raw in samples.items():
        check(name, raw)
    print("\n확인 완료")
