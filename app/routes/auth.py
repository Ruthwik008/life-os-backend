from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import hash_password, verify_password, create_access_token
from uuid import uuid4
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import verify_access_token
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from app.schemas.user import LoginRequest

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):

    # 🔍 Check if email already exists
    result = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": user_data.email}
    ).fetchone()

    if result:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🧂 Hash password
    hashed_password = hash_password(user_data.password)

    # 🆕 Insert new user
    user_id = str(uuid4())

    db.execute(
        text("""
            INSERT INTO users (
            
                id, name, email, phone_number, password_hash
            )
            VALUES (
                :id, :name, :email, :phone_number, :password_hash
            )
        """),
        {
            "id": user_id,
            "name": user_data.name,
            "email": user_data.email,
            "phone_number": user_data.phone_number,
            "password_hash": hashed_password
        }
    )

    db.commit()

    return {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email
    }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login", response_model=Token)
def login(user_data: LoginRequest, db: Session = Depends(get_db)):

    result = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": user_data.email}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_dict = dict(result._mapping)

    if not verify_password(user_data.password, user_dict["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user_dict["id"])})

    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user_id = verify_access_token(token)

    user = db.execute(
        text("SELECT * FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.delete("/users/me")
def delete_user(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.execute(
        text("DELETE FROM users WHERE id = :id"),
        {"id": current_user.id}
    )
    db.commit()

    return {"message": "User deleted successfully"}

@router.get("/me")
def get_current_user_info(current_user = Depends(get_current_user)):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }

