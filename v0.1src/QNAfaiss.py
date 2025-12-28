# verify_faiss.py
import sys
import traceback

print("[STEP 0] FAISS 검증 시작 (구버전 langchain.embeddings 사용)")

try:
    from langchain_community.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings
    print("[OK] imports 성공: langchain_community + langchain.embeddings")
except Exception:
    print("[ERROR] import 실패")
    traceback.print_exc()
    sys.exit(1)

print("[STEP 1] Embeddings 생성")
try:
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sbert-nli",
        model_kwargs={"device": "cuda:0"}  # GPU 없어도 테스트는 됨
    )
    print("[OK] Embeddings 객체 생성 완료")
except Exception:
    print("[ERROR] Embeddings 생성 실패")
    traceback.print_exc()
    sys.exit(1)

print("[STEP 2] FAISS 인덱스 로드")
try:
    index = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )
    print("[OK] FAISS 인덱스 로드 성공")
    print(f"[INFO] FAISS ntotal = {index.index.ntotal}")
except Exception:
    print("[ERROR] FAISS 인덱스 로드 실패")
    traceback.print_exc()
    sys.exit(1)

print("[STEP 3] similarity_search 테스트")
try:
    query = "P프로젝트"
    print("[DEBUG] FAISS index dimension (self.d) =", index.index.d)
    q_vec = embeddings.embed_query(query)
    print("[DEBUG] Query embedding length =", len(q_vec))

    docs = index.similarity_search(query, k=3)

    print(f"[QUERY] {query}")
    print(f"[INFO] 반환된 문서 수: {len(docs)}")

    for i, d in enumerate(docs, 1):
        print(f"\n[{i}] Document")
        print(d.page_content[:300])
        print("-" * 60)

    print("\n[RESULT] FAISS 검색 정상 동작 확인 완료")
except Exception:
    print("[ERROR] similarity_search 실패")
    traceback.print_exc()
    sys.exit(1)

print("\n[FINAL] FAISS + Embeddings + 검색 검증 완료")
