# classifier.py
# 양식 설명 생성 모듈 (양식 클리닝)

import re
from pathlib import Path
from typing import Dict

# ======================================
# 0) 양식/신청서 여부 판별
# ======================================

def is_form(row: Dict) -> bool:
    """
    title, file_path, meta_id 등에서 키워드로 판별
    예: '신청서', '양식', '서식', '지원서' 등
    """
    file_path = (row.get("file_path") or "").lower()
    meta_id = (row.get("meta_id") or "").lower()
    title = (row.get("title") or "").lower()  # 나중에 JOIN 해두면 같이 씀

    # 파일명만 따로 한 번 더 반영 (확장자 제외)
    filename = ""
    if file_path:
        filename = Path(file_path).stem.lower()

    text_for_check = " ".join([file_path, meta_id, title, filename])

    keywords = [
        "신청서",
        "요청서",
        "추천서",
        "증명서",
        "확인서",
        "동의서",
        "서약서",
        "신고서",
        "계약서",
        "지원서",
        "양식",
        "서식",
        "표지",
        "복학원",
        "휴학원",
        "학적변동원",
        "form",
    ]

    return any(kw in text_for_check for kw in keywords)


# ======================================
# 1) 문서 종류별 행동 문구
# ======================================

DOC_TYPE_ACTION = {
    "신청서": "신청할 때",
    "요청서": "요청할 때",
    "추천서": "추천할 때",
    "증명서": "증명할 때",
    "확인서": "확인할 때",
    "동의서": "동의 내용을 기록할 때",
    "서약서": "서약 내용을 기록할 때",
    "신고서": "신고할 때",
    "계약서": "계약 내용을 기록할 때",
    "표지": "제출 시 사용하는 표지 양식입니다.",
    "원": "신청할 때",  # 복학원, 휴학원, 학적변동원 등
}

DOC_TYPE_KEYWORDS = list(DOC_TYPE_ACTION.keys())


# ======================================
# 2) 제목 정제
# ======================================

def clean_title(filename_or_title: str) -> str:
    """
    파일명 또는 원본 제목에서 사람이 읽기 좋은 제목을 만든다.
    (서식1,2), (양식), [붙임2] 같은 메타 괄호는 통째로 제거한다.
    """
    name = Path(filename_or_title).stem  # 확장자 제거

    # 1) '서식', '양식', '붙임'이 들어간 괄호 전체 제거
    #    예: (서식1,2), (양식), [붙임2], (붙임 3. 신청서 양식) 등
    name = re.sub(
        r"[\(\[][^\)\]]*(양식|서식|붙임[0-9,]*|붙임)[^\)\]]*[\)\]]",
        " ",
        name,
    )

    # 2) 언더바/하이픈 → 공백
    name = name.replace("_", " ").replace("-", " ")

    # 3) 남아 있는 괄호 기호만 제거 (안의 글자는 살림)
    name = name.replace("(", " ").replace(")", " ")
    name = name.replace("[", " ").replace("]", " ")

    # 4) 시작 부분의 '양식', '서식', '붙임...' 제거
    name = re.sub(r"^(양식|서식|붙임[0-9,]*|붙임)\s*", "", name)

    # 5) 중간에 단독 토큰 '양식', '서식' 있으면 제거
    name = re.sub(r"\b(양식|서식)\b", " ", name)

    # 6) 공백 정리
    name = re.sub(r"\s+", " ", name).strip()

    return name


# ======================================
# 3) 목적어에서 노이즈 토큰 제거
# ======================================

def _remove_noise_tokens_for_purpose(text: str) -> str:
    """
    목적어에서 '양식', '서식', '붙임2' 같은 노이즈 토큰 제거.
    제목 자체는 건드리지 않고, purpose 생성할 때만 사용.
    """
    tokens = text.split()

    cleaned = []
    for t in tokens:
        # 붙임2, 붙임3, 붙임 등
        if re.fullmatch(r"붙임\d*", t):
            continue
        if t in {"양식", "서식"}:
            continue
        cleaned.append(t)

    if not cleaned:
        return text.strip()

    return " ".join(cleaned)


# ======================================
# 4) 제목에서 목적어 + 문서 종류 추출
# ======================================

def extract_purpose_and_type(title: str):
    """
    제목에서 '목적어'와 '문서 종류(신청서/요청서/증명서/표지/원 등)'를 분리한다.

    예:
      "예방접종비 지원 신청서"         -> ("예방접종비 지원", "신청서")
      "성적정정 요청서"                 -> ("성적정정", "요청서")
      "가천대 레포트 표지1"             -> ("가천대 레포트", "표지")
      "간호 복학원"                     -> ("간호 복학", "원") 정도로 해석
    """
    title = title.strip()

    # 1) 강한 문서 타입들 (신청서/요청서/증명서/표지 등)
    for doc_type in DOC_TYPE_KEYWORDS:
        # 완전 단어로 끝날 때 (예: "예방접종비 지원 신청서")
        if title.endswith(doc_type):
            purpose_raw = title[: -len(doc_type)].strip()
            purpose = _remove_noise_tokens_for_purpose(purpose_raw)
            return purpose, doc_type

        # 중간에 끼어 있는 경우 (예: "가천대 레포트 표지1" -> '표지' 찾기)
        idx = title.rfind(doc_type)
        if idx != -1 and doc_type == "표지":
            purpose_raw = title[:idx].strip()
            purpose = _remove_noise_tokens_for_purpose(purpose_raw)
            return purpose, "표지"

    # 2) '복학원', '휴학원', '학적변동원' 같은 '원' 계열 처리
    if title.endswith("원"):
        core = title[:-1].strip()
        core_clean = _remove_noise_tokens_for_purpose(core)
        return core_clean, "원"

    # 3) 아무 타입도 못 찾으면 목적어만 있고 타입은 None
    purpose = _remove_noise_tokens_for_purpose(title)
    return purpose, None


# ======================================
# 5) 폼 전용 설명 생성 (파일명/제목 기준)
# ======================================

def build_form_description(filename_or_title: str) -> str:
    """
    파일명/제목을 입력받아서, 양식 문서에 대한 설명 문장을 생성한다.
    """
    title = clean_title(filename_or_title)
    purpose, doc_type = extract_purpose_and_type(title)

    # 1) 문서 종류를 아는 경우
    if doc_type:
        # 표지의 경우는 약간 다른 문장
        if doc_type == "표지":
            if any(k in purpose for k in ["레포트", "보고서"]):
                return (
                    f"{title} 양식입니다. "
                    f"이 문서는 {purpose} 제출 시 사용하는 표지 양식입니다."
                )
            else:
                return (
                    f"{title} 양식입니다. "
                    f"이 문서는 {purpose}와 관련된 문서의 표지로 사용하는 양식입니다."
                )

        action_phrase = DOC_TYPE_ACTION.get(doc_type, "사용할 때")

        # purpose가 정상적으로 뽑힌 경우
        if purpose and purpose != title:
            # 확인서 / 증명서는 한국어 템플릿을 조금 다르게
            if doc_type == "확인서":
                return (
                    f"{title} 양식입니다. "
                    f"이 문서는 {purpose}을(를) 확인하기 위해 사용하는 공식 서류입니다."
                )
            if doc_type == "증명서":
                return (
                    f"{title} 양식입니다. "
                    f"이 문서는 {purpose}을(를) 증명하기 위해 사용하는 공식 서류입니다."
                )

            # 나머지 서류들 (신청서, 요청서, 추천서, 원 등)
            return (
                f"{title} 양식입니다. "
                f"이 문서는 {purpose}을(를) {action_phrase} 사용하는 공식 서류입니다."
            )

        # 목적어 뽑기가 애매한 경우
        return (
            f"{title} 양식입니다. "
            f"이 문서는 {action_phrase} 사용하는 공식 서류입니다."
        )

    # 2) 문서 종류를 모르는 경우 (그냥 양식인데 타입 애매)
    return (
        f"{title} 양식입니다. "
        f"이 문서는 {purpose}와 관련된 업무를 처리할 때 사용하는 학교 행정 서류입니다."
    )


# ======================================
# 6) 호출 형식 통일용 통합 함수
# ======================================

def build_description(filename: str, text: str) -> str:
    """
    호출 형식 통일용
    """
    return build_form_description(filename)


# ======================================
# 8) row 단위로 설명 생성 (파이프라인용)
# ======================================

def clean_form_file(row: Dict) -> str:
    """
    DB row를 입력받아서, 양식 문서에 대한 설명 문자열을 생성한다.
    - file_path가 있으면 그걸 제목/파일명으로 사용
    - 없으면 meta_id 사용
    - 둘 다 없으면 '양식 문서'라는 기본 제목 사용
    """
    file_path = row.get("file_path") or ""
    meta_id = row.get("meta_id") or ""
    raw = row.get("raw_data") or ""

    filename_for_desc = file_path or meta_id or "양식 문서"

    return build_description(filename_for_desc, raw)



# ======================================
# 9) 로컬 간단 테스트용
# ======================================

if __name__ == "__main__":
    samples = [
        # (1) 신청서류
        {"file_path": "예방접종비_지원_신청서.hwp", "meta_id": "", "raw_data": ""},
        {"file_path": "성적정정요청서.pdf", "meta_id": "", "raw_data": ""},
        {"file_path": "가천대_레포트_표지1.hwp", "meta_id": "", "raw_data": ""},
        {"file_path": "간호_복학원.hwp", "meta_id": "", "raw_data": ""},
        {"file_path": "붙임2_휴학원_양식.hwp", "meta_id": "", "raw_data": ""},

        # (2) 양식 아닌 일반 공지 (is_form 잘 거르는지 확인용)
        {"file_path": "2025-1_수강신청_안내.pdf", "meta_id": "meta-001", "raw_data": ""},
    ]

    for i, row in enumerate(samples, start=1):
        print(f"\n=== SAMPLE {i} ===")
        print("file_path:", row["file_path"])
        print("is_form :", is_form(row))

        desc = clean_form_file(row)
        print("description:")
        print(desc)
