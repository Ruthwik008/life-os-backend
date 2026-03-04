from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.post("/")
def create_task(
    title: str,
    description: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db.execute(
        text("""
        INSERT INTO tasks (user_id, title, description)
        VALUES (:user_id, :title, :description)
        """),
        {
            "user_id": current_user["id"],
            "title": title,
            "description": description
        }
    )

    db.commit()

    return {"message": "Task created successfully"}

@router.post("/")
def create_task(

    title: str,
    description: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db.execute(
        text("""
        INSERT INTO tasks (user_id, title, description)
        VALUES (:user_id, :title, :description)
        """),
        {
            "user_id": current_user["id"],
            "title": title,
            "description": description
        }
    )

    db.commit()

    return {"message": "Task created successfully"}

@router.get("/")
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT *
        FROM tasks
        WHERE user_id = :user_id
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    tasks = [dict(row._mapping) for row in result]

    return {"tasks": tasks}

@router.post("/{task_id}/done")
def mark_task_done(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        INSERT INTO task_logs (task_id, log_date, status, completed_at)
        VALUES (:task_id, CURRENT_DATE, 'DONE', NOW())
        ON CONFLICT (task_id, log_date)
        DO UPDATE SET
            status='DONE',
            completed_at=NOW()
        """),
        {"task_id": task_id}
    )

    db.commit()

    return {"message": "Task marked as done"}

@router.post("/{task_id}/progress")
def add_progress(
    task_id: str,
    progress_value: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        INSERT INTO task_logs (task_id, log_date, progress_value)
        VALUES (:task_id, CURRENT_DATE, :progress_value)
        ON CONFLICT (task_id, log_date)
        DO UPDATE SET
            progress_value = task_logs.progress_value + :progress_value
        """),
        {
            "task_id": task_id,
            "progress_value": progress_value
        }
    )

    db.commit()

    return {"message": "Progress added"}