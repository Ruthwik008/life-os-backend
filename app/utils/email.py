import smtplib
from email.mime.text import MIMEText
from sqlalchemy import text
from app.db.session import SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_email_notification(user_id, reminder_title):

    db = SessionLocal()

    try:

        user = db.execute(
            text("SELECT email FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not user:
            return

        email = user._mapping["email"]

        msg = MIMEText(f"Reminder: {reminder_title}")
        msg["Subject"] = "LifeOS Reminder"
        msg["From"] = SMTP_EMAIL
        msg["To"] = email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        server.login(SMTP_EMAIL, SMTP_PASSWORD)

        server.send_message(msg)

        server.quit()

    finally:

        db.close()