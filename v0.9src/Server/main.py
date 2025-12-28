# fastapi(server/api)를 실행시키는 코드
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "server.api:app",
        host="0.0.0.0",
        port=5000, #나중에 http://ceprj2.gachon.ac.kr:65022
        reload=True
    )
