from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_community.embeddings import HuggingFaceEmbeddings
import pymysql
import os

from langchain_services import chunk_text, get_connection, load_texts_from_db, build_documents

# loader = TextLoader('02957-test-result-v3.txt')
# data = loader.load()

# text = data[0].page_content

embeddings_model = HuggingFaceEmbeddings(
    model_name='jhgan/ko-sbert-nli',
    model_kwargs={'device':'cpu'},
    encode_kwargs={'normalize_embeddings':True},
)

if not os.path.exists("faiss_index/index.faiss"):
    documents = build_documents()

    vectorstore = FAISS.from_documents(
        documents,
        embedding=embeddings_model,
        distance_strategy=DistanceStrategy.COSINE,
    )
else:
    vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings_model,
    allow_dangerous_deserialization=True,  # 여기 그 429 말고 pickle 경고 나왔던 그 옵션
)

# 로컬에 저장
vectorstore.save_local("faiss_index")

