# Updated server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from email_chain import make_email_chain

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the chain once
email_chain = make_email_chain()

class Question(BaseModel):
    question: str

@app.post("/chat")
def chat_api(q: Question):
    """Single endpoint that handles everything: fetch → build → chat"""
    result = email_chain({"question": q.question})
    return {
        "answer": result["answer"],
        
    }

@app.get("/health")
def health():
    return {"status": "ok"}