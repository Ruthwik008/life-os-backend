from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

@router.get("/")#  Get all notifications sent
def get_notifications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT id, message, is_read, created_at
        FROM notifications
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    notifications = [dict(row._mapping) for row in result]

    return {"notifications": notifications}

@router.get("/unread") #Get unread notifications which user has not yet opened 
def get_unread_notifications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT id, message, created_at
        FROM notifications
        WHERE user_id = :user_id
        AND is_read = false
        ORDER BY created_at DESC
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    notifications = [dict(row._mapping) for row in result]

    return {"unread_notifications": notifications}

@router.patch("/{notification_id}/read") # Mark notification as read user has opned it
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    db.execute(
        text("""
        UPDATE notifications
        SET is_read = true
        WHERE id = :notification_id
        AND user_id = :user_id
        """),
        {
            "notification_id": notification_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Notification marked as read"}

@router.delete("/{notification_id}") # Delete notification yet to decide whearther to use this or not
def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    db.execute(
        text("""
        DELETE FROM notifications
        WHERE id = :notification_id
        AND user_id = :user_id
        """),
        {
            "notification_id": notification_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Notification deleted"}