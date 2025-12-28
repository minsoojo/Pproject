# rag_engine/chunker.py
from typing import Optional
import logging

from .db import get_connection
from .preprocess import chunk_text, sha256_text
from .repository import (
    load_main_texts,
    get_existing_source_hash,
    delete_chunks_for_meta,
    insert_chunk,
)

logger = logging.getLogger(__name__)


def rebuild_chunks(
    chunk_size: int = 350,
    overlap: int = 60,
    limit: Optional[int] = None,
):
    """
    meta_id 기준으로 chunks를 재구성.

    중요:
    - meta_id/청크마다 새 DB 커넥션을 열면 Windows에서 로컬 포트(TIME_WAIT) 고갈로
      WinError 10048이 발생할 수 있어, 1개의 커넥션을 재사용합니다.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            rows = load_main_texts(limit=limit, cur=cur)
            logger.info(f"[CHUNKER] 청킹 대상 문서 수 {len(rows)} (limit={limit})")

            if not rows:
                logger.info("[INFO] 청킹 대상 문서가 없습니다.")
                return

            for row in rows:
                meta_id = row["meta_id"]
                text = row["text"] or ""

                logger.info(f"[CHUNKER] meta_id={meta_id} 청킹 시작")

                if not text.strip():
                    logger.error(f"[SKIP] 빈 텍스트 meta_id={meta_id}")
                    continue

                new_hash = sha256_text(text + f"\n__chunk_size={chunk_size},overlap={overlap}__")
                old_hash = get_existing_source_hash(meta_id, cur=cur)

                if old_hash == new_hash:
                    logger.info(f"[SKIP] 내용 동일, 재청킹 생략: meta_id={meta_id}")
                    continue

                delete_chunks_for_meta(meta_id, cur=cur, commit=False)

                chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
                for idx, chunk in enumerate(chunks):
                    insert_chunk(
                        meta_id=meta_id,
                        chunk_index=idx,
                        text=chunk,
                        source_hash=new_hash,
                        cur=cur,
                        commit=False,
                    )

                conn.commit()
                logger.info(f"[CHUNKER] meta_id={meta_id} 청킹 완료 ({len(chunks)} chunks)")

        logger.info("[DONE] chunks 테이블 재구성 완료")
    finally:
        conn.close()

