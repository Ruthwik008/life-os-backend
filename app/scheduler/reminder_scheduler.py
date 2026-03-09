from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.utils.email import send_email_notification
from app.utils.reminder_time import calculate_next_send_time
import random
from app.utils.mood_setter import messages

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

def check_date_marker_reminders():

    from app.db.session import SessionLocal
    from app.utils.email import send_email_notification

    db = SessionLocal()

    today = datetime.now().date()

    markers = db.execute(
        text("""
        SELECT id, user_id, title, event_date, notify_before_days
        FROM date_markers
        """)
    ).fetchall()

    for marker in markers:

        reminder_date = marker.event_date - timedelta(days=marker.notify_before_days)

        if reminder_date == today:

            message = f"Reminder: {marker.title} on {marker.event_date}"

            # INSERT NOTIFICATION
            db.execute(
                text("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (:user_id, :title, :message)
                """),
                {
                    "user_id": marker.user_id,
                    "title": "Upcoming Event",
                    "message": message
                }
            )

            db.commit()

            # SEND EMAIL
            send_email_notification(marker.user_id, message)

    db.close()

scheduler.add_job(
    check_date_marker_reminders,
    "interval",
    minutes=60
)

def send_motivational_message():

    db = SessionLocal()

    users = db.execute(
        text("SELECT id FROM users")
    ).fetchall()

    message = random.choice(messages)

    for user in users:

        db.execute(
            text("""
            INSERT INTO notifications (user_id, title, message)
            VALUES (:user_id, :title, :message)
            """),
            {
                "user_id": user.id,
                "title": "Daily Motivation",
                "message": message
            }
        )

        send_email_notification(user.id, message)

    db.commit()
    db.close()

scheduler.add_job(
    send_motivational_message,
    "cron",
    hour=8,
    minute=0
)   

scheduler.add_job(
    send_motivational_message,
    "cron",
    hour=21,
    minute=0
)   

def random_motivation_scheduler():

    random_hour = random.randint(10, 18)

    scheduler.add_job(
        send_motivational_message,
        "cron",
        hour=random_hour,
        minute=0
    )

scheduler.add_job(
    random_motivation_scheduler,
    "cron",
    hour=0,
    minute=0
)   


