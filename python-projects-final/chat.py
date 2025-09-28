# chat.py
from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import GPT4All
from vectorstore import load_vectorstore

def make_chatbot():
    vs = load_vectorstore()
    llm = GPT4All(model="mistral-7b-instruct-v0.1.Q4_0.gguf", allow_download=True)

    chat = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vs.as_retriever(search_kwargs={"k": 2}),
        return_source_documents=True,
    )
    return chat
