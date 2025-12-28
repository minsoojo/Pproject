import json
from collections import defaultdict

def create_duplicate_metadata(input_path, output_path):
    groups = defaultdict(list)

    # 1) JSONL 파일 읽어서 id별 수집
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            row = json.loads(line)
            row_id = row.get("id")
            if row_id:
                groups[row_id].append(row)

    # 2) id 개수 2개 이상 → 중복된 id
    duplicates = {id_: rows for id_, rows in groups.items() if len(rows) > 1}

    # 3) 파일로 저장
    with open(output_path, "w", encoding="utf-8") as out:
        for row_id, rows in duplicates.items():
            out.write(json.dumps({
                "id": row_id,
                "rows": rows   # 중복된 모든 행
            }, ensure_ascii=False) + "\n")

    print(f"[완료] 중복된 id만 모은 JSONL 생성 → {output_path}")
    print(f"[INFO] 중복된 id 개수: {len(duplicates)}")


# 실행 예시
create_duplicate_metadata(
    input_path="/home/t25315/data/metadata_fixed.jsonl",
    output_path="/home/t25315/data/metadata_id_ver2.jsonl"
)
