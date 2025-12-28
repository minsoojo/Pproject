from connection.pipeline.gpt_only import gpt_clean_text_only
from connection.db.main_dao import get_row_by_meta_id, update_clean_data

TARGET_IDS = [
    "manual_yo_2020_curriculum",   
    "manual_yo_2020_general",
    "manual_yo_2021_curriculum",
    "manual_yo_2021_general",
    "manual_yo_2022_general",
    "manual_yo_2022_handbook",
    "manual_yo_2023_curriculum_cs",
    "manual_yo_2023_general",
    "manual_yo_2024_major",
    "manual_yo_2024_general", # "," 오타 있었음 아마 GPT 클리닝 중 id 안맞아서 오류날꺼임 나중에 얘만 따로 돌릴것
    "manual_yo_2025_major",
    "manual_yo_2025_general"
] 


for row_id in TARGET_IDS:
    print(f"[START] id={row_id}")

    row = get_row_by_meta_id(row_id)
    if not row or not row.get("raw_data"):
        print(f"[SKIP] id={row_id} raw_data 없음")
        continue

    raw = row["raw_data"]
    db_id = row["id"]

    cleaned = gpt_clean_text_only(raw)

    update_clean_data(db_id, cleaned)
    print(f"[OK] id={row_id} GPT-clean 완료")
