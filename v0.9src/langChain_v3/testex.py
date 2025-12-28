# build_index.py
from langChain_v3.vectorstore import build_vectorstore, DEFAULT_INDEX_DIR

if __name__ == "__main__":
    # 분할이 필요하면 chunk_size, overlap 조정
    build_vectorstore(index_dir=DEFAULT_INDEX_DIR, chunk_size=500, overlap=100)

#############################

# 벡터 DB 빌드

# from rag_engine.vectorstore import build_vectorstore
# build_vectorstore()


# 벡터 DB 불러오기

# from rag_engine.vectorstore import load_vectorstore
# load_vectorstore
##############################


# 테스트용(main) 에서 chunker로 각각 -> Document 변환 -> 벡터화 -> FAISS 저장
# 검색시 Query 에 대해 벡터화 -> FAISS 검색 -> metadata JOIN 후 결과 반환


# # search_test.py
# from langChain_v3.rag import semantic_search

# if __name__ == "__main__":
#     query = "신약개발 기간 줄이기"
#     results = semantic_search(query, k=3)

#     print(f"Query: {query}")
#     for i, r in enumerate(results, start=1):
#         print(f"\n=== RESULT {i} ===")
#         print("meta_id:", r["meta_id"])
#         print("title  :", r["title"])
#         print("url    :", r["url"])
#         print("score  :", r["score"])
#         print("chunk  :", r["chunk_text"][:200], "...")
