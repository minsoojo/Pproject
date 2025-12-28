import os
import json
import shutil

# 찾을 ID 목록
target_ids = [
    "file-793-434",
    "file-1135-703",
    "file-1194-832",
    "file-2778-1449",
    "file-4102-1797",
    "file-5710-3153",
    "file-5793-3279",
    "file-6462-3863",
]

metadata_path = "/home/t25315/data/metadata_updated.jsonl"
output_dir = "/home/t25315/data/seg_files"

os.makedirs(output_dir, exist_ok=True)

found = 0

with open(metadata_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        # 현재 JSON 라인에 우리가 찾는 id가 있는지 확인
        if item.get("id") in target_ids:
            file_path = item.get("file_path")

            if file_path and os.path.exists(file_path):
                # 파일명만 추출
                filename = os.path.basename(file_path)
                dst_path = os.path.join(output_dir, filename)

                shutil.copy2(file_path, dst_path)
                print(f"[COPIED] {file_path} → {dst_path}")

                found += 1
            else:
                print(f"[NOT FOUND] 파일 없음: {file_path}")

print(f"\n[DONE] 총 {found}개의 파일을 복사 완료.")
