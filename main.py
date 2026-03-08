from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from app.db.session import engine, Base, get_db
from app.models import user  # registers model
from app.routes import auth
from app.routes import office
from app.routes import tasks
from app.routes import reminders
from app.scheduler.reminder_scheduler import start_scheduler

#Lifespan handler (modern replacement for on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    Base.metadata.create_all(bind=engine)
    print("Database tables checked/created successfully ")
    start_scheduler()
    yield

    # Shutdown logic (if needed)
    print("Application shutting down...")

app = FastAPI(lifespan=lifespan)

@app.on_event("startup")
def startup_event():
    start_scheduler()

app.include_router(auth.router)
app.include_router(office.router, prefix="/api/v1")
app.include_router(tasks.router)
app.include_router(reminders.router)

@app.get("/") #ondu
def root():
    return {"message": "Life OS Backend Running"}

@app.get("/api/v1/health/db") #eradu
def check_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("select 1"))  # Simple query to test connection
        return {"status": "success", "message": "Database connected successfully "}
    except Exception as e:
        return {"status": "error", "message": str(e)}