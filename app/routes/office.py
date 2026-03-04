from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/office", tags=["Office"])

@router.post("/start")
def start_work(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # check if user already started work
    active_session = db.execute(
        text("""
        SELECT id
        FROM login_sessions
        WHERE user_id = :user_id
        AND logout_time IS NULL
        """),
        {"user_id": current_user["id"]}
    ).fetchone()

    if active_session:
        raise HTTPException(status_code=400, detail="Work session already active")

    db.execute(
        text("""
        INSERT INTO login_sessions (user_id, login_time)
        VALUES (:user_id, NOW())
        """),
        {"user_id": current_user["id"]}
    )

    db.commit()

    return {"message": "Work started successfully"}

@router.post("/end")
def end_work(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    result = db.execute(
        text("""
        UPDATE login_sessions
        SET logout_time = NOW()
        WHERE user_id = :user_id
        AND logout_time IS NULL
        RETURNING id
        """),
        {"user_id": current_user["id"]}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=400, detail="No active work session")

    db.commit()

    return {"message": "Work ended successfully"}

@router.get("/status")
def get_work_status(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    result = db.execute(
        text("""
        SELECT login_time
        FROM login_sessions
        WHERE user_id = :user_id
        AND logout_time IS NULL
        """),
        {"user_id": current_user["id"]}
    ).fetchone()

    if not result:
        return {
            "working": False,
            "message": "User not currently working"
        }

    login_time = result.login_time

    duration = db.execute(
        text("""
        SELECT NOW() - :login_time AS duration
        """),
        {"login_time": login_time}
    ).fetchone()

    return {
        "working": True,
        "login_time": login_time,
        "duration": str(duration.duration)
    }

@router.get("/history")
def get_work_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    result = db.execute(
        text("""
        SELECT
            login_time,
            logout_time,
            COALESCE(logout_time, NOW()) - login_time AS duration
        FROM login_sessions
        WHERE user_id = :user_id
        ORDER BY login_time DESC
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    history = []

    for row in result:
        history.append({
            "login_time": row.login_time,
            "logout_time": row.logout_time,
            "duration": str(row.duration)
        })

    return {"history": history}