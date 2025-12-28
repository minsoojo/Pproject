# 해시 기반 중복 처리 스크립트

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
metadata_updated.jsonl 안에서

- 각 레코드의 text_path 를 따라 들어가 텍스트 내용을 읽고
- 내용이 완전히 같은 텍스트 파일들(= 같은 해시값)을 "중복"으로 간주하여
  * 첫 번째 하나만 남기고
  * 나머지 레코드들은 메타데이터에서 제거
  * 동시에 해당 레코드가 가리키는 file_path (원본 파일)를 삭제
  * (옵션) text_path 도 삭제 가능

⚠️ 실제 파일 삭제가 일어날 수 있으니,
   먼저 DRY_RUN 모드를 켜고 결과를 확인한 뒤 끄는 걸 추천합니다.
"""

import os
import json
import hashlib

# ===================== 사용자 설정 =====================

# 1) 메타데이터 jsonl 파일 경로
METADATA_IN = "/home/t25315/data/metadata_updated.jsonl"
# METADATA_IN = "/home/t25315/data/metadata_dedup_by_text.jsonl"    # v2
# 2) 결과를 쓸 파일 경로
METADATA_OUT = "/home/t25315/data/metadata_dedup_by_text.jsonl"
# METADATA_OUT = "/home/t25315/data/metadata_dedup_by_text_v2.jsonl"    #v2

# 3) 파일 경로 기준이 되는 base 디렉터리
#    - file_path, text_path 가 상대경로일 때 이 디렉터리를 기준으로 실제 경로를 만듦
# BASE_DIR = os.path.dirname(os.path.abspath(METADATA_IN))
BASE_DIR = "/home/t25315/"

# 4) 실제 파일 삭제를 할지 여부
#    - True  : 어떤 것도 삭제하지 않고, "삭제 예정" 이라고만 로그 출력 (연습 모드)
#    - False : 실제로 os.remove() 를 호출해서 파일 삭제
DRY_RUN = False

# 5) 중복 텍스트의 text_path 도 같이 지울지 여부
DELETE_TEXT_FILES = True

# =====================================================


def resolve_path(base_dir: str, p: str) -> str:
    """상대 경로/절대 경로를 받아 실제 절대 경로로 변환."""
    if not p:
        return ""
    if os.path.isabs(p):
        return p
    return os.path.join(base_dir, p)


def load_text_for_hash(text_abs_path: str) -> str:
    """
    텍스트 파일을 읽어서 해시용 문자열로 반환.
    너무 공격적인 전처리는 하지 않고, 최소한의 정규화만 적용.
    """
    with open(text_abs_path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()

    # 해시 계산 전에 아주 가벼운 정규화 정도만 (필요에 따라 조정 가능)
    txt = txt.replace("\r\n", "\n").replace("\r", "\n").strip()

    return txt


def calc_hash(text: str) -> str:
    """텍스트 내용에 대한 SHA-256 해시를 hex 문자열로 반환."""
    h = hashlib.sha256()
    # UTF-8 인코딩 기준
    h.update(text.encode("utf-8"))
    return h.hexdigest()


def main():
    # 이미 결과 파일이 있다면 실수 방지용으로 에러
    if os.path.exists(METADATA_OUT):
        print(f"[ERROR] 출력 파일이 이미 존재합니다: {METADATA_OUT}")
        print("        덮어쓰려면 삭제하거나, METADATA_OUT 이름을 변경하세요.")
        return

    seen_by_hash = {}  # content_hash -> {"text_path": ..., "file_path": ..., "id": ...}

    total = 0
    kept = 0
    dup_meta = 0
    dup_file_deleted = 0
    dup_text_deleted = 0
    text_not_found = 0

    with open(METADATA_IN, "r", encoding="utf-8") as fin, \
         open(METADATA_OUT, "w", encoding="utf-8") as fout:

        for line_no, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            total += 1

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[WARN] JSON 파싱 실패 (line {line_no}): {e} → 원본 그대로 복사")
                fout.write(line + "\n")
                kept += 1
                continue

            # 메타데이터에서 필요한 필드
            text_path = obj.get("text_path")
            file_path = obj.get("file_path")
            doc_id = obj.get("id")

            # text_path 가 없으면 중복 판단 불가 → 그대로 유지
            if not text_path:
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
                continue

            # text_path 를 실제 경로로 변환
            text_abs = resolve_path(BASE_DIR, text_path)

            if not os.path.exists(text_abs):
                print(f"[WARN] text_path 파일 없음 (line {line_no}, id={doc_id}): {text_abs}")
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
                text_not_found += 1
                continue

            try:
                txt = load_text_for_hash(text_abs)
            except Exception as e:
                print(f"[WARN] 텍스트 로드 실패 (line {line_no}, id={doc_id}): {text_abs} ({e})")
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
                continue

            if not txt:
                # 내용이 비어있으면 중복 여부 판단하기 애매하니까 그냥 통과
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
                continue

            content_hash = calc_hash(txt)

            # 아직 이 해시를 본 적 없으면 → 대표로 채택
            if content_hash not in seen_by_hash:
                seen_by_hash[content_hash] = {
                    "text_path": text_path,
                    "file_path": file_path,
                    "id": doc_id,
                }
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
                continue

            # 여기까지 왔으면 같은 내용의 텍스트가 이미 존재 = 중복
            dup_meta += 1
            canonical = seen_by_hash[content_hash]

            print(f"[DUP] 텍스트 내용 중복 발견 (line {line_no}, id={doc_id})")
            print(f"      대표 id={canonical.get('id')} text_path={canonical.get('text_path')}")

            # --- 1) 원본 파일(file_path) 삭제 ---
            if file_path:
                file_abs = resolve_path(BASE_DIR, file_path)

                if os.path.exists(file_abs):
                    if DRY_RUN:
                        print(f"  -> DRY_RUN: 중복 원본 파일 삭제 예정: {file_abs}")
                    else:
                        try:
                            os.remove(file_abs)
                            dup_file_deleted += 1
                            print(f"  -> 중복 원본 파일 삭제 완료: {file_abs}")
                        except Exception as e:
                            print(f"  -> 중복 원본 파일 삭제 실패: {file_abs} ({e})")
                else:
                    print(f"  -> 원본 파일이 존재하지 않아 삭제 생략: {file_abs}")
            else:
                print("  -> file_path 없음 (원본 파일 삭제 스킵)")

            # --- 2) 텍스트 파일(text_path) 삭제 (옵션) ---
            if DELETE_TEXT_FILES and text_path:
                # 대표와 같은 text_path 를 가리키는 경우는 삭제하면 안 됨
                if text_path != canonical.get("text_path"):
                    if os.path.exists(text_abs):
                        if DRY_RUN:
                            print(f"  -> DRY_RUN: 중복 텍스트 파일 삭제 예정: {text_abs}")
                        else:
                            try:
                                os.remove(text_abs)
                                dup_text_deleted += 1
                                print(f"  -> 중복 텍스트 파일 삭제 완료: {text_abs}")
                            except Exception as e:
                                print(f"  -> 중복 텍스트 파일 삭제 실패: {text_abs} ({e})")
                    else:
                        print(f"  -> 텍스트 파일이 존재하지 않아 삭제 생략: {text_abs}")
                else:
                    print("  -> 대표와 같은 text_path 이므로 텍스트 파일 삭제는 하지 않음")

            # 중복 엔트리는 fout 에 쓰지 않는다 (메타데이터에서 제거)

    print("======================================")
    print(f"총 레코드 수              : {total}")
    print(f"유지된 레코드 수          : {kept}")
    print(f"텍스트 중복 메타 제거 수   : {dup_meta}")
    print(f"텍스트 파일 없음 (스킵)   : {text_not_found}")
    print(f"삭제된 원본 파일 수       : {dup_file_deleted} (DRY_RUN={DRY_RUN})")
    print(f"삭제된 텍스트 파일 수     : {dup_text_deleted} (DRY_RUN={DRY_RUN}, DELETE_TEXT_FILES={DELETE_TEXT_FILES})")
    print(f"새 메타데이터 파일        : {os.path.abspath(METADATA_OUT)}")
    print("======================================")


if __name__ == "__main__":
    main()
