# vectorstore.py
import os
from dotenv import load_dotenv
load_dotenv()

from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import FAISS

EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
PERSIST_DIR = "faiss_index"

def build_vectorstore_from_emails(emails, persist=True):
    texts = []
    metadatas = []
    for e in emails:
        text = f"From: {e['from']}\nDate: {e['date']}\nSubject: {e['subject']}\n\n{e['body']}"
        texts.append(text)
        metadatas.append({
            "from": e["from"],
            "sender_email": e.get("sender_email"),
            "date": e["date"],
            "subject": e["subject"],
            "body": e["body"][:200] 
        })

    embeddings = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)

    if persist:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        vectorstore.save_local(PERSIST_DIR)

    return vectorstore


def load_vectorstore():
    embeddings = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)
    if not os.path.exists(PERSIST_DIR):
        raise FileNotFoundError("Index not found. Run build_vectorstore_from_emails first.")
    return FAISS.load_local(PERSIST_DIR, embeddings,allow_dangerous_deserialization=True)
