from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: str
    phone_number: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str