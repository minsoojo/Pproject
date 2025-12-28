#파일(hwp만) txt를 <Test>Main DB에 넣는 코드
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pymysql

# HWP에서 변환된 txt 파일들이 있는 폴더
HWP_TXT_FOLDER = "/home/t25315/data/hwp_files_txt"


def get_connection():
    """MariaDB 연결 함수 (환경에 맞게 수정)"""
    return pymysql.connect(
        host="localhost",
        user="dbid253",        # 실제 계정
        password="dbpass253",  # 실제 비밀번호
        database="db25322",    # TestMain, metadata 있는 DB
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def build_hwp_txt_path(file_path):
    """
    metadata.file_path 예:
        'data/files/[본문] 2025년도 ... 안내.hwp'
    → HWP_TXT_FOLDER + 같은 이름 + .txt 로 변환:

        '/home/t25315/data/hwp_files_txt/[본문] 2025년도 ... 안내.txt'
    """
    basename = os.path.basename(file_path)          # [본문] 2025년도 ... 안내.hwp
    stem, _ = os.path.splitext(basename)            # ([본문] 2025년도 ... 안내, '.hwp')
    txt_name = stem + ".txt"                        # [본문] 2025년도 ... 안내.txt
    return os.path.join(HWP_TXT_FOLDER, txt_name)


def import_hwp_texts_to_testmain(limit=None):
    conn = get_connection()
    inserted = 0
    updated = 0
    skipped_missing = 0
    skipped_error = 0
    skipped_non_hwp = 0

    try:
        # 1) metadata에서 file_path가 .hwp인 행들만 가져오기
        with conn.cursor() as cursor:
            sql = """
            SELECT meta_id, file_path
            FROM metadata
            WHERE file_path IS NOT NULL
              AND LOWER(file_path) LIKE 'data/files/%%.hwp'
            ORDER BY meta_id
            """
            if limit is not None:
                sql += " LIMIT %s"
                cursor.execute(sql, (int(limit),))
            else:
                cursor.execute(sql)

            rows = cursor.fetchall()

        print("[INFO] metadata rows with HWP file_path:", len(rows))

        # 2) 각 HWP 파일에 대응하는 TXT 파일을 찾아 읽어서 TestMain에 저장
        with conn.cursor() as cursor:
            for row in rows:
                meta_id = str(row["meta_id"])
                file_path = row["file_path"]

                if not file_path:
                    continue

                # 혹시 모를 다른 확장자는 스킵 (안전장치)
                if not file_path.lower().endswith(".hwp"):
                    print("[SKIP] .hwp 아님, 건너뜀:",
                          "meta_id=", meta_id, "file_path=", file_path)
                    skipped_non_hwp += 1
                    continue

                txt_path = build_hwp_txt_path(file_path)

                if not os.path.exists(txt_path):
                    print("[WARN] HWP TXT 파일 없음, 건너뜀:",
                          "meta_id=", meta_id, "txt_path=", txt_path)
                    skipped_missing += 1
                    continue

                # 3) TXT 파일 읽기 (utf-8 우선, 안 되면 cp949 시도)
                try:
                    try:
                        with open(txt_path, "r", encoding="utf-8") as f:
                            raw_text = f.read()
                    except UnicodeDecodeError:
                        with open(txt_path, "r", encoding="cp949") as f:
                            raw_text = f.read()
                except Exception as e:
                    print("[ERROR] HWP TXT 파일 읽기 실패:",
                          "meta_id=", meta_id, "path=", txt_path, "err=", repr(e))
                    skipped_error += 1
                    continue

                if not raw_text.strip():
                    print("[WARN] 빈 HWP TXT, 건너뜀:",
                          "meta_id=", meta_id, "path=", txt_path)
                    continue

                # 4) TestMain에 이미 같은 meta_id가 있는지 확인
                cursor.execute(
                    "SELECT id FROM TestMain WHERE meta_id = %s",
                    (meta_id,),
                )
                existing = cursor.fetchone()

                if existing:
                    # UPDATE: raw_data만 갱신, clean_data는 그대로 둠
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
            "[DONE]",
            "inserted=", inserted,
            "updated=", updated,
            "missing_txt=", skipped_missing,
            "file_errors=", skipped_error,
            "skipped_non_hwp=", skipped_non_hwp,
        )

    finally:
        conn.close()


if __name__ == "__main__":
    import_hwp_texts_to_testmain(limit=None)
