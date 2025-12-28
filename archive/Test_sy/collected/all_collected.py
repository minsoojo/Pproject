#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import zipfile
import hashlib
from pathlib import Path

# --------------------------------------
# 설정
# --------------------------------------
SRC_DIR = Path("/home/t25315/data/files")
OUT_DIR = SRC_DIR / "all_files"

OUT_DIR.mkdir(parents=True, exist_ok=True)

seen_hashes = set()


# --------------------------------------
# 유틸 함수들
# --------------------------------------
def hash_file(path: Path, chunk_size: int = 65536) -> str:
    """로컬 파일 SHA-256 해시"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes) -> str:
    """메모리에 로드된 바이트 데이터 SHA-256 해시"""
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def handle_duplicate_name(path: Path) -> Path:
    """파일명 충돌 시 filename (1).ext 형태로 변경"""
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
    ZIP 파일명 복구 (cp437 → cp949)
    UTF-8 플래그 있으면 그대로 사용
    """
    raw = zinfo.filename

    if zinfo.flag_bits & 0x800:
        return raw

    try:
        return raw.encode("cp437").decode("cp949")
    except UnicodeDecodeError:
        return raw


# --------------------------------------
# 메인 함수
# --------------------------------------
def collect_all_files(src_dir: Path, out_dir: Path):
    for root, dirs, files in os.walk(src_dir):

        # 폴더는 무시하지만 파일 탐색은 진행
        for file in files:
            fpath = Path(root) / file

            # 결과 폴더 내부 파일은 스킵
            if out_dir in fpath.parents:
                continue

            ext = fpath.suffix.lower()

            # --------------------------
            # 1) ZIP이 아닌 일반 파일
            # --------------------------
            if ext != ".zip":
                try:
                    file_hash = hash_file(fpath)
                except Exception as e:
                    print(f"[ERROR] 해시 실패: {fpath} ({e})")
                    continue

                if file_hash in seen_hashes:
                    print(f"[SKIP] 중복 파일: {fpath}")
                    continue

                seen_hashes.add(file_hash)
                print(f"[FILE] {fpath}")

                dst = out_dir / fpath.name
                if dst.exists():
                    dst = handle_duplicate_name(dst)

                shutil.copy2(fpath, dst)
                continue

            # --------------------------
            # 2) ZIP 내부 모든 파일 처리
            # --------------------------
            print(f"[ZIP] 압축 파일 검사: {fpath}")

            try:
                with zipfile.ZipFile(fpath, "r") as zipf:
                    for zinfo in zipf.infolist():
                        # 폴더는 스킵
                        if zinfo.is_dir():
                            continue

                        # ZIP 내부 파일 내용 읽기
                        try:
                            with zipf.open(zinfo, "r") as zf:
                                data = zf.read()
                        except Exception as e:
                            print(f"    [ERROR] ZIP 내부 파일 읽기 실패: {zinfo.filename} ({e})")
                            continue

                        # 내용 기반 중복 체크
                        file_hash = hash_bytes(data)
                        if file_hash in seen_hashes:
                            print(f"    [SKIP] ZIP 내부 중복 파일: {zinfo.filename}")
                            continue

                        seen_hashes.add(file_hash)

                        # ZIP 한글 파일명 복구
                        fixed_name = decode_zip_filename(zinfo)
                        inner_name = os.path.basename(fixed_name)
                        if not inner_name:
                            inner_name = "unnamed_from_zip"

                        print(f"    → ZIP 파일 저장: {inner_name}")

                        dst = out_dir / inner_name
                        if dst.exists():
                            dst = handle_duplicate_name(dst)

                        # 내용 저장
                        with dst.open("wb") as out_f:
                            out_f.write(data)

            except zipfile.BadZipFile:
                print(f"[ERROR] 손상 ZIP: {fpath}")
                continue


# --------------------------------------
# 실행
# --------------------------------------
if __name__ == "__main__":
    print("[INFO] 전체 파일 수집 시작 (중복 제거)")

    if not SRC_DIR.exists():
        raise FileNotFoundError(f"[ERROR] 원본 디렉토리가 존재하지 않습니다: {SRC_DIR}")

    collect_all_files(SRC_DIR, OUT_DIR)

    print(f"[DONE] 전체 파일 수집 완료 → {OUT_DIR}")
