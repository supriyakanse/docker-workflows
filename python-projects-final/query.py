# query.py
import os
import json
import datetime
import re
from dotenv import load_dotenv
load_dotenv()
# summarize.py
from langchain_community.llms import GPT4All

from langchain.chains import RetrievalQA
from vectorstore import load_vectorstore

def make_qa():
    vs = load_vectorstore()
    llm = GPT4All(model="mistral-7b-instruct-v0.1.Q4_0.gguf", allow_download=True)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vs.as_retriever(search_kwargs={"k": 10})
    )
    return qa

def ask(query_text):
    qa = make_qa()
    return qa.run(query_text)

def did_receive_from(name_or_email, date=None):
    """Check saved emails JSON for a sender match."""
    if date is None:
        date = datetime.date.today()
    fname = f"data/emails_{date.isoformat()}.json"
    if not os.path.exists(fname):
        return False, []

    with open(fname, "r", encoding="utf-8") as f:
        emails = json.load(f)

    pat = re.compile(re.escape(name_or_email), re.IGNORECASE)
    matches = []
    for e in emails:
        if (e.get("sender_email") and pat.search(e["sender_email"])) or pat.search(e.get("from", "")):
            matches.append(e)
    return (len(matches) > 0), matches
