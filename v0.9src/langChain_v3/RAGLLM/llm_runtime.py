# # langChain_v3/RAGLLM/llm_runtime.py

# from .load_local_gpt_oss import load_local_gpt_oss

# _llm = None

# def get_llm():
#     global _llm
#     if _llm is None:
#         print("[LLM] Loading gpt-oss-20b (once)...")
#         _llm = load_local_gpt_oss(
#             model_path="/home/t25315/models/gpt-oss-20b-bf16",
#             max_new_tokens=256,
#         )
#         print("[LLM] Loaded.")
#     return _llm

# 주의!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
