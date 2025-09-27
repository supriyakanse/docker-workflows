# summarize.py - Using FREE OpenRouter
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain_community.llms import GPT4All

# Get your FREE API key from https://openrouter.ai/settings/keys
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

def summarize_emails(emails, bullets=20):
    if not OPENROUTER_KEY:
        return "Please set OPENROUTER_API_KEY in your .env file. Get a free key at https://openrouter.ai/settings/keys"
    
    # Prepare combined email text
    parts = []
    for e in emails:
        body = e.get("body", "") or ""
        if len(body) > 800:
            body = body[:800] + " ... (truncated)"
        parts.append(f"From: {e['from']}\nSubject: {e['subject']}\nBody:\n{body}")

    combined = "\n\n---\n\n".join(parts) if parts else "No emails."

    # Use FREE OpenRouter model - DeepSeek R1 is free and powerful!
    llm = GPT4All(
        model="mistral-7b-instruct-v0.1.Q4_0.gguf"
        # api_key=OPENROUTER_KEY,
        # base_url="https://openrouter.ai/api/v1",
        # temperature=0,
        # max_tokens=800
    )

    template = """You are an assistant that reads emails and creates concise summaries.

Create exactly {bullets} bullet points that summarize the important information from these emails. Each bullet should be one clear, actionable sentence.

If there's nothing important, just say "No important emails today."

Emails:
{emails}

Summary bullets:"""

    prompt = PromptTemplate(input_variables=["emails", "bullets"], template=template)
    
    chain = prompt | llm
    
    try:
        result = chain.invoke({"emails": combined, "bullets": bullets})
        return result.content if hasattr(result, 'content') else str(result)
    except Exception as e:
        return f"Error: {str(e)}. Make sure you have a valid OpenRouter API key."