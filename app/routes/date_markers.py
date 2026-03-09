from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/date-markers", tags=["Date Markers"])


@router.post("/")# CREATE DATE MARKER
def create_date_marker(
    title: str,
    event_date: str,
    notify_before_days: int = 0,
    category: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        INSERT INTO date_markers (
            user_id,
            title,
            event_date,
            notify_before_days,
            category
        )
        VALUES (
            :user_id,
            :title,
            :event_date,
            :notify_before_days,
            :category
        )
        """),
        {
            "user_id": current_user["id"],
            "title": title,
            "event_date": event_date,
            "notify_before_days": notify_before_days,
            "category": category
        }
    )

    db.commit()

    return {"message": "Date marker created successfully"}

@router.get("/")# GET ALL DATE MARKERS
def get_date_markers(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT *
        FROM date_markers
        WHERE user_id = :user_id
        ORDER BY event_date
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    markers = [dict(row._mapping) for row in result]

    return {"date_markers": markers}

@router.delete("/{marker_id}")# DELETE DATE MARKER
def delete_date_marker(
    marker_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        DELETE FROM date_markers
        WHERE id = :marker_id
        AND user_id = :user_id
        """),
        {
            "marker_id": marker_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Date marker deleted"}