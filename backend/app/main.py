from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from . import models, auth
from .database import engine, get_session
from .auth_routes import router as auth_router
from .admin_routes import router as admin_router
from .student_routes import router as student_router
from .task_comments_routes import router as task_comments_router

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
app.include_router(admin_router)
app.include_router(student_router)
app.include_router(task_comments_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}