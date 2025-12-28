import os, shutil
from langChain_v3.vectorstore import build_vectorstore, load_vectorstore, DEFAULT_INDEX_DIR
from langChain_v3.embeddings import load_embedding_model

def main():
    print("DEFAULT_INDEX_DIR =", DEFAULT_INDEX_DIR)

    # 1) 현재 임베딩 차원 체크
    emb = load_embedding_model()
    dim = len(emb.embed_query("dim check"))
    print("Embedding dim =", dim)

    # 2) 인덱스 폴더 초기화
    print("Reset index dir...")
    shutil.rmtree(DEFAULT_INDEX_DIR, ignore_errors=True)
    os.makedirs(DEFAULT_INDEX_DIR, exist_ok=True)

    # 3) 빌드 (처음엔 limit 걸어서 스모크 테스트 추천)
    vs, _ = build_vectorstore(
        index_dir=DEFAULT_INDEX_DIR,
        chunk_size=500,
        overlap=100,
        limit=1000,      # ✅ 먼저 1000개로 성공 확인 → 이후 None으로 전체 빌드
        batch_size=64,   # OpenAI 임베딩이면 너무 크게 잡지 말기
    )
    print("Built: d =", vs.index.d, "ntotal =", vs.index.ntotal)

    # 4) 로드 + 검색 테스트
    vs2, _ = load_vectorstore(index_dir=DEFAULT_INDEX_DIR)
    print("Loaded: d =", vs2.index.d, "ntotal =", vs2.index.ntotal)

    out = vs2.similarity_search_with_score("일반 휴학 최대 몇 학기", k=3)
    print("Search OK, top1 score =", out[0][1])

if __name__ == "__main__":
    main()
