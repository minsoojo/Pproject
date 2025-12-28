# 클리닝용 서버 코드(베타)
# 현재 기능 - 
# 1. file_path를 이용해서 있으면 file, 없으면 html 구분

from fastapi import FastAPI
import pymysql
from typing import Optional

app = FastAPI()

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="dbid253",
        password="dbpass253",
        database="db25322",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_rows_with_meta(limit: Optional[int] = None):
    """
    TestMain + Metadata JOIN 해서
    id, meta_id, file_path, source_type 까지 붙여서 반환해주는 공통 함수
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT m.id, md.meta_id, md.file_path
            FROM TestMain m
            JOIN metadata md ON m.meta_id = md.meta_id
            """
            if limit is not None:
                sql += " LIMIT %s"
                cursor.execute(sql, (limit,))
            else:
                cursor.execute(sql)

            rows = cursor.fetchall()

            for r in rows:
                file_path = r.get("file_path")
                if file_path:
                    r["source_type"] = "file"
                else:
                    r["source_type"] = "html"

        return rows
    finally:
        conn.close()

@app.get("/raw_with_meta")
def raw_with_meta():
    rows = fetch_rows_with_meta()
    return rows


@app.get("/metrics")
def metrics():
    print("서버가 매트릭스 요청을 했다...")
    return "ok"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("SubServer:app", host="0.0.0.0", port=8000, reload=True)
