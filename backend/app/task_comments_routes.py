from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from . import models, auth, schemas
from .database import get_session

router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["task-comments"])


@router.get("", response_model=List[schemas.CodeCommentRead])
async def get_task_comments(
    task_id: int,
    student_id: Optional[int] = Query(None, description="Student ID (required for teachers, ignored for students)"),
    current_user: models.Student | models.Teacher = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Get comments for a task.
    - For students: student_id is ignored, returns comments by the current student
    - For teachers: student_id is required, returns comments by that student
    """
    # Verify task exists and user has access
    task_result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups), selectinload(models.Task.assigned_students))
        .where(models.Task.id == task_id)
    )
    task = task_result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Determine user type and permissions
    if isinstance(current_user, models.Student):
        # Student: get their own comments for this task
        student_id = current_user.id
        assigned = any(item.id == student_id for item in task.assigned_students) or (current_user.group_id is not None and any(group.id == current_user.group_id for group in task.assigned_groups))
        if not assigned or not task.is_visible:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this test"
            )
    elif isinstance(current_user, models.Teacher):
        # Teacher: must provide student_id
        if student_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_id parameter is required for teachers"
            )
        # Verify teacher owns the test
        if task.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view comments for this task"
            )
        assigned_ids = {item.id for item in task.assigned_students}
        for group in task.assigned_groups:
            group_students = (await db.execute(select(models.Student.id).where(models.Student.group_id == group.id))).scalars().all()
            assigned_ids.update(group_students)
        if student_id not in assigned_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not enrolled in this test"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    # Get comments
    result = await db.execute(
        select(models.CodeComment)
        .where(
            models.CodeComment.task_id == task_id,
            models.CodeComment.student_id == student_id
        )
        .order_by(models.CodeComment.created_at)
    )
    comments = result.scalars().all()

    return comments


@router.post("", response_model=schemas.CodeCommentRead)
async def create_task_comment(
    task_id: int,
    comment_create: schemas.CodeCommentCreate,
    student_id: Optional[int] = Query(None, description="Student ID (required for teachers when commenting on student's work)"),
    current_user: models.Student | models.Teacher = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Create a comment on a task.
    - For students: author_type=student, student_id from JWT, task_id from path
    - For teachers: author_type=teacher, student_id from query (whose work is being commented on), task_id from path
    """
    # Verify task exists
    task_result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups), selectinload(models.Task.assigned_students))
        .where(models.Task.id == task_id)
    )
    task = task_result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Determine user type and set comment properties
    if isinstance(current_user, models.Student):
        # Student commenting on their own work
        author_type = models.AuthorType.student
        actual_student_id = current_user.id

        assigned = any(item.id == actual_student_id for item in task.assigned_students) or (current_user.group_id is not None and any(group.id == current_user.group_id for group in task.assigned_groups))
        if not assigned or not task.is_visible:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this test"
            )

    elif isinstance(current_user, models.Teacher):
        # Teacher commenting on student's work
        if student_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_id parameter is required for teachers"
            )
        author_type = models.AuthorType.teacher
        actual_student_id = student_id

        # Verify teacher owns the test
        if task.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to comment on this task"
            )
        assigned_ids = {item.id for item in task.assigned_students}
        for group in task.assigned_groups:
            group_students = (await db.execute(select(models.Student.id).where(models.Student.group_id == group.id))).scalars().all()
            assigned_ids.update(group_students)
        if actual_student_id not in assigned_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not enrolled in this test"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    # Create the comment
    comment = models.CodeComment(
        task_id=task_id,
        student_id=actual_student_id,
        author_type=author_type,
        line_number=comment_create.line_number,
        text=comment_create.text
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return comment


# Note: The grade endpoint will be added to admin_routes.py as requested
