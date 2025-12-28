import json
import pandas as pd

from ragas import evaluate
from ragas.metrics import (
    context_recall,
    context_precision,
    faithfulness,
    answer_relevancy
)
from datasets import Dataset

def load_logs(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def to_ragas_dataset(logs):
    return Dataset.from_list([
        {
            "question": r["question"],
            "answer": r["answer"],
            "contexts": [c["text"] for c in r["contexts"]],
            "ground_truth": r["gold_answer"]
        }
        for r in logs
    ])

def main():
    logs = load_logs("rag_eval_logs.jsonl")
    ds = to_ragas_dataset(logs)

    result = evaluate(
        ds,
        metrics=[
            context_recall,
            context_precision,
            faithfulness,
            answer_relevancy
        ]
    )

    df = result.to_pandas()
    df.to_csv("ragas_result.csv", index=False, encoding="utf-8-sig")

    print("=== RAGAS RESULT (mean) ===")
    print(df.mean())

if __name__ == "__main__":
    main()
