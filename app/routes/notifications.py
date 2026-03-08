from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

@router.get("/")
def get_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT *
        FROM notifications
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    notifications = [dict(row._mapping) for row in result]

    return {"notifications": notifications}