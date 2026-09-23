import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import auth, models, schemas
from .database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/student-login")
async def student_login(
    response: Response,
    credentials: schemas.StudentLogin,
    db: AsyncSession = Depends(get_session)
):
    student = await auth.authenticate_student(db, credentials.username, credentials.password)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    # Create JWT token
    access_token = auth.create_access_token(
        data={"sub": str(student.id), "role": "student"}
    )
    auth.set_jwt_cookie(response, access_token)
    return {"message": "Login successful", "needs_group": student.group_id is None}


@router.post("/student-register", response_model=schemas.StudentProfile, status_code=status.HTTP_201_CREATED)
async def student_register(
    payload: schemas.StudentRegister,
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    username = payload.username.strip().lower()
    existing = await db.execute(select(models.Student.id).where(models.Student.username == username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken")
    student = models.Student(
        username=username,
        password_hash=auth.get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        group_name="unassigned",
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    token = auth.create_access_token(data={"sub": str(student.id), "role": "student"})
    auth.set_jwt_cookie(response, token)
    return schemas.StudentProfile(id=student.id, username=student.username, full_name=student.full_name)


@router.post("/teacher-login")
async def teacher_login(
    response: Response,
    login_data: schemas.TeacherLogin,
    db: AsyncSession = Depends(get_session)
):
    # logger.debug(f"Teacher login request received for email: {login_data.email}")
    teacher = await auth.authenticate_teacher(db, login_data.email, login_data.password)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": str(teacher.id), "role": "teacher"}
    )
    auth.set_jwt_cookie(response, access_token)
    return {"message": "Login successful"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="token", path="/", domain="localhost")
    return {"message": "Logged out"}


# Dependencies for protected routes
get_current_student = auth.get_current_student
get_current_teacher = auth.get_current_teacher
