from fastapi import FastAPI
from app.vector_store import vectorstore
from app.llm import llm
from langchain_core.documents import Document

app = FastAPI(title="Python GenAI Bot")

@app.post("/ingest")
def ingest(text: str):
    doc = Document(page_content=text)
    vectorstore.add_documents([doc])
    return {"status": "stored"}
@app.get("/ask")
def ask(question: str):
    docs = vectorstore.similarity_search(question, k=3)

    context = "\n".join(d.page_content for d in docs)

    prompt = f"""
    Use the context below to answer the question.

    Context:
    {context}

    Question:
    {question}
    """

    response = llm.invoke(prompt)
    return {"answer": response.content}


#docker compose down
#docker compose up --build -d