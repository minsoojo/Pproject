import re
from pathlib import Path

#양식/신청서를 요약 - 클리닝하는 코드입니다.

# (전처리 고민).이랑 한글자 숫자는 지워도 되지 않으려나?

# ======================================
# 문서 종류별 행동 문구
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
# 제목 정제
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
# 목적어에서 노이즈 토큰 제거
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
# 제목에서 목적어 + 문서 종류 추출
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
        if idx != -1:
            tail = title[idx + len(doc_type) :].strip()
            if doc_type == "표지":
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
# 텍스트에서 액션 문장 뽑기 (참고용)
# ======================================


def extract_action_phrase(text: str) -> str | None:
    """
    양식 문서 특유의 '무엇을 하기 위한 문서인지'를 보여주는 문장을 추출.
    안 써도 되지만, 디버깅용으로 유지.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    candidate_lines = [ln for ln in lines if len(ln) >= 8]

    patterns = [
        r"([^\n]*신청하고자[^\n]*)",
        r"([^\n]*취소하고자[^\n]*)",
        r"([^\n]*변경하고자[^\n]*)",
        r"([^\n]*복학하고자[^\n]*)",
        r"([^\n]*휴학하고자[^\n]*)",
        r"([^\n]*제출하오니[^\n]*)",
        r"([^\n]*허가하여 주시기 바랍니다[^\n]*)",
    ]

    joined = "\n".join(candidate_lines)

    for pat in patterns:
        m = re.search(pat, joined)
        if m:
            return m.group(1).strip()

    # fallback: 키워드 포함된 문장
    fallback_kw = ["신청서", "원서", "신청", "취소", "변경", "복학", "휴학"]
    for ln in candidate_lines:
        if any(k in ln for k in fallback_kw) and len(ln) >= 10:
            return ln.strip()

    return None


# ======================================
# 폼 전용 설명 생성
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
# 외부에서 쓰는 통합 함수
# (지금은 폼 전용으로 text는 안 씀)
# ======================================


def build_description(filename: str, text: str) -> str:
    """
    현재 버전: 양식(form) 전용.
    나중에 안내문/공지 쪽 로직을 분리할 때 여기서 분기만 추가하면 됨.
    """
    return build_form_description(filename)


# ======================================
# 테스트: 사용자 요청 형태 그대로
# ======================================

TEST_FILE_PATH = (
    r"C:\Users\s7302\OneDrive\바탕 화면\p프로젝트\xlsx_files\5.학과별_전과_심사기준.xls"
)
TEST_ENCODING = "cp949"  # 나중에 자동 인코딩 감지로 교체 가능


if __name__ == "__main__":
    path = Path(TEST_FILE_PATH)

    if not path.exists():
        print(f"파일이 존재하지 않습니다: {path}")
        exit(1)

    # 텍스트 읽기
    text = path.read_text(encoding=TEST_ENCODING, errors="ignore")

    # 분석
    title = clean_title(path.name)
    action = extract_action_phrase(text)
    desc = build_description(path.name, text)

    print("==== 분석 결과 ====")
    print("파일명:", path.name)
    print("제목:", title)
    print("생성된 설명:", desc)
