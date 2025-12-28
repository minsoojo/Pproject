# rag_engine/mapping.py
import logging

from .db import get_connection

logger = logging.getLogger(__name__)


def save_faiss_mapping(vectorstore, *, batch_size: int = 2000):
    """
    LangChain FAISS vectorstore에서 faiss_id -> (chunk_id, meta_id) 매핑을 추출해
    DB의 faiss_mapping 테이블에 저장.

    중요:
    - faiss_id마다 커넥션/INSERT를 하면 매우 느리고, Windows에서 포트 고갈로
      WinError 10048이 날 수 있어, 단일 커넥션 + executemany 배치로 처리합니다.
    """
    ntotal = int(vectorstore.index.ntotal)
    logger.info("[INFO] FAISS ntotal = %d", ntotal)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM faiss_mapping")

            sql = "INSERT INTO faiss_mapping (faiss_id, chunk_id, meta_id) VALUES (%s, %s, %s)"
            batch = []

            for faiss_id in range(ntotal):
                doc_id = vectorstore.index_to_docstore_id[faiss_id]
                doc = vectorstore.docstore.search(doc_id)

                chunk_id = doc.metadata.get("chunk_id")
                meta_id = doc.metadata.get("meta_id")
                batch.append((faiss_id, chunk_id, meta_id))

                if len(batch) >= batch_size:
                    cur.executemany(sql, batch)
                    batch.clear()

            if batch:
                cur.executemany(sql, batch)

        conn.commit()
        logger.info("[INFO] faiss_mapping 저장 완료")
    finally:
        conn.close()

