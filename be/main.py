from fastapi import FastAPI

app = FastAPI()


# 프론트엔드는 Vite 프록시를 통해 /api/* 요청을 이 서버로 보낸다
@app.get("/api/health")
def health():
    return {"status": "ok"}
