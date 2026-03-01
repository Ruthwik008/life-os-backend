from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import hash_password, verify_password, create_access_token
from uuid import uuid4

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

@router.post("/login", response_model=Token)
def login(email: str, password: str, db: Session = Depends(get_db)):

    result = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_dict = dict(result._mapping)

    if not verify_password(password, user_dict["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user_dict["id"]})

    return {"access_token": access_token, "token_type": "bearer"}