from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from . import models, auth
from .database import engine, get_session
from .auth_routes import router as auth_router

# Create tables
# Note: In production, you would use Alembic migrations, not create_all.
# But for development, we can use this to create tables if they don't exist.
# However, since we are using Alembic, we should not use create_all.
# We'll comment it out and rely on Alembic.
# models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Testing Platform API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/test-student")
async def test_student(student: models.Student = Depends(auth.get_current_student)):
    return student


@app.get("/test-teacher")
async def test_teacher(teacher: models.Teacher = Depends(auth.get_current_teacher)):
    return teacher