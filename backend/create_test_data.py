import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app import models, auth

async def create_teacher_and_test():
    async with AsyncSessionLocal() as session:
        # Check if teacher already exists
        result = await session.execute(select(models.Teacher).where(models.Teacher.email == "teacher@example.com"))
        teacher = result.scalars().first()
        if not teacher:
            teacher = models.Teacher(
                email="teacher@example.com",
                password_hash=auth.get_password_hash("password123")
            )
            session.add(teacher)
            await session.flush()
            print(f"Created teacher with id {teacher.id}")
        else:
            print(f"Teacher already exists with id {teacher.id}")

        # Check if test already exists for this teacher
        result = await session.execute(select(models.Test).where(models.Test.access_code == "TEST123"))
        test = result.scalars().first()
        if not test:
            test = models.Test(
                title="Test Test",
                access_code="TEST123",
                created_by=teacher.id
            )
            session.add(test)
            await session.flush()
            print(f"Created test with id {test.id} for teacher {teacher.id}")
        else:
            print(f"Test already exists with id {test.id}")

        await session.commit()

if __name__ == "__main__":
    asyncio.run(create_teacher_and_test())