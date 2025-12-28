#파일(hwp 제외) txt를 <Test>Main DB에 넣는 코드

import os
import pymysql

# TXT 파일이 실제로 있는 폴더 (파일 텍스트 클리닝 결과)
TXT_FOLDER = "/home/t25315/data/file_text_clean"


# DB 연결 함수 (환경에 맞게 수정)
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="dbid253",        # ← 실제 계정
        password="dbpass253",  # ← 실제 비밀번호
        database="db25322",    # ← TestMain, metadata 있는 DB
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def build_full_text_path_from_file_path(file_path: str) -> str:
    """
    metadata.file_path 예: 'data/files/[본문] 2025년도 ... 안내.pdf'
    → TXT_FOLDER + 같은 이름 + .txt 로 매핑:

    /home/t25315/data/file_text_clean/[본문] 2025년도 ... 안내.txt
    """
    basename = os.path.basename(file_path)           # [본문] 2025년도 ... 안내.pdf
    stem, _ = os.path.splitext(basename)             # ([본문] 2025년도 ... 안내, '.pdf')
    txt_name = stem + ".txt"                         # [본문] 2025년도 ... 안내.txt
    return os.path.join(TXT_FOLDER, txt_name)


def import_file_texts_to_testmain(limit=None):
    conn = get_connection()
    inserted = 0
    updated = 0
    skipped_missing = 0
    skipped_error = 0
    skipped_hwp = 0

    try:
        # 1) metadata에서 file_path 있는 애들만 가져오기
        with conn.cursor() as cursor:
            sql = """
            SELECT meta_id, file_path
            FROM metadata
            WHERE file_path IS NOT NULL
            ORDER BY meta_id
            """
            if limit is not None:
                sql += f" LIMIT {int(limit)}"

            cursor.execute(sql)
            rows = cursor.fetchall()

        print(f"[INFO] metadata rows with file_path: {len(rows)}")

        # 2) 각 file_path → TXT_FOLDER의 txt 파일로 매핑해서 읽고 TestMain에 넣기
        with conn.cursor() as cursor:
            for row in rows:
                meta_id = str(row["meta_id"])
                file_path = row["file_path"]

                if not file_path:
                    continue

                # hwp는 이 폴더에 txt가 없다고 하셨으니 스킵
                if file_path.lower().endswith(".hwp"):
                    print(f"[SKIP] HWP 파일 (별도 처리 예정): meta_id={meta_id}, file_path={file_path}")
                    skipped_hwp += 1
                    continue

                full_txt_path = build_full_text_path_from_file_path(file_path)

                if not os.path.exists(full_txt_path):
                    print(f"[WARN] TXT 파일 없음, 건너뜀: meta_id={meta_id}, txt_path={full_txt_path}")
                    skipped_missing += 1
                    continue

                # 3) 텍스트 파일 읽기 (인코딩은 utf-8 우선, 안 되면 cp949 시도)
                try:
                    try:
                        with open(full_txt_path, "r", encoding="utf-8") as f:
                            raw_text = f.read()
                    except UnicodeDecodeError:
                        with open(full_txt_path, "r", encoding="cp949") as f:
                            raw_text = f.read()
                except Exception as e:
                    print(f"[ERROR] TXT 파일 읽기 실패: meta_id={meta_id}, path={full_txt_path}, err={e}")
                    skipped_error += 1
                    continue

                if not raw_text.strip():
                    print(f"[WARN] 빈 TXT, 건너뜀: meta_id={meta_id}, path={full_txt_path}")
                    continue

                # 4) 이미 TestMain에 같은 meta_id가 있는지 확인
                cursor.execute(
                    "SELECT id FROM TestMain WHERE meta_id = %s",
                    (meta_id,),
                )
                existing = cursor.fetchone()

                if existing:
                    # UPDATE: raw_data만 갱신, clean_data는 손대지 않음
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

        print(
            f"[DONE] inserted={inserted}, updated={updated}, "
            f"missing_txt={skipped_missing}, file_errors={skipped_error}, skipped_hwp={skipped_hwp}"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    # 전체 돌리기 전에 limit=10 같은 걸로 먼저 테스트 추천
    import_file_texts_to_testmain(limit=None)
