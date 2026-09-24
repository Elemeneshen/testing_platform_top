from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Boolean,
    Float,
    LargeBinary,
    Table,
    UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
from enum import Enum as PyEnum


class Base(AsyncAttrs, DeclarativeBase):
    pass


# Association table for many-to-many between Student and Test
student_test_association = Table(
    "student_test",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("test_id", Integer, ForeignKey("tests.id"), primary_key=True),
    Column("enrolled_at", DateTime, default=datetime.utcnow, nullable=False),
)

task_group_assignment = Table(
    "task_group_assignment", Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("student_groups.id", ondelete="CASCADE"), primary_key=True),
)

task_student_assignment = Table(
    "task_student_assignment", Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", Integer, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
)


class TaskType(PyEnum):
    auto_check = "auto_check"
    code_review = "code_review"


class CheckerType(PyEnum):
    exact = "exact"
    regex = "regex"
    tokenized = "tokenized"


class AuthorType(PyEnum):
    student = "student"
    teacher = "teacher"


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tests = relationship("Test", back_populates="creator")
    groups = relationship("StudentGroup", back_populates="teacher", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="creator", foreign_keys="Task.created_by")
    # Note: We don't have a direct relationship to submissions or comments via teacher,
    # but we can get them through tests if needed.


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=True)
    group_name = Column("group", String, nullable=False, default="unassigned")
    group_id = Column(Integer, ForeignKey("student_groups.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    submissions = relationship("Submission", back_populates="student")
    code_comments = relationship("CodeComment", back_populates="student")
    code_sessions = relationship("StudentCodeSession", back_populates="student", cascade="all, delete-orphan")
    group = relationship("StudentGroup", back_populates="students")
    assigned_tasks = relationship("Task", secondary=task_student_assignment, back_populates="assigned_students")
    tests = relationship("Test", secondary=student_test_association, back_populates="students")


class StudentGroup(Base):
    __tablename__ = "student_groups"
    __table_args__ = (UniqueConstraint("teacher_id", "name", name="uq_teacher_group_name"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    teacher = relationship("Teacher", back_populates="groups")
    students = relationship("Student", back_populates="group")
    tasks = relationship("Task", secondary=task_group_assignment, back_populates="assigned_groups")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    access_code = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("Teacher", back_populates="tests")
    tasks = relationship("Task", back_populates="test", cascade="all, delete-orphan")
    students = relationship("Student", secondary=student_test_association, back_populates="tests")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(TaskType), nullable=False)
    order_index = Column(Integer, nullable=False)
    is_visible = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    test = relationship("Test", back_populates="tasks")
    creator = relationship("Teacher", back_populates="tasks", foreign_keys=[created_by])
    assigned_groups = relationship("StudentGroup", secondary=task_group_assignment, back_populates="tasks")
    assigned_students = relationship("Student", secondary=task_student_assignment, back_populates="assigned_tasks")
    auto_check_task = relationship(
        "AutoCheckTask", uselist=False, back_populates="task", cascade="all, delete-orphan"
    )
    code_review_task = relationship(
        "CodeReviewTask", uselist=False, back_populates="task", cascade="all, delete-orphan"
    )
    submissions = relationship("Submission", back_populates="task")
    code_comments = relationship("CodeComment", back_populates="task")
    grades = relationship("Grade", back_populates="task")
    code_sessions = relationship("StudentCodeSession", back_populates="task", cascade="all, delete-orphan")


class AutoCheckTask(Base):
    __tablename__ = "auto_check_tasks"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    checker_type = Column(Enum(CheckerType), nullable=False)
    expected_value = Column(Text, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="auto_check_task")


class CodeReviewTask(Base):
    __tablename__ = "code_review_tasks"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    source_code = Column(Text, nullable=False)
    language = Column(String, nullable=False)
    student_mode = Column(String, nullable=False, default="review")

    # Relationships
    task = relationship("Task", back_populates="code_review_task")


class StudentCodeSession(Base):
    __tablename__ = "student_code_sessions"
    __table_args__ = (UniqueConstraint("task_id", "student_id", name="uq_student_code_session"),)

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    source_code = Column(Text, nullable=False)
    ydoc_state = Column(LargeBinary, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    task = relationship("Task", back_populates="code_sessions")
    student = relationship("Student", back_populates="code_sessions")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")


class CodeComment(Base):
    __tablename__ = "code_comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    author_type = Column(Enum(AuthorType), nullable=False)
    line_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="code_comments")
    student = relationship("Student", back_populates="code_comments")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    score = Column(Float, nullable=False)
    teacher_comment = Column(Text, nullable=True)
    graded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="grades")
    student = relationship("Student")
