from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import random
import string

from . import models, auth, schemas
from .database import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


def generate_access_code(length: int = 8) -> str:
    """Generate a random access code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))


@router.post("/tests", response_model=schemas.TestRead)
async def create_test(
    test_create: schemas.TestCreate,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """Create a new test for the current teacher."""
    # If access_code not provided, generate one
    access_code = test_create.access_code
    if not access_code:
        # Generate a unique access code
        while True:
            access_code = generate_access_code()
            result = await db.execute(select(models.Test).where(models.Test.access_code == access_code))
            if not result.scalars().first():
                break

    test = models.Test(
        title=test_create.title,
        access_code=access_code,
        created_by=teacher.id
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)
    return test


@router.get("/tests", response_model=List[schemas.TestRead])
async def list_tests(
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """List all tests created by the current teacher."""
    result = await db.execute(
        select(models.Test).where(models.Test.created_by == teacher.id)
    )
    tests = result.scalars().all()
    return tests


@router.post("/tests/{test_id}/tasks", response_model=schemas.TaskRead)
async def create_task(
    test_id: int,
    task_create: schemas.TaskCreate,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """Create a new task in the specified test."""
    # Verify the test exists and belongs to the teacher
    result = await db.execute(
        select(models.Test).where(
            models.Test.id == test_id,
            models.Test.created_by == teacher.id
        )
    )
    test = result.scalars().first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found or not authorized"
        )

    # Create the task
    task = models.Task(
        test_id=test_id,
        title=task_create.title,
        description=task_create.description,
        type=task_create.type,
        order_index=0  # We'll set order_index later; for now, put at end
    )
    db.add(task)
    await db.flush()  # Get the task ID

    # Create the associated detail record based on type
    if task_create.type == models.TaskType.auto_check:
        auto_check_task = models.AutoCheckTask(
            task_id=task.id,
            checker_type=task_create.checker_type,
            expected_value=task_create.expected_value
        )
        db.add(auto_check_task)
    elif task_create.type == models.TaskType.code_review:
        code_review_task = models.CodeReviewTask(
            task_id=task.id,
            source_code=task_create.source_code,
            language=task_create.language
        )
        db.add(code_review_task)

    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/tasks/{task_id}", response_model=schemas.TaskRead)
async def update_task(
    task_id: int,
    task_update: schemas.TaskCreate,  # Reuse the same schema for simplicity
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """Update an existing task."""
    # Get the task with its test to verify ownership
    result = await db.execute(
        select(models.Task)
        .join(models.Test)
        .where(
            models.Task.id == task_id,
            models.Test.created_by == teacher.id
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not authorized"
        )

    # Update task fields
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    # Note: We do not allow changing the type or order_index via this endpoint for simplicity.
    # If needed, we could add separate endpoints.

    # Update the associated detail record
    if task.type == models.TaskType.auto_check:
        if task_update.checker_type is not None:
            # Update the auto_check_task
            result = await db.execute(
                select(models.AutoCheckTask).where(models.AutoCheckTask.task_id == task_id)
            )
            auto_check_task = result.scalars().first()
            if auto_check_task:
                auto_check_task.checker_type = task_update.checker_type
                if task_update.expected_value is not None:
                    auto_check_task.expected_value = task_update.expected_value
    elif task.type == models.TaskType.code_review:
        if task_update.source_code is not None or task_update.language is not None:
            result = await db.execute(
                select(models.CodeReviewTask).where(models.CodeReviewTask.task_id == task_id)
            )
            code_review_task = result.scalars().first()
            if code_review_task:
                if task_update.source_code is not None:
                    code_review_task.source_code = task_update.source_code
                if task_update.language is not None:
                    code_review_task.language = task_update.language

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """Delete a task."""
    # Verify the task exists and belongs to the teacher (via test)
    result = await db.execute(
        select(models.Task)
        .join(models.Test)
        .where(
            models.Task.id == task_id,
            models.Test.created_by == teacher.id
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not authorized"
        )

    # Delete the task (cascade will delete associated details)
    await db.delete(task)
    await db.commit()
    return None


@router.get("/tests/{test_id}/students", response_model=List[schemas.StudentProgress])
async def list_test_students(
    test_id: int,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """List students who have taken the test, with their progress."""
    # Verify the test exists and belongs to the teacher
    result = await db.execute(
        select(models.Test).where(
            models.Test.id == test_id,
            models.Test.created_by == teacher.id
        )
    )
    test = result.scalars().first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found or not authorized"
        )

    # Get all students associated with this test (via the association table)
    # We'll also compute:
    #   submitted_tasks: count of submissions for this student in this test
    #   total_tasks: total number of tasks in the test (same for all students)
    #   pending_code_review: for each student, count of code review tasks where:
    #        - the student has left at least one comment (author_type=student)
    #        - AND there is no Grade for that student and task

    # First, get the total tasks in the test
    total_tasks_result = await db.execute(
        select(func.count(models.Task.id)).where(models.Task.test_id == test_id)
    )
    total_tasks = total_tasks_result.scalar() or 0

    # Query to get students and their stats
    # We'll break it down into subqueries for clarity, but we can do it in one query with multiple joins.

    # Get students enrolled in the test
    stmt = (
        select(
            models.Student.id,
            models.Student.full_name,
            models.Student.group,
        )
        .select_from(models.Student)
        .join(models.student_test_association, models.Student.id == models.student_test_association.c.student_id)
        .where(models.student_test_association.c.test_id == test_id)
    )
    result = await db.execute(stmt)
    students = result.all()

    # For each student, compute submitted_tasks and pending_code_review
    progress_list = []
    for student in students:
        student_id = student.id

        # Count submissions for this student in this test
        submitted_result = await db.execute(
            select(func.count(models.Submission.id))
            .join(models.Task, models.Submission.task_id == models.Task.id)
            .where(
                models.Task.test_id == test_id,
                models.Submission.student_id == student_id
            )
        )
        submitted_tasks = submitted_result.scalar() or 0

        # Count pending code review tasks for this student
        # We need to find code review tasks in the test where:
        #   - The student has left at least one comment (author_type=student)
        #   - AND there is no Grade for that student and task
        pending_result = await db.execute(
            select(func.count(models.Task.id))
            .select_from(models.Task)
            .join(models.CodeReviewTask, models.Task.id == models.CodeReviewTask.task_id)
            .outerjoin(
                models.CodeComment,
                (models.CodeComment.task_id == models.Task.id) &
                (models.CodeComment.student_id == student_id) &
                (models.CodeComment.author_type == models.AuthorType.student)
            )
            .outerjoin(
                models.Grade,
                (models.Grade.task_id == models.Task.id) &
                (models.Grade.student_id == student_id)
            )
            .where(
                models.Task.test_id == test_id,
                models.CodeComment.id.is_not(None),  # At least one student comment
                models.Grade.id.is_none()             # No grade yet
            )
        )
        pending_code_review = pending_result.scalar() or 0

        progress_list.append(
            schemas.StudentProgress(
                student_id=student_id,
                full_name=student.full_name,
                group=student.group,
                submitted_tasks=submitted_tasks,
                total_tasks=total_tasks,
                pending_code_review=pending_code_review
            )
        )

    return progress_list