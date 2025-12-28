from typing import List
import tiktoken
# from transformers import AutoTokenizer
import re

# tokenizer = AutoTokenizer.from_pretrained(
#     "/home/t25315/models/gpt-oss-20b",   # 모델 다운로드 경로
#     use_fast=True
# )

def normalize_newlines(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", text)


def split_into_paragraphs(text: str) -> List[str]:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    return parts


def chunk_by_tokens(paragraphs: List[str], max_tokens=800):
    encoder = tiktoken.encoding_for_model("gpt-4.1-mini")
    # encoder = tiktoken.get_encoding("cl100k_base")

    combined = "\n\n".join(paragraphs)
    tokens = encoder.encode(combined)

    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = encoder.decode(tokens[i:i + max_tokens])
        chunks.append(chunk)

    return chunks

# def chunk_by_tokens(paragraphs: List[str], max_tokens=800):
#     chunks = []
#     current_text = ""

#     for para in paragraphs:
#         # 다음 paragraph를 붙였을 때 토큰 길이 계산
#         new_text = para if not current_text else current_text + "\n\n" + para
#         encoded = tokenizer.encode(new_text)

#         if len(encoded) <= max_tokens:
#             current_text = new_text      # 아직 max 이하이면 계속 누적
#         else:
#             chunks.append(current_text)  # 초과하면 하나 청크 확정
#             current_text = para          # 새 청크 시작

#     if current_text:
#         chunks.append(current_text)

#     return chunks
