# connection/pipeline/run_cleaning_parallel.py

from concurrent.futures import ThreadPoolExecutor, as_completed

from connection.db.main_dao import fetch_rows_to_clean
from connection.pipeline.run_cleaning import process_one_row
from connection.utils.logger import log, log_error_json


BATCH_SIZE = 50      # 한 번에 DB에서 가져올 row 개수
MAX_WORKERS = 8      # 우선 6~8 정도 권장


def run_parallel_cleaning(batch_size: int = BATCH_SIZE,
                          max_workers: int = MAX_WORKERS):
    """
    clean_data가 비어 있는 row들을 batch 단위로 가져와서
    각 batch 안에서 process_one_row를 병렬로 실행.
    """
    total_processed = 0

    while True:
        # 1) 아직 클리닝 안 된 row를 조금씩 가져오기
        rows = fetch_rows_to_clean(limit=batch_size)

        if not rows:
            print("✨ 더 이상 클리닝할 문서가 없습니다. 작업 종료!")
            break

        print(f"\n📦 새 배치: {len(rows)}개 row 가져옴 (현재까지 처리: {total_processed}개)")
        log.info(f"[parallel] fetched {len(rows)} rows from DB")

        # 2) 병렬 처리
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {
                executor.submit(process_one_row, row): row["id"]
                for row in rows
            }

            for future in as_completed(future_to_id):
                row_id = future_to_id[future]
                try:
                    # process_one_row 내부에서 예외 나면 여기서 터짐
                    future.result()
                    total_processed += 1

                    if total_processed % 50 == 0:
                        msg = f"[parallel] 현재까지 {total_processed}개 처리 완료"
                        print("✅", msg)
                        log.info(msg)

                except Exception as e:
                    err_msg = f"[parallel worker error] row_id={row_id}, err={e}"
                    print("❌", err_msg)
                    log_error_json(row_id, err_msg)

    print(f"\n🎉 전체 병렬 클리닝 완료! 총 {total_processed}개 문서 처리")


if __name__ == "__main__":
    # 처음엔 조금 보수적으로 6~8개 사이에서 시작해보고
    # 429 (Too Many Requests) 거의 안 뜨면 올려가도 됨.
    run_parallel_cleaning(batch_size=BATCH_SIZE, max_workers=MAX_WORKERS)
