import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import random
import string

logger = logging.getLogger(__name__)

from . import models, auth, schemas
from .database import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


def generate_access_code(length: int = 8) -> str:
    """Generate a random access code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))


def group_to_schema(group: models.StudentGroup, teacher_email: str) -> schemas.GroupRead:
    return schemas.GroupRead(id=group.id, name=group.name, teacher_id=group.teacher_id, teacher_email=teacher_email, student_count=len(group.students), created_at=group.created_at)


@router.get("/groups", response_model=List[schemas.GroupRead])
async def list_groups(teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(models.StudentGroup).options(selectinload(models.StudentGroup.students)).where(models.StudentGroup.teacher_id == teacher.id).order_by(models.StudentGroup.name)
    )
    return [group_to_schema(group, teacher.email) for group in result.scalars().unique().all()]


@router.post("/groups", response_model=schemas.GroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(payload: schemas.GroupCreate, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    name = payload.name.strip()
    existing = await db.execute(select(models.StudentGroup.id).where(models.StudentGroup.teacher_id == teacher.id, func.lower(models.StudentGroup.name) == name.lower()))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A group with this name already exists")
    group = models.StudentGroup(name=name, teacher_id=teacher.id)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return schemas.GroupRead(id=group.id, name=group.name, teacher_id=teacher.id, teacher_email=teacher.email, student_count=0, created_at=group.created_at)


@router.patch("/groups/{group_id}", response_model=schemas.GroupRead)
async def update_group(group_id: int, payload: schemas.GroupUpdate, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(models.StudentGroup).options(selectinload(models.StudentGroup.students)).where(models.StudentGroup.id == group_id, models.StudentGroup.teacher_id == teacher.id))
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    group.name = payload.name.strip()
    for student in group.students:
        student.group_name = group.name
    await db.commit()
    await db.refresh(group)
    return group_to_schema(group, teacher.email)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: int, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(models.StudentGroup).options(selectinload(models.StudentGroup.students)).where(models.StudentGroup.id == group_id, models.StudentGroup.teacher_id == teacher.id))
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if group.students:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Move students to another group before deleting this group")
    await db.delete(group)
    await db.commit()


@router.get("/assignment-options")
async def assignment_options(teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    groups_result = await db.execute(
        select(models.StudentGroup).options(selectinload(models.StudentGroup.students)).where(models.StudentGroup.teacher_id == teacher.id).order_by(models.StudentGroup.name)
    )
    groups = groups_result.scalars().unique().all()
    return {"groups": [{"id": group.id, "name": group.name, "students": [{"id": student.id, "full_name": student.full_name, "username": student.username} for student in group.students]} for group in groups]}


@router.get("/students")
async def list_teacher_students(teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(models.Student, models.StudentGroup)
        .join(models.StudentGroup, models.Student.group_id == models.StudentGroup.id)
        .where(models.StudentGroup.teacher_id == teacher.id)
        .order_by(models.Student.full_name)
    )
    return [{"id": student.id, "full_name": student.full_name, "username": student.username, "group_id": group.id, "group_name": group.name} for student, group in result.all()]


@router.patch("/students/{student_id}/group", response_model=schemas.StudentProfile)
async def change_student_group(student_id: int, payload: schemas.StudentGroupSelect, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    student_result = await db.execute(select(models.Student).join(models.StudentGroup).where(models.Student.id == student_id, models.StudentGroup.teacher_id == teacher.id))
    student = student_result.scalars().first()
    group_result = await db.execute(select(models.StudentGroup).where(models.StudentGroup.id == payload.group_id, models.StudentGroup.teacher_id == teacher.id))
    group = group_result.scalars().first()
    if not student or not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student or group not found")
    student.group_id = group.id
    student.group_name = group.name
    await db.commit(); await db.refresh(student)
    return schemas.StudentProfile(id=student.id, username=student.username, full_name=student.full_name, group_id=group.id, group_name=group.name)


async def resolve_task_students(db: AsyncSession, task: models.Task) -> list[models.Student]:
    student_map = {student.id: student for student in task.assigned_students}
    for group in task.assigned_groups:
        for student in group.students:
            student_map[student.id] = student
    return sorted(student_map.values(), key=lambda student: student.full_name)


@router.get("/tasks", response_model=List[schemas.ManagedTaskRead])
async def list_managed_tasks(teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(models.Task)
        .options(
            selectinload(models.Task.assigned_groups).selectinload(models.StudentGroup.students),
            selectinload(models.Task.assigned_students),
        )
        .where(models.Task.created_by == teacher.id)
        .order_by(models.Task.created_at.desc())
    )
    tasks = result.scalars().unique().all()
    response = []
    for task in tasks:
        assigned = await resolve_task_students(db, task)
        response.append(schemas.ManagedTaskRead(
            id=task.id, test_id=task.test_id, created_by=task.created_by, title=task.title,
            description=task.description, type=task.type, order_index=task.order_index,
            is_visible=task.is_visible, created_at=task.created_at,
            groups=[schemas.TaskRecipient(id=group.id, name=group.name) for group in task.assigned_groups],
            students=[schemas.TaskRecipient(id=student.id, name=student.full_name) for student in task.assigned_students],
            assigned_student_count=len(assigned),
        ))
    return response


@router.post("/tasks", response_model=schemas.ManagedTaskRead, status_code=status.HTTP_201_CREATED)
async def create_assigned_task(payload: schemas.TaskCreate, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    groups_result = await db.execute(select(models.StudentGroup).options(selectinload(models.StudentGroup.students)).where(models.StudentGroup.id.in_(payload.group_ids), models.StudentGroup.teacher_id == teacher.id)) if payload.group_ids else None
    groups = list(groups_result.scalars().unique().all()) if groups_result else []
    if len(groups) != len(set(payload.group_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more groups are invalid")
    students_result = await db.execute(select(models.Student).join(models.StudentGroup).where(models.Student.id.in_(payload.student_ids), models.StudentGroup.teacher_id == teacher.id)) if payload.student_ids else None
    students = list(students_result.scalars().unique().all()) if students_result else []
    if len(students) != len(set(payload.student_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more students are invalid")
    if not groups and not students:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Select at least one group or student")

    task = models.Task(created_by=teacher.id, title=payload.title.strip(), description=payload.description, type=payload.type, order_index=0, is_visible=payload.is_visible, assigned_groups=groups, assigned_students=students)
    db.add(task)
    await db.flush()
    if payload.type == models.TaskType.auto_check:
        db.add(models.AutoCheckTask(task_id=task.id, checker_type=payload.checker_type, expected_value=payload.expected_value))
    else:
        db.add(models.CodeReviewTask(task_id=task.id, source_code=payload.source_code, language=payload.language, student_mode=payload.student_mode))
    await db.commit()
    assigned_ids = {student.id for student in students}
    for group in groups:
        assigned_ids.update(student.id for student in group.students)
    return schemas.ManagedTaskRead(id=task.id, test_id=None, created_by=teacher.id, title=task.title, description=task.description, type=task.type, order_index=0, is_visible=task.is_visible, created_at=task.created_at, groups=[schemas.TaskRecipient(id=g.id, name=g.name) for g in groups], students=[schemas.TaskRecipient(id=s.id, name=s.full_name) for s in students], assigned_student_count=len(assigned_ids))


@router.patch("/tasks/{task_id}/visibility", response_model=schemas.ManagedTaskRead)
async def set_task_visibility(task_id: int, payload: schemas.TaskVisibilityUpdate, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(models.Task).options(selectinload(models.Task.assigned_groups).selectinload(models.StudentGroup.students), selectinload(models.Task.assigned_students)).where(models.Task.id == task_id, models.Task.created_by == teacher.id))
    task = result.scalars().unique().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task.is_visible = payload.is_visible
    await db.commit()
    assigned = await resolve_task_students(db, task)
    return schemas.ManagedTaskRead(id=task.id, test_id=task.test_id, created_by=task.created_by, title=task.title, description=task.description, type=task.type, order_index=task.order_index, is_visible=task.is_visible, created_at=task.created_at, groups=[schemas.TaskRecipient(id=g.id, name=g.name) for g in task.assigned_groups], students=[schemas.TaskRecipient(id=s.id, name=s.full_name) for s in task.assigned_students], assigned_student_count=len(assigned))


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


@router.post("/tests/with-task", response_model=schemas.TestWithTaskRead, status_code=status.HTTP_201_CREATED)
async def create_test_with_task(
    payload: schemas.TestWithTaskCreate,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """Create a test and its first task atomically."""
    access_code = payload.access_code.strip().upper() if payload.access_code else None
    if access_code:
        existing = await db.execute(select(models.Test.id).where(models.Test.access_code == access_code))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Access code is already in use")
    else:
        while True:
            access_code = generate_access_code()
            existing = await db.execute(select(models.Test.id).where(models.Test.access_code == access_code))
            if existing.scalar_one_or_none() is None:
                break

    test = models.Test(title=payload.title.strip(), access_code=access_code, created_by=teacher.id)
    db.add(test)
    await db.flush()

    task_payload = payload.task
    task = models.Task(
        test_id=test.id,
        created_by=teacher.id,
        title=task_payload.title.strip(),
        description=task_payload.description,
        type=task_payload.type,
        order_index=0,
    )
    db.add(task)
    await db.flush()

    if task_payload.type == schemas.TaskType.auto_check:
        db.add(models.AutoCheckTask(
            task_id=task.id,
            checker_type=task_payload.checker_type,
            expected_value=task_payload.expected_value,
        ))
    else:
        db.add(models.CodeReviewTask(
            task_id=task.id,
            source_code=task_payload.source_code,
            language=task_payload.language,
            student_mode=task_payload.student_mode,
        ))

    await db.commit()
    await db.refresh(test)
    await db.refresh(task)
    return schemas.TestWithTaskRead(test=test, task=task)


@router.get("/tests", response_model=List[schemas.TeacherTestSummary])
async def list_tests(
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """List all tests created by the current teacher."""
    logger.debug(f"list_tests endpoint called")
    logger.debug(f"teacher dependency result: {teacher}")
    if teacher is None:
        logger.debug("Teacher is None - authentication failed")
    else:
        logger.debug(f"Teacher authenticated: id={teacher.id}")
    result = await db.execute(
        select(models.Test)
        .options(selectinload(models.Test.tasks), selectinload(models.Test.students))
        .where(models.Test.created_by == teacher.id)
        .order_by(models.Test.created_at.desc())
    )
    tests = result.scalars().unique().all()
    logger.debug(f"Found {len(tests)} tests for teacher {teacher.id if teacher else 'None'}")
    return [
        schemas.TeacherTestSummary.model_validate({
            "id": test.id,
            "title": test.title,
            "access_code": test.access_code,
            "created_by": test.created_by,
            "created_at": test.created_at,
            "tasks": sorted(test.tasks, key=lambda task: (task.order_index, task.id)),
            "student_count": len(test.students),
        })
        for test in tests
    ]


@router.get("/tasks/{task_id}/progress", response_model=schemas.TeacherTaskProgress)
async def get_task_progress(
    task_id: int,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session),
):
    """Return the real students and their activity for one teacher-owned task."""
    result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups).selectinload(models.StudentGroup.students).selectinload(models.Student.group), selectinload(models.Task.assigned_students).selectinload(models.Student.group))
        .where(models.Task.id == task_id, models.Task.created_by == teacher.id)
    )
    task = result.scalars().unique().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not authorized")

    students_progress = []
    for student in await resolve_task_students(db, task):
        submissions_result = await db.execute(
            select(models.Submission)
            .where(models.Submission.task_id == task.id, models.Submission.student_id == student.id)
            .order_by(models.Submission.submitted_at.desc())
        )
        submissions = list(submissions_result.scalars().all())
        comments_count_result = await db.execute(
            select(func.count(models.CodeComment.id)).where(
                models.CodeComment.task_id == task.id,
                models.CodeComment.student_id == student.id,
            )
        )
        grade_result = await db.execute(
            select(models.Grade).where(models.Grade.task_id == task.id, models.Grade.student_id == student.id)
        )
        code_session_result = await db.execute(
            select(models.StudentCodeSession).where(
                models.StudentCodeSession.task_id == task.id,
                models.StudentCodeSession.student_id == student.id,
            )
        )
        code_session = code_session_result.scalars().first()
        latest_submission = submissions[0] if submissions else None
        students_progress.append(schemas.StudentTaskProgress(
            student_id=student.id,
            full_name=student.full_name,
            username=student.username,
            group=student.group.name if student.group else student.group_name,
            submission_count=len(submissions),
            latest_answer=latest_submission.answer_text if latest_submission else None,
            is_correct=latest_submission.is_correct if latest_submission else None,
            comments_count=comments_count_result.scalar() or 0,
            has_code_changes=code_session is not None,
            last_code_update=code_session.updated_at if code_session else None,
            grade=grade_result.scalars().first(),
        ))

    return schemas.TeacherTaskProgress(task=task, students=students_progress)


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
        created_by=teacher.id,
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
            language=task_create.language,
            student_mode=task_create.student_mode,
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
        .where(
            models.Task.id == task_id,
            models.Task.created_by == teacher.id
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
        if task_update.type == schemas.TaskType.auto_check:
            # Update the auto_check_task
            result = await db.execute(
                select(models.AutoCheckTask).where(models.AutoCheckTask.task_id == task_id)
            )
            auto_check_task = result.scalars().first()
            if auto_check_task:
                if task_update.checker_type is not None:
                    auto_check_task.checker_type = task_update.checker_type
                if task_update.expected_value is not None:
                    auto_check_task.expected_value = task_update.expected_value
    elif task.type == models.TaskType.code_review:
        if task_update.type == schemas.TaskType.code_review:
            result = await db.execute(
                select(models.CodeReviewTask).where(models.CodeReviewTask.task_id == task_id)
            )
            code_review_task = result.scalars().first()
            if code_review_task:
                if task_update.source_code is not None:
                    code_review_task.source_code = task_update.source_code
                if task_update.language is not None:
                    code_review_task.language = task_update.language
                code_review_task.student_mode = task_update.student_mode

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
        .where(
            models.Task.id == task_id,
            models.Task.created_by == teacher.id
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

    students_result = await db.execute(
        select(models.Student)
        .options(selectinload(models.Student.group))
        .join(models.student_test_association)
        .where(models.student_test_association.c.test_id == test_id)
        .order_by(models.Student.full_name)
    )
    students = list(students_result.scalars().all())
    total_tasks_result = await db.execute(select(func.count(models.Task.id)).where(models.Task.test_id == test_id))
    total_tasks = total_tasks_result.scalar() or 0
    progress = []
    for student in students:
        submitted_result = await db.execute(
            select(func.count(func.distinct(models.Submission.task_id)))
            .join(models.Task, models.Submission.task_id == models.Task.id)
            .where(models.Task.test_id == test_id, models.Submission.student_id == student.id)
        )
        pending_result = await db.execute(
            select(func.count(func.distinct(models.CodeComment.task_id)))
            .join(models.Task, models.CodeComment.task_id == models.Task.id)
            .outerjoin(models.Grade, (models.Grade.task_id == models.CodeComment.task_id) & (models.Grade.student_id == student.id))
            .where(models.Task.test_id == test_id, models.CodeComment.student_id == student.id, models.CodeComment.author_type == models.AuthorType.student, models.Grade.id.is_(None))
        )
        progress.append(schemas.StudentProgress(
            student_id=student.id,
            full_name=student.full_name,
            group=student.group.name if student.group else student.group_name,
            submitted_tasks=submitted_result.scalar() or 0,
            total_tasks=total_tasks,
            pending_code_review=pending_result.scalar() or 0,
        ))
    return progress


@router.post("/tasks/{task_id}/grade", response_model=schemas.GradeRead)
async def create_or_update_grade(
    task_id: int,
    grade_create: schemas.GradeRequest,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """Create or update a grade for a student's task (teacher only)."""
    # Verify the task exists and belongs to the teacher
    result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups).selectinload(models.StudentGroup.students), selectinload(models.Task.assigned_students))
        .where(
            models.Task.id == task_id,
            models.Task.created_by == teacher.id
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not authorized"
        )

    # Check if grade already exists for this student and task
    result = await db.execute(
        select(models.Grade).where(
            models.Grade.task_id == task_id,
            models.Grade.student_id == grade_create.student_id
        )
    )
    existing_grade = result.scalars().first()

    if existing_grade:
        # Update existing grade
        if grade_create.score is not None:
            existing_grade.score = grade_create.score
        if grade_create.teacher_comment is not None:
            existing_grade.teacher_comment = grade_create.teacher_comment
        # graded_at will be updated automatically by the database if we have onupdate set
        await db.commit()
        await db.refresh(existing_grade)
        return existing_grade
    else:
        # Create new grade
        grade = models.Grade(
            task_id=task_id,
            student_id=grade_create.student_id,
            score=grade_create.score,
            teacher_comment=grade_create.teacher_comment
        )
        db.add(grade)
        await db.commit()
        await db.refresh(grade)
        return grade


@router.get("/tasks/{task_id}/students/{student_id}/review", response_model=schemas.TaskReview)
async def get_task_review(
    task_id: int,
    student_id: int,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session)
):
    """Get task review data for teacher: source_code + all comments + current grade."""
    # Verify the task exists and belongs to the teacher
    result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups).selectinload(models.StudentGroup.students), selectinload(models.Task.assigned_students))
        .where(
            models.Task.id == task_id,
            models.Task.created_by == teacher.id
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not authorized"
        )

    assigned_ids = {student.id for student in await resolve_task_students(db, task)}
    if student_id not in assigned_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task is not assigned to this student"
        )

    # Get the code review task details (only for code_review tasks)
    source_code = None
    language = None
    if task.type == models.TaskType.code_review:
        result = await db.execute(
            select(models.CodeReviewTask).where(models.CodeReviewTask.task_id == task_id)
        )
        code_review_task = result.scalars().first()
        if code_review_task:
            session_result = await db.execute(
                select(models.StudentCodeSession).where(
                    models.StudentCodeSession.task_id == task_id,
                    models.StudentCodeSession.student_id == student_id,
                )
            )
            student_session = session_result.scalars().first()
            source_code = student_session.source_code if student_session else code_review_task.source_code
            language = code_review_task.language

    # Get all comments for this task and student (both student and teacher comments)
    result = await db.execute(
        select(models.CodeComment)
        .where(
            models.CodeComment.task_id == task_id,
            models.CodeComment.student_id == student_id
        )
        .order_by(models.CodeComment.created_at)
    )
    comments = result.scalars().all()

    # Get current grade for this student and task
    result = await db.execute(
        select(models.Grade)
        .where(
            models.Grade.task_id == task_id,
            models.Grade.student_id == student_id
        )
    )
    grade = result.scalars().first()

    return schemas.TaskReview(
        task_id=task_id,
        student_id=student_id,
        source_code=source_code,
        language=language,
        comments=comments,
        grade=grade
    )


@router.put("/tasks/{task_id}/students/{student_id}/code", response_model=schemas.StudentCodeRead)
async def update_student_code_by_teacher(
    task_id: int,
    student_id: int,
    payload: schemas.StudentCodeUpdate,
    teacher: models.Teacher = Depends(auth.get_current_teacher),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(models.Task)
        .options(selectinload(models.Task.assigned_groups).selectinload(models.StudentGroup.students), selectinload(models.Task.assigned_students))
        .where(models.Task.id == task_id, models.Task.created_by == teacher.id)
    )
    task = result.scalars().unique().first()
    if not task or task.type != models.TaskType.code_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code review task not found")
    if student_id not in {student.id for student in await resolve_task_students(db, task)}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task is not assigned to this student")
    session_result = await db.execute(select(models.StudentCodeSession).where(models.StudentCodeSession.task_id == task_id, models.StudentCodeSession.student_id == student_id))
    session = session_result.scalars().first()
    if session:
        session.source_code = payload.source_code
    else:
        session = models.StudentCodeSession(task_id=task_id, student_id=student_id, source_code=payload.source_code)
        db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

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
