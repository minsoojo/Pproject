# db_fetcher.py
# DB에서 id, meta_id, file_path, raw_data 받아오게 해주는 함수
import pymysql
from typing import Optional, List, Dict

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="dbid253",
        password="dbpass253",
        database="db25322",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_rows_with_meta(limit: Optional[int] = None) -> List[Dict]:
    """
    TestMain + Metadata JOIN 해서
    id, meta_id, file_path, source_type 까지 붙여서 반환해주는 공통 함수
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT m.id, md.meta_id, md.file_path, m.raw_data
            FROM TestMain m
            JOIN metadata md ON m.meta_id = md.meta_id
            WHERE m.clean_data IS NULL
            """
            if limit is not None:
                sql += " LIMIT %s"
                cursor.execute(sql, (limit,))
            else:
                cursor.execute(sql)

            rows = cursor.fetchall()

            # file_path 기준으로 source_type 붙이기
            for r in rows:
                file_path = r.get("file_path")
                if file_path:
                    r["source_type"] = "file"
                else:
                    r["source_type"] = "html"

        return rows
    finally:
        conn.close()
