#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import zipfile
import hashlib
from pathlib import Path

# --------------------------
# 설정
# --------------------------
SRC_DIR = Path("/home/t25315/data/files")
OUT_DIR = SRC_DIR / "docx_files"

OUT_DIR.mkdir(parents=True, exist_ok=True)

DOC_EXTENSIONS = {
    # Word documents
    ".doc", ".docx", ".docm", ".dot", ".dotx",
    ".DOC", ".DOCX", ".DOCM", ".DOT", ".DOTX"
}

seen_hashes = set()


# --------------------------
# 유틸 함수들
# --------------------------
def hash_file(path: Path, chunk_size: int = 65536) -> str:
    """로컬 파일 SHA256 해시 계산"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes) -> str:
    """ZIP 내부에서 읽은 바이트 해시"""
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def handle_duplicate_name(path: Path) -> Path:
    """파일명 중복 시 filename (1).docx 형태로 변경"""
    base = path.stem
    suffix = path.suffix
    parent = path.parent

    counter = 1
    new_path = path

    while new_path.exists():
        new_path = parent / f"{base} ({counter}){suffix}"
        counter += 1

    return new_path


def decode_zip_filename(zinfo: zipfile.ZipInfo) -> str:
    """
    ZIP 내부 파일명 한글 복구:
    - UTF-8 플래그면 그대로
    - 아니면 cp437 → cp949 복구 시도
    """
    raw = zinfo.filename

    if zinfo.flag_bits & 0x800:
        return raw

    try:
        return raw.encode("cp437").decode("cp949")
    except UnicodeDecodeError:
        return raw


# --------------------------
# 메인 함수
# --------------------------
def collect_docs_from_directory(src_dir: Path, out_dir: Path):
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            fpath = Path(root) / file

            # docx_files 내부는 무시
            if out_dir in fpath.parents:
                continue

            ext = fpath.suffix

            # ------------------------------
            # 1) 직접 존재하는 문서 파일
            # ------------------------------
            if ext in DOC_EXTENSIONS:
                try:
                    file_hash = hash_file(fpath)
                except Exception as e:
                    print(f"[ERROR] 해시 실패: {fpath} ({e})")
                    continue

                if file_hash in seen_hashes:
                    print(f"[SKIP] 중복 DOC: {fpath}")
                    continue

                seen_hashes.add(file_hash)
                print(f"[DOC] {fpath}")

                dst = out_dir / file
                if dst.exists():
                    dst = handle_duplicate_name(dst)

                shutil.copy2(fpath, dst)
                continue

            # ------------------------------
            # 2) ZIP 내부 문서 파일
            # ------------------------------
            if ext.lower() == ".zip":
                print(f"[ZIP] 문서 검사: {fpath}")

                try:
                    with zipfile.ZipFile(fpath, "r") as zipf:
                        for zinfo in zipf.infolist():
                            inner_ext = Path(zinfo.filename).suffix
                            if inner_ext not in DOC_EXTENSIONS:
                                continue

                            # ZIP 내부 파일 내용 읽기
                            try:
                                with zipf.open(zinfo, "r") as zf:
                                    data = zf.read()
                            except Exception as e:
                                print(f"    [ERROR] ZIP 내부 문서 읽기 실패: {zinfo.filename} ({e})")
                                continue

                            file_hash = hash_bytes(data)
                            if file_hash in seen_hashes:
                                print(f"    [SKIP] ZIP 중복 DOC: {zinfo.filename}")
                                continue

                            seen_hashes.add(file_hash)

                            # 파일명 인코딩 복구
                            fixed_name = decode_zip_filename(zinfo)
                            inner_name = os.path.basename(fixed_name) or "unnamed_from_zip.docx"

                            print(f"    → ZIP DOC 저장: {inner_name}")

                            dst = out_dir / inner_name
                            if dst.exists():
                                dst = handle_duplicate_name(dst)

                            with dst.open("wb") as out_f:
                                out_f.write(data)

                except zipfile.BadZipFile:
                    print(f"[ERROR] 손상 ZIP: {fpath}")
                    continue


# --------------------------
# 실행 부분
# --------------------------
if __name__ == "__main__":
    print("[INFO] 문서(doc/docx/odt 등) 수집 시작")

    if not SRC_DIR.exists():
        raise FileNotFoundError(f"[ERROR] 원본 디렉토리가 존재하지 않습니다: {SRC_DIR}")

    collect_docs_from_directory(SRC_DIR, OUT_DIR)

    print(f"[DONE] 문서 파일 수집 완료 → {OUT_DIR}")
