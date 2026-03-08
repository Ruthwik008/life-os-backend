from pydantic import BaseModel
from typing import Optional


class ReminderCreate(BaseModel):
    title: str
    reminder_type: str
    reminder_time: Optional[str] = None
    reminder_days: Optional[str] = None
    reminder_date: Optional[str] = None
    priority: str = "MEDIUM"
    timezone: str = "Asia/Kolkata"


class ReminderResponse(BaseModel):
    id: str
    user_id: str
    title: str
    reminder_type: str
    reminder_time: Optional[str]
    reminder_days: Optional[str]
    reminder_date: Optional[str]
    priority: str
    timezone: str
    next_send_time: str
    is_active: bool
    created_at: str
