import smtplib
from email.mime.text import MIMEText
from sqlalchemy import text
from app.db.session import SessionLocal


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
        msg["From"] = "your_email@gmail.com"
        msg["To"] = email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        server.login("your_email@gmail.com", "your_app_password")

        server.send_message(msg)

        server.quit()

    finally:

        db.close()