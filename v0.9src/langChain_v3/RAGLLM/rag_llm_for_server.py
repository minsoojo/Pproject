import os
from typing import Dict, Any, List

from langChain_v3.RAGLLM.rag import (
    semantic_search,
    semantic_search_rerank,
    hybrid_search_rerank,
)
from langChain_v3.vectorstore import DEFAULT_INDEX_DIR
from langChain_v3.RAGLLM.llm_service import generate_answer

RAG_RERANK_ENABLED = os.getenv("RAG_RERANK_ENABLED", "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}
RERANK_MODEL_NAME = os.getenv("RERANK_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2").strip()
KOREAN_RERANK_MODEL_NAME = os.getenv(
    "KOREAN_RERANK_MODEL_NAME", "Dongjin-kr/ko-reranker-base"
).strip()
WEB_SEARCH_ENABLED = os.getenv("WEB_SEARCH_ENABLED", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
WEB_SEARCH_TOP_K = int(os.getenv("WEB_SEARCH_TOP_K", "10"))
FAISS_SEARCH_TOP_K = int(os.getenv("FAISS_SEARCH_TOP_K", "20"))


def answer_with_rag_for_server(
    question: str,
    k: int = 5,
    window: int = 1,
    index_dir: str = DEFAULT_INDEX_DIR,
) -> Dict[str, Any]:
    """
    FastAPI 서버 전용 RAG 응답 함수
    - JSON-friendly 반환
    """

    if WEB_SEARCH_ENABLED:
        retrieved: List[Dict[str, Any]] = hybrid_search_rerank(
            query=question,
            faiss_k=FAISS_SEARCH_TOP_K,
            web_k=WEB_SEARCH_TOP_K,
            top_n=k,
            window=window,
            index_dir=index_dir,
            rerank_model_name=KOREAN_RERANK_MODEL_NAME,
        )
    elif RAG_RERANK_ENABLED:
        retrieved = semantic_search_rerank(
            query=question,
            k=max(k * 4, 20),
            top_n=k,
            window=window,
            index_dir=index_dir,
            rerank_model_name=RERANK_MODEL_NAME,
        )
    else:
        retrieved = semantic_search(
            query=question,
            k=k,
            window=window,
            index_dir=index_dir,
        )

    # 2) 검색 실패
    if not retrieved:
        answer = generate_answer(
            user_prompt=question,
            system_prompt=(
                "당신은 가천대학교 AI 챗봇입니다.\n"
                "관련 문서를 찾지 못한 경우, 일반적인 안내만 간단히 제공하세요.\n"
                "추측하지 말고 한국어로 답변하세요."
            ),
        )
        return {
            "answer": answer,
            "contexts": [],
            "used_rag": False,
        }

    # 3) 컨텍스트 구성
    context_blocks = []
    for r in retrieved:
        r.setdefault("source", "internal")
        context_blocks.append(
            f"[SOURCE] {r.get('source','')}\n"
            f"[TITLE] {r.get('title','')}\n"
            f"[URL] {r.get('url','')}\n"
            f"[CONTENT]\n{r.get('context_text','')}"
        )

    context_text = "\n\n---\n\n".join(context_blocks)

    system_prompt = (
        "당신은 가천대학교 학사정보 RAG 어시스턴트입니다.\n"
        "아래 제공된 컨텍스트를 근거로만 답변하세요.\n"
        "컨텍스트에 없는 내용은 '확인할 수 없습니다'라고 답하세요.\n"
        "한국어 존댓말로 답변하세요."
    )

    user_prompt = (
        f"[컨텍스트]\n{context_text}\n\n"
        f"[질문]\n{question}\n\n"
        "위 컨텍스트를 활용하여 질문에 답변하세요."
    )

    # 4) LLM 호출
    answer = generate_answer(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
    )

    return {
        "answer": answer,
        "contexts": retrieved,
        "used_rag": True,
        "k": k,
        "window": window,
        "rerank_enabled": RAG_RERANK_ENABLED,
        "rerank_model_name": (
            KOREAN_RERANK_MODEL_NAME if WEB_SEARCH_ENABLED else RERANK_MODEL_NAME
        )
        if RAG_RERANK_ENABLED or WEB_SEARCH_ENABLED
        else None,
        "web_search_enabled": WEB_SEARCH_ENABLED,
        "web_search_top_k": WEB_SEARCH_TOP_K if WEB_SEARCH_ENABLED else None,
        "faiss_search_top_k": FAISS_SEARCH_TOP_K if WEB_SEARCH_ENABLED else None,
    }
