from langChain_v3.vectorstore import build_vectorstore
from langChain_v3.log_chunk import setup_logging
import logging

if __name__ == "__main__":
    build_vectorstore(
        index_dir="faiss_index",
        chunk_size=350,
        overlap=60,
        limit=None,
    )