# from db.main_dao import fetch_rows_to_clean, update_clean_data
# from cleaner.chunker import normalize_newlines, split_into_paragraphs, chunk_by_tokens
# from cleaner.gpt_cleaner import clean_with_gpt
# from utils.logger import log, log_error_json
from connection.db.main_dao import fetch_rows_to_clean, update_clean_data
from connection.cleaner.chunker import normalize_newlines, split_into_paragraphs, chunk_by_tokens
from connection.cleaner.gpt_cleaner import clean_with_gpt
from connection.utils.logger import log, log_error_json, LOG_DIR



def process_one_row(row):
    row_id = row["id"]
    raw = row["raw_data"]

    try:
        log.info(f"Processing row {row_id}")

        # 1) normalize
        normalized = normalize_newlines(raw)

        # 2) paragraphs
        paragraphs = split_into_paragraphs(normalized)

        # 3) chunking
        chunks = chunk_by_tokens(paragraphs, max_tokens=800)

        cleaned_chunks = []
        for i, chunk in enumerate(chunks):
            log.info(f" → Cleaning chunk {i+1}/{len(chunks)} for row {row_id}")
            cleaned = clean_with_gpt(chunk)
            cleaned_chunks.append(cleaned)

        final_clean = "\n\n".join(cleaned_chunks)

        # update_clean_data(row_id, final_clean)

        log.info(f"[OK] row {row_id} cleaned successfully")

        # 완료 ID도 파일로 적재
        with open(LOG_DIR / "cleaned_ids.txt", "a") as f:
            f.write(str(row_id) + "\n")

    except Exception as e:
        err = str(e)
        log.error(f"[ERROR] row {row_id}: {err}")
        log_error_json(row_id, err)  # ← DB 저장 대신 파일 저장으로 변경
        
    return final_clean
# def main():
#     while True:
#         rows = fetch_rows_to_clean(limit=20)

#         if not rows:
#             print("✨ 모든 문서 클리닝 완료")
#             break

#         for row in rows:
#             print(f"\n📌 Processing row {row['id']}")
#             process_one_row(row)


# if __name__ == "__main__":
#     main()
