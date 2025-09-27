from langchain_openai import ChatOpenAI
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# Initialize LLM
llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",
    openai_api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    max_tokens=500
)

# Use local embeddings (no API key needed)
embeddings = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# Documents
docs = [
    "Python is a high-level programming language used for web development, AI, and scripting.",
    "LangChain is a framework to build LLM applications with chains, prompts, agents, and memory.",
    "RAG stands for Retrieval-Augmented Generation: use documents + LLM to answer questions accurately."
]

print("Creating embeddings...")
vectorstore = FAISS.from_texts(docs, embeddings)

print("Setting up retrieval chain...")
retriever = vectorstore.as_retriever()

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff"
    # return_source_documents=True
)

query = "What is Node?"
print(f"Question: {query}")
print("Generating answer...")
answer = qa_chain.run(query)
print(f"Answer: {answer}")