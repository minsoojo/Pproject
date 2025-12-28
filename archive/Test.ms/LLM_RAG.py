from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA

prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 전문 검색 기반 어시스턴트입니다."),
    ("human", "{question}")
])

qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt}
)

resp = qa.invoke({"question": "가천대학교 컴공 졸업 요건 알려줘"})
print(resp)
