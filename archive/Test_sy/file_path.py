#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os  
import json
from pathlib import Path

# --------------------------------------
# 설정
# --------------------------------------
BASE_DIR = Path("/home/t25315/data/files")
META_PATH = Path("/home/t25315/data/metadata.jsonl")  # metadata.jsonl 의 실제 경로
OUT_META_PATH = Path("/home/t25315/data/metadata_updated_sy.jsonl")  # 수정본 출력


# --------------------------------------
# 1) 실제 존재하는 모든 파일 경로 수집
# --------------------------------------
def build_real_file_map(base_dir: Path):
    """
    모든 파일을 스캔해서:
    { "원본파일명.lower()" : "실제 경로 문자열" }
    형태로 매핑을 만든다.
    """
    name_to_path = {}

    for root, dirs, files in os.walk(base_dir):
        for f in files:
            p = Path(root) / f
            name_to_path[f.lower()] = str(p)

    print(f"[INFO] 총 {len(name_to_path)}개의 파일 경로 인덱싱 완료")
    return name_to_path


# --------------------------------------
# 2) metadata.jsonl 갱신
# --------------------------------------
def update_metadata(meta_path: Path, out_path: Path, real_map: dict):
    updated = 0
    missing = 0

    with meta_path.open("r", encoding="utf-8") as infile, \
         out_path.open("w", encoding="utf-8") as outfile:

        for line in infile:
            obj = json.loads(line)

            # file_path가 있는 경우에만 처리
            if "file_path" in obj and obj["file_path"]:
                old_path = Path(obj["file_path"])
                filename = old_path.name.lower()  # 파일명만 추출

                if filename in real_map:
                    # 새 경로로 업데이트
                    obj["file_path"] = real_map[filename]
                    updated += 1
                else:
                    # 실제 위치를 못 찾음
                    missing += 1
                    print(f"[WARN] 실제 파일을 찾을 수 없음: {old_path}")
                    obj["file_path"] = None  # 또는 그대로 둘 수도 있음

            outfile.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"\n[INFO] 수정 완료")
    print(f" - 경로 업데이트 성공: {updated}개")
    print(f" - 실제 파일 없음: {missing}개")
    print(f" - 결과 저장: {out_path}")


# --------------------------------------
# 실행
# --------------------------------------
if __name__ == "__main__":
    print("[INFO] 실제 파일 매핑 생성 중...")
    real_map = build_real_file_map(BASE_DIR)

    print("[INFO] metadata.jsonl 업데이트 시작...")
    update_metadata(META_PATH, OUT_META_PATH, real_map)
