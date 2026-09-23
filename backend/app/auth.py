import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Cookie, Response
from jose import JWTError, jwt
import bcrypt
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

logger = logging.getLogger(__name__)

load_dotenv()  # take environment variables from .env.

from . import models
from .database import get_session

# These should be read from environment variables
SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def get_student_by_name_and_test(db: AsyncSession, full_name: str, access_code: str):
    # Find test by access_code
    result = await db.execute(select(models.Test).where(models.Test.access_code == access_code))
    test = result.scalars().first()
    if not test:
        return None, None  # test not found

    # Find or create student with this full_name
    result = await db.execute(select(models.Student).where(models.Student.full_name == full_name))
    student = result.scalars().first()
    if not student:
        # Create student (group can be default or from somewhere else; we'll set a default)
        student = models.Student(full_name=full_name, group="default")
        db.add(student)
        await db.flush()  # to get the id

    # Associate student with test (via association table)
    # Check if already associated
    stmt = select(models.student_test_association).where(
        models.student_test_association.c.student_id == student.id,
        models.student_test_association.c.test_id == test.id
    )
    result = await db.execute(stmt)
    association = result.first()
    if not association:
        # Insert association
        await db.execute(
            insert(models.student_test_association).values(
                student_id=student.id,
                test_id=test.id,
                enrolled_at=datetime.utcnow()
            )
        )
    await db.commit()
    return student, test


async def authenticate_teacher(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(models.Teacher).where(models.Teacher.email == email))
    teacher = result.scalars().first()
    if not teacher:
        return False
    if not verify_password(password, teacher.password_hash):
        return False
    return teacher


async def authenticate_student(db: AsyncSession, username: str, password: str):
    result = await db.execute(select(models.Student).where(models.Student.username == username.strip().lower()))
    student = result.scalars().first()
    if not student or not student.password_hash:
        return False
    if not verify_password(password, student.password_hash):
        return False
    return student


def set_jwt_cookie(response: Response, token: str):
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        # secure=True,  # in production
        samesite="lax",
        path="/",
        domain="localhost",
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user_from_token(token: str = Cookie(None)):
    logger.debug(f"get_current_user_from_token: token received: {token}")
    if token is None:
        logger.debug("get_current_user_from_token: No token cookie found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        role: str = payload.get("role")
        test_id: Optional[int] = payload.get("test_id")
        logger.debug(f"get_current_user_from_token: payload: {payload}")
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": user_id, "role": role, "test_id": test_id}
    except JWTError as e:
        logger.debug(f"get_current_user_from_token: JWTError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    """Return the current user (Student or Teacher) based on JWT token."""
    logger.debug(f"get_current_user: token from cookie: {token}")
    user_data = get_current_user_from_token(token)
    logger.debug(f"get_current_user: user_data: {user_data}")
    if user_data["role"] == "student":
        result = await db.execute(select(models.Student).where(models.Student.id == user_data["user_id"]))
        student = result.scalars().first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Student not found",
            )
        return student
    elif user_data["role"] == "teacher":
        result = await db.execute(select(models.Teacher).where(models.Teacher.id == user_data["user_id"]))
        teacher = result.scalars().first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Teacher not found",
            )
        return teacher
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user role",
        )


async def get_current_student(
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    user = await get_current_user(token, db)
    if not isinstance(user, models.Student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a student",
        )
    return user


async def get_current_teacher(
    token: str = Cookie(None),
    db: AsyncSession = Depends(get_session)
):
    user = await get_current_user(token, db)
    if not isinstance(user, models.Teacher):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a teacher",
        )
    return user
