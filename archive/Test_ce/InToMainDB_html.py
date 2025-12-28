#html txt를 <Test>Main DB에 넣는 코드

import os
import pymysql
from typing import Optional

# txt 파일이 실제로 있는 폴더
TXT_FOLDER = "/home/t25315/data/text"


# DB 연결 함수 (환경에 맞게 수정)
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="dbid253",        # 네 DB 계정
        password="dbpass253",  # 네 DB 비밀번호
        database="db25322",    # TestMain, metadata 있는 DB
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def build_full_text_path(text_path: str) -> str:
    """
    metadata.text_path 예: 'data/text/01078.txt'
    → TXT_FOLDER + 파일명으로 실제 경로 만들기
      /home/t25315/data/text/01078.txt
    """
    filename = os.path.basename(text_path)  # '01078.txt'
    return os.path.join(TXT_FOLDER, filename)

def import_text_files_to_testmain(limit: Optional[int] = None):
    conn = get_connection()
    inserted = 0
    updated = 0
    skipped_missing = 0
    skipped_error = 0

    try:
        with conn.cursor() as cursor:
            # 1) metadata에서 text_path 있는 애들만 가져오기
            sql = """
            SELECT meta_id, text_path
            FROM metadata
            WHERE text_path IS NOT NULL
            ORDER BY meta_id
            """
            if limit is not None:
                sql += f" LIMIT {int(limit)}"

            cursor.execute(sql)
            rows = cursor.fetchall()

        print(f"[INFO] metadata rows with text_path: {len(rows)}")

        with conn.cursor() as cursor:
            for row in rows:
                meta_id = str(row["meta_id"])
                text_path = row["text_path"]

                if not text_path:
                    continue

                full_path = build_full_text_path(text_path)

                if not os.path.exists(full_path):
                    print(f"[WARN] 파일 없음, 건너뜀: meta_id={meta_id}, path={full_path}")
                    skipped_missing += 1
                    continue

                # 2) 파일 읽기 (인코딩 깨지면 cp949도 시도)
                try:
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            raw_text = f.read()
                    except UnicodeDecodeError:
                        with open(full_path, "r", encoding="cp949") as f:
                            raw_text = f.read()
                except Exception as e:
                    print(f"[ERROR] 파일 읽기 실패: meta_id={meta_id}, path={full_path}, err={e}")
                    skipped_error += 1
                    continue

                if not raw_text.strip():
                    print(f"[WARN] 빈 텍스트, 건너뜀: meta_id={meta_id}, path={full_path}")
                    continue

                # 3) 이미 TestMain에 같은 meta_id가 있는지 확인
                cursor.execute(
                    "SELECT id FROM TestMain WHERE meta_id = %s",
                    (meta_id,),
                )
                existing = cursor.fetchone()

                if existing:
                    # UPDATE: raw_data만 갱신, clean_data는 그대로 두거나 NULL 유지
                    sql_update = """
                    UPDATE TestMain
                    SET raw_data = %s
                    WHERE id = %s
                    """
                    cursor.execute(sql_update, (raw_text, existing["id"]))
                    updated += 1
                else:
                    # INSERT: clean_data는 일단 NULL
                    sql_insert = """
                    INSERT INTO TestMain (meta_id, raw_data, clean_data)
                    VALUES (%s, %s, %s)
                    """
                    cursor.execute(sql_insert, (meta_id, raw_text, None))
                    inserted += 1

            conn.commit()

        print(f"[DONE] inserted={inserted}, updated={updated}, "
              f"missing_files={skipped_missing}, file_errors={skipped_error}")

    finally:
        conn.close()


if __name__ == "__main__":
    # limit=None 이면 전체, 숫자 넣으면 일부만 테스트
    import_text_files_to_testmain(limit=None)
