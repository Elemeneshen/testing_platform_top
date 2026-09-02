from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from . import auth, schemas
from .database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/student-login")
async def student_login(
    response: Response,
    credentials: schemas.StudentLogin,
    db: AsyncSession = Depends(get_session)
):
    student, test = await auth.get_student_by_name_and_test(
        db, credentials.full_name, credentials.access_code
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid full name or access code",
        )
    # Create JWT token
    access_token = auth.create_access_token(
        data={"sub": student.id, "role": "student", "test_id": test.id}
    )
    auth.set_jwt_cookie(response, access_token)
    return {"message": "Login successful"}


@router.post("/teacher-login")
async def teacher_login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
):
    teacher = await auth.authenticate_teacher(db, form_data.username, form_data.password)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": teacher.id, "role": "teacher"}
    )
    auth.set_jwt_cookie(response, access_token)
    return {"message": "Login successful"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out"}


# Dependencies for protected routes
get_current_student = auth.get_current_student
get_current_teacher = auth.get_current_teacher