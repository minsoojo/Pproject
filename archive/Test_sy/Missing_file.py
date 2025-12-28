import json

ERROR_LOG = "/home/t25315/data/error_files.txt"          # 이 텍스트 파일 경로
METADATA_IN = "/home/t25315/data/metadata.jsonl"         # 기존 메타데이터
METADATA_OUT = "/home/t25315/data/metadata_missingfile.jsonl"  # 새로 만들 파일


def collect_missing_ids(error_log_path: str):
    """
    error_files.txt 에서 상태가 MISSING_FILE 인 file_id 들만 모아서 set 으로 반환
    """
    missing_ids = set()

    with open(error_log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 라인 형식:
            # [timestamp] file-88-19 | url | MISSING_FILE | path
            parts = line.split("|")
            if len(parts) < 3:
                continue

            status = parts[2].strip()
            if status != "MISSING_FILE":
                continue

            # 왼쪽 부분에서 file_id 추출
            # "[2025-11-29 16:42:33.626857] file-88-19 "
            left = parts[0]
            try:
                after_bracket = left.split("]", 1)[1].strip()  # "file-88-19"
                file_id = after_bracket.split()[0]             # "file-88-19"
                missing_ids.add(file_id)
            except Exception:
                # 예상과 다르게 포맷된 라인은 그냥 무시
                continue

    return missing_ids


def filter_metadata_by_ids(metadata_in: str, metadata_out: str, target_ids: set):
    """
    metadata.jsonl 에서 id 가 target_ids 에 포함된 라인만 골라 metadata_out 에 저장
    """
    count_in = 0
    count_out = 0

    with open(metadata_in, "r", encoding="utf-8") as fin, \
         open(metadata_out, "w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            count_in += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            file_id = obj.get("id")
            if file_id in target_ids:
                fout.write(line + "\n")
                count_out += 1

    print(f"[INFO] metadata 입력 라인 수: {count_in}")
    print(f"[INFO] MISSING_FILE id 개수: {len(target_ids)}")
    print(f"[INFO] metadata_missingfile.jsonl 에 저장된 라인 수: {count_out}")


if __name__ == "__main__":
    # 1) error_files.txt 에서 MISSING_FILE id 수집
    missing_ids = collect_missing_ids(ERROR_LOG)
    print(f"[INFO] MISSING_FILE file_id 개수: {len(missing_ids)}")
    print(sorted(missing_ids))

    # 2) metadata.jsonl 필터링해서 새 파일 생성
    filter_metadata_by_ids(METADATA_IN, METADATA_OUT, missing_ids)

    print(f"[DONE] 결과 저장 완료 → {METADATA_OUT}")
