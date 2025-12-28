# rag_engine/rag_oss.py
# LLM에게 줄 재료를 만드는 함수
# LLM + RAG 결합. 문맥 확장된 검색 결과 가져와서 URL, 문서 제목 붙여서 컨텍스트로 합치고 
# 최종 프롬프트 만들어서 OSS 부른 뒤 프롬프트 집어넣음. 답변 받아옴.

from typing import Dict, Any, List

from .rag import semantic_search
from langChain_v3.vectorstore import DEFAULT_INDEX_DIR
from .load_local_gpt_oss import load_local_gpt_oss


def answer_with_rag_oss(
    question: str,
    k: int = 5,
    window: int = 1,
    index_dir: str = DEFAULT_INDEX_DIR,
    model_path: str = "/home/t25315/models/gpt-oss-20b-bf16",
) -> Dict[str, Any]:
    """
    OpenAI API 없이, 로컬 OSS 모델만 사용하는 RAG 파이프라인.
    """

    # 1) 검색 (Retrieval)
    retrieved = semantic_search(
        query=question,
        k=k,
        window=window,
        index_dir=index_dir,
    )

    if not retrieved:
        return {"answer": "관련 문서를 찾을 수 없습니다.", "contexts": []}

    # 2) LLM에 전달할 컨텍스트 생성
    context_blocks = []
    for r in retrieved:
        title = r["title"] or "(제목 없음)"
        url = r["url"] or "(URL 없음)"

        block = (
            f"[문서 제목] {title}\n"
            f"[URL] {url}\n"
            f"[문맥]\n{r['context_text']}"
        )
        context_blocks.append(block)

    full_context = "\n\n-----\n\n".join(context_blocks)

    # 3) 프롬프트 생성
    system_prompt = (
        "당신은 가천대학교 학사 행정 정보를 답변하는 AI입니다."
        "반드시 제공된 컨텍스트에 있는 내용만 사용해 답변하십시오."
        "답변은 한국어 존댓말로 1~2문장만 작성하십시오."
        "답변 외의 설명, 분석, 메모, 영어 문장은 절대 출력하지 마십시오."
        "답변은 문장이 중간에 끊기지 않도록 끝까지 작성하세요."
    )

    user_prompt = (
        f"[컨텍스트]\n{full_context}\n\n"
        f"[질문]\n{question}\n\n"
        "위 컨텍스트만 사용하여 질문에 답변하세요."
    )

    #final_prompt = system_prompt + "\n" + user_prompt

    # 4) OSS 모델 불러오기
    llm = load_local_gpt_oss(model_path=model_path, debug_print=True)  # 디버그 켤거면 True

    # 5) 답변 생성
    answer = llm.generate(system_prompt, user_prompt)

    return {
        "answer": answer,
        "contexts": retrieved,
        "used_k": k,
        "used_window": window,
    }

# 나중에는 HTTP 요청으로 질문을 받아와야 함
# 지금은 임시로 질문 하드 코딩
if __name__ == "__main__":
    import time
    print("[START] rag_oss.py 실행됨")
    q = "빅데이터경영전공 교육과정 편성의 기본원칙은 무엇인가요?"
    t0 = time.time()

    try:
        result = answer_with_rag_oss(q, k=3, window=1)
        print("[DONE] 실행 완료, 걸린 시간:", round(time.time() - t0, 2), "초")
        print("\n[ANSWER]\n", result.get("answer")) #이게 사용자에게 보여줘야 하는 최종 답변
        print("\n[CONTEXTS 개수]", len(result.get("contexts", [])))
        if result.get("contexts"):
            c0 = result["contexts"][0]
            print("\n[첫 컨텍스트 미리보기]")
            print("title:", c0.get("title"))
            print("url:", c0.get("url"))
            print("text:", (c0.get("context_text") or "")[:200])
    except Exception as e:
        print("[ERROR] 실행 중 예외 발생:", repr(e))
        raise
