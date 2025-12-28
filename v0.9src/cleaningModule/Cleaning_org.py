# import os
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# cleaning.py
from typing import Optional

from .DBfetcher import fetch_rows_with_meta #file/html 나눠주는 친구
from .FormClassifier import is_form #양식인지 구분해주는 친구
from .htmlNotFormCleaner import clean_html_NotForm #비양식 클리닝
from .FormCleaner import clean_form_file #양식 클리닝
from connection.pipeline.run_cleaning import process_one_row
from connection.db.main_dao import fetch_rows_to_clean, update_clean_data   # ← 여기서만 DB에 저장



# 5) 전체 파이프라인
def run_cleaning_pipeline(limit: Optional[int] = 1000):
    rows = fetch_rows_with_meta(limit=limit)

    for row in rows:
        row_id = row["id"]
        stype = row.get("source_type")

        if stype != "file":
            cleaned = process_one_row(row)
            cleaning_method = "html_gpt"
        else:
            if is_form(row):
                cleaned = clean_form_file(row)
                cleaning_method = "file_form_rule"
            else:
                cleaned = process_one_row(row)
                cleaning_method = "file_gpt"

        if isinstance(cleaned, str) and cleaned.strip():
            update_clean_data(row_id, cleaned)  # ← 여기서 TestMain.id 기준으로 저장
            print(f"[OK] id={row_id} ({cleaning_method}) 저장 완료")
        else:
            print(f"[WARN] id={row_id} 클린 결과가 비었거나 문자열이 아닙니다: {type(cleaned)}")

# # 6) 디버그용 파이프라인
# def run_cleaning_pipeline_debug(limit: Optional[int] = 50):
#     print(f"[DEBUG] run_cleaning_pipeline_debug() 시작, limit={limit}")
#     rows = fetch_rows_with_meta(limit=limit)

#     for idx, row in enumerate(rows, start=1):
#         stype = row.get("source_type")
#         doc_id = row.get("id")
#         title = row.get("title")
#         file_path = row.get("file_path")

#         print("\n" + "=" * 60)
#         print(f"[{idx}] id={doc_id} | source_type={stype}")
#         print(f"    title     = {title}")
#         print(f"    file_path = {file_path}")

#         # 실제 파이프라인 흐름과 동일하게 분기하면서
#         # 중간중간 로그만 더 찍어줌
#         if stype != "file":
#             print("    → HTML 문서로 판단: clean_html_NotForm() 호출")
#             cleaned = clean_html_NotForm(row)
#         else:
#             print("    → 파일 문서로 판단")
#             form_flag = is_form(row)
#             print(f"    is_form() 결과: {form_flag}")

#             if form_flag:
#                 print("    → 양식/신청서로 분류: clean_form_file() 호출")
#                 cleaned = clean_form_file(row)
#             else:
#                 print("    → 일반 파일로 분류: clean_html_NotForm() 호출")
#                 cleaned = clean_html_NotForm(row)

#         # cleaned 내용 간단히 확인
#         print(f"    클리닝 결과 타입: {type(cleaned)}")

#         if isinstance(cleaned, str):
#             snippet = cleaned[:120].replace("\n", " ")
#             if len(cleaned) > 120:
#                 snippet += " ..."
#             print(f"    클리닝 결과 앞 120자: {repr(snippet)}")
#         else:
#             print(f"    클리닝 결과(비문자열): {repr(cleaned)}")

#     print("\n[DEBUG] run_cleaning_pipeline_debug() 종료")

# def run_cleaning_pipeline_debug_files(
#     file_limit: int = 50,
#     fetch_limit: int = 5000,
# ):
#     """
#     - DB에서 최대 fetch_limit개를 가져온 뒤
#     - 그 중에서 source_type == 'file' 인 row만 골라
#       최대 file_limit개만 디버깅하는 함수
#     """
#     print(f"[DEBUG] run_cleaning_pipeline_debug_files() 시작")
#     print(f"        DB에서 우선 {fetch_limit}개 fetch")
#     print(f"        그 중 파일 문서 최대 {file_limit}개만 디버깅\n")

#     rows = fetch_rows_with_meta(limit=fetch_limit)

#     file_count = 0
#     total_count = 0

#     for row in rows:
#         total_count += 1
#         stype = row.get("source_type")

#         # 파일만 보고 싶으니까, 파일 아니면 스킵
#         if stype != "file":
#             continue

#         file_count += 1

#         doc_id = row.get("id")
#         title = row.get("title")
#         file_path = row.get("file_path")

#         print("\n" + "=" * 60)
#         print(f"[{file_count}] (전체 {total_count}번째 row)")
#         print(f"    id        = {doc_id}")
#         print(f"    source_type = {stype}")
#         print(f"    title     = {title}")
#         print(f"    file_path = {file_path}")
#         print("    → 파일 문서로 판단")

#         # 양식 여부
#         form_flag = is_form(row)
#         print(f"    is_form() 결과: {form_flag}")

#         if form_flag:
#             print("    → 양식/신청서로 분류: clean_form_file() 호출")
#             cleaned = clean_form_file(row)
#         else:
#             print("    → 일반 파일로 분류: clean_html_NotForm() 호출")
#             cleaned = clean_html_NotForm(row)

#         # 결과 타입/내용 일부 확인
#         print(f"    클리닝 결과 타입: {type(cleaned)}")

#         if isinstance(cleaned, str):
#             snippet = cleaned[:120].replace("\n", " ")
#             if len(cleaned) > 120:
#                 snippet += " ..."
#             print(f"    클리닝 결과 앞 120자: {repr(snippet)}")
#         else:
#             print(f"    클리닝 결과(비문자열): {repr(cleaned)}")

#         # 원하는 파일 개수만큼 봤으면 종료
#         if file_count >= file_limit:
#             break

#     print(f"\n[DEBUG] run_cleaning_pipeline_debug_files() 종료")
#     print(f"    전체 조회 row 수: {total_count}")
#     print(f"    그 중 파일 문서 수: {file_count}")


if __name__ == "__main__":
    # 원래 파이프라인 대신 디버그 버전부터 돌려보기
    # 실제로는 숫자 조금만 (예: 20~50개) 돌려서 로그 확인 추천
    # run_cleaning_pipeline_debug(limit=10000)
    # run_cleaning_pipeline(file_limit=100, fetch_limit=10000)
    run_cleaning_pipeline(limit=100000)


