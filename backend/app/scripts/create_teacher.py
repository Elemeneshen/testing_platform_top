#!/usr/bin/env python3
"""
CLI script to create the first teacher (admin) account.
Usage:
    python -m app.scripts.create_teacher --email admin@example.com --password secret
"""
import argparse
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import from the app package
from ..auth import get_password_hash
from .. import models
from ..database import get_session


async def create_teacher(email: str, password: str) -> None:
    """Create a teacher if not exists."""
    # Get an async session
    async for session in get_session():
        # Check if teacher with this email already exists
        result = await session.execute(select(models.Teacher).where(models.Teacher.email == email))
        existing = result.scalars().first()
        if existing:
            print(f"Teacher with email '{email}' already exists. Aborting.")
            return

        # Hash the password
        hashed_password = get_password_hash(password)

        # Create new teacher
        teacher = models.Teacher(email=email, password_hash=hashed_password)
        session.add(teacher)
        await session.commit()
        await session.refresh(teacher)
        print(f"Teacher created successfully with ID: {teacher.id}")
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a teacher account.")
    parser.add_argument(
        "--email",
        required=True,
        help="Email address for the teacher",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Password for the teacher",
    )
    args = parser.parse_args()

    try:
        asyncio.run(create_teacher(args.email, args.password))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()