# MeaningClassifier.py
import re

# 1차 기준
MIN_LENGTH = 150
MIN_KOREAN_RATIO = 0.10
MAX_NOISE_RATIO = 0.30

# 2차 보정 기준
SECOND_CHANCE_LENGTH = 300   # 길이가 이 이상이면 다시 clean 취급


def korean_ratio(text: str) -> float:
    if not text:
        return 0.0
    korean_chars = re.findall(r"[가-힣]", text)
    return len(korean_chars) / len(text)


def noise_ratio(text: str) -> float:
    if not text:
        return 0.0
    noise_chars = re.findall(r"[<>/\\{}\[\]=&;]", text)
    return len(noise_chars) / len(text)


def classify_text(text: str) -> str:
    """
    텍스트를 'clean' 또는 'trash' 로 분류
    단, 의미 없음으로 판정돼도 길이가 매우 긴 경우(clean 상황 가능)는 clean으로 보정
    """
    if not text:
        return "trash"

    length = len(text)
    kr = korean_ratio(text)
    nz = noise_ratio(text)

    # 1차 분류: 의미 없음 조건
    is_meaningless = (
        length < MIN_LENGTH or
        kr < MIN_KOREAN_RATIO or
        nz > MAX_NOISE_RATIO
    )

    # 2차 보정: 의미 없음으로 보이지만, 길이가 너무 길다면 clean 가능성 ↑
    if is_meaningless:
        if length >= SECOND_CHANCE_LENGTH:
            return "clean"
        else:
            return "trash"

    return "clean"
