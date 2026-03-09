from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/places", tags=["Places To Visit"])

@router.post("/")
def add_place(
    place_name: str,
    iframe_url: str,
    category: str = None,
    note: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        INSERT INTO places_to_visit (
            user_id,
            place_name,
            iframe_url,
            category,
            note
        )
        VALUES (
            :user_id,
            :place_name,
            :iframe_url,
            :category,
            :note
        )
        """),
        {
            "user_id": current_user["id"],
            "place_name": place_name,
            "iframe_url": iframe_url,
            "category": category,
            "note": note
        }
    )

    db.commit()

    return {"message": "Place added successfully"}

@router.get("/")
def get_places(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT
            id,
            place_name,
            iframe_url,
            category,
            note,
            created_at
        FROM places_to_visit
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    places = [dict(row._mapping) for row in result]

    return {"places": places}

@router.delete("/{place_id}")
def delete_place(
    place_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        DELETE FROM places_to_visit
        WHERE id = :place_id
        AND user_id = :user_id
        """),
        {
            "place_id": place_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Place deleted"}

@router.patch("/{place_id}/visited") # Mark Place as Visited
def mark_place_visited(
    place_id: str,
    visited: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    db.execute(
        text("""
        UPDATE places_to_visit
        SET visited = :visited
        WHERE id = :place_id
        AND user_id = :user_id
        """),
        {
            "visited": visited,
            "place_id": place_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Place visit status updated"}



