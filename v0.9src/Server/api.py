# server/api.py
# 클라이언트 요청을 받아서 RAG 엔진에 넘겨주는 API
# HTML 요청 받는 곳

from fastapi import FastAPI
from pydantic import BaseModel

from Pproject.langChain_v3.RAGLLM.rag_llm import answer_with_rag_oss


class QueryItem(BaseModel):
    question: str
    k: int = 5
    window: int = 1


app = FastAPI()

# # 1) 정적 파일 mount (프론트 빌드 결과 경로 맞춰주기)
# app.mount(
#     "/",
#     StaticFiles(directory="frontend/dist", html=True),  # 경로는 상황에 맞게 변경
#     name="static",
# )

@app.post("/rag/answer")
def rag_answer(item: QueryItem):
    result = answer_with_rag_oss(
        question=item.question,
        k=item.k,
        window=item.window,
    )
    return result
