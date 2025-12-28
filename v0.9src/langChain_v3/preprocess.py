from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib
import tiktoken

# tokenizer 준비 (전역으로 1번만)
_enc = tiktoken.get_encoding("cl100k_base")

def token_len(text: str) -> int:
    return len(_enc.encode(text))

def chunk_text(text: str, chunk_size: int = 350, overlap: int = 60):
    """
    RecursiveCharacterTextSplitter 기반 토큰 청킹
    """
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " "],
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=token_len,
    )
    return splitter.split_text(text or "")

# ✅ 반드시 필요
def sha256_text(text: str) -> str:
    """
    문서 내용 + 청킹 설정 기반 해시
    → 재청킹 필요 여부 판단용
    """
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
