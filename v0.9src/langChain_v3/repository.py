# rag_engine/repository.py
from typing import Any, Dict, List, Optional

from .db import get_connection


def _fetchall(cur, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    cur.execute(sql, params or ())
    return cur.fetchall()


def _fetchone(cur, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    cur.execute(sql, params or ())
    return cur.fetchone()


# ========= Main / metadata =========


def load_main_texts(limit: Optional[int] = None, *, cur=None) -> List[Dict[str, Any]]:
    """
    TestMain 테이블에서 청킹 대상 텍스트 로드.
    clean_data 우선, 없으면 raw_data 사용.
    """
    sql = """
    SELECT
        M.meta_id,
        COALESCE(M.clean_data, M.raw_data) AS text
    FROM TestMain AS M
    WHERE COALESCE(M.clean_data, M.raw_data) IS NOT NULL
    """

    if cur is not None:
        if limit is not None:
            return _fetchall(cur, sql + " LIMIT %s", (limit,))
        return _fetchall(cur, sql)

    conn = get_connection()
    try:
        with conn.cursor() as _cur:
            return load_main_texts(limit=limit, cur=_cur)
    finally:
        conn.close()


def get_metadata(meta_id: str, *, cur=None) -> Optional[Dict[str, Any]]:
    """
    특정 meta_id에 대한 metadata 단건 조회.
    """
    sql = "SELECT * FROM metadata WHERE meta_id = %s"

    if cur is not None:
        return _fetchone(cur, sql, (meta_id,))

    conn = get_connection()
    try:
        with conn.cursor() as _cur:
            return get_metadata(meta_id, cur=_cur)
    finally:
        conn.close()


# ========= chunks =========


def get_existing_source_hash(meta_id: str, *, cur=None) -> Optional[str]:
    """
    chunks 테이블에서 meta_id 기준으로 기존 source_hash 조회.
    """
    sql = """
    SELECT source_hash
    FROM chunks
    WHERE meta_id = %s
    LIMIT 1
    """

    if cur is not None:
        row = _fetchone(cur, sql, (meta_id,))
        return row["source_hash"] if row else None

    conn = get_connection()
    try:
        with conn.cursor() as _cur:
            return get_existing_source_hash(meta_id, cur=_cur)
    finally:
        conn.close()


def delete_chunks_for_meta(meta_id: str, *, cur=None, commit: bool = True):
    """
    특정 meta_id에 해당하는 모든 chunk 삭제.

    주의:
    faiss_mapping.chunk_id가 chunks.chunk_id를 FK로 참조하는 구조라면,
    faiss_mapping(자식) -> chunks(부모) 순서로 삭제해야 함.
    """
    sql_delete_mapping = """
    DELETE fm
    FROM faiss_mapping fm
    JOIN chunks c ON c.chunk_id = fm.chunk_id
    WHERE c.meta_id = %s
    """
    sql_delete_chunks = "DELETE FROM chunks WHERE meta_id = %s"

    if cur is not None:
        cur.execute(sql_delete_mapping, (meta_id,))
        cur.execute(sql_delete_chunks, (meta_id,))
        if commit:
            cur.connection.commit()
        return

    conn = get_connection()
    try:
        with conn.cursor() as _cur:
            delete_chunks_for_meta(meta_id, cur=_cur, commit=False)
        if commit:
            conn.commit()
    finally:
        conn.close()


def insert_chunk(
    meta_id: str,
    chunk_index: int,
    text: str,
    source_hash: str,
    *,
    cur=None,
    commit: bool = True,
):
    """
    chunks 테이블에 단일 chunk INSERT.
    """
    sql = """
    INSERT INTO chunks (
        meta_id,
        chunk_index,
        text,
        source_hash
    )
    VALUES (%s, %s, %s, %s)
    """

    if cur is not None:
        cur.execute(sql, (meta_id, chunk_index, text, source_hash))
        if commit:
            cur.connection.commit()
        return

    conn = get_connection()
    try:
        with conn.cursor() as _cur:
            insert_chunk(
                meta_id=meta_id,
                chunk_index=chunk_index,
                text=text,
                source_hash=source_hash,
                cur=_cur,
                commit=False,
            )
        if commit:
            conn.commit()
    finally:
        conn.close()


def load_all_chunks(*, cur=None) -> List[Dict[str, Any]]:
    """
    chunks 테이블 전체 로드.
    """
    sql = """
    SELECT
        chunk_id,
        meta_id,
        chunk_index,
        text
    FROM chunks
    ORDER BY chunk_id
    """

    if cur is not None:
        return _fetchall(cur, sql)

    conn = get_connection()
    try:
        with conn.cursor() as _cur:
            return load_all_chunks(cur=_cur)
    finally:
        conn.close()


# ========= faiss_mapping =========


def clear_faiss_mapping(*, cur=None, commit: bool = True):
    """
    faiss_mapping 테이블 전체 삭제.
    """
    if cur is not None:
        cur.execute("DELETE FROM faiss_mapping")
        if commit:
            cur.connection.commit()
        return

    conn = get_connection()
    try:
        with conn.cursor() as _cur:
            clear_faiss_mapping(cur=_cur, commit=False)
        if commit:
            conn.commit()
    finally:
        conn.close()


def insert_faiss_mapping(faiss_id: int, chunk_id: int, meta_id: str, *, cur=None, commit: bool = True):
    """
    faiss_mapping 테이블에 매핑 INSERT.
    """
    sql = """
    INSERT INTO faiss_mapping (faiss_id, chunk_id, meta_id)
    VALUES (%s, %s, %s)
    """

    if cur is not None:
        cur.execute(sql, (faiss_id, chunk_id, meta_id))
        if commit:
            cur.connection.commit()
        return

    conn = get_connection()
    try:
        with conn.cursor() as _cur:
            insert_faiss_mapping(faiss_id, chunk_id, meta_id, cur=_cur, commit=False)
        if commit:
            conn.commit()
    finally:
        conn.close()

