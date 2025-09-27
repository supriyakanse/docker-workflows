# fetch_emails.py
import imaplib
import email
import os
import datetime
import json
import re
from email.header import decode_header
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("EMAIL_IMAP_PORT", 993))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")


def _decode_mime_words(value):
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded += part.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += part
    return decoded


def _get_body(msg):
    # prefer text/plain, fallback to text/html
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            dispo = str(part.get("Content-Disposition"))
            if ctype == "text/plain" and "attachment" not in dispo:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="ignore")
        # fallback to HTML
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    soup = BeautifulSoup(payload, "html.parser")
                    return soup.get_text("\n")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(errors="ignore")
    return ""


def fetch_emails_since(date=None, mailbox="INBOX"):
    """Fetch emails since given date (date is a datetime.date). Defaults to today."""
    if date is None:
        date = datetime.date.today()
    date_str = date.strftime("%d-%b-%Y")  # IMAP date format
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    imap.login(EMAIL_USER, EMAIL_PASS)
    imap.select(mailbox)

    typ, data = imap.search(None, f'(SINCE "{date_str}")')
    emails = []
    if data and data[0]:
        for num in data[0].split():
            typ, msg_data = imap.fetch(num, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject = _decode_mime_words(msg.get("Subject"))
            frm = _decode_mime_words(msg.get("From"))
            date_hdr = _decode_mime_words(msg.get("Date"))
            body = _get_body(msg) or ""

            # try to extract an email address from the From header
            m = re.search(r"<([^>]+)>", frm)
            sender_email = m.group(1) if m else (re.search(r"[\w\.-]+@[\w\.-]+", frm).group(0) if re.search(r"[\w\.-]+@[\w\.-]+", frm) else None)

            emails.append({
                "uid": num.decode() if isinstance(num, bytes) else str(num),
                "date": date_hdr,
                "from": frm,
                "sender_email": sender_email,
                "subject": subject,
                "body": body
            })

    imap.close()
    imap.logout()

    os.makedirs("data", exist_ok=True)
    fname = f"data/emails_{date.isoformat()}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)

    return emails


if __name__ == "__main__":
    emails = fetch_emails_since()
    print(f"Fetched {len(emails)} emails. Saved to data/emails_{datetime.date.today().isoformat()}.json")
    if emails:
        print("Sample:")
        print("-", emails[0]["subject"], "|", emails[0]["from"])
