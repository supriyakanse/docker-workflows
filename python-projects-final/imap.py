import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(EMAIL_USER, EMAIL_PASSWORD)
mail.select("inbox")

status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()

print(f"Found {len(email_ids)} emails in inbox.")
