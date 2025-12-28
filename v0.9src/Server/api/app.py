from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, root_validator

import os
import re
import difflib
from pathlib import Path
from typing import Optional, List
# print("📁 FILE PATH:", os.path.abspath(__file__))
# key.env 환경변수 로드 (없으면 무시)
_env_path = Path(__file__).resolve().parents[2] / "key.env"
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(_env_path)
except Exception:
    if _env_path.exists():
        for _line in _env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            _line = _line.strip()
            if not _line or _line.startswith("#"):
                continue
            if _line.startswith("export "):
                _line = _line[7:].lstrip()
            if "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))
                
# from langChain_v3.RAGLLM.llm_runtime import get_llm
from langChain_v3.RAGLLM.rag_llm_for_server import answer_with_rag_for_server
from langChain_v3.RAGLLM.llm_service import generate_answer


# ===============================
# FastAPI
# ===============================
app = FastAPI(title="∞ Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RAG_ENABLED = os.getenv("RAG_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}
DEBUG_RAG_ERRORS = os.getenv("DEBUG_RAG_ERRORS", "1").strip().lower() in {"1", "true", "yes", "on"}

# @app.on_event("startup")
# def startup():
#     print("[Server] Loading LLM once...")
#     get_llm()

# ===============================
# Request Model
# ===============================
class ChatRequest(BaseModel):
    message: str | None = None
    question: str | None = None

    @root_validator(pre=True)
    def ensure_message(cls, values):
        msg = values.get("message") or values.get("question")
        if not msg:
            raise ValueError("message is required")
        values["message"] = str(msg)
        return values

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/chat")
def chat_info():
    return {"status": "ok", "detail": "Use POST /api/chat with a message."}

# ===============================
# 규칙 기반 로직 (프론트 분 코드 유지)
# ===============================

CHOSUNG_LIST = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]

def get_chosung(text: str) -> str:
    result = []
    for ch in text:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            idx = (code - 0xAC00) // 588
            result.append(CHOSUNG_LIST[idx])
    return "".join(result)

def is_chosung_input(text: str) -> bool:
    return bool(text) and all(ch in CHOSUNG_LIST for ch in text)


def correct_typo(msg: str, categories: List[str]) -> Optional[str]:
    matches = difflib.get_close_matches(msg, categories, n=1, cutoff=0.6)
    return matches[0] if matches else None

CATEGORY_RESPONSES = {
    "캠퍼스맵": {"reply": "가천대학교 캠퍼스맵 안내입니다.", "chosung": "ㅋㅍㅅㅁ"},
    "학사일정": {"reply": "학사일정 안내입니다.", "chosung": "ㅎㅅㅇㅈ"},
    "수강신청": {"reply": "수강신청 관련 안내입니다.", "chosung": "ㅅㄱㅅㅊ"},
    "교내연락처": {"reply": "교내 주요 부서 연락처 안내입니다.", "chosung": "ㄱㄴㅇㄹㅊ"},
    "등록금": {"reply": "등록금 납부 안내입니다.", "chosung": "ㄷㄹㄱ"},
    "편의시설": {"reply": "편의시설 안내입니다.", "chosung": "ㅍㅇㅅㅅ"},
    "도서관": {"reply": "도서관 이용 안내입니다.", "chosung": "ㄷㅅㄱ"},
}

# ===============================
# 통합 Chat API
# ===============================
# @app.post("/api/chat")
# def chat(req: ChatRequest):
#     msg = re.sub(r"[^\w가-힣]", "", req.message.strip())
#     categories = list(CATEGORY_RESPONSES.keys())

#     # 1) 정확/포함 매칭
#     for category, data in CATEGORY_RESPONSES.items():
#         if category in msg:
#             return {
#                 "type": "category",
#                 "category": category,
#                 "reply": data["reply"],
#                 "suggestions": [
#                     f"{category} 상세 안내",
#                     f"{category} 이용 방법",
#                 ],
#             }

#     # 2) 초성
#     user_chosung = msg if is_chosung_input(msg) else get_chosung(msg)
#     for category, data in CATEGORY_RESPONSES.items():
#         if user_chosung == data["chosung"]:
#             return {
#                 "type": "category",
#                 "category": category,
#                 "reply": data["reply"],
#                 "suggestions": [
#                     f"{category} 상세 안내",
#                     f"{category} 이용 방법",
#                 ],
#             }

#     # 3) 오타 보정
#     corrected = correct_typo(msg, categories)
#     if corrected:
#         data = CATEGORY_RESPONSES[corrected]
#         return {
#             "type": "category",
#             "category": corrected,
#             "reply": data["reply"],
#         }

#     # 4) 🔥 fallback → RAG
#     if not RAG_ENABLED:
#         answer = generate_answer(
#             system_prompt=(
#                 "당신은 가천대학교 AI 챗봇입니다.\n"
#                 "한국어 존댓말로 1~3문장으로 답변하세요."
#             ),
#             user_prompt=req.message,
#         )
#         return {"type": "llm", "reply": answer, "used_rag": False}

#     try:
#         rag_result = answer_with_rag_for_server(req.message)
#         # print(rag_result.get("contexts", []))
#         return {
#             "type": "rag",
#             "reply": rag_result["answer"],
#             "contexts": rag_result.get("contexts", []),
#             "used_rag": rag_result.get("used_rag", True),
#         }
#     except Exception as e:
#         answer = generate_answer(
#             system_prompt=(
#                 "당신은 가천대학교 AI 챗봇입니다.\n"
#                 "한국어 존댓말로 1~3문장으로 답변하세요."
#             ),
#             user_prompt=req.message,
#         )
#         resp = {"type": "llm", "reply": answer, "used_rag": False}
#         if DEBUG_RAG_ERRORS:
#             resp["rag_error"] = repr(e)
#         return resp
@app.post("/api/chat")
async def chat(req: ChatRequest):
    msg = re.sub(r"[^\w가-힣]", "", req.message.strip())
    categories = list(CATEGORY_RESPONSES.keys())

    # 1) 카테고리 매칭
    for category, data in CATEGORY_RESPONSES.items():
        if category in msg:
            return {
                "type": "category",
                "category": category,
                "reply": data["reply"],
                "suggestions": [
                    f"{category} 상세 안내",
                    f"{category} 이용 방법",
                ],
            }

    # 2) 초성
    user_chosung = msg if is_chosung_input(msg) else get_chosung(msg)
    for category, data in CATEGORY_RESPONSES.items():
        if user_chosung == data["chosung"]:
            return {
                "type": "category",
                "category": category,
                "reply": data["reply"],
                "suggestions": [
                    f"{category} 상세 안내",
                    f"{category} 이용 방법",
                ],
            }

    # 3) 오타 보정
    corrected = correct_typo(msg, categories)
    if corrected:
        data = CATEGORY_RESPONSES[corrected]
        return {
            "type": "category",
            "category": corrected,
            "reply": data["reply"],
        }

    # 4) fallback
    if not RAG_ENABLED:
        answer = generate_answer(
            system_prompt=(
                "당신은 가천대학교 AI 챗봇입니다.\n"
                "한국어 존댓말로 1~3문장으로 답변하세요."
            ),
            user_prompt=req.message,
        )
        return {"type": "llm", "reply": answer, "used_rag": False}

    try:
        rag_result = answer_with_rag_for_server(
            question=req.message,
            k=5
            )
        return {
            "type": "rag",
            "reply": rag_result["answer"],
            "contexts": rag_result.get("contexts", []),
            "used_rag": rag_result.get("used_rag", True),
        }

    except Exception as e:
        answer = generate_answer(
            system_prompt=(
                "당신은 가천대학교 AI 챗봇입니다.\n"
                "한국어 존댓말로 1~3문장으로 답변하세요."
            ),
            user_prompt=req.message,
        )
        resp = {"type": "llm", "reply": answer, "used_rag": False}
        if DEBUG_RAG_ERRORS:
            resp["rag_error"] = repr(e)
        return resp
# ===============================
# React dist 서빙
# ===============================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# FRONTEND_DIR = BASE_DIR / "muhanchatbot" / "dist" / "public"
FRONTEND_DIR = BASE_DIR / "muhanchatbot-main" / "dist" / "public"
# app.mount("/", StaticFiles(directory="muhanchatbot/dist", html=True), name="frontend")
app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend",
)
# app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
