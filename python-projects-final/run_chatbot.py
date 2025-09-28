# run_chatbot.py
from chat import make_chatbot

def main():
    chatbot = make_chatbot()
    chat_history = []

    print("📧 Email Chatbot Ready! Ask me anything about your emails.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("You: ")
        if question.lower() in ["exit", "quit"]:
            break

        result = chatbot({"question": question, "chat_history": chat_history})
        answer = result["answer"].strip()
        sources = result.get("source_documents", [])

        # Handle "no info" case more nicely
        if "I couldn’t find anything in today’s emails" in answer:
            print("\nBot: ❌ No relevant info found in today’s emails.\n")
        else:
            print(f"\nBot: {answer}\n")

            if sources:
                print("🔗 Sources:")
                for doc in sources[:2]:  # show top 2 sources
                    meta = doc.metadata
                    print(f"- {meta.get('subject')} ({meta.get('from')})")
                print()

        # update memory
        chat_history.append((question, answer))


if __name__ == "__main__":
    main()
