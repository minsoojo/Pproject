# extract 모듈 이용, jsonl 기반 파일 텍스트 변환 스크립트


# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

# import os
# import json
# from extract import extract_by_ext

# DATA_DIR = "data"
# FILE_DIR = os.path.join(DATA_DIR, "files")
# FILE_TEXT_DIR = os.path.join(DATA_DIR, "file_text")
# METADATA_FILE = os.path.join(DATA_DIR, "metadata.jsonl")

# os.makedirs(FILE_TEXT_DIR, exist_ok=True)


# def load_metadata():
#     with open(METADATA_FILE, "r", encoding="utf-8") as f:
#         for line in f:
#             yield json.loads(line)


# def save_metadata(all_meta):
#     """metadata.jsonl 전체를 다시 저장 (선택 기능)"""
#     with open(METADATA_FILE, "w", encoding="utf-8") as f:
#         for meta in all_meta:
#             f.write(json.dumps(meta, ensure_ascii=False) + "\n")


# def extract_by_metadata():
#     all_meta = list(load_metadata())  # JSONL 전체 로드
#     modified = False
#     processed = 0
#     created = 0

#     print("\n[INFO] metadata 기반 파일 전처리 시작")

#     for meta in all_meta:
#         if not meta["type"].startswith("file"):
#             continue  # HTML은 무시

#         file_path = meta.get("file_path")
#         text_path = meta.get("text_path")

#         print(f"\n[FILE] {meta['id']} → {meta['url']}")

#         # 파일 경로가 없으면 스킵
#         if not file_path or not os.path.exists(file_path):
#             print("   [SKIP] 파일 없음:", file_path)
#             continue

#         # text_path가 이미 존재하면 스킵
#         if text_path and os.path.exists(text_path):
#             print("   [SKIP] 이미 텍스트 있음:", text_path)
#             continue

#         # 새 text_path 설정 (없으면 생성)
#         if not text_path:
#             base = os.path.splitext(os.path.basename(file_path))[0]
#             text_path = os.path.join(FILE_TEXT_DIR, base + ".txt")
#             meta["text_path"] = text_path
#             modified = True

#         # 텍스트 추출
#         print("   [EXTRACT] 텍스트 추출 중…")
#         extracted = extract_by_ext(file_path)

#         if not extracted.strip():
#             print("   [WARN] 텍스트 추출 실패 or 빈 내용")
#             continue

#         # 저장
#         with open(text_path, "w", encoding="utf-8", errors="ignore") as f:
#             f.write(extracted)

#         print("   [OK] 저장됨 →", text_path)
#         created += 1
#         processed += 1

#     # metadata.jsonl 업데이트 (원하면)
#     if modified:
#         print("\n[INFO] metadata.jsonl 업데이트 중…")
#         save_metadata(all_meta)

#     print("\n[DONE] 파일 메타데이터 개수:", len(all_meta))
#     print("[DONE] 전처리된 파일 수:", processed)
#     print("[DONE] 텍스트 생성:", created)


# if __name__ == "__main__":
#     extract_by_metadata()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from multiprocessing import Process, Queue
from datetime import datetime

from extract import extract_by_ext

DATA_DIR = "data"
FILE_DIR = os.path.join(DATA_DIR, "files")
FILE_TEXT_DIR = os.path.join(DATA_DIR, "file_text")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.jsonl")

ERROR_LOG = os.path.join(DATA_DIR, "error_files.txt")
UPDATED_META = os.path.join(DATA_DIR, "metadata_updated.jsonl")

os.makedirs(FILE_TEXT_DIR, exist_ok=True)

ALLOWED_EXTS = {
    ".pdf", ".hwp", ".hwpx",
    ".doc", ".docx",
    ".xls", ".xlsx",
    ".ppt", ".pptx",
    ".zip"
}


def load_metadata():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def save_updated_meta(modified_list):
    """수정된 metadata 항목만 따로 저장"""
    if not modified_list:
        return
    with open(UPDATED_META, "w", encoding="utf-8") as f:
        for m in modified_list:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")


# -------------------------
# 자식 프로세스용 워커
# -------------------------
def _worker_extract(path, q):
    try:
        text = extract_by_ext(path)
        q.put({"status": "ok", "text": text})
    except Exception as e:
        q.put({"status": "error", "error": str(e)})


def safe_extract(path, timeout=45):
    """extract_by_ext()를 별도 프로세스에서 안전하게 실행"""
    q = Queue()
    p = Process(target=_worker_extract, args=(path, q))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return {"status": "timeout", "text": ""}

    if p.exitcode not in (0, None):
        return {"status": "segfault", "text": "", "exitcode": p.exitcode}

    if not q.empty():
        return q.get()

    return {"status": "unknown", "text": ""}


def log_error(meta, reason, extra=""):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {meta['id']} | {meta.get('url')} | {reason} | {extra}\n")


def extract_by_metadata():
    all_meta = list(load_metadata())
    modified_list = []  # 메타데이터가 변경된 항목 저장

    processed = 0
    created = 0

    print("\n[INFO] metadata 기반 파일 전처리 시작\n")

    for meta in all_meta:
        if not meta["type"].startswith("file"):
            continue

        file_id = meta["id"]
        url = meta["url"]
        file_path = meta.get("file_path")
        text_path = meta.get("text_path")

        print(f"\n[FILE] {file_id} → {url}")

        # 1) file_path 없으면 오류 로그
        if not file_path:
            log_error(meta, "NO_FILE_PATH")
            print("   [ERROR] file_path 없음 → 로그 기록")
            continue

        # 2) crdownload 처리
        if file_path.endswith(".crdownload"):
            normal_path = file_path[:-11]
            if os.path.exists(normal_path):
                print(f"   [FIX] crdownload → {normal_path}")
                meta["file_path"] = normal_path
                file_path = normal_path
                modified_list.append(meta)
            else:
                log_error(meta, "CRDOWNLOAD_NO_REAL_FILE", file_path)
                print("   [SKIP] crdownload인데 실제 파일 없음 → 로그 기록")
                continue

        # 3) 파일 존재 여부 확인
        if not os.path.exists(file_path):
            log_error(meta, "MISSING_FILE", file_path)
            print("   [ERROR] 실제 파일 없음 → 로그 기록")
            continue

        # 4) 확장자 필터링
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ALLOWED_EXTS:
            print(f"   [SKIP] 지원하지 않는 확장자({ext})")
            continue

        # 5) text_path 이미 있으면 스킵
        if text_path and os.path.exists(text_path):
            print("   [SKIP] 이미 전처리된 텍스트 존재")
            continue

        # 6) text_path 자동 생성
        if not text_path:
            base = os.path.splitext(os.path.basename(file_path))[0]
            text_path = os.path.join(FILE_TEXT_DIR, base + ".txt")
            meta["text_path"] = text_path
            modified_list.append(meta)

        print("   [EXTRACT] 텍스트 추출 중…")

        # 7) 안전 추출
        result = safe_extract(file_path)

        if result["status"] == "segfault":
            log_error(meta, "SEGFAULT", f"exitcode={result.get('exitcode')}")
            print("   [ERROR] 세그폴트 → 로그 기록")
            continue

        if result["status"] == "timeout":
            log_error(meta, "TIMEOUT")
            print("   [ERROR] 시간 초과 → 로그 기록")
            continue

        if result["status"] == "error":
            log_error(meta, "EXTRACT_ERROR", result.get("error"))
            print("   [ERROR] 추출 중 파이썬 오류 → 로그 기록")
            continue

        text = result.get("text", "")

        if not text.strip():
            log_error(meta, "EMPTY_TEXT")
            print("   [WARN] 텍스트 비어있음 → 로그 기록")
            continue

        # 8) 텍스트 저장
        with open(text_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)

        print("   [OK] 저장됨 →", text_path)
        processed += 1
        created += 1

    # 수정된 metadata만 따로 저장
    save_updated_meta(modified_list)

    print("\n[DONE] 처리된 파일 수:", processed)
    print("[DONE] 새 텍스트 생성:", created)
    print("[DONE] 메타데이터 변경 항목:", len(modified_list))
    print(f"[DONE] 오류 로그 저장 위치: {ERROR_LOG}")
    print(f"[DONE] 변경된 메타데이터 목록: {UPDATED_META}")


if __name__ == "__main__":
    extract_by_metadata()
