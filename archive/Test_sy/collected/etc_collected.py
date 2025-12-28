#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import hashlib
from pathlib import Path

# --------------------------------------
# 기본 설정
# --------------------------------------
SRC_DIR = Path("/home/t25315/data/files")
OUT_DIR = SRC_DIR / "etc_files"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 이미 따로 수집해 둔 타입들 (확장자)
HWP_EXTS = {".hwp", ".hwpx"}
PDF_EXTS = {".pdf"}
EXCEL_EXTS = {
    ".xls", ".xlsx", ".xlsm", ".xlsb",
    ".xlt", ".xltx", ".xltm",
    ".csv", ".tsv", ".ods",
}
DOC_EXTS = {
    ".doc", ".docx", ".docm", ".dot", ".dotx",
    ".odt", ".fodt",
    ".gdoc", ".gsheet", ".gslides",
    ".rtf", ".txt", ".md", ".pages",
}
IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
}
VIDEO_EXTS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".m4v", ".flv", ".webm",
}

ALREADY_COLLECTED_EXTS = (
    HWP_EXTS
    | PDF_EXTS
    | EXCEL_EXTS
    | DOC_EXTS
    | IMAGE_EXTS
    | VIDEO_EXTS
)

# 이미 모아둔 결과 폴더들 (여기 안에 있는 파일들은 "수집된 것"으로 취급)
CATEGORY_DIR_NAMES = {
    "hwp_file",
    "img_files",
    "pdf_files",
    "xlsx_files",
    "docx_files",
    "mp4_files",
    "all_files",
}

# --------------------------------------
# 유틸 함수
# --------------------------------------
def hash_file(path: Path, chunk_size: int = 65536) -> str:
    """파일 내용을 SHA-256으로 해싱"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def handle_duplicate_name(path: Path) -> Path:
    """같은 이름이 이미 있으면 filename (1).ext, filename (2).ext... 식으로 변경"""
    base = path.stem
    suffix = path.suffix
    parent = path.parent

    counter = 1
    new_path = path
    while new_path.exists():
        new_path = parent / f"{base} ({counter}){suffix}"
        counter += 1
    return new_path


# --------------------------------------
# 1) 이미 수집된 파일들의 해시 모으기
# --------------------------------------
def build_known_hashes() -> set[str]:
    known = set()

    # 카테고리 폴더들 + etc_files 안의 기존 파일들까지 포함
    target_dirs = [SRC_DIR / name for name in CATEGORY_DIR_NAMES] + [OUT_DIR]

    for d in target_dirs:
        if not d.exists():
            continue

        for root, dirs, files in os.walk(d):
            for file in files:
                fpath = Path(root) / file
                try:
                    h = hash_file(fpath)
                except Exception as e:
                    print(f"[WARN] 해시 실패 (known): {fpath} ({e})")
                    continue
                known.add(h)

    print(f"[INFO] 이미 수집된 파일 해시 개수: {len(known)}")
    return known


# --------------------------------------
# 2) etc 후보 파일 수집
# --------------------------------------
def collect_etc_files(src_dir: Path, out_dir: Path, known_hashes: set[str]):
    # etc 내에서 이번 실행 중에 새로 추가되는 파일 해시
    etc_hashes = set(known_hashes)  # 이미 수집된 것들도 포함해서 시작

    for root, dirs, files in os.walk(src_dir):
        # 카테고리 폴더 / etc_files 안으로는 들어가지 않기
        dirs[:] = [
            d for d in dirs
            if d not in CATEGORY_DIR_NAMES and (src_dir / d) != out_dir
        ]

        for file in files:
            fpath = Path(root) / file

            # etc_files 자기 자신은 무시
            if out_dir in fpath.parents:
                continue

            ext = fpath.suffix.lower()

            # 이미 수집 대상으로 사용한 확장자는 etc에서 제외
            if ext in ALREADY_COLLECTED_EXTS:
                continue

            # 내용 기준 중복 체크
            try:
                h = hash_file(fpath)
            except Exception as e:
                print(f"[WARN] 해시 실패 (etc 후보): {fpath} ({e})")
                continue

            if h in etc_hashes:
                print(f"[SKIP] 내용 중복 (이미 수집됨): {fpath}")
                continue

            etc_hashes.add(h)
            print(f"[ETC] {fpath}")

            dst = out_dir / file
            if dst.exists():
                dst = handle_duplicate_name(dst)

            shutil.copy2(fpath, dst)


# --------------------------------------
# 실행
# --------------------------------------
if __name__ == "__main__":
    print("[INFO] etc_files 재구성 시작")

    if not SRC_DIR.exists():
        raise FileNotFoundError(f"[ERROR] SRC_DIR 경로가 존재하지 않습니다: {SRC_DIR}")

    known_hashes = build_known_hashes()
    collect_etc_files(SRC_DIR, OUT_DIR, known_hashes)

    print(f"[DONE] etc_files 정리 완료 → {OUT_DIR}")
