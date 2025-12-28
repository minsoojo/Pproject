from langChain_v3.RAGLLM.load_local_gpt_oss_test import load_local_gpt_oss_test
from langChain_v3.RAGLLM.load_local_gpt_oss import load_local_gpt_oss

if __name__ == "__main__":
    llm = load_local_gpt_oss(
    # llm = load_local_gpt_oss_test(
        # model_path="/home/t25315/models/gpt-oss-20b",
        max_new_tokens=128,
    )

    prompt = """당신은 가천대학교 학사 Q&A 챗봇입니다.
질문: 등록금 납부 기간은 언제인가요?
답변:"""

    out = llm.generate(prompt)
    print("=== LLM OUTPUT ===")
    print(out)
