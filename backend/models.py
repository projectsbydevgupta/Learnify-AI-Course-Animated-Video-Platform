import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    clerk_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    courses = relationship("Course", back_populates="user", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("GenerationJob", back_populates="user", cascade="all, delete-orphan")

class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String, default="Beginner")
    duration_minutes = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="courses")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String, primary_key=True, default=generate_uuid)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)

    course = relationship("Course", back_populates="chapters")
    lessons = relationship("Lesson", back_populates="chapter", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)  # Nullable for single topics
    title = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, default="Beginner")
    order_index = Column(Integer, default=1)
    status = Column(String, default="pending")  # pending, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="lessons")
    chapter = relationship("Chapter", back_populates="lessons")
    content = relationship("LessonContent", back_populates="lesson", uselist=False, cascade="all, delete-orphan")
    video = relationship("Video", back_populates="lesson", uselist=False, cascade="all, delete-orphan")
    quiz = relationship("Quiz", back_populates="lesson", uselist=False, cascade="all, delete-orphan")

class LessonContent(Base):
    __tablename__ = "lesson_contents"

    id = Column(String, primary_key=True, default=generate_uuid)
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False, unique=True)
    explanation = Column(Text, nullable=False)
    examples_json = Column(JSON, nullable=True)
    learning_objectives_json = Column(JSON, nullable=True)
    prerequisites_json = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    verification_score = Column(Integer, nullable=True)
    verification_report_json = Column(JSON, nullable=True)
    judge_model = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lesson = relationship("Lesson", back_populates="content")

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=generate_uuid)
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False, unique=True)
    video_url = Column(String, nullable=True)
    script_text = Column(Text, nullable=True)
    scene_plan_json = Column(JSON, nullable=True)
    render_status = Column(String, default="pending")  # pending, rendering, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lesson = relationship("Lesson", back_populates="video")

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, default=generate_uuid)
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False, unique=True)
    questions_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lesson = relationship("Lesson", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Float, nullable=False)
    answers_json = Column(JSON, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    quiz = relationship("Quiz", back_populates="attempts")

class StudentProgress(Base):
    __tablename__ = "student_progress"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False)
    completed = Column(Boolean, default=False)
    quiz_score = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    job_type = Column(String, nullable=False)  # "topic" or "course"
    status = Column(String, default="pending")  # pending, processing, completed, failed
    progress_percent = Column(Integer, default=0)
    current_stage = Column(String, default="initialized")
    error_message = Column(Text, nullable=True)
    target_id = Column(String, nullable=True)  # ID of generated Lesson or Course
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="jobs")
    agent_runs = relationship("AgentRun", back_populates="job", cascade="all, delete-orphan")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, ForeignKey("generation_jobs.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    status = Column(String, default="running")  # running, completed, failed
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("GenerationJob", back_populates="agent_runs")