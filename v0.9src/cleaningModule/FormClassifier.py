# classifier.py (통합 버전)
# 양식인지 아닌지 rule-base로 점수 매겨 판단
import re
from typing import Dict, Tuple, List

# 1) 파일명/메타데이터 기반 양식 키워드
FORM_KEYWORDS = [
    "신청서", "지원서", "요청서", "추천서", "증명서", "확인서",
    "위임장", "계획서", "제출서", "서약서", "동의서",
    "복학원", "휴학원", "변경원", "학적변동원",
    "계산서", "원서", "자퇴원",
    "양식", "서식", "form", "application",
]

# 파일명 정규화: 공백/괄호/기호 제거해서 키워드 매칭 강화
# 예) "생 리 공 결 신 청 서.txt" -> "생리공결신청서txt"
def normalize_filename_for_kw(name: str) -> str:
    s = name.lower()
    # 공백, 괄호, 대괄호, 중괄호, 언더바, 하이픈, 점, 플러스 등 제거
    s = re.sub(r"[\s\(\)\[\]\{\}_\-\.\+]+", "", s)
    return s


# 2) 본문 문장 패턴 (양식에서 자주 나오는 문장들)
FORM_TEXT_PATTERNS = [
    r"신청\s*하고자",          # ~ 신청하고자 합니다
    r"복학\s*하고자",
    r"휴학\s*하고자",
    r"변경\s*하고자",
    r"제출\s*하오니",
    r"제출\s*합니다",
    r"허가하여\s*주시기\s*바랍니다",
    r"허가\s*바랍니다",
    r"승인\s*바랍니다",
]


# 3) 입력필드 패턴: 학과(전공), 학번, 성명(인) 등
def has_input_field_patterns(text: str) -> bool:
    patterns = [
        r"학과\s*\(전공\)",      # 학과(전공)
        r"전공\s*\(",            # 전공(
        r"학번",                 # 학번
        r"성명\s*\(인\)",        # 성명(인)
        r"성명\s*[:：]",         # 성명:
        r"주민등록번호",         # 주민등록번호
        r"연락처",               # 연락처
        r"전화번호",             # 전화번호
        r"주소",                 # 주소
    ]
    for pat in patterns:
        if re.search(pat, text):
            return True
    return False


# 4) 폼/표 레이아웃 패턴: 밑줄, 체크박스, 표 테두리 등
def has_form_layout_patterns(text: str) -> bool:
    # 긴 밑줄 ________
    if re.search(r"_{4,}", text):
        return True

    # 체크박스: □, ☐, ■, [ ]
    if re.search(r"[□☐■]", text):
        return True
    if re.search(r"\[[ ]\]", text):
        return True

    # 표 테두리 문자들: ┌ ┬ ┐ │ ┼ ┘ └ 등
    if re.search(r"[┌┬┐│┼┘└╋╂╊╉]", text):
        return True

    return False


# 내부 공통 스코어링 함수
# 점수 규칙은 기존 classifier.py 그대로 유지:
# [A] 키워드 매치: +5
# [B] 문장 패턴: +1
# [C] 입력필드: +2
# [D] 레이아웃: +2
def _score_form(row: Dict) -> Tuple[int, List[str]]:
    score = 0
    hits = []

    file_meta = row.get("file_path", "") + " " + row.get("title", "") + " " + row.get("meta_id", "")
    file_meta_lower = file_meta.lower()
    file_meta_norm = normalize_filename_for_kw(file_meta_lower)

    raw = row.get("raw_data", "") or ""

    # [A] 파일명/경로 키워드
    for kw in FORM_KEYWORDS:
        kw_lower = kw.lower()
        if kw_lower in file_meta_lower or kw_lower in file_meta_norm:
            score += 5
            hits.append(f"KW:{kw}")

    # [B] 본문 텍스트 패턴
    for pat in FORM_TEXT_PATTERNS:
        if re.search(pat, raw):
            score += 1
            hits.append(f"TXT:{pat}")

    # [C] 입력필드
    if has_input_field_patterns(raw):
        score += 2
        hits.append("InputField")

    # [D] 레이아웃
    if has_form_layout_patterns(raw):
        score += 2
        hits.append("Layout")

    return score, hits


def is_form(row: Dict) -> bool:
    score, hits = _score_form(row)
    return score >= 5


def is_form_debug(row: Dict) -> Tuple[bool, int, List[str]]:
    score, hits = _score_form(row)
    return (score >= 5), score, hits

