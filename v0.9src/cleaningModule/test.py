# form_test.py
import re
import pymysql
from typing import Dict

#########################################
# 1) Form Classifier
#########################################

FORM_KEYWORDS = [
    "신청서", "지원서", "요청서", "추천서", "증명서", "확인서",
    "위임장", "계획서", "제출서", "서약서", "동의서",
    "복학원", "휴학원", "변경원", "학적변동원",
    "계산서", "원서", "자퇴원",
    "양식", "서식", "form", "application",
]

def normalize_filename_for_kw(name: str) -> str:
    s = name.lower()
    # 공백/괄호/기호 제거
    s = re.sub(r"[\s\(\)\[\]\{\}_\-\.\+]+", "", s)
    return s

FORM_TEXT_PATTERNS = [
    r"신청\s*하고자",
    r"복학\s*하고자",
    r"휴학\s*하고자",
    r"변경\s*하고자",
    r"제출\s*하오니",
    r"제출\s*합니다",
    r"허가하여\s*주시기\s*바랍니다",
    r"허가\s*바랍니다",
    r"승인\s*바랍니다",
]

def has_input_field_patterns(text: str) -> bool:
    patterns = [
        r"학과\s*\(전공\)",
        r"전공\s*\(",
        r"학번",
        r"성명\s*\(인\)",
        r"성명\s*[:：]",
        r"주민등록번호",
        r"연락처",
        r"전화번호",
        r"주소",
    ]
    return any(re.search(p, text) for p in patterns)

def has_form_layout_patterns(text: str) -> bool:
    # 긴 밑줄
    if re.search(r"_{4,}", text):
        return True
    # 체크박스
    if re.search(r"[□☐■]", text):
        return True
    if re.search(r"\[[ ]\]", text):
        return True
    # 표 테두리 문자
    if re.search(r"[┌┬┐│┼┘└╋╂╊╉]", text):
        return True
    return False

def is_form_debug(row: Dict) -> (bool, int, list):
    file_path = (row.get("file_path") or "")
    meta_id = (row.get("meta_id") or "")
    raw = (row.get("raw_data") or "")

    file_meta_lower = (file_path + " " + meta_id).lower()
    file_meta_norm = normalize_filename_for_kw(file_path)

    score = 0
    hits = []

    # [A] 파일명/메타 기반
    for kw in FORM_KEYWORDS:
        kw_lower = kw.lower()
        if kw_lower in file_meta_lower or kw_lower in file_meta_norm:
            score += 5
            hits.append(f"KW:{kw}")

    # [B] 본문 문장 패턴
    for pat in FORM_TEXT_PATTERNS:
        if re.search(pat, raw):
            score += 3
            hits.append(f"TXT:{pat}")

    # [C] 입력 필드
    if has_input_field_patterns(raw):
        score += 1
        hits.append("InputField")

    # [D] 레이아웃
    if has_form_layout_patterns(raw):
        score += 2
        hits.append("Layout")

    # Strong signal
    if has_input_field_patterns(raw) and has_form_layout_patterns(raw):
        hits.append("StrongSignal")
        return True, score, hits

    return (score >= 5), score, hits


#########################################
# 2) DB 설정
#########################################

DB_CONFIG = {
    "host": "localhost",
    "user": "dbid253",
    "password": "dbpass253",
    "database": "db25322",
    "charset": "utf8mb4",
}


#########################################
# 3) 메인: TestMain + metadata 조인해서 출력
#########################################

def main():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # TestMain(meta_id) + metadata(meta_id) 조인
            sql = """
                SELECT m.id, md.meta_id, md.file_path, m.raw_data
                FROM TestMain m
                JOIN metadata md ON m.meta_id = md.meta_id
            """
            cur.execute(sql)
            rows = cur.fetchall()

            print(f"총 {len(rows)}개 row 테스트\n")

            # 컬럼 순서: id, meta_id, file_path, raw_data
            for id_, meta_id, file_path, raw_data in rows:
                row_dict = {
                    "file_path": file_path or "",
                    "meta_id": meta_id or "",
                    "raw_data": raw_data or "",
                }

                is_form_flag, score, hits = is_form_debug(row_dict)
                label = "FORM" if is_form_flag else "NORMAL"
                rules_str = ",".join(hits) if hits else "-"

                # 제목 = file_path (없으면 raw 앞부분 fallback)
                if file_path and file_path.strip():
                    display_title = file_path.strip()
                else:
                    snippet = (raw_data or "").replace("\n", " ")
                    display_title = snippet[:40] if snippet else "(no title)"

                print(
                    f"[{label:6}] id={id_:5}  "
                    f"title={display_title[:40]:40}  "
                    f"score={score:<2}  "
                    f"rules={rules_str}"
                )

    finally:
        conn.close()


if __name__ == "__main__":
    main()


