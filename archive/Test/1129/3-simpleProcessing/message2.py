# 개행, 문자 정규화 등 스크립트

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import unicodedata
from pathlib import Path


# ==============================
# 설정
# ==============================
INPUT_DIR = "/home/t25315/data/file_text"
OUTPUT_DIR = "/home/t25315/data/file_text_clean"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==============================
# 전처리 함수들
# ==============================

def normalize_newlines(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def remove_control_chars(text: str) -> str:
    # 제로폭 문자 제거
    zero_width = ["\u200b", "\u200c", "\u200d", "\ufeff"]
    for z in zero_width:
        text = text.replace(z, "")

    # C0/C1 control chars 제거
    text = "".join(ch for ch in text if (ch >= " " or ch == "\n"))
    return text


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def clean_special_chars(text: str) -> str:
    # 불릿 → "-" 로 통일
    bullets = ["●", "■", "◆", "▶", "▷", "◦", "·", "∙", "•"]
    for b in bullets:
        text = text.replace(b, "- ")

    # non-breaking space → 일반 공백
    text = text.replace("\u00a0", " ")

    # 불필요 특수문자 제거
    text = re.sub(r"[^\w가-힣ㄱ-ㅎㅏ-ㅣ\s\.\,\-\?\!]", " ", text)

    # 연속 공백 정규화
    text = re.sub(r"[ \t]+", " ", text)

    # 연속 구두점 정리
    text = re.sub(r"\.{4,}", "...", text)

    return text


def merge_lines_to_paragraphs(text: str) -> str:
    lines = text.split("\n")
    paragraphs = []
    buffer = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
        else:
            buffer.append(stripped)

    if buffer:
        paragraphs.append(" ".join(buffer))

    return "\n\n".join(paragraphs)


def remove_short_paragraphs(text: str, min_len: int = 5) -> str:
    paragraphs = [p.strip() for p in text.split("\n\n")]
    paragraphs = [p for p in paragraphs if len(p) >= min_len]
    return "\n\n".join(paragraphs)


def preprocess_text(text: str) -> str:
    text = normalize_newlines(text)
    text = remove_control_chars(text)
    text = normalize_unicode(text)
    text = clean_special_chars(text)
    text = merge_lines_to_paragraphs(text)
    text = remove_short_paragraphs(text, min_len=5)
    return text.strip()


# ==============================
# 폴더 전체 전처리
# ==============================

def preprocess_folder(input_dir: str, output_dir: str):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    count = 0

    for txt_path in input_dir.glob("*.txt"):
        count += 1
        print(f"[{count}] 전처리 중: {txt_path}")

        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        cleaned = preprocess_text(raw)

        out_path = output_dir / txt_path.name
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(cleaned)

    print(f"=== 전처리 완료: {count}개 파일 처리됨 ===")
    print(f"결과 저장 폴더 → {output_dir}")


if __name__ == "__main__":
    preprocess_folder(INPUT_DIR, OUTPUT_DIR)