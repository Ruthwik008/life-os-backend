from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.post("/") #11 task du "1" --create task
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

@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    db.execute(
        text("""
        DELETE FROM tasks
        WHERE id = :task_id
        AND user_id = :user_id
        """),
        {
            "task_id": task_id,
            "user_id": current_user["id"]
        }
    )

    db.commit()

    return {"message": "Task deleted"}

@router.get("/analytics")
def get_task_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # total tasks
    total_tasks = db.execute(
        text("""
        SELECT COUNT(*)
        FROM tasks
        WHERE user_id = :user_id
        """),
        {"user_id": current_user["id"]}
    ).scalar()

    # completed tasks
    completed_tasks = db.execute(
        text("""
        SELECT COUNT(*)
        FROM task_logs tl
        JOIN tasks t ON t.id = tl.task_id
        WHERE t.user_id = :user_id
        AND tl.status = 'DONE'
        """),
        {"user_id": current_user["id"]}
    ).scalar()

    # today's progress
    today_progress = db.execute(
        text("""
        SELECT COALESCE(SUM(progress_value),0)
        FROM task_logs tl
        JOIN tasks t ON t.id = tl.task_id
        WHERE t.user_id = :user_id
        AND tl.log_date = CURRENT_DATE
        """),
        {"user_id": current_user["id"]}
    ).scalar()

    completion_percentage = 0

    if total_tasks > 0:
        completion_percentage = round((completed_tasks / total_tasks) * 100, 2)

    return {
        "total_tasks": total_tasks,
        "tasks_completed": completed_tasks,
        "completion_percentage": completion_percentage,
        "today_progress": today_progress
    }

@router.get("/today")
def get_today_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = db.execute(
        text("""
        SELECT
            t.id,
            t.title,
            t.description,
            tl.status,
            tl.progress_value
        FROM tasks t
        LEFT JOIN task_logs tl
        ON t.id = tl.task_id
        AND tl.log_date = CURRENT_DATE
        WHERE t.user_id = :user_id
        """),
        {"user_id": current_user["id"]}
    ).fetchall()

    tasks = [dict(row._mapping) for row in result]

    return {"tasks": tasks}
    
@router.get("/{task_id}/summary")
def get_task_summary(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # get task info
    task = db.execute(
        text("""
        SELECT id, title, description, target_value, unit
        FROM tasks
        WHERE id = :task_id AND user_id = :user_id
        """),
        {
            "task_id": task_id,
            "user_id": current_user["id"]
        }
    ).fetchone()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_dict = dict(task._mapping)

    # total progress
    total_progress = db.execute(
        text("""
        SELECT COALESCE(SUM(progress_value),0)
        FROM task_logs
        WHERE task_id = :task_id
        """),
        {"task_id": task_id}
    ).scalar()

    # completion percentage
    completion_percentage = 0

    if task_dict["target_value"]:
        completion_percentage = round(
            (total_progress / task_dict["target_value"]) * 100, 2
        )

    # history
    history = db.execute(
        text("""
        SELECT log_date, progress_value
        FROM task_logs
        WHERE task_id = :task_id
        ORDER BY log_date DESC
        """),
        {"task_id": task_id}
    ).fetchall()

    history_list = [
        {
            "date": row.log_date,
            "progress": row.progress_value
        }
        for row in history
    ]

    return {
        "task": task_dict,
        "progress": {
            "total_progress": total_progress,
            "completion_percentage": completion_percentage
        },
        "history": history_list
    }   