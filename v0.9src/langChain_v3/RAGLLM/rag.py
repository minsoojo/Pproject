# langChains_v3/rag.py
# FAISS에서 top-k chunk 검색 후, 검색된 결과에 대해 문맥 확장된 청크를 전송
# rag_engine/rag.py
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Callable, Iterable, Optional

from langChain_v3.vectorstore import load_vectorstore, DEFAULT_INDEX_DIR
from langChain_v3.db import get_connection

# Remove duplicate overlap between adjacent chunks.
def _trim_overlap(prev_text: str, next_text: str, max_overlap_chars: int = 1000) -> str:
    if not prev_text or not next_text:
        return next_text

    max_len = min(len(prev_text), len(next_text), max_overlap_chars)
    for size in range(max_len, 0, -1):
        if prev_text.endswith(next_text[:size]):
            return next_text[size:]

    return next_text


def _merge_chunks_without_overlap(
    texts: List[str], max_overlap_chars: int = 1000
) -> str:
    merged: List[str] = []
    prev_text = ""

    for text in texts:
        if not text:
            continue
        if not merged:
            merged.append(text)
            prev_text = text
            continue

        trimmed = _trim_overlap(prev_text, text, max_overlap_chars)
        if trimmed:
            merged.append(trimmed)
        prev_text = text

    return "\n\n".join(merged)


def _default_rerank_device() -> str:
    forced = os.getenv("RERANK_DEVICE", "").strip().lower()
    if forced:
        return forced
    try:
        import torch  # type: ignore

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _attach_source(
    rows: Iterable[Dict[str, Any]], source: str
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        tagged = dict(row)
        tagged.setdefault("source", source)
        tagged.setdefault("source_rank", idx)
        out.append(tagged)
    return out


def _normalize_web_results(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        title = row.get("title") or row.get("name") or ""
        url = row.get("url") or row.get("link") or ""
        snippet = row.get("snippet") or row.get("content") or row.get("text") or ""
        if not (title or url or snippet):
            continue
        item: Dict[str, Any] = {
            "title": title,
            "url": url,
            "snippet": snippet,
            "context_text": snippet,
            "source": "web",
            "source_rank": idx,
        }
        if row.get("score") is not None:
            try:
                item["score"] = float(row["score"])
            except Exception:
                pass
        normalized.append(item)
    return normalized


def _dedupe_results(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for row in rows:
        source = row.get("source")
        url = (row.get("url") or "").strip().lower()
        if url:
            key = ("url", source, url)
        else:
            key = (
                "meta",
                source,
                row.get("meta_id"),
                row.get("chunk_id"),
                row.get("title"),
            )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _collect_web_results(
    query: str, web_k: int, web_search_fn: Callable[..., List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    try:
        return web_search_fn(query, k=web_k)
    except TypeError:
        return web_search_fn(query, web_k)
    except Exception:
        return []

#문맥 확장 함수
def expand_context(cur, meta_id: str, center_index: int, window: int = 1) -> str:
    """
    같은 문서(meta_id) 안에서 center_index 주변 청크들을 window 범위만큼 합쳐서
    하나의 텍스트 블록으로 만들어준다.
    예: window = 1 → chunk_index 6,7,8 (±1 확장)
    """
    cur.execute(
        """
        SELECT chunk_index, text
        FROM chunks
        WHERE meta_id = %s
          AND chunk_index BETWEEN %s AND %s
        ORDER BY chunk_index
        """,
        (meta_id, center_index - window, center_index + 2*window),
    )
    rows = cur.fetchall()

    # 텍스트만 정렬된 순서대로 이어붙임
    texts = [r["text"] for r in rows if r["text"]]
    return _merge_chunks_without_overlap(texts)


#   의미 기반 검색 함수 + 문맥 확장.
def semantic_search(
    query: str,
    k: int = 5,
    index_dir: str = DEFAULT_INDEX_DIR,
    window: int = 1,  # 문맥 확장을 위한 추가 파라미터
) -> List[Dict[str, Any]]:
    """
    - FAISS 인덱스에서 top-k chunk 검색
    - 각 chunk의 meta_id를 이용해 metadata에서 title, url 조회
    - 같은 meta_id의 주변 청크(chunk_index ± window)까지 붙여 문맥 확장(context_text) 생성
    - 결과를 리스트[dict] 형태로 반환
    """
    vectorstore, _ = load_vectorstore(index_dir=index_dir)

    # doc, score 튜플들을 가져옴
    docs_and_scores = vectorstore.similarity_search_with_score(query, k=k)

    results: List[Dict[str, Any]] = []

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            for doc, score in docs_and_scores:
                meta = doc.metadata
                meta_id = meta.get("meta_id")
                chunk_id = meta.get("chunk_id")
                chunk_index = meta.get("chunk_index")

                # 문서 제목/URL 조회
                cur.execute(
                    """
                    SELECT title, url
                    FROM metadata
                    WHERE meta_id = %s
                    """,
                    (meta_id,),
                )
                row = cur.fetchone()
                title = row["title"] if row else None
                url = row["url"] if row else None

                # 🔥 문맥 확장 수행
                # chunk_index 주변 window 만큼 청크를 합쳐 context_text 생성
                context_text = expand_context(cur, meta_id, chunk_index, window)

                # 결과 저장
                results.append(
                    {
                        "meta_id": meta_id,
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_index,

                        # 검색 점수(그대로 사용)
                        "score": float(score),

                        # 문서 정보
                        "title": title,
                        "url": url,

                        # 기존 단일 청크 텍스트
                        "chunk_text": doc.page_content,

                        # 🔥 문맥 확장된 블록 (LLM에는 이걸 주면 됨)
                        "context_text": context_text,
                        "context_window": window,
                    }
                )
    finally:
        conn.close()

    return results


def semantic_search_rerank(
    query: str,
    k: int = 20,
    top_n: int = 5,
    index_dir: str = DEFAULT_INDEX_DIR,
    window: int = 1,
    rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> List[Dict[str, Any]]:
    """
    semantic_search()로 FAISS top-k 청크를 가져온 뒤 Cross-Encoder로 rerank하여 top_n을 반환.

    - rerank는 rag_test.py와 동일하게 chunk_text(원 청크) 기준으로 점수를 계산
    - 반환 dict에 rerank_score(float) 추가
    """
    retrieved = semantic_search(
        query=query,
        k=k,
        index_dir=index_dir,
        window=window,
    )

    if not retrieved or top_n <= 0:
        return []

    # Lazy import: sentence_transformers는 환경에 따라 없을 수 있음.
    try:
        from sentence_transformers import CrossEncoder  # type: ignore
    except Exception as e:
        raise ImportError(
            "semantic_search_rerank requires sentence-transformers. "
            "Install it or use semantic_search() instead."
        ) from e

    reranker = CrossEncoder(rerank_model_name)
    # reranker = CrossEncoder(
    #     "Dongjin-kr/ko-reranker-base",
    #     device="cuda"
    # )

    pairs = []
    valid_rows: List[Dict[str, Any]] = []
    for r in retrieved:
        text = r.get("context_text")
        if text:
            pairs.append((query, text))
            valid_rows.append(r)

    if not pairs:
        return []

    scores = reranker.predict(pairs)

    reranked = sorted(
        zip(valid_rows, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    results: List[Dict[str, Any]] = []
    for r, s in reranked[: min(top_n, len(reranked))]:
        out = dict(r)
        out["rerank_score"] = float(s)
        results.append(out)

    return results


def hybrid_search_rerank(
    query: str,
    *,
    faiss_k: int = 20,
    web_k: int = 10,
    top_n: int = 5,
    merge_k: Optional[int] = None,
    index_dir: str = DEFAULT_INDEX_DIR,
    window: int = 1,
    rerank_model_name: str = "Dongjin-kr/ko-reranker-base",
    web_search_fn: Optional[Callable[..., List[Dict[str, Any]]]] = None,
    parallel: bool = True,
) -> List[Dict[str, Any]]:
    if merge_k is None:
        merge_k = faiss_k + web_k

    def fetch_internal() -> List[Dict[str, Any]]:
        return semantic_search(query=query, k=faiss_k, index_dir=index_dir, window=window)

    def fetch_web() -> List[Dict[str, Any]]:
        if web_search_fn is None:
            try:
                from langChain_v3 import web_search  # type: ignore

                return _collect_web_results(query, web_k, web_search.search_web)
            except Exception:
                return []
        return _collect_web_results(query, web_k, web_search_fn)

    if parallel:
        with ThreadPoolExecutor(max_workers=2) as executor:
            internal_future = executor.submit(fetch_internal)
            web_future = executor.submit(fetch_web)
            internal_rows = internal_future.result()
            web_rows = web_future.result()
    else:
        internal_rows = fetch_internal()
        web_rows = fetch_web()

    internal_rows = _attach_source(internal_rows, "internal")
    web_rows = _normalize_web_results(web_rows)

    merged = _dedupe_results(list(internal_rows) + list(web_rows))
    merged = merged[:merge_k]

    if not merged or top_n <= 0:
        return []

    try:
        from sentence_transformers import CrossEncoder  # type: ignore
    except Exception as e:
        raise ImportError(
            "hybrid_search_rerank requires sentence-transformers."
        ) from e

    reranker = CrossEncoder(rerank_model_name, device=_default_rerank_device())

    pairs: List[tuple[str, str]] = []
    valid_rows: List[Dict[str, Any]] = []
    for row in merged:
        # text = row.get("context_text") or row.get("chunk_text") or row.get("snippet")
        text = row.get("chunk_text") or row.get("snippet")
        if text:
            pairs.append((query, text))
            valid_rows.append(row)

    if not pairs:
        return []

    scores = reranker.predict(pairs)
    reranked = sorted(
        zip(valid_rows, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    results: List[Dict[str, Any]] = []
    for row, score in reranked[: min(top_n, len(reranked))]:
        out = dict(row)
        out["rerank_score"] = float(score)
        results.append(out)

    return results
