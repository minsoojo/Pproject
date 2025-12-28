#메타데이터.jsonl을 metadata DB에 넣는 코드

import json
import pymysql
from pathlib import Path

# 1) DB 연결 함수
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="dbid253",           # 바꿔 쓰기
        password="dbpass253",   # 바꿔 쓰기
        database="db25322",       # 메타데이터 DB 이름
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


# 2) 한 줄(JSON) → INSERT용 튜플로 변환
def json_to_row(obj: dict):
    # meta_id: json의 id를 문자열로
    meta_id = str(obj.get("id"))

    meta_type = obj.get("type")
    url = obj.get("url")
    title = obj.get("title")

    # timestamp: float → int로 변환 (초 단위로 저장)
    ts = obj.get("timestamp")
    if ts is not None:
        try:
            ts_int = int(ts)
        except (TypeError, ValueError):
            ts_int = None
    else:
        ts_int = None

    # 기본값 None
    ref_page_url = obj.get("ref_page_url")
    ref_page_id = obj.get("ref_page_id")
    if ref_page_id is not None:
        ref_page_id = str(ref_page_id)

    text_col = None         # DB의 text 컬럼 (지금은 안 씀)
    text_path = None
    file_path = None

    # type에 따라 분기
    if meta_type and meta_type.startswith("html"):
        # html 메타: text 필드에 텍스트 파일 경로가 들어있음
        text_path = obj.get("text")
    else:
        # file 메타: file_path가 있음
        file_path = obj.get("file_path")

    return (
        meta_id,
        meta_type,
        url,
        text_col,
        ref_page_url,
        ref_page_id,
        text_path,
        file_path,
        title,
        ts_int,
    )


# 3) JSONL 파일을 읽어서 DB에 INSERT (ON DUPLICATE KEY UPDATE)
def import_metadata(jsonl_path: str, table_name: str = "metadata"):
    path = Path(jsonl_path)
    if not path.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {path}")
        return

    conn = get_connection()
    inserted = 0
    updated = 0

    try:
        with conn.cursor() as cursor, path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"[WARN] JSON 파싱 실패, 건너뜀: {e} :: {line[:80]}")
                    continue

                row = json_to_row(obj)

                sql = f"""
                INSERT INTO {table_name} (
                    meta_id, type, url,
                    text, ref_page_url, ref_page_id,
                    text_path, file_path,
                    title, timestamp
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    type = VALUES(type),
                    url = VALUES(url),
                    text = VALUES(text),
                    ref_page_url = VALUES(ref_page_url),
                    ref_page_id = VALUES(ref_page_id),
                    text_path = VALUES(text_path),
                    file_path = VALUES(file_path),
                    title = VALUES(title),
                    timestamp = VALUES(timestamp)
                """

                cursor.execute(sql, row)

                if cursor.rowcount == 1:
                    inserted += 1      # 새로 추가
                elif cursor.rowcount == 2:
                    updated += 1       # 기존 행 업데이트

        conn.commit()
        print(f"[DONE] inserted={inserted}, updated={updated}")

    finally:
        conn.close()


if __name__ == "__main__":
    # 여기에 실제 jsonl 파일 경로 넣으면 됨
    import_metadata("/home/t25315/data/metadata.jsonl", table_name="metadata")
