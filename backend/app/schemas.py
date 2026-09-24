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
    username: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int
    group_id: Optional[int] = None
    created_at: datetime


class StudentRegister(BaseSchema):
    username: str = Field(..., min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=120)


class StudentProfile(BaseSchema):
    id: int
    username: str
    full_name: str
    group_id: Optional[int] = None
    group_name: Optional[str] = None


class StudentGroupSelect(BaseSchema):
    group_id: int


class GroupCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=80)


class GroupUpdate(GroupCreate):
    pass


class GroupRead(BaseSchema):
    id: int
    name: str
    teacher_id: int
    teacher_email: Optional[str] = None
    student_count: int = 0
    created_at: datetime


# Test schemas
class TestBase(BaseSchema):
    title: str
    access_code: str


class TestCreate(BaseSchema):
    title: str
    access_code: Optional[str] = None


class TestRead(TestBase):
    id: int
    created_by: int
    created_at: datetime


# Task schemas
class TaskCreateBase(BaseSchema):
    title: str
    description: Optional[str] = None
    group_ids: List[int] = []
    student_ids: List[int] = []
    is_visible: bool = False


class AutoCheckTaskCreate(TaskCreateBase):
    type: Literal["auto_check"]
    checker_type: CheckerType
    expected_value: str


class CodeReviewTaskCreate(TaskCreateBase):
    type: Literal["code_review"]
    source_code: str
    language: str
    student_mode: Literal["review", "live"] = "review"


TaskCreate = Union[AutoCheckTaskCreate, CodeReviewTaskCreate]


class TaskRead(BaseSchema):
    id: int
    test_id: Optional[int] = None
    created_by: int
    title: str
    description: Optional[str] = None
    type: TaskType
    order_index: int
    is_visible: bool = False
    created_at: datetime


class TaskVisibilityUpdate(BaseSchema):
    is_visible: bool


class TaskRecipient(BaseSchema):
    id: int
    name: str


class ManagedTaskRead(TaskRead):
    groups: List[TaskRecipient] = []
    students: List[TaskRecipient] = []
    assigned_student_count: int = 0


class TestWithTaskCreate(BaseSchema):
    """Payload for creating a test and its first task in one transaction."""
    title: str = Field(..., min_length=1, max_length=255)
    access_code: Optional[str] = Field(default=None, min_length=4, max_length=32)
    task: TaskCreate


class TestWithTaskRead(BaseSchema):
    test: TestRead
    task: TaskRead


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
    student_mode: Literal["review", "live"] = "review"


class CodeReviewTaskCreate(CodeReviewTaskBase):
    task_id: int


class CodeReviewTaskRead(CodeReviewTaskBase):
    task_id: int


class StudentCodeUpdate(BaseSchema):
    source_code: str


class StudentCodeRead(StudentCodeUpdate):
    task_id: int
    student_id: int
    updated_at: datetime


# Submission schemas
class SubmissionBase(BaseSchema):
    answer_text: str


class SubmissionRequest(SubmissionBase):
    """Student payload; task and student are derived from route/auth context."""
    pass


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


class CodeCommentCreate(BaseSchema):
    """Comment payload; ownership and author type are derived server-side."""
    line_number: int = Field(..., ge=1)
    text: str = Field(..., min_length=1, max_length=4000)


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


class GradeRequest(BaseSchema):
    """Teacher payload; task is derived from the route."""
    student_id: int
    score: float = Field(..., ge=0, le=100)
    teacher_comment: Optional[str] = None


class GradeRead(GradeBase):
    id: int
    task_id: int
    student_id: int
    graded_at: datetime


# Auth schemas
class StudentLogin(BaseSchema):
    username: str
    password: str


class TeacherLogin(BaseSchema):
    email: str
    password: str


# Combined schemas for nested relationships (for API responses)
class TaskWithDetails(TaskRead):
    student_id: Optional[int] = None
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


class TeacherTestSummary(TestRead):
    tasks: List[TaskRead] = []
    student_count: int = 0


class StudentTaskProgress(BaseSchema):
    student_id: int
    full_name: str
    username: str
    group: str
    submission_count: int = 0
    latest_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    comments_count: int = 0
    has_code_changes: bool = False
    last_code_update: Optional[datetime] = None
    grade: Optional[GradeRead] = None


class TeacherTaskProgress(BaseSchema):
    task: TaskRead
    test: Optional[TestRead] = None
    students: List[StudentTaskProgress] = []


class TaskReview(BaseSchema):
    task_id: int
    student_id: int
    source_code: Optional[str] = None
    language: Optional[str] = None
    comments: List[CodeCommentRead] = []
    grade: Optional[GradeRead] = None
