from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum as PyEnum
from typing import Literal


# Enums (matching SQLAlchemy models)
class TaskType(str, PyEnum):
    auto_check = "auto_check"
    code_review = "code_review"


class CheckerType(str, PyEnum):
    exact = "exact"
    regex = "regex"
    tokenized = "tokenized"


class AuthorType(str, PyEnum):
    student = "student"
    teacher = "teacher"


# Base schemas with common fields
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# Teacher schemas
class TeacherBase(BaseSchema):
    email: str


class TeacherCreate(TeacherBase):
    password: str = Field(..., min_length=8)


class TeacherRead(TeacherBase):
    id: int
    created_at: datetime


# Student schemas
class StudentBase(BaseSchema):
    full_name: str
    group: str


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int
    created_at: datetime


# Test schemas
class TestBase(BaseSchema):
    title: str
    access_code: str


class TestCreate(TestBase):
    created_by: int


class TestRead(TestBase):
    id: int
    created_by: int
    created_at: datetime


# Task schemas
class TaskCreateBase(BaseSchema):
    title: str
    description: Optional[str] = None


class AutoCheckTaskCreate(TaskCreateBase):
    type: Literal["auto_check"]
    checker_type: CheckerType
    expected_value: str


class CodeReviewTaskCreate(TaskCreateBase):
    type: Literal["code_review"]
    source_code: str
    language: str


TaskCreate = Union[AutoCheckTaskCreate, CodeReviewTaskCreate]


class TaskRead(BaseSchema):
    id: int
    test_id: int
    title: str
    description: Optional[str] = None
    type: TaskType
    order_index: int
    created_at: datetime


# AutoCheckTask schemas
class AutoCheckTaskBase(BaseSchema):
    checker_type: CheckerType
    expected_value: str


class AutoCheckTaskCreate(AutoCheckTaskBase):
    task_id: int


class AutoCheckTaskRead(AutoCheckTaskBase):
    task_id: int


# CodeReviewTask schemas
class CodeReviewTaskBase(BaseSchema):
    source_code: str
    language: str


class CodeReviewTaskCreate(CodeReviewTaskBase):
    task_id: int


class CodeReviewTaskRead(CodeReviewTaskBase):
    task_id: int


# Submission schemas
class SubmissionBase(BaseSchema):
    answer_text: str


class SubmissionCreate(SubmissionBase):
    task_id: int
    student_id: int


class SubmissionRead(SubmissionBase):
    id: int
    task_id: int
    student_id: int
    is_correct: Optional[bool] = None
    submitted_at: datetime


# CodeComment schemas
class CodeCommentBase(BaseSchema):
    line_number: int
    text: str
    author_type: AuthorType


class CodeCommentCreate(CodeCommentBase):
    task_id: int
    student_id: int


class CodeCommentRead(CodeCommentBase):
    id: int
    task_id: int
    student_id: int
    created_at: datetime


# Grade schemas
class GradeBase(BaseSchema):
    score: float
    teacher_comment: Optional[str] = None


class GradeCreate(GradeBase):
    task_id: int
    student_id: int


class GradeRead(GradeBase):
    id: int
    task_id: int
    student_id: int
    graded_at: datetime


# Auth schemas
class StudentLogin(BaseSchema):
    full_name: str
    access_code: str


# Combined schemas for nested relationships (for API responses)
class TaskWithDetails(TaskRead):
    auto_check_task: Optional[AutoCheckTaskRead] = None
    code_review_task: Optional[CodeReviewTaskRead] = None
    submissions: List[SubmissionRead] = []
    code_comments: List[CodeCommentRead] = []
    grades: List[GradeRead] = []


class TestWithDetails(TestRead):
    tasks: List[TaskWithDetails] = []


class TeacherWithDetails(TeacherRead):
    tests: List[TestWithDetails] = []


class StudentWithDetails(StudentRead):
    submissions: List[SubmissionRead] = []
    code_comments: List[CodeCommentRead] = []
    grades: List[GradeRead] = []


# Admin response schemas
class StudentProgress(BaseSchema):
    student_id: int
    full_name: str
    group: str
    submitted_tasks: int
    total_tasks: int
    pending_code_review: int