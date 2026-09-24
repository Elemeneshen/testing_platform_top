from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import re

from . import models, auth, schemas
from .database import get_session
from .services.checker import check_answer

router = APIRouter(tags=["student"])


def task_is_assigned(task: models.Task, student: models.Student) -> bool:
    return any(item.id == student.id for item in task.assigned_students) or (student.group_id is not None and any(group.id == student.group_id for group in task.assigned_groups))


@router.get("/tasks", response_model=List[schemas.TaskWithDetails])
async def list_student_tasks(student: models.Student = Depends(auth.get_current_student), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(models.Task).options(selectinload(models.Task.assigned_groups), selectinload(models.Task.assigned_students), selectinload(models.Task.auto_check_task), selectinload(models.Task.code_review_task)).where(models.Task.is_visible.is_(True)).order_by(models.Task.created_at.desc()))
    tasks = [task for task in result.scalars().unique().all() if task_is_assigned(task, student)]
    response = []
    for task in tasks:
        submissions = list((await db.execute(select(models.Submission).where(models.Submission.task_id == task.id, models.Submission.student_id == student.id))).scalars().all())
        comments = list((await db.execute(select(models.CodeComment).where(models.CodeComment.task_id == task.id, models.CodeComment.student_id == student.id))).scalars().all())
        grades = list((await db.execute(select(models.Grade).where(models.Grade.task_id == task.id, models.Grade.student_id == student.id))).scalars().all())
        response.append(schemas.TaskWithDetails.model_validate({"id": task.id, "test_id": None, "created_by": task.created_by, "title": task.title, "description": task.description, "type": task.type, "order_index": task.order_index, "is_visible": task.is_visible, "created_at": task.created_at, "auto_check_task": task.auto_check_task, "code_review_task": task.code_review_task, "submissions": submissions, "code_comments": comments, "grades": grades}))
    return response


@router.get("/student/groups", response_model=List[schemas.GroupRead])
async def list_available_groups(
    student: models.Student = Depends(auth.get_current_student),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(models.StudentGroup, models.Teacher.email)
        .options(selectinload(models.StudentGroup.students))
        .join(models.Teacher, models.StudentGroup.teacher_id == models.Teacher.id)
        .where(models.StudentGroup.teacher_id == student.registration_teacher_id)
        .order_by(models.StudentGroup.name)
    )
    return [schemas.GroupRead(
        id=group.id,
        name=group.name,
        teacher_id=group.teacher_id,
        teacher_email=email,
        student_count=len(group.students),
        created_at=group.created_at,
    ) for group, email in result.all()]


@router.get("/student/profile", response_model=schemas.StudentProfile)
async def get_student_profile(
    student: models.Student = Depends(auth.get_current_student),
    db: AsyncSession = Depends(get_session),
):
    group_name = None
    if student.group_id:
        group_name = (await db.execute(select(models.StudentGroup.name).where(models.StudentGroup.id == student.group_id))).scalar_one_or_none()
    return schemas.StudentProfile(
        id=student.id,
        username=student.username,
        full_name=student.full_name,
        group_id=student.group_id,
        group_name=group_name,
    )


@router.put("/student/profile/group", response_model=schemas.StudentProfile)
async def select_student_group(
    payload: schemas.StudentGroupSelect,
    student: models.Student = Depends(auth.get_current_student),
    db: AsyncSession = Depends(get_session),
):
    if student.group_id is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only a teacher can change an existing group assignment")
    result = await db.execute(select(models.StudentGroup).where(
        models.StudentGroup.id == payload.group_id,
        models.StudentGroup.teacher_id == student.registration_teacher_id,
    ))
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    student.group_id = group.id
    student.group_name = group.name
    await db.commit()
    await db.refresh(student)
    return schemas.StudentProfile(id=student.id, username=student.username, full_name=student.full_name, group_id=group.id, group_name=group.name)


@router.get("/tests/current", response_model=schemas.TestWithDetails)
async def get_current_test(
    student: models.Student = Depends(auth.get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Get the current test for the student (from JWT) with tasks."""
    # Get user info from token
    # We need to get the test_id from the student's token/context
    # Since get_current_student doesn't return test_id, we need to get it differently
    # Let's get all tests the student is enrolled in and return the first one (or we could store test_id in token)

    # For now, let's get the student's enrolled tests
    result = await db.execute(
        select(models.Test)
        .join(models.student_test_association)
        .where(models.student_test_association.c.student_id == student.id)
    )
    tests = result.scalars().all()

    if not tests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tests found for student"
        )

    # Return the first test (in a real app, we might want to get the active/current test)
    test = tests[0]

    # Get tasks for this test
    result = await db.execute(
        select(models.Task)
        .where(models.Task.test_id == test.id)
        .order_by(models.Task.order_index)
    )
    tasks = result.scalars().all()

    # Build response with task details
    task_details = []
    for task in tasks:
        # Get task details based on type
        auto_check_task = None
        code_review_task = None

        if task.type == models.TaskType.auto_check:
            result = await db.execute(
                select(models.AutoCheckTask).where(models.AutoCheckTask.task_id == task.id)
            )
            auto_check_task = result.scalars().first()
        elif task.type == models.TaskType.code_review:
            result = await db.execute(
                select(models.CodeReviewTask).where(models.CodeReviewTask.task_id == task.id)
            )
            code_review_task = result.scalars().first()
            if code_review_task:
                session_result = await db.execute(
                    select(models.StudentCodeSession).where(
                        models.StudentCodeSession.task_id == task.id,
                        models.StudentCodeSession.student_id == student.id,
                    )
                )
                session = session_result.scalars().first()
                if session:
                    code_review_task = schemas.CodeReviewTaskRead(
                        task_id=task.id,
                        source_code=session.source_code,
                        language=code_review_task.language,
                        student_mode=code_review_task.student_mode,
                    )

        submissions_result = await db.execute(
            select(models.Submission).where(models.Submission.task_id == task.id, models.Submission.student_id == student.id)
        )
        comments_result = await db.execute(
            select(models.CodeComment).where(models.CodeComment.task_id == task.id, models.CodeComment.student_id == student.id).order_by(models.CodeComment.created_at)
        )
        grades_result = await db.execute(
            select(models.Grade).where(models.Grade.task_id == task.id, models.Grade.student_id == student.id)
        )

        task_detail = schemas.TaskWithDetails(
            id=task.id,
            test_id=task.test_id,
            created_by=task.created_by,
            title=task.title,
            description=task.description,
            type=task.type,
            order_index=task.order_index,
            is_visible=task.is_visible,
            created_at=task.created_at,
            auto_check_task=auto_check_task,
            code_review_task=code_review_task,
            submissions=list(submissions_result.scalars().all()),
            code_comments=list(comments_result.scalars().all()),
            grades=list(grades_result.scalars().all())
        )
        task_details.append(task_detail)

    return schemas.TestWithDetails(
        id=test.id,
        title=test.title,
        access_code=test.access_code,
        created_by=test.created_by,
        created_at=test.created_at,
        tasks=task_details
    )


@router.get("/tasks/{task_id}", response_model=schemas.TaskWithDetails)
async def get_task(
    task_id: int,
    student: models.Student = Depends(auth.get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Get details of a specific task."""
    # Verify the task exists and student has access (via test enrollment)
    result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups), selectinload(models.Task.assigned_students))
        .where(models.Task.id == task_id, models.Task.is_visible.is_(True))
    )
    task = result.scalars().first()

    if not task or not task_is_assigned(task, student):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not authorized"
        )

    # Get task details based on type
    auto_check_task = None
    code_review_task = None

    if task.type == models.TaskType.auto_check:
        result = await db.execute(
            select(models.AutoCheckTask).where(models.AutoCheckTask.task_id == task_id)
        )
        auto_check_task = result.scalars().first()
    elif task.type == models.TaskType.code_review:
        result = await db.execute(
            select(models.CodeReviewTask).where(models.CodeReviewTask.task_id == task_id)
        )
        code_review_task = result.scalars().first()
        if code_review_task:
            session_result = await db.execute(
                select(models.StudentCodeSession).where(
                    models.StudentCodeSession.task_id == task.id,
                    models.StudentCodeSession.student_id == student.id,
                )
            )
            session = session_result.scalars().first()
            if session:
                code_review_task = schemas.CodeReviewTaskRead(
                    task_id=task.id,
                    source_code=session.source_code,
                    language=code_review_task.language,
                    student_mode=code_review_task.student_mode,
                )

    submissions_result = await db.execute(
        select(models.Submission).where(models.Submission.task_id == task.id, models.Submission.student_id == student.id)
    )
    comments_result = await db.execute(
        select(models.CodeComment).where(models.CodeComment.task_id == task.id, models.CodeComment.student_id == student.id).order_by(models.CodeComment.created_at)
    )
    grades_result = await db.execute(
        select(models.Grade).where(models.Grade.task_id == task.id, models.Grade.student_id == student.id)
    )

    # For code_review tasks, we might want to hide source_code from students in some contexts
    # But as per requirements, we need to show code for commenting, so we'll include it

    task_detail = schemas.TaskWithDetails(
        id=task.id,
        student_id=student.id,
        test_id=task.test_id,
        created_by=task.created_by,
        title=task.title,
        description=task.description,
        type=task.type,
        order_index=task.order_index,
        is_visible=task.is_visible,
        created_at=task.created_at,
        auto_check_task=auto_check_task,
        code_review_task=code_review_task,
        submissions=list(submissions_result.scalars().all()),
        code_comments=list(comments_result.scalars().all()),
        grades=list(grades_result.scalars().all())
    )

    return task_detail


@router.put("/tasks/{task_id}/code", response_model=schemas.StudentCodeRead)
async def save_student_code(
    task_id: int,
    payload: schemas.StudentCodeUpdate,
    student: models.Student = Depends(auth.get_current_student),
    db: AsyncSession = Depends(get_session),
):
    """Autosave a student's private working copy for a live-coding task."""
    result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups), selectinload(models.Task.assigned_students))
        .where(models.Task.id == task_id, models.Task.is_visible.is_(True))
    )
    task = result.scalars().first()
    if not task or not task_is_assigned(task, student) or task.type != models.TaskType.code_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Live-coding task not found or not authorized")

    details_result = await db.execute(select(models.CodeReviewTask).where(models.CodeReviewTask.task_id == task_id))
    details = details_result.scalars().first()
    if not details or details.student_mode != "live":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This task is configured as review only")

    session_result = await db.execute(
        select(models.StudentCodeSession).where(
            models.StudentCodeSession.task_id == task_id,
            models.StudentCodeSession.student_id == student.id,
        )
    )
    session = session_result.scalars().first()
    if session:
        session.source_code = payload.source_code
    else:
        session = models.StudentCodeSession(task_id=task_id, student_id=student.id, source_code=payload.source_code)
        db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/tasks/{task_id}/submit", response_model=schemas.SubmissionRead)
async def submit_task(
    task_id: int,
    submission_create: schemas.SubmissionRequest,
    student: models.Student = Depends(auth.get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Submit an answer for an auto_check task."""
    # Verify the task exists, is auto_check type, and student has access
    result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups), selectinload(models.Task.assigned_students))
        .where(
            models.Task.id == task_id,
            models.Task.type == models.TaskType.auto_check,
            models.Task.is_visible.is_(True),
        )
    )
    task = result.scalars().first()

    if not task or not task_is_assigned(task, student):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found, not an auto_check task, or not authorized"
        )

    # Get the auto_check task details
    result = await db.execute(
        select(models.AutoCheckTask).where(models.AutoCheckTask.task_id == task_id)
    )
    auto_check_task = result.scalars().first()

    if not auto_check_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auto check task details not found"
        )

    # Check the answer using our checker service
    is_correct = check_answer(
        submission_create.answer_text,
        auto_check_task.checker_type,
        auto_check_task.expected_value
    )

    # Create submission
    submission = models.Submission(
        task_id=task_id,
        student_id=student.id,
        answer_text=submission_create.answer_text,
        is_correct=is_correct
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return submission
