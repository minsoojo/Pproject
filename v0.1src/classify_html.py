# 쓰레기 데이터 거르는 코드
import os
import shutil
import re

# ===== 설정 =====
TEXT_DIR = "/home/t25315/data/text"        # 원본 txt 폴더
CLEAN_DIR = "/home/t25315/data/text_clean"      # 의미 있는 파일 복사 폴더
TRASH_DIR = "/home/t25315/data/text_trash"      # 의미 없는 파일 복사 폴더

os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(TRASH_DIR, exist_ok=True)


def korean_ratio(text: str) -> float:
    """전체 문자 중 한글(가-힣) 비율"""
    if not text:
        return 0.0
    korean_chars = re.findall(r"[가-힣]", text)
    return len(korean_chars) / len(text)


def noise_ratio(text: str) -> float:
    """
    HTML 태그/특수문자 비율 추정
    - <, >, {, }, [, ], /, \, =, &, ; 같은 문자 개수를 기준으로 계산
    """
    if not text:
        return 0.0
    noise_chars = re.findall(r"[<>/\\{}\[\]=&;]", text)
    return len(noise_chars) / len(text)


def is_meaningless(text: str) -> bool:
    """주어진 3가지 기준으로 의미 없는 파일인지 판정"""

    length = len(text)

    # 1) 글자 수 너무 적음
    if length < 150:
        return True

    # 2) 한글 비율 너무 낮음
    kr_ratio = korean_ratio(text)
    if kr_ratio < 0.10:   # 필요하면 0.15, 0.2 등으로 조정 가능
        return True

    # 3) HTML 찌꺼기/특수문자 비율이 비정상적으로 높음
    nz_ratio = noise_ratio(text)
    if nz_ratio > 0.30:   # 필요하면 0.25 ~ 0.4 사이로 튜닝
        return True

    return False


def classify_files():
    files = [f for f in os.listdir(TEXT_DIR) if f.endswith(".txt")]

    for filename in files:
        src_path = os.path.join(TEXT_DIR, filename)

        # 텍스트 읽기
        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        if is_meaningless(text):
            dst_path = os.path.join(TRASH_DIR, filename)
            shutil.copy(src_path, dst_path)
            print(f"[TRASH] {filename}")
        else:
            dst_path = os.path.join(CLEAN_DIR, filename)
            shutil.copy(src_path, dst_path)


if __name__ == "__main__":
    classify_files()
    print("\n분류 완료!")

# 일정 길이 이상이면 다시 clean으로 넘겨라
import os
import shutil

TRASH_DIR = "/home/t25315/data/text_trash"
CLEAN_DIR = "/home/t25315/data/text_clean"

THRESHOLD = 300  # 이 길이 이상이면 clean 폴더로 이동

os.makedirs(CLEAN_DIR, exist_ok=True)


def move_long_files():
    files = [f for f in os.listdir(TRASH_DIR) if f.endswith(".txt")]

    for filename in files:
        src_path = os.path.join(TRASH_DIR, filename)

        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        length = len(text)

        # 기준 넘으면 clean으로 이동
        if length >= THRESHOLD:
            dst_path = os.path.join(CLEAN_DIR, filename)
            shutil.move(src_path, dst_path)
            print(f"📄 MOVE → {filename} ({length}자)")
        else:
            print(f"🚮 STAY → {filename} ({length}자)")


if __name__ == "__main__":
    move_long_files()
    print("\n✔ 재분류 완료!")
