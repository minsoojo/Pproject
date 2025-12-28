# hwp 임시 텍스트 추출 스크립트

# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# import json
# import os

# INPUT_FILE = "/home/t25315/data/metadata_updated_sy.jsonl"          # 입력 메타데이터 파일
# OUTPUT_FILE = "/home/t25315/data/metadata_hwp_only.jsonl" # 결과 저장 파일
# OUTPUT_LIST = "hwp_paths.txt"           # HWP 실제 파일 경로만 저장


# def is_hwp_type(t: str) -> bool:
#     """type 필드가 HWP/HWPX인지 확인"""
#     t = (t or "").lower()
#     return "hwp" in t  # hwp / hwpx 모두 잡힘


# def extract_hwp():
#     if not os.path.exists(INPUT_FILE):
#         print(f"[ERROR] 입력 파일 없음: {INPUT_FILE}")
#         return
    
#     hwp_entries = []
#     hwp_paths = []

#     with open(INPUT_FILE, "r", encoding="utf-8") as f:
#         for line in f:
#             try:
#                 obj = json.loads(line)
#             except json.JSONDecodeError:
#                 continue

#             file_type = obj.get("type", "")
#             if is_hwp_type(file_type):
#                 hwp_entries.append(obj)

#                 # 파일 경로만 따로 저장
#                 fpath = obj.get("file_path")
#                 if fpath:
#                     hwp_paths.append(fpath)

#     # HWP 전체 메타데이터 저장
#     with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#         for item in hwp_entries:
#             f.write(json.dumps(item, ensure_ascii=False) + "\n")

#     # HWP 파일 경로 저장
#     with open(OUTPUT_LIST, "w", encoding="utf-8") as f:
#         for p in hwp_paths:
#             f.write(p + "\n")

#     print(f"[DONE] HWP 메타데이터 개수: {len(hwp_entries)}")
#     print(f"[DONE] 저장 파일:")
#     print(f" - {OUTPUT_FILE}")
#     print(f" - {OUTPUT_LIST}")


# if __name__ == "__main__":
#     extract_hwp()
import json
import os

INPUT_FILE = "/home/t25315/data/metadata_updated_sy.jsonl"          # 입력 메타데이터 파일
OUTPUT_FILE = "/home/t25315/data/metadata_hwp_only.jsonl" # 결과 저장 파일

def extract_hwp():
    out = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except:
                continue

            file_path = obj.get("file_path")
            if not file_path:
                continue

            ext = os.path.splitext(file_path)[1].lower()

            if ext in [".hwp", ".hwpx"]:
                out.append(obj)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for obj in out:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"[DONE] file_path 기반 HWP 추출: {len(out)}개")

if __name__ == "__main__":
    extract_hwp()
