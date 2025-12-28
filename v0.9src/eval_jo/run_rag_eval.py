import json
from datetime import datetime

from rag_pipeline import run_retrieval, generate_answer
# ↑ 이미 있는 함수들에 맞게 이름만 연결하면 됨

TOP_K = 5
MODEL_NAME = "gpt-4.1-mini"

def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def save_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    dataset = load_dataset("eval_dataset.jsonl")
    eval_logs = []

    for row in dataset:
        question = row["question"]

        # 1️⃣ Retrieval
        contexts = run_retrieval(question, top_k=TOP_K)
        # contexts = [{text, chunk_id, meta_id, score, url}, ...]

        # 2️⃣ Answer generation
        answer = generate_answer(question, contexts)

        # 3️⃣ Evaluation log
        eval_logs.append({
            "id": row["id"],
            "question": question,
            "answer": answer,
            "gold_answer": row["gold_answer"],
            "contexts": [
                {
                    "text": c["text"],
                    "meta_id": c["meta_id"],
                    "chunk_id": c["chunk_id"],
                    "score": c["score"]
                } for c in contexts
            ],
            "is_unstructured": row["is_unstructured"],
            "model": MODEL_NAME,
            "top_k": TOP_K,
            "timestamp": datetime.utcnow().isoformat()
        })

        print(f"[OK] {row['id']} processed")

    save_jsonl("rag_eval_logs.jsonl", eval_logs)

if __name__ == "__main__":
    main()
