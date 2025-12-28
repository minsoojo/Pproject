from connection.utils.export_clean_data import export_clean_data_to_txt

META_IDS = [
    "manual_yo_2020_curriculum",
    "manual_yo_2020_general",
    "manual_yo_2021_curriculum",
    "manual_yo_2021_general",
    "manual_yo_2022_general",
    "manual_yo_2022_handbook",
    "manual_yo_2023_curriculum_cs",
    "manual_yo_2023_general",
    "manual_yo_2024_major",
    "manual_yo_2024_general",   # ← 쉼표 제거함
    "manual_yo_2025_major",
    "manual_yo_2025_general",
]
#     "manual_yo_2020_curriculum",
#     "manual_yo_2020_general",
#     "manual_yo_2021_curriculum",
#     "manual_yo_2021_general",
#     "manual_yo_2022_general",
#     "manual_yo_2022_handbook",
#     "manual_yo_2023_curriculum_cs",
#     "manual_yo_2023_general",
#     "manual_yo_2024_major",
#     "manual_yo_2024_general",   # ← 쉼표 제거함
#     "manual_yo_2025_major",
#     "manual_yo_2025_general",
# ]

export_clean_data_to_txt(
    meta_ids=META_IDS,
    output_dir="/home/t25315/data/clean_texts"
)