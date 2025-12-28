#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
from pathlib import Path

# ==========================
# 설정
# ==========================
ETC_DIR = Path("/home/t25315/data/files/etc_files")

# True  → 어떤 파일이 지워질지만 출력 (실제 삭제 없음)
# False → 실제로 파일 삭제
DRY_RUN = True  # 처음엔 True로 한번 확인하고, 이후 False로 바꿔서 실행 추천


# ==========================
# 유틸: 파일 해시 계산
# ==========================
def hash_file(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# ==========================
# 메인 로직: 중복 삭제
# ==========================
def remove_duplicates_in_dir(target_dir: Path):
    if not target_dir.exists():
        raise FileNotFoundError(f"대상 디렉토리가 존재하지 않습니다: {target_dir}")

    hash_to_file = {}  # hash -> 첫 번째 파일 경로
    duplicates = []    # (원본, 중복) 튜플 리스트

    # 1) 전체 파일 해시 계산 & 중복 탐지
    for root, dirs, files in os.walk(target_dir):
        for name in files:
            fpath = Path(root) / name

            # 혹시 디렉토리 심볼릭 링크 등 방어
            if not fpath.is_file():
                continue

            try:
                h = hash_file(fpath)
            except Exception as e:
                print(f"[WARN] 해시 실패: {fpath} ({e})")
                continue

            if h in hash_to_file:
                original = hash_to_file[h]
                duplicates.append((original, fpath))
            else:
                hash_to_file[h] = fpath

    # 2) 중복 파일 삭제 (또는 미리보기)
    print(f"\n[INFO] 중복으로 판단된 파일 수: {len(duplicates)}")

    for original, dup in duplicates:
        if DRY_RUN:
            print(f"[DRY-RUN] 삭제 대상: {dup} (원본은 유지: {original})")
        else:
            try:
                dup.unlink()
                print(f"[DELETE] {dup} (원본: {original})")
            except Exception as e:
                print(f"[ERROR] 삭제 실패: {dup} ({e})")

    if DRY_RUN:
        print("\n[INFO] DRY_RUN 모드이므로 실제로 아무 파일도 삭제되지 않았습니다.")
        print("삭제를 실행하려면 DRY_RUN = False 로 변경 후 다시 실행하세요.")
    else:
        print("\n[INFO] 실제 중복 파일 삭제가 완료되었습니다.")


# ==========================
# 실행
# ==========================
if __name__ == "__main__":
    remove_duplicates_in_dir(ETC_DIR)
