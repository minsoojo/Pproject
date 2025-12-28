import os
from connection.db.main_dao import get_clean_data_by_meta_id


def export_clean_data_to_txt(
    meta_ids: list[str],
    output_dir: str = "./exported_clean_texts"
):
    """
    meta_id 목록에 해당하는 clean_data를
    meta_id.txt 파일로 저장
    """
    os.makedirs(output_dir, exist_ok=True)

    for meta_id in meta_ids:
        print(f"[START] {meta_id}")

        clean_data = get_clean_data_by_meta_id(meta_id)

        if not clean_data or not clean_data.strip():
            print(f"[SKIP] {meta_id} clean_data 없음")
            continue

        filename = f"{meta_id}.txt"
        path = os.path.join(output_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            f.write(clean_data)

        print(f"[OK] 저장 완료 → {path}")
