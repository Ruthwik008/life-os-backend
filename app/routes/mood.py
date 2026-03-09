from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date

from app.db.session import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/mood", tags=["Mood Tracker"])

@router.post("/")
def log_mood(
    mood: str,
    energy_level: str,
    note: str = None,
    log_date: date = date.today(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        INSERT INTO mood_logs (
            user_id,
            mood,
            energy_level,
            note,
            log_date
        )
        VALUES (
            :user_id,
            :mood,
            :energy_level,
            :note,
            :log_date
        )
        ON CONFLICT (user_id, log_date)
        DO UPDATE SET
            mood = EXCLUDED.mood,
            energy_level = EXCLUDED.energy_level,
            note = EXCLUDED.note
        """),
        {
            "user_id": current_user["id"],
            "mood": mood,
            "energy_level": energy_level,
            "note": note,
            "log_date": log_date
        }
    )

    db.commit()

    return {"message": "Mood logged successfully"}

@router.get("/history")
def mood_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT
            mood,
            energy_level,
            note,
            log_date
        FROM mood_logs
        WHERE user_id = :user_id
        ORDER BY log_date DESC
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    moods = [dict(row._mapping) for row in result]

    return {"mood_history": moods}

@router.get("/analytics")
def mood_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT
            mood,
            COUNT(*) AS count
        FROM mood_logs
        WHERE user_id = :user_id
        GROUP BY mood
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    analytics = [dict(row._mapping) for row in result]

    return {"analytics": analytics}

@router.get("/today")
def get_today_mood(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT
            mood,
            energy_level,
            note
        FROM mood_logs
        WHERE user_id = :user_id
        AND log_date = CURRENT_DATE
        """),
        {"user_id": current_user["id"]}
    ).fetchone()

    if not result:
        return {"message": "No mood logged today"}

    return dict(result._mapping)

@router.delete("/{log_date}")
def delete_mood(
    log_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        DELETE FROM mood_logs
        WHERE user_id = :user_id
        AND log_date = :log_date
        """),
        {
            "user_id": current_user["id"],
            "log_date": log_date
        }
    )

    db.commit()

    return {"message": "Mood entry deleted"}
