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
SRC_DIR = Path("/home/t25315/data/files")   # 원본 폴더
OUT_DIR = SRC_DIR / "hwp_file"              # 수집 폴더

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 이미 저장한 파일(내용) 해시 모음
seen_hashes = set()


# --------------------------
# 유틸 함수들
# --------------------------
def hash_file(path: Path, chunk_size: int = 65536) -> str:
    """로컬 파일의 SHA256 해시 계산"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes) -> str:
    """메모리에 있는 바이트 데이터의 SHA256 해시 계산"""
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def handle_duplicate_name(target_path: Path) -> Path:
    """
    서로 다른 내용인데 파일명만 같은 경우를 위해
    filename (1).hwp, filename (2).hwp 처럼 이름만 바꿔줌.
    (내용 중복은 seen_hashes로 이미 필터링)
    """
    base = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent

    counter = 1
    new_path = target_path

    while new_path.exists():
        new_path = parent / f"{base} ({counter}){suffix}"
        counter += 1

    return new_path


def decode_zip_filename(zinfo: zipfile.ZipInfo) -> str:
    """
    ZIP 엔트리 이름을 최대한 올바른 한글로 복구한다.

    - UTF-8 플래그가 켜져 있는 경우: 그대로 사용
    - 그렇지 않은 경우:
        cp437 로 인코딩된 문자열을 cp949 로 다시 디코딩 시도
        실패하면 원래 이름 그대로 반환
    """
    raw_name = zinfo.filename

    # UTF-8 플래그가 켜져 있으면 zipfile 이 이미 UTF-8 로 처리한 상태
    if zinfo.flag_bits & 0x800:
        return raw_name

    # 윈도우/한글 환경에서 만든 ZIP 의 흔한 패턴:
    #   내부적으로 cp949 → cp437 로 깨진 걸 다시 되살리기
    try:
        return raw_name.encode("cp437").decode("cp949")
    except UnicodeDecodeError:
        return raw_name  # 복구 실패하면 그냥 원본 사용


# --------------------------
# 메인 수집 함수
# --------------------------
def collect_hwp_from_directory(src_dir: Path, out_dir: Path):
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            fpath = Path(root) / file

            # out_dir 내부는 다시 돌지 않도록 무시 (무한루프 방지)
            if out_dir in fpath.parents:
                continue

            # ------------------------------
            # 1) 직접 .hwp 파일인 경우
            # ------------------------------
            if file.lower().endswith(".hwp"):
                try:
                    file_hash = hash_file(fpath)
                except Exception as e:
                    print(f"[ERROR] 해시 계산 실패: {fpath} ({e})")
                    continue

                if file_hash in seen_hashes:
                    print(f"[SKIP] 내용 중복 HWP: {fpath}")
                    continue

                seen_hashes.add(file_hash)
                print(f"[HWP] {fpath}")

                dst = out_dir / file
                if dst.exists():
                    dst = handle_duplicate_name(dst)

                shutil.copy2(fpath, dst)
                continue

            # ------------------------------
            # 2) ZIP 내부에 .hwp 파일이 있는 경우
            # ------------------------------
            if file.lower().endswith(".zip"):
                print(f"[ZIP] 내부 검사: {fpath}")

                try:
                    with zipfile.ZipFile(fpath, "r") as zipf:
                        for zinfo in zipf.infolist():
                            if not zinfo.filename.lower().endswith(".hwp"):
                                continue

                            # 파일 내용 읽기
                            try:
                                with zipf.open(zinfo, "r") as zf:
                                    data = zf.read()
                            except Exception as e:
                                print(f"    [ERROR] ZIP 내부 파일 읽기 실패: {zinfo.filename} ({e})")
                                continue

                            # 내용 해시로 중복 체크
                            file_hash = hash_bytes(data)
                            if file_hash in seen_hashes:
                                print(f"    [SKIP] ZIP 내부 내용 중복 HWP: {zinfo.filename}")
                                continue

                            seen_hashes.add(file_hash)

                            # 파일명 인코딩 복구 시도
                            fixed_name = decode_zip_filename(zinfo)
                            inner_name = os.path.basename(fixed_name)
                            if not inner_name:  # 혹시 폴더일 수 있으니 방어
                                inner_name = "unnamed_from_zip.hwp"

                            print(f"    → ZIP HWP 저장: {inner_name}")

                            dst = out_dir / inner_name
                            if dst.exists():
                                dst = handle_duplicate_name(dst)

                            # 내용 쓰기
                            with dst.open("wb") as out_f:
                                out_f.write(data)

                except zipfile.BadZipFile:
                    print(f"[ERROR] 손상된 ZIP: {fpath}")
                    continue


# --------------------------
# 실행
# --------------------------
if __name__ == "__main__":
    print("[INFO] HWP 수집 (인코딩 복구 + 내용 중복 제거) 시작")
    if not SRC_DIR.exists():
        raise FileNotFoundError(f"SRC_DIR 경로가 존재하지 않습니다: {SRC_DIR}")

    collect_hwp_from_directory(SRC_DIR, OUT_DIR)
    print(f"[DONE] 수집 완료 → {OUT_DIR}")
