#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import shutil

# 경로 설정
ERROR_LOG_PATH = "/home/t25315/data/error_files.txt"          # <- 필요시 수정
METADATA_PATH = "/home/t25315/data/metadata_updated.jsonl"
DEST_DIR = "/home/t25315/data/img_pdf"

def load_empty_text_ids(error_log_path: str):
    """
    error_files.txt 에서 EMPTY_TEXT 인 file-*-* id만 추출
    """
    ids = set()

    with open(error_log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "EMPTY_TEXT" not in line:
                continue

            # 예: [2025-11-29 ...] file-2-3 | URL | EMPTY_TEXT |
            try:
                parts = line.split("|")
                # parts[0] = "[timestamp] file-2-3 "
                left_part = parts[0].strip()
                file_id = left_part.split()[-1]  # 마지막 토큰 -> file-2-3
                ids.add(file_id)
            except Exception:
                # 형식이 이상한 줄은 그냥 스킵
                continue

    return ids


def main():
    # 1) EMPTY_TEXT 인 id 모으기
    print(f"[INFO] Loading EMPTY_TEXT ids from: {ERROR_LOG_PATH}")
    empty_ids = load_empty_text_ids(ERROR_LOG_PATH)
    print(f"[INFO] Found {len(empty_ids)} ids with EMPTY_TEXT")

    if not empty_ids:
        print("[INFO] No EMPTY_TEXT ids found. Exit.")
        return

    # 2) 타겟 폴더 준비
    os.makedirs(DEST_DIR, exist_ok=True)
    print(f"[INFO] Target directory: {DEST_DIR}")

    copied = 0
    skipped_not_pdf = 0
    skipped_not_found = 0

    # 3) metadata_updated.jsonl 순회
    print(f"[INFO] Reading metadata from: {METADATA_PATH}")
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            file_id = record.get("id")
            if file_id not in empty_ids:
                continue

            file_path = record.get("file_path") or record.get("path")

            if not file_path:
                continue

            # 필요하면 여기서 절대경로 보정
            if not os.path.isabs(file_path):
                # 메타데이터에 상대경로가 들어있다면 이 부분을 맞게 고쳐줘야 함
                file_path = os.path.join("/home/t25315", file_path)

            # pdf만 대상으로
            if not file_path.lower().endswith(".pdf"):
                skipped_not_pdf += 1
                continue

            if not os.path.exists(file_path):
                print(f"[WARN] File not found: {file_path}")
                skipped_not_found += 1
                continue

            # 4) img_pdf 폴더로 복사
            base_name = os.path.basename(file_path)
            dest_path = os.path.join(DEST_DIR, base_name)

            # 이름이 중복되면 id를 앞에 붙여서 저장
            if os.path.exists(dest_path):
                root, ext = os.path.splitext(base_name)
                dest_path = os.path.join(DEST_DIR, f"{file_id}_{root}{ext}")

            shutil.copy2(file_path, dest_path)
            copied += 1
            print(f"[COPY] {file_id}: {file_path} -> {dest_path}")

    print("\n===== SUMMARY =====")
    print(f"Copied PDF files     : {copied}")
    print(f"Skipped (not PDF)    : {skipped_not_pdf}")
    print(f"Skipped (not found)  : {skipped_not_found}")
    print("===================")


if __name__ == "__main__":
    main()
