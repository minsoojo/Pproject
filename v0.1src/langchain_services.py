# -*- coding: utf-8 -*-

# pip install -q langchain_community
# pip install -q langchain_openai
# pip install -qU sentence-transformers
# pip install -q langchain_core
# pip install -q faiss-cpu

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_community.embeddings import HuggingFaceEmbeddings
import pymysql
import os
"""---
텍스트 로더
"""
loader = TextLoader('02957-test-result-v3.txt')
data = loader.load()

# print(type(data))
# print(len(data))

text = data[0].page_content


"""---
청킹
"""
def chunk_text(text, chunk_size_prams=500, overlap_prams=100):
  text_splitter = RecursiveCharacterTextSplitter(
      separators=["\n\n", "\n", ". ", " "],  # 문단 > 문장 > 공백 우선
      chunk_size=chunk_size_prams,
      chunk_overlap=overlap_prams,
      length_function=len,
  )

  chunks = text_splitter.split_text(text)
  return chunks

# chunks = chunk_text(text)
# for i, chunk in enumerate(chunks):
#     print(f"\n=== CHUNK {i+1} ===")
#     print(chunk)

"""---
임베딩
"""



"""---
faiss
"""
# pip install -q faiss-gpu
# !pip install faiss-gpu --no-cache-dir

# documents = [
#     Document(page_content=chunk, metadata={"chunk_id": i})
#     for i, chunk in enumerate(chunks)
# ]
embeddings_model = HuggingFaceEmbeddings(
    model_name='jhgan/ko-sbert-nli',
    model_kwargs={'device':'cpu'},
    encode_kwargs={'normalize_embeddings':True},
)

# vectorstore = FAISS.from_documents(documents,
#                                    embedding = embeddings_model,
#                                    distance_strategy = DistanceStrategy.COSINE
#                                   )
# vectorstore

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1234",
        database="a123456",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

def load_texts_from_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
            SELECT M.id AS main_id,
                   M.meta_id,
                   COALESCE(M.clean_data, M.raw_data) AS text
            FROM Main AS M
            WHERE COALESCE(M.clean_data, M.raw_data) IS NOT NULL
            """
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()

def build_documents():
    rows = load_texts_from_db()
    docs = []

    for row in rows:
        meta_id = row["meta_id"]
        full_text = row["text"] or ""
        if not full_text.strip():
            continue

        chunks = chunk_text(full_text, chunk_size=500, overlap=100)

        for idx, (chunk, start, end) in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "meta_id": meta_id,
                    "chunk_index": idx,
                    "start_offset": start,
                    "end_offset": end,
                },
            )
            docs.append(doc)

    return docs

documents = build_documents()

vectorstore = FAISS.from_documents(
    documents,
    embedding=embeddings_model,
    distance_strategy=DistanceStrategy.COSINE,
)

# 로컬에 저장
vectorstore.save_local("faiss_index")

vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings_model,
    allow_dangerous_deserialization=True,  # 여기 그 429 말고 pickle 경고 나왔던 그 옵션
)

#################################### 업데이트 기능 미완성
# def load_new_texts():
#     conn = get_connection()
#     try:
#         with conn.cursor() as cur:
#             sql = """
#             SELECT M.id AS main_id,
#                    M.meta_id,
#                    COALESCE(M.clean_data, M.raw_data) AS text
#             FROM Main AS M
#             WHERE M.updated = 1  -- 새로운 데이터만 가져오는 조건 예시
#             """
#             cur.execute(sql)
#             return cur.fetchall()
#     finally:
#         conn.close()


# def build_new_documents():
#     rows = load_new_texts()
#     documents = []

#     for row in rows:
#         meta_id = row["meta_id"]
#         full_text = row["text"] or ""

#         chunks = chunk_text(full_text)

#         for idx, chunk in enumerate(chunks):
#             doc = Document(
#                 page_content=chunk,
#                 metadata={
#                     "meta_id": meta_id,
#                     "chunk_index": idx
#                 }
#             )
#             documents.append(doc)
    
#     return documents


# def update_faiss_index():
#     embeddings_model = HuggingFaceEmbeddings(
#         model_name='jhgan/ko-sbert-nli',
#         model_kwargs={'device':'cpu'},
#         encode_kwargs={'normalize_embeddings':True},
#     )

#     # 1. 기존 인덱스 로드
#     if os.path.exists("faiss_index/index.faiss"):
#         vectorstore = FAISS.load_local(
#             "faiss_index",
#             embeddings_model,
#             allow_dangerous_deserialization=True
#         )
#         print("기존 인덱스 로드 완료")
#     else:
#         # 없으면 새로 생성
#         print("인덱스 없음 → 새로 생성합니다.")
#         docs = build_documents()
#         vectorstore = FAISS.from_documents(
#             docs,
#             embedding=embeddings_model,
#             distance_strategy=DistanceStrategy.COSINE
#         )
#         vectorstore.save_local("faiss_index")
#         return

#     # 2. 신규 Document 생성
#     new_docs = build_new_documents()
#     if not new_docs:
#         print("추가할 새로운 문서 없음")
#         return

#     print(f"{len(new_docs)}개의 신규 문서를 추가합니다.")

#     # 3. 인덱스 업데이트
#     vectorstore.add_documents(
#         new_docs,
#         embedding=embeddings_model
#     )

#     # 4. 저장
#     vectorstore.save_local("faiss_index")
#     print("FAISS 인덱스 업데이트 완료")
