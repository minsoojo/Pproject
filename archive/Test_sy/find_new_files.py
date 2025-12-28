#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os

# 🔧 여기만 너 환경에 맞게 수정
OLD_META_PATH = "/home/t25315/data_backup/metadata.jsonl"  # 재크롤링 전 백업본
NEW_META_PATH = "/home/t25315/data/metadata.jsonl"         # 지금 최신
OUT_PATH_JSONL = "/home/t25315/data/new_files_only.jsonl"
OUT_PATH_TXT   = "/home/t25315/data/new_files_only_paths.txt"

def load_old_file_urls(path):
    urls = set()
    if not os.path.exists(path):
        print(f"[WARN] old metadata not found: {path}")
        return urls

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except:
                continue

            # type이 file: 인 항목만
            if str(row.get("type", "")).startswith("file:") and row.get("url"):
                urls.add(row["url"])

    print(f"[INFO] old file urls: {len(urls)}개")
    return urls


def main():
    old_urls = load_old_file_urls(OLD_META_PATH)

    new_entries = []
    new_file_paths = []

    with open(NEW_META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except:
                continue

            mtype = str(row.get("type", ""))
            url   = row.get("url")
            fpath = row.get("file_path")

            # 파일이 아닌 메타는 무시
            if not mtype.startswith("file:") or not url:
                continue

            # 예전 meta에 없던 url 이면 → "새로 생긴 파일"
            if url not in old_urls:
                new_entries.append(row)
                if fpath:
                    new_file_paths.append(fpath)

    print(f"[INFO] 새로 생긴 파일 메타 수: {len(new_entries)}개")

    # 새 파일들의 메타데이터만 따로 저장
    with open(OUT_PATH_JSONL, "w", encoding="utf-8") as fout:
        for row in new_entries:
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")

    # 파일 경로만 보고 싶으면 이거 보면 됨
    with open(OUT_PATH_TXT, "w", encoding="utf-8") as fout:
        for p in new_file_paths:
            fout.write(p + "\n")

    print(f"[INFO] 새 파일 메타: {OUT_PATH_JSONL}")
    print(f"[INFO] 새 파일 경로 목록: {OUT_PATH_TXT}")


if __name__ == "__main__":
    main()
