# main.py
import argparse
import datetime
import json
import os
# summarize.py
from langchain_community.llms import GPT4All

from fetch_emails import fetch_emails_since
from vectorstore import build_vectorstore_from_emails
from summarize import summarize_emails
from query import ask, did_receive_from

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Fetch today's emails and save to data/")
    parser.add_argument("--build", action="store_true", help="Build FAISS vector store from fetched emails")
    parser.add_argument("--summarize", action="store_true", help="Summarize today's emails into 5 bullets")
    parser.add_argument("--ask", type=str, help="Ask a question to the QA system (retrieval)")
    parser.add_argument("--from", dest="from_query", type=str, help="Check if email from this name/email arrived today")
    args = parser.parse_args()

    today = datetime.date.today()
    data_fname = f"data/emails_{today.isoformat()}.json"

    if args.fetch:
        emails = fetch_emails_since(today)
        print(f"Fetched {len(emails)} emails. Saved to {data_fname}")

    if args.build:
        if not os.path.exists(data_fname):
            print("No emails JSON found for today. Run --fetch first.")
        else:
            with open(data_fname, "r", encoding="utf-8") as f:
                emails = json.load(f)
            build_vectorstore_from_emails(emails)
            print("Built vectorstore at faiss_index/")

    if args.summarize:
        if not os.path.exists(data_fname):
            print("No emails JSON found for today. Run --fetch first.")
        else:
            with open(data_fname, "r", encoding="utf-8") as f:
                emails = json.load(f)
            summary = summarize_emails(emails, bullets=5)
            print("\n=== SUMMARY ===\n")
            print(summary)
            print("\n===============")

    if args.ask:
        print("Answer:\n")
        print(ask(args.ask))

    if args.from_query:
        found, matches = did_receive_from(args.from_query, today)
        print("Found:", found)
        if matches:
            print("Matches:")
            for m in matches:
                print("-", m.get("subject"), "|", m.get("from"))

if __name__ == "__main__":
    main()
