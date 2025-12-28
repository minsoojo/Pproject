# 크롤링 때, 메타데이터 파일경로에 간혈적으로 생기는 crdownload 제거 스크립트
# 
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

DATA_DIR = "data"
FILE_DIR = os.path.join(DATA_DIR, "files")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.jsonl")

def load_metadata():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def save_metadata(all_meta):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        for m in all_meta:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

def fix_crdownload():
    all_meta = list(load_metadata())
    modified = False
    fixed_count = 0
    removed_count = 0

    print("\n[INFO] metadata.jsonl의 .crdownload 경로 정리 시작\n")

    for meta in all_meta:
        fp = meta.get("file_path")
        if not fp:
            continue

        # .crdownload 파일만 처리
        if not fp.endswith(".crdownload"):
            continue

        print(f"[CRDL] 처리 대상: {fp}")

        # crdownload 제거한 정상 경로 후보
        normal_path = fp.replace(".crdownload", "")

        # 정상 파일이 실제로 존재하는지 체크
        if os.path.exists(normal_path):
            print(f"   → 정상 파일 발견!  {normal_path}")
            meta["file_path"] = normal_path  # 경로 수정
            fixed_count += 1
            modified = True

        else:
            print("   → 정상 파일 없음 → 잘못된 다운로드로 판단 (그대로 둠)")
            removed_count += 1

    # 변경사항이 있으면 metadata.jsonl 저장
    if modified:
        save_metadata(all_meta)
        print("\n[INFO] metadata.jsonl 업데이트 완료!")
    else:
        print("\n[INFO] 변경 없음")

    print("\n[DONE] 정상 파일로 교체된 항목:", fixed_count)
    print("[DONE] 미완성(crdownload) 상태로 남은 항목:", removed_count)

if __name__ == "__main__":
    fix_crdownload()
