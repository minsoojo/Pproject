import pymysql
from pathlib import Path

conn = pymysql.connect(
    host="localhost",
    user="dbid253",
    password="dbpass253",
    database="db25322",
    charset="utf8mb4"
)

files = [
    ("manual_yo_2020_curriculum","data/yo_txt/yo_txt_encoding/2020_요람(교육과정)_raw_utf8.txt"),
    ("manual_yo_2020_general","data/yo_txt/yo_txt_encoding/2020_요람(총람)_raw_utf8.txt"),
    ("manual_yo_2021_curriculum","data/yo_txt/yo_txt_encoding/2021_요람(교육과정)_raw_utf8.txt"),
    ("manual_yo_2021_general","data/yo_txt/yo_txt_encoding/2021_요람(총람)_raw_utf8.txt"),
    ("manual_yo_2022_general","data/yo_txt/yo_txt_encoding/2022_요람(총람)_raw_utf8.txt"),
    ("manual_yo_2022_handbook","data/yo_txt/yo_txt_encoding/2022_학사요람_raw_utf8.txt"),
    ("manual_yo_2023_curriculum_cs","data/yo_txt/yo_txt_encoding/2023_요람(교육과정)시반전자반영_raw_utf8.txt"),
    ("manual_yo_2023_general","data/yo_txt/yo_txt_encoding/2023_요람(총람)_raw_utf8.txt"),
    ("manual_yo_2024_major","data/yo_txt/yo_txt_encoding/2024_요람(전공)전의예반영_raw_utf8.txt"),
    ("manual_yo_2024_general","data/yo_txt/yo_txt_encoding/2024_요람(총람및교양)_raw_utf8.txt"),
    ("manual_yo_2025_major","data/yo_txt/yo_txt_encoding/2025_요람(전공)전의예반영_raw_utf8.txt"),
    ("manual_yo_2025_general","data/yo_txt/yo_txt_encoding/2025_요람(총람및교양)_raw_utf8.txt"),
]

with conn.cursor() as cur:
    for meta_id, path in files:
        text = Path(path).read_text(encoding="utf-8")
        cur.execute(
            "INSERT INTO TestMain (meta_id, raw_data) VALUES (%s, %s)",
            (meta_id, text)
        )
conn.commit()
conn.close()

# UPDATE metadata SET text_path = 'data/yo_txt/yo_txt_encoding/2024_요람(전공)전의예반영_raw_utf8.txt',file_path = 'data/yo_txt/yo_txt_encoding/2024_요람(전공)전의예반영_raw_utf8.txt' WHERE meta_id = 'manual_yo_2024_major';
# UPDATE metadata SET text_path = 'data/yo_txt/yo_txt_encoding/2025_요람(전공)전의예반영_raw_utf8.txt',file_path = 'data/yo_txt/yo_txt_encoding/2024_요람(전공)전의예반영_raw_utf8.txt' WHERE meta_id = 'manual_yo_2025_major';

# INSERT INTO metadata (meta_id, type, url, ref_page_url, ref_page_id, text_path, file_path, title, timestamp) VALUES
# ('manual_yo_2020_curriculum','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2020_요람(교육과정)_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2020_요람(교육과정)_raw_utf8.txt',
#  '2020 요람 교육과정',1596240000),

# ('manual_yo_2020_general','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2020_요람(총람)_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2020_요람(총람)_raw_utf8.txt',
#  '2020 요람 총람',1596240000),

# ('manual_yo_2021_curriculum','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2021_요람(교육과정)_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2021_요람(교육과정)_raw_utf8.txt',
#  '2021 요람 교육과정',1638316800),

# ('manual_yo_2021_general','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2021_요람(총람)_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2021_요람(총람)_raw_utf8.txt',
#  '2021 요람 총람',1638316800),

# ('manual_yo_2022_general','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2022_요람(총람)_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2022_요람(총람)_raw_utf8.txt',
#  '2022 요람 총람',1654041600),

# ('manual_yo_2022_handbook','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2022_학사요람_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2022_학사요람_raw_utf8.txt',
#  '2022 학사 요람',1654041600),

# ('manual_yo_2023_curriculum_cs','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2023_요람(교육과정)시반전자반영_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2023_요람(교육과정)시반전자반영_raw_utf8.txt',
#  '2023 요람 교육과정 (시스템·전자 반영)',1688169600),

# ('manual_yo_2023_general','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2023_요람(총람)_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2023_요람(총람)_raw_utf8.txt',
#  '2023 요람 총람',1688169600),

# ('manual_yo_2024_major','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2024_요람(전공)전예비영_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2024_요람(전공)전예비영_raw_utf8.txt',
#  '2024 요람 전공 (전자·예비)',1717200000),

# ('manual_yo_2024_general','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2024_요람(총람및교양)_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2024_요람(총람및교양)_raw_utf8.txt',
#  '2024 요람 총람 및 교양',1717200000),

# ('manual_yo_2025_major','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2025_요람(전공)전예비영_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2025_요람(전공)전예비영_raw_utf8.txt',
#  '2025 요람 전공 (전자·예비)',1748736000),

# ('manual_yo_2025_general','file',NULL,NULL,NULL,
#  'data/yo_txt/yo_txt_encoding/2025_요람(총람및교양)_raw_utf8.txt',
#  'data/yo_txt/yo_txt_encoding/2025_요람(총람및교양)_raw_utf8.txt',
#  '2025 요람 총람 및 교양',1748736000);
