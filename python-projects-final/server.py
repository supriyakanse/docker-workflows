# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime, os, json

from chat import make_chatbot
from fetch_emails import fetch_emails_since
from vectorstore import build_vectorstore_from_emails
from query import ask, did_receive_from

app = FastAPI()

# Enable CORS so Angular can call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot = make_chatbot()

class Question(BaseModel):
    question: str

@app.post("/chat")
def chat_api(q: Question):
    result = chatbot({"question": q.question, "chat_history": []})
    return {"answer": result["answer"]}

@app.get("/fetch")
def fetch():
    today = datetime.date.today()
    emails = fetch_emails_since(today)
    return {"fetched": len(emails)}

@app.get("/build")
def build():
    today = datetime.date.today()
    data_fname = f"data/emails_{today.isoformat()}.json"
    if not os.path.exists(data_fname):
        return {"error": "No emails found. Run fetch first."}
    with open(data_fname, "r", encoding="utf-8") as f:
        emails = json.load(f)
    build_vectorstore_from_emails(emails)
    return {"status": "Vectorstore built"}
