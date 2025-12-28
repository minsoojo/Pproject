    # db/main_dao.py
from .connection import get_connection

from .connection import get_connection

def fetch_rows_to_clean(limit=50):
    """
    TestMain 테이블에서
    - clean_data가 NULL이고
    - raw_data는 존재하는 행만 가져옴
    (클리닝 대상만 선택)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, meta_id, raw_data 
                FROM TestMain
                WHERE clean_data IS NULL 
                  AND raw_data IS NOT NULL
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def update_clean_data(row_id: int, cleaned_text: str):
    """
    TestMain.id = row_id 인 행의 clean_data 업데이트
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE TestMain
                SET clean_data = %s
                WHERE id = %s
            """, (cleaned_text, row_id))
        conn.commit()
    finally:
        conn.close()

def get_row_by_meta_id(meta_id: str):
    """
    meta_id 기준으로 TestMain row 조회
    (manual_yo_* 같은 문서 재처리용)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    id,
                    meta_id,
                    raw_data,
                    clean_data
                FROM TestMain
                WHERE meta_id = %s
            """
            cursor.execute(sql, (meta_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def get_clean_data_by_meta_id(meta_id: str):
    """
    meta_id 기준으로 clean_data 조회
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT clean_data
                FROM TestMain
                WHERE meta_id = %s
                  AND clean_data IS NOT NULL
            """
            cursor.execute(sql, (meta_id,))
            row = cursor.fetchone()
            return row["clean_data"] if row else None
    finally:
        conn.close()
# 필요하면 나중에 다시 살려서 사용
# def log_error(row_id: int, error_msg: str):
#     conn = get_connection()
#     try:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 INSERT INTO cleaning_errors (row_id, error_message)
#                 VALUES (%s, %s)
#             """, (row_id, error_msg[:2000]))
#         conn.commit()
#     finally:
#         conn.close()
