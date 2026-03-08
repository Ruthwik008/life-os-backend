from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

from app.db.session import SessionLocal
from app.utils.email import send_email_notification
from app.utils.reminder_time import calculate_next_send_time


def check_reminders():

    db = SessionLocal()

    try:

        # fetch reminders ready to trigger
        reminders = db.execute(
            text("""
            SELECT *
            FROM reminders
            WHERE
                is_active = TRUE
                AND (
                    (snooze_until IS NOT NULL AND snooze_until <= NOW())
                    OR
                    (snooze_until IS NULL AND next_send_time <= NOW())
                )
            """)
        ).fetchall()

        for reminder in reminders:

            reminder_data = dict(reminder._mapping)

            user_id = reminder_data["user_id"]
            title = reminder_data["title"]

            # create notification entry
            db.execute(
                text("""
                INSERT INTO notifications (
                    user_id,
                    title,
                    message,
                    notification_type
                )
                VALUES (
                    :user_id,
                    :title,
                    :message,
                    'REMINDER'
                )
                """),
                {
                    "user_id": user_id,
                    "title": title,
                    "message": f"Reminder: {title}"
                }
            )

            # send email
            send_email_notification(user_id, title)

            # escalation logic
            if reminder_data["priority"] in ("HIGH", "CRITICAL"):

                if reminder_data["retry_count"] < reminder_data["max_retries"]:

                    db.execute(
                        text("""
                        UPDATE reminders
                        SET
                            retry_count = retry_count + 1,
                            next_send_time = NOW() + (retry_interval * INTERVAL '1 minute'),
                            last_sent_at = NOW()
                        WHERE id = :id
                        """),
                        {"id": reminder_data["id"]}
                    )

                else:

                    db.execute(
                        text("""
                        UPDATE reminders
                        SET retry_count = 0
                        WHERE id = :id
                        """),
                        {"id": reminder_data["id"]}
                    )

            # normal reminder flow
            else:

                next_time = calculate_next_send_time(reminder_data)

                db.execute(
                    text("""
                    UPDATE reminders
                    SET
                        next_send_time = :next_time,
                        snooze_until = NULL,
                        last_sent_at = NOW()
                    WHERE id = :id
                    """),
                    {
                        "next_time": next_time,
                        "id": reminder_data["id"]
                    }
                )

        db.commit()

    finally:

        db.close()


scheduler = BackgroundScheduler()


def start_scheduler():

    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=1
    )

    scheduler.start()

    print("Reminder scheduler started")