# connection/pipeline/gpt_only.py

from connection.pipeline.run_cleaning import (
    normalize_newlines,
    split_into_paragraphs,
    chunk_by_tokens
)
from connection.cleaner.gpt_cleaner import clean_with_gpt


def gpt_clean_text_only(
    raw_text: str,
    max_tokens: int = 800
) -> str:
    """
    파일 분류, trash 판단, DB 접근 없이
    raw_text 하나를 GPT-cleaning만 수행
    """

    # 1) normalize
    normalized = normalize_newlines(raw_text)

    # 2) 문단 분리
    paragraphs = split_into_paragraphs(normalized)

    # 3) chunking
    chunks = chunk_by_tokens(paragraphs, max_tokens=max_tokens)

    # 4) GPT-clean
    cleaned_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"[GPT-ONLY] chunk {i+1}/{len(chunks)}")
        cleaned = clean_with_gpt(chunk)
        cleaned_chunks.append(cleaned)

    return "\n\n".join(cleaned_chunks)
