from langchain_community.document_loaders import UnstructuredPDFLoader

pdf_filepath = '000660_SK_2023.pdf'

# 전체 텍스트를 단일 문서 객체로 변환
loader = UnstructuredPDFLoader(pdf_filepath)
pages = loader.load()

len(pages)