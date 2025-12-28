# langChain_v3/RAGLLM/llm_service.py

# from .llm_runtime import get_llm


# SYSTEM_PROMPT_DEFAULT = (
#     "당신은 가천대학교 학사·행정 정보를 도와주는 AI 어시스턴트입니다.\n"
#     "질문에 대해 간결하고 정확하게 한국어로 답변하세요.\n"
#     "불확실한 정보는 추측하지 말고 '확인할 수 없습니다'라고 답하세요.\n"
# )


# def generate_answer(
#     user_prompt: str,
#     system_prompt: str = SYSTEM_PROMPT_DEFAULT,
# ) -> str:
#     """
#     서버/CLI/RAG에서 공통으로 사용하는 LLM 호출 함수
#     """
#     llm = get_llm()          # 🔥 여기서 단 한 번만 로드됨
#     return llm.generate(system_prompt, user_prompt)

from langChain_v3.RAGLLM.gpt_api_llm import GPTAPILLM

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = GPTAPILLM()
    return _llm

def generate_answer(system_prompt, user_prompt):
    llm = get_llm()
    return llm.generate(system_prompt, user_prompt)