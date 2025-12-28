import logging
import json
from datetime import datetime
from pathlib import Path

# 공용 aidata/logs 경로 (v0.9src/aidata 정션 사용)
_AIDATA_DIR = Path(__file__).resolve().parents[2] / "aidata"
LOG_DIR = _AIDATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 일반 텍스트 로그
logging.basicConfig(
    filename=LOG_DIR / "cleaning.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

log = logging.getLogger("cleaner")


# JSONL 에러 로그 기록 함수
def log_error_json(row_id: int, error_msg: str):
    entry = {
        "id": row_id,
        "error": error_msg,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(LOG_DIR / "error_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
