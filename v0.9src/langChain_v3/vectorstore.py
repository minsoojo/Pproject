# rag_engine/vectorstore.py
import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Any

from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy

from .embeddings import load_embedding_model
from .chunker import rebuild_chunks
from .documents import build_documents_from_chunks
from .mapping import save_faiss_mapping

# Aidata 루트는 v0.9src/aidata 정션을 따라 실제 공용 데이터 디렉터리로 연결된다.
AIDATA_DIR = Path(__file__).resolve().parents[1] / "aidata"
DEFAULT_INDEX_DIR = str(AIDATA_DIR / "faiss_index")

logger = logging.getLogger(__name__)


def build_vectorstore(
    index_dir: str = DEFAULT_INDEX_DIR,
    chunk_size: int = 500,
    overlap: int = 100,
    limit: Optional[int] = None,      # 10개 테스트 같은 제한 옵션
    batch_size: int = 128,            # 임베딩 진행률 로그를 위해 배치 단위로 처리
) -> Tuple[FAISS, Any]:
    """
    1) TestMain(clean_data 우선) → chunks 재구성 (DB에 저장)
    2) chunks → LangChain Document 리스트 생성
    3) Document 임베딩 → FAISS 인덱스 생성 (배치 처리 + 진행률 로그)
    4) 인덱스 로컬 저장 + faiss_mapping 테이블 업데이트
    """

    logger.info("[STEP] TestMain → chunks 재구성")
    rebuild_chunks(
        chunk_size=chunk_size,
        overlap=overlap,
        limit=limit,
    )

    logger.info("[STEP] chunks → Document 리스트 생성")
    documents = build_documents_from_chunks()
    total_docs = len(documents)
    logger.info("[INFO] Document 수: %d", total_docs)

    logger.info("[STEP] 임베딩 모델 로드")
    embeddings = load_embedding_model()

    logger.info("[STEP] FAISS 인덱스 생성 (batched)")
    if total_docs == 0:
        raise ValueError("Document가 0개입니다. chunks 생성/조회 로직을 확인해주세요.")

    if batch_size <= 0:
        raise ValueError("batch_size는 1 이상이어야 합니다.")

    vectorstore: Optional[FAISS] = None

    for start in range(0, total_docs, batch_size):
        end = min(start + batch_size, total_docs)
        logger.info("Embedding progress: %d/%d", end, total_docs)

        batch_docs = documents[start:end]

        if vectorstore is None:
            vectorstore = FAISS.from_documents(
                batch_docs,
                embedding=embeddings,
                distance_strategy=DistanceStrategy.COSINE,
            )
        else:
            vectorstore.add_documents(batch_docs)

    assert vectorstore is not None  # 위에서 total_docs==0 방어했으니 여기선 항상 존재

    logger.info("[STEP] 인덱스 로컬 저장: %s", index_dir)
    os.makedirs(index_dir, exist_ok=True)
    vectorstore.save_local(index_dir)

    logger.info("[STEP] faiss_mapping 테이블 저장")
    save_faiss_mapping(vectorstore)

    logger.info("[DONE] FAISS 인덱스 빌드 완료")
    return vectorstore, embeddings


def load_vectorstore(
    index_dir: str = DEFAULT_INDEX_DIR,
) -> Tuple[FAISS, Any]:
    """
    기존 FAISS 인덱스를 로드.
    없으면 예외 발생.
    """
    index_path = os.path.join(index_dir, "index.faiss")
    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"FAISS 인덱스({index_path})가 없습니다. 먼저 build_vectorstore()를 실행하세요."
        )

    embeddings = load_embedding_model()
    vectorstore = FAISS.load_local(
        index_dir,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return vectorstore, embeddings
