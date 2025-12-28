from langChain_v3.RAGLLM.rag import semantic_search
from typing import Dict, Any, List
from sentence_transformers import CrossEncoder

question = input("질문 입력 : ")

# ===============================
# 1️⃣ FAISS 1차 검색
# ===============================
retrieved: List[Dict[str, Any]] = semantic_search(
    query=question,
    k=20,
    window=2,
)

print("\n==============================")
print("📌 BEFORE RERANK (FAISS order)")
print("==============================")

for i, r in enumerate(retrieved[:10], 1):
    print(f"[{i}] faiss_score={r.get('score')}")
    print(f"[{i}] meta_id={r.get('meta_id')}")
    print(f"[{i}] chunk_id={r.get('chunk_id')}")
    print(f"[{i}] chunk_index={r.get('chunk_index')}")
    print(r.get("context_text", "")[:])
    # print(r.get("chunk_text", "")[:])
    print("-" * 80)

# ===============================
# 2️⃣ 리랭커 로딩
# ===============================
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# ===============================
# 3️⃣ (질문, 문서) 쌍 생성
# ===============================
pairs = []
valid_rows = []

for r in retrieved:
    # text = r.get("chunk_text")
    text = r.get("context_text")
    if text:
        pairs.append((question, text))
        valid_rows.append(r)

print(f"\n[DEBUG] rerank 대상 문서 수: {len(pairs)}")

# ===============================
# 4️⃣ 리랭크 점수 계산
# ===============================
scores = reranker.predict(pairs)

print("\n[DEBUG] rerank scores (top 10 raw):")
for i, s in enumerate(scores[:10], 1):
    print(f"{i}: {float(s):.4f}")

# ===============================
# 5️⃣ 점수 기준 재정렬
# ===============================
reranked = sorted(
    zip(valid_rows, scores),
    key=lambda x: x[1],
    reverse=True
)

# ===============================
# 6️⃣ Top-N 선택
# ===============================
TOP_N = 5
top_retrieved = reranked[:TOP_N]

# ===============================
# 7️⃣ 리랭크 결과 출력
# ===============================
print("\n==============================")
print("🚀 AFTER RERANK (Cross-Encoder)")
print("==============================")

for i, (r, rerank_score) in enumerate(top_retrieved, 1):
    print(f"[{i}] rerank_score={float(rerank_score):.4f} | faiss_score={r.get('score')}")
    # print(r["chunk_text"][:300])
    print(r["context_text"][:300])
    print("-" * 80)

# ===============================
# 8️⃣ 순위 변화 요약
# ===============================
print("\n📊 RANK CHANGE SUMMARY")
print("==============================")

for i, (r, rerank_score) in enumerate(top_retrieved, 1):
    old_rank = retrieved.index(r) + 1
    print(
        f"문서 {i}: FAISS rank {old_rank} → RERANK rank {i} "
        f"(rerank_score={float(rerank_score):.4f})"
    )
