# rag_chain.py
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

class RAGBot:
    def __init__(self, vectorstore, model=os.getenv('DEPLOYMENT_NAME')):
        self.llm = AzureChatOpenAI(
            azure_deployment=model,
            api_version=os.getenv("API_VERSION"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_API_KEY"),
            temperature=0.3
        )
        self.vectorstore = vectorstore
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
        self.qa_chain = self._create_chain()
    
    def _create_chain(self):
        """Create the RAG chain using LCEL"""
        
        # Custom prompt template
        template = """You are a helpful assistant. Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Answer: """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Create RAG chain using LCEL
        chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain
    
    def ask(self, question):
        """Ask a question and get an answer"""
        answer = self.qa_chain.invoke(question)
        sources = self.retriever.invoke(question)
        
        return {
            "answer": answer,
            "sources": sources
        }

# Advanced: Conversational RAG with memory


class ConversationalRAGBot:
    def __init__(self, vectorstore, model=os.getenv('DEPLOYMENT_NAME')):
        self.llm = AzureChatOpenAI(
            azure_deployment=model,
            api_version=os.getenv("API_VERSION"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_API_KEY"),
            temperature=0.3
        )
        self.vectorstore = vectorstore
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
        self.session_histories = {}  # Store chat history per session
        self.qa_chain = self._create_chain()
    
    def _create_chain(self):
        """Create conversational RAG chain using LCEL"""
        
        template = """You are a helpful assistant. Use the following pieces of context and chat history to answer the question. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Chat History:
        {chat_history}
        
        Context: {context}
        
        Question: {question}
        
        Answer: """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        def format_chat_history(history):
            if not history:
                return "No previous conversation"
            formatted = []
            for msg in history:
                if isinstance(msg, HumanMessage):
                    formatted.append(f"Human: {msg.content}")
                elif isinstance(msg, AIMessage):
                    formatted.append(f"Assistant: {msg.content}")
            return "\n".join(formatted)
        
        # Create conversational RAG chain using LCEL
        chain = (
            {
                "context": lambda x: format_docs(self.retriever.invoke(x["question"])),
                "chat_history": lambda x: format_chat_history(x["chat_history"]),
                "question": lambda x: x["question"]
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain
    
    def chat(self, question, session_id=None):
        """Have a conversation with session-based memory"""
        # Use session_id to manage separate conversation histories
        if session_id is None:
            session_id = "default"
        
        # Initialize session history if not exists
        if session_id not in self.session_histories:
            self.session_histories[session_id] = []
        
        chat_history = self.session_histories[session_id]
        
        answer = self.qa_chain.invoke({
            "question": question,
            "chat_history": chat_history
        })
        sources = self.retriever.invoke(question)
        
        # Update chat history for this session
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=answer))
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    def clear_session(self, session_id):
        """Clear chat history for a specific session"""
        if session_id in self.session_histories:
            del self.session_histories[session_id]
    
    def clear_all_sessions(self):
        """Clear all session histories"""
        self.session_histories = {}