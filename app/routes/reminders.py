from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.routes.auth import get_current_user
from app.utils.reminder_time import calculate_next_send_time

router = APIRouter(prefix="/api/v1/reminders", tags=["Reminders"])

@router.post("/")
def create_reminder(
    title: str,
    reminder_type: str,
    reminder_time: str = None,
    reminder_days: str = None,
    reminder_date: str = None,
    priority: str = "MEDIUM",
    timezone: str = "Asia/Kolkata",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # prepare reminder data
    reminder_data = {
        "reminder_type": reminder_type,
        "reminder_time": reminder_time,
        "reminder_days": reminder_days,
        "reminder_date": reminder_date,
        "timezone": timezone
    }

    # calculate next reminder time
    next_send_time = calculate_next_send_time(reminder_data)

    # insert reminder
    db.execute(
        text("""
        INSERT INTO reminders (
            user_id,
            title,
            reminder_type,
            reminder_time,
            reminder_days,
            reminder_date,
            priority,
            timezone,
            next_send_time
        )
        VALUES (
            :user_id,
            :title,
            :reminder_type,
            :reminder_time,
            :reminder_days,
            :reminder_date,
            :priority,
            :timezone,
            :next_send_time
        )
        """),
        {
            "user_id": current_user["id"],
            "title": title,
            "reminder_type": reminder_type,
            "reminder_time": reminder_time,
            "reminder_days": reminder_days,
            "reminder_date": reminder_date,
            "priority": priority,
            "timezone": timezone,
            "next_send_time": next_send_time
        }
    )

    db.commit()

    return {"message": "Reminder created successfully"}

@router.get("/")
def get_reminders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT *
        FROM reminders
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    reminders = [dict(row._mapping) for row in result]

    return {"reminders": reminders}

@router.patch("/{reminder_id}")#uodate reminder 
def update_reminder(
    reminder_id: str,
    title: str,
    reminder_time: str,
    priority: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        UPDATE reminders
        SET
            title = :title,
            reminder_time = :reminder_time,
            priority = :priority
        WHERE id = :reminder_id
        AND user_id = :user_id
        """),
        {
            "title": title,
            "reminder_time": reminder_time,
            "priority": priority,
            "reminder_id": reminder_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Reminder updated"}

@router.delete("/{reminder_id}") 
def delete_reminder(
    reminder_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        DELETE FROM reminders
        WHERE id = :reminder_id
        AND user_id = :user_id
        """),
        {
            "reminder_id": reminder_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Reminder deleted"}

@router.post("/{reminder_id}/snooze")
def snooze_reminder(
    reminder_id: str,
    minutes: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        UPDATE reminders
        SET snooze_until = NOW() + (:minutes * INTERVAL '1 minute')
        WHERE id = :reminder_id
        AND user_id = :user_id
        """),
        {
            "minutes": minutes,
            "reminder_id": reminder_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Reminder snoozed"}

