# rag_engine/documents.py
# 청킹한 조각을 임베딩하기 위해 LangChain Document 객체로 변환
from typing import List
from langchain_core.documents import Document

from .repository import load_all_chunks
import logging
logger = logging.getLogger(__name__)


def build_documents_from_chunks() -> List[Document]:
    """
    chunks 테이블의 내용을 LangChain Document 리스트로 변환.
    meta_id 기준 구조.
    """
    rows = load_all_chunks()
    docs: List[Document] = []

    for row in rows:
        docs.append(
            Document(
                page_content=row["text"] or "",
                metadata={
                    "chunk_id": row["chunk_id"],
                    "meta_id": row["meta_id"],          # ✅ 문서 식별자
                    "chunk_index": row["chunk_index"],  # ✅ 문서 내 위치
                },
            )
        )

    logger.info(f"[INFO] Document 개수: {len(docs)}")
    return docs
