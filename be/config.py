import os
from pathlib import Path

from dotenv import load_dotenv

# 어느 폴더에서 서버를 실행해도 be/.env를 읽도록 경로를 고정한다
load_dotenv(Path(__file__).parent / ".env")

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")

if not KAKAO_REST_API_KEY:
    raise RuntimeError("KAKAO_REST_API_KEY가 없습니다. be/.env를 확인하세요.")
