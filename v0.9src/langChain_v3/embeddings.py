import os
import sys
from typing import Any, List, Optional

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

# Block TensorFlow/Keras when using transformers-backed models (avoid Keras 3 checks / accidental TF import).
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

sys.modules["tensorflow"] = None
sys.modules["keras"] = None
sys.modules["tf_keras"] = None


def _default_device() -> str:
    forced = os.getenv("EMBEDDINGS_DEVICE", "").strip().lower()
    if forced:
        return forced

    try:
        import torch  # type: ignore

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _maybe_prefix(text: str, prefix: str) -> str:
    if not text:
        return prefix
    normalized = text.lstrip().lower()
    if normalized.startswith("query:") or normalized.startswith("passage:"):
        return text
    return f"{prefix}{text}"


class E5PrefixedEmbeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
        device: Optional[str] = None,
        query_prefix: Optional[str] = None,
        passage_prefix: Optional[str] = None,
        base_kwargs: Optional[dict[str, Any]] = None,
    ):
        self.query_prefix = query_prefix or os.getenv("E5_QUERY_PREFIX", "query: ")
        self.passage_prefix = passage_prefix or os.getenv("E5_PASSAGE_PREFIX", "passage: ")

        model_kwargs: dict[str, Any] = {"device": device or _default_device()}
        kwargs = dict(base_kwargs or {})
        kwargs.setdefault("model_name", model_name)
        kwargs.setdefault("model_kwargs", model_kwargs)
        kwargs.setdefault("encode_kwargs", {"normalize_embeddings": True})
        self._base = HuggingFaceEmbeddings(**kwargs)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        prefixed = [_maybe_prefix(t, self.passage_prefix) for t in texts]
        return self._base.embed_documents(prefixed)

    def embed_query(self, text: str) -> List[float]:
        return self._base.embed_query(_maybe_prefix(text, self.query_prefix))

    def __getattr__(self, name: str):
        return getattr(self._base, name)


def load_embedding_model():
    """
    기본값: 한국어 전용 임베딩 + GPU 사용.

    - 기본 모델: jhgan/ko-sbert-nli
    - 디바이스: CUDA 사용 가능 시 cuda, 아니면 cpu
    - DistanceStrategy.COSINE을 쓰므로 normalize_embeddings=True 권장

    환경변수:
    - EMBEDDINGS_MODEL_NAME: 기본 모델명 override
    - EMBEDDINGS_DEVICE: "cuda" | "cpu" 강제
    - EMBEDDINGS_MODE: "ko" (기본) | "e5"

    주의: 임베딩 모델/설정 변경은 기존 FAISS 인덱스와 호환되지 않으므로 인덱스 재빌드가 필요합니다.
    """
    mode = os.getenv("EMBEDDINGS_MODE", "ko").strip().lower()
    if mode == "e5":
        return E5PrefixedEmbeddings()

    model_name = os.getenv("EMBEDDINGS_MODEL_NAME", "jhgan/ko-sbert-nli").strip()
    device = _default_device()
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )

