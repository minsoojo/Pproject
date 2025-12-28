from langChain_v3.vectorstore import build_vectorstore, DEFAULT_INDEX_DIR


if __name__ == "__main__":
    # NOTE: 임베딩 모델/설정이 바뀌면 기존 FAISS 인덱스와 호환되지 않으므로
    # 반드시 인덱스를 재빌드해야 합니다.
    build_vectorstore(
        index_dir=DEFAULT_INDEX_DIR,
        chunk_size=350,
        overlap=60,
        limit=None,
    )

