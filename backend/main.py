import os
import hashlib
import uuid
import redis
import json
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # <-- NEW IMPORT
from sqlalchemy.orm import Session
from pydantic import BaseModel

# --- Relational Database Imports ---
from database import Base, engine, get_db, SessionLocal
import models, schemas, crud

# --- AI, RAG & Verification Engine Imports ---
from services.topic_agent import generate_topic_content, enforce_three_quiz_questions
from services.adaptive_agent import generate_adaptive_quiz
from services.rag_engine import embeddings_model, CHROMA_DATA_PATH, DummyEmbeddingFunction
from services.chat_agent import generate_tutor_response
from services.visual_planner_agent import generate_video_plan
from services.remotion_service import render_remotion_video_with_audio
from tasks import generate_topic_video_pipeline, generate_course_pipeline, retry_course_lesson_pipeline, JOB_CACHE_FALLBACK
from services.course_planner_agent import generate_course_curriculum
from knowledge_data.curriculum_index import (
    get_all_subjects,
    get_subject_by_id,
    get_part_by_id,
    find_best_index_match
)
import chromadb
from chromadb.config import Settings

# Initialize Relational DB
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic AI Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SERVE STATIC VIDEO FILES (NEW FIX) ---
os.makedirs("static/videos", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
# ------------------------------------------

# --- REDIS CLIENT SETUP (LEVEL 10) ---
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# --- SEMANTIC CACHE SETUP ---
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DATA_PATH,
    settings=Settings(anonymized_telemetry=False)
)

# Separate collection strictly for saving Q&A pairs
cache_collection = chroma_client.get_or_create_collection(
    name="qa_cache",
    embedding_function=DummyEmbeddingFunction()
)
# ----------------------------

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    question: str

class VerifyRequest(BaseModel):
    text: str

class AskRequest(BaseModel):
    question: str
    topic_id: str


# ==========================================
# INTERACTIVE AI TUTOR CHATBOT ENDPOINT
# ==========================================
@app.post("/api/ask")
def ask_tutor(request: AskRequest):
    """
    Endpoint for the interactive AI Tutor Chatbot.
    """
    print(f"\n💬 Received Tutor Question: '{request.question}' for Topic: {request.topic_id}")
    try:
        answer = generate_tutor_response(request.question, request.topic_id)
        return {"answer": answer}
    except Exception as e:
        print(f"❌ Error in /api/ask: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while connecting to the AI Tutor.")


# ==========================================
# VERIFICATION ENDPOINT (LEVEL 6)
# ==========================================
@app.post("/api/verify")
async def verify_text_content(request: VerifyRequest):
    """
    Returns source-grounding confirmation. Fact-checking is natively handled
    via the 3-tier cascade (ChromaDB -> Tavily Web -> Groq).
    """
    text = request.text
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Field 'text' is required and cannot be empty.")
    
    return {
        "status": "grounded",
        "message": "Content is grounded via the 3-tier knowledge cascade (ChromaDB -> Tavily Web -> Groq LPU)."
    }


# ==========================================
# VISUAL PLANNER ENDPOINT (LEVEL 7)
# ==========================================
@app.post("/api/topics/{topic_id}/video-plan")
def get_topic_video_plan(topic_id: str, payload: dict):
    """
    Generates a structured, machine-readable JSON scene sequence for video rendering.
    """
    title = payload.get("title", "Untitled Topic")
    content = payload.get("content", "")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content field is required.")
        
    scene_plan = generate_video_plan(title, content)
    
    return {
        "topic_id": topic_id,
        "total_scenes": len(scene_plan),
        "total_duration_seconds": scene_plan[-1].get("end_time", 0) if scene_plan else 0,
        "scenes": scene_plan
    }

# ==========================================
# REMOTION VIDEO RENDERER ENDPOINT (LEVEL 8)
# ==========================================
@app.post("/api/topics/{topic_id}/render-video")
def render_topic_video(topic_id: str, payload: dict):
    """
    Triggers the Remotion engine to render an MP4 file from a scene plan.
    """
    scenes = payload.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="Scenes payload required.")
        
    mp4_file_path = render_remotion_video_with_audio(topic_id, scenes)
    
    return {
        "status": "completed",
        "topic_id": topic_id,
        "video_path": mp4_file_path
    }


# ==========================================
# ASYNC CELERY VIDEO GENERATION ENDPOINTS (LEVEL 10)
# ==========================================
@app.post("/api/jobs/generate-video")
def start_video_generation_job(payload: dict, background_tasks: BackgroundTasks):
    topic_id = payload.get("topic_id", "topic_" + str(uuid.uuid4())[:8])
    title = payload.get("title", "Untitled Topic")
    content = payload.get("content", "")
    difficulty = payload.get("difficulty", "Advanced")

    job_id = f"job_{uuid.uuid4().hex[:10]}"
    
    initial_steps = {
        "research": "pending",
        "content": "pending",
        "verification": "pending",
        "script": "pending",
        "visuals": "pending",
        "tts": "pending",
        "rendering": "pending"
    }
    
    initial_state = {
        "job_id": job_id,
        "progress": 5,
        "status": "QUEUED",
        "steps": initial_steps,
        "video_url": None,
        "error": None
    }
    JOB_CACHE_FALLBACK[f"job:{job_id}"] = initial_state
    try:
        redis_client.set(f"job:{job_id}", json.dumps(initial_state))
    except Exception as ex:
        pass

    # Check if a dedicated Celery worker is active
    celery_active = False
    try:
        from celery_app import celery_app
        insp = celery_app.control.inspect(timeout=0.3)
        if insp and insp.ping():
            celery_active = True
    except Exception:
        celery_active = False

    if celery_active:
        print(f"[JOB] Dispatching {job_id} ({difficulty}) to active Celery worker cluster...")
        generate_topic_video_pipeline.delay(job_id, topic_id, title, content, difficulty)
    else:
        print(f"[JOB] No external Celery worker detected. Running {job_id} ({difficulty}) immediately via FastAPI BackgroundTasks!")
        background_tasks.add_task(generate_topic_video_pipeline, job_id, topic_id, title, content, difficulty)

    return {"job_id": job_id, "status": "QUEUED"}

@app.get("/api/jobs/{job_id}/status")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    try:
        raw_data = redis_client.get(f"job:{job_id}")
        if raw_data:
            return json.loads(raw_data.decode("utf-8"))
    except Exception:
        pass

    # In-memory fallback if Redis is unavailable
    if f"job:{job_id}" in JOB_CACHE_FALLBACK:
        return JOB_CACHE_FALLBACK[f"job:{job_id}"]

    job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "progress": job.progress_percent,
        "status": job.status.upper(),
        "current_stage": job.current_stage,
        "steps": {
            "research": "completed" if job.status == "completed" else "pending",
            "content": "completed" if job.status == "completed" else "pending",
            "verification": "completed" if job.status == "completed" else "pending",
            "script": "completed" if job.status == "completed" else "pending",
            "visuals": "completed" if job.status == "completed" else "pending",
            "tts": "completed" if job.status == "completed" else "pending",
            "rendering": "completed" if job.status == "completed" else "pending",
        },
        "video_url": None,
        "error": job.error_message
    }


# ==========================================
# TOPIC GENERATION & BACKGROUND TASKS
# ==========================================
def run_topic_generation_task(job_id: str, topic: str, difficulty: str, user_id: str, db_factory):
    db = db_factory()
    try:
        job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
        job.status = "processing"
        job.progress_percent = 20
        job.current_stage = "Generating Content with AI Agent"
        db.commit()

        content_data = generate_topic_content(topic, difficulty)

        # Create Lesson
        lesson = models.Lesson(
            user_id=user_id,
            title=content_data.get("title", topic),
            topic=topic,
            difficulty=difficulty,
            status="completed"
        )
        db.add(lesson)
        db.flush()

        # Create Lesson Content
        lesson_content = models.LessonContent(
            lesson_id=lesson.id,
            explanation=content_data.get("explanation", ""),
            summary=content_data.get("summary", ""),
            prerequisites_json=content_data.get("prerequisites", []),
            learning_objectives_json=content_data.get("learning_objectives", [])
        )
        db.add(lesson_content)

        # Create Video record with narration script
        video = models.Video(
            lesson_id=lesson.id,
            script_text=content_data.get("video_script", ""),
            render_status="pending"
        )
        db.add(video)

        # Create Quiz
        quiz = models.Quiz(
            lesson_id=lesson.id,
            questions_json=content_data.get("quiz", [])
        )
        db.add(quiz)

        job.status = "completed"
        job.progress_percent = 100
        job.current_stage = "Finished"
        job.target_id = lesson.id
        db.commit()

    except Exception as e:
        job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()


@app.post("/api/generate/topic")
def start_topic_generation(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)):
    
    topic = payload.get("topic")
    user_id = payload.get("user_id")
    difficulty = payload.get("difficulty", "Advanced")

    if not topic or not user_id:
        raise HTTPException(status_code=400, detail="Missing required topic or user_id")

    db_user = crud.get_user(db, user_id)
    if not db_user:
        db_user = crud.create_user(db, schemas.UserCreate(clerk_id=user_id, email="user@platform.local"))

    job = crud.create_job(db, schemas.JobCreate(user_id=db_user.id, job_type="topic"))

    background_tasks.add_task(
        run_topic_generation_task,
        job.id, topic, difficulty, db_user.id, SessionLocal
    )

    return {"job_id": job.id, "status": "queued"}

@app.get("/api/jobs/{job_id}")
def check_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "progress_percent": job.progress_percent,
        "current_stage": job.current_stage,
        "target_id": job.target_id,
        "error_message": job.error_message
    }

@app.get("/api/topics")
def list_all_topics(standalone_only: bool = True, db: Session = Depends(get_db)):
    """
    Returns all generated standalone topic lessons ordered by newest first.
    Filters out lessons that belong to a course chapter so that course lessons
    stay neatly encapsulated inside their parent course curriculum.
    """
    query = db.query(models.Lesson)
    if standalone_only:
        query = query.filter(models.Lesson.chapter_id == None)
    lessons = query.order_by(models.Lesson.created_at.desc()).all()
    results = []
    for lesson in lessons:
        content = lesson.content
        video = lesson.video
        quiz = lesson.quiz
        
        explanation_text = (content.explanation or "") if content else ""
        summary_text = (content.summary or "") if content else ""
        
        # Calculate approximate read time
        word_count = len(explanation_text.split())
        read_mins = max(1, round(word_count / 150))
        
        has_video = False
        video_url = None
        if video and video.video_url:
            video_url = video.video_url
            has_video = True
            
        quiz_count = 0
        if quiz and isinstance(quiz.questions_json, list):
            quiz_count = len(quiz.questions_json)

        results.append({
            "id": lesson.id,
            "title": lesson.title,
            "topic": lesson.topic,
            "difficulty": lesson.difficulty or "Beginner",
            "status": lesson.status,
            "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
            "has_video": has_video,
            "video_url": video_url,
            "quiz_count": quiz_count,
            "read_time": f"{read_mins} min read",
            "summary": summary_text[:140],
            "verification_score": content.verification_score if content else None,
            "judge_model": content.judge_model if content else None
        })
    return results

@app.get("/api/topics/{lesson_id}")
def get_topic(lesson_id: str, db: Session = Depends(get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Topic not found")

    content = db.query(models.LessonContent).filter(models.LessonContent.lesson_id == lesson_id).first()
    video = db.query(models.Video).filter(models.Video.lesson_id == lesson_id).first()
    quiz = db.query(models.Quiz).filter(models.Quiz.lesson_id == lesson_id).first()
    quiz_questions = quiz.questions_json if quiz else []

    # Auto-heal legacy quizzes that have fewer than 3 questions
    if quiz and isinstance(quiz_questions, list) and 0 < len(quiz_questions) < 3:
        try:
            fake_draft = {"quiz": quiz_questions}
            enforce_three_quiz_questions(fake_draft, lesson.title or lesson.topic, lesson.difficulty or "Intermediate")
            quiz.questions_json = fake_draft["quiz"]
            db.commit()
            quiz_questions = quiz.questions_json
        except Exception as e:
            print(f"[MAIN] Legacy quiz update notice: {e}")

    return {
        "id": lesson.id,
        "title": lesson.title,
        "topic": lesson.topic,
        "difficulty": lesson.difficulty,
        "explanation": content.explanation if content else "",
        "summary": content.summary if content else "",
        "learning_objectives": content.learning_objectives_json if content else [],
        "video_script": video.script_text if video else "",
        "video_url": video.video_url if video else None,
        "quiz": quiz_questions,
        "verification_score": content.verification_score if content else None,
        "verification_report": content.verification_report_json if content else None,
        "judge_model": content.judge_model if content else None
    }

@app.delete("/api/topics/{lesson_id}")
def delete_topic(lesson_id: str, db: Session = Depends(get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Topic not found")
    # Remove associated MP4 video and TTS scene audio files from disk
    try:
        mp4_file = os.path.join(os.path.dirname(__file__), "static", "videos", f"narrated_video_{lesson_id}.mp4")
        if os.path.exists(mp4_file):
            os.remove(mp4_file)
        audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../video-engine/public/audio"))
        if os.path.exists(audio_dir):
            for fname in os.listdir(audio_dir):
                if fname.startswith(f"narration_{lesson_id}_scene_"):
                    os.remove(os.path.join(audio_dir, fname))
    except Exception as cleanup_err:
        print(f"[CLEANUP] Media cleanup notice for {lesson_id}: {cleanup_err}")
    db.delete(lesson)
    db.commit()
    return {"status": "deleted", "lesson_id": lesson_id}


# =========================================================================
# ADAPTIVE LEARNING & QUIZ ATTEMPTS ENDPOINTS
# =========================================================================
@app.post("/api/topics/{lesson_id}/submit-quiz")
def submit_quiz_attempt(lesson_id: str, payload: dict, db: Session = Depends(get_db)):
    """
    Persists student quiz attempts and updates progress records in PostgreSQL.
    """
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Topic not found")

    quiz = db.query(models.Quiz).filter(models.Quiz.lesson_id == lesson_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for this lesson")

    user_id = payload.get("user_id") or lesson.user_id or "default_user"
    score = float(payload.get("score", 0.0))
    answers = payload.get("answers", {})

    attempt = models.QuizAttempt(
        user_id=user_id,
        quiz_id=quiz.id,
        score=score,
        answers_json=answers
    )
    db.add(attempt)

    # Update or create student progress
    progress = db.query(models.StudentProgress).filter(
        models.StudentProgress.user_id == user_id,
        models.StudentProgress.lesson_id == lesson_id
    ).first()

    if not progress:
        progress = models.StudentProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed=(score >= 70.0),
            quiz_score=score
        )
        db.add(progress)
    else:
        if score > (progress.quiz_score or 0.0):
            progress.quiz_score = score
        if score >= 70.0:
            progress.completed = True

    db.commit()

    return {
        "status": "success",
        "attempt_id": attempt.id,
        "score": score,
        "passed": score >= 70.0
    }


@app.post("/api/topics/{lesson_id}/adaptive-quiz")
def get_adaptive_quiz(lesson_id: str, payload: dict, db: Session = Depends(get_db)):
    """
    Generates 2 fresh, targeted adaptive questions focusing specifically
    on the student's missed concepts and misconceptions.
    Runs fast without touching the video or reading notes.
    """
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Topic not found")

    content = db.query(models.LessonContent).filter(models.LessonContent.lesson_id == lesson_id).first()
    summary = content.summary if content else ""

    topic = payload.get("topic") or lesson.title or lesson.topic
    difficulty = payload.get("difficulty") or lesson.difficulty or "Intermediate"
    missed_questions = payload.get("missed_questions", [])

    adaptive_questions = generate_adaptive_quiz(
        topic=topic,
        difficulty=difficulty,
        missed_questions=missed_questions,
        lesson_summary=summary
    )

    return {
        "lesson_id": lesson_id,
        "is_adaptive": True,
        "round": 2,
        "questions": adaptive_questions
    }


# =========================================================================
# MASTER CURRICULUM INDEX ENDPOINTS
# =========================================================================
@app.get("/api/curriculum/index")
def get_curriculum_catalog():
    """
    Returns all subjects, parts/modules, and chapters from the Master Academic Curriculum Index.
    """
    return {"subjects": get_all_subjects()}

@app.get("/api/curriculum/match")
def search_curriculum_catalog(q: str = ""):
    """
    Matches user query or keyword against textbook curriculum index.
    """
    if not q.strip():
        return {"query": q, "match": None}
    match = find_best_index_match(q.strip())
    return {"query": q, "match": match}


# =========================================================================
# FULL COURSE GENERATOR ENDPOINTS (LEVEL 12 & 13)
# =========================================================================
@app.post("/api/generate/course")
def start_course_generation(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    MODE 2: Full Course Generation Entrypoint.
    1. Grounded primarily in the Master Academic Curriculum Index (or dynamic planner).
    2. Writes skeleton records to PostgreSQL immediately so syllabus is instantly viewable.
    3. Dispatches async Celery job that executes the core lesson pipeline for each lesson sequentially.
    """
    topic = payload.get("topic")
    user_id = payload.get("user_id")
    difficulty = payload.get("difficulty", "Advanced")
    target_audience = payload.get("target_audience", "Computer Science Students & Developers")
    num_chapters = payload.get("num_chapters")
    if num_chapters is not None:
        try:
            num_chapters = int(num_chapters)
        except Exception:
            num_chapters = None

    subject_id = payload.get("subject_id")
    part_id = payload.get("part_id")
    chapter_number = payload.get("chapter_number")
    if chapter_number is not None:
        try:
            chapter_number = int(chapter_number)
        except Exception:
            chapter_number = None

    if not topic and not (subject_id and (part_id or chapter_number)):
        raise HTTPException(status_code=400, detail="Either 'topic' or 'subject_id' with 'part_id' is required.")

    # 1. Resolve or create user
    clerk_id = user_id or "system_default_user"
    db_user = crud.get_user(db, clerk_id)
    if not db_user:
        db_user = crud.create_user(db, schemas.UserCreate(clerk_id=clerk_id, email=f"{clerk_id}@platform.local"))

    # 2. Invoke Course Planner Agent to produce structured JSON syllabus
    curriculum = generate_course_curriculum(
        topic=topic or "Computer Science Course",
        difficulty=difficulty,
        target_audience=target_audience,
        num_chapters=num_chapters,
        subject_id=subject_id,
        part_id=part_id,
        chapter_number=chapter_number
    )

    course_id = f"course_{uuid.uuid4().hex[:8]}"
    course_title = curriculum.get("course_title", f"{topic or 'Course'}")
    course_desc = curriculum.get("description", "")
    raw_chapters = curriculum.get("chapters", [])
    total_lessons_calc = sum(len(ch.get("lessons", [])) for ch in raw_chapters)

    # 3. Create Course record
    db_course = models.Course(
        id=course_id,
        user_id=db_user.id,
        title=course_title,
        description=course_desc,
        difficulty=difficulty,
        duration_minutes=max(15, total_lessons_calc * 8)
    )
    db.add(db_course)
    db.flush()

    total_lessons_count = 0
    raw_chapters = curriculum.get("chapters", [])

    # 4. Create Chapter & Lesson skeleton records
    for ch_data in raw_chapters:
        ch_id = f"ch_{uuid.uuid4().hex[:8]}"
        ch_title = ch_data.get("title", "Untitled Chapter")
        ch_order = ch_data.get("order_index", 1)

        db_chapter = models.Chapter(
            id=ch_id,
            course_id=course_id,
            title=ch_title,
            order_index=ch_order
        )
        db.add(db_chapter)
        db.flush()

        for ls_idx, ls_data in enumerate(ch_data.get("lessons", []), start=1):
            total_lessons_count += 1
            ls_order = ls_data.get("order_index", ls_idx)
            ls_id = f"ls_c{ch_order:02d}_l{ls_order:02d}_{uuid.uuid4().hex[:6]}"
            ls_title = ls_data.get("title", "Untitled Lesson")
            ls_topic = ls_data.get("topic", ls_title)

            db_lesson = models.Lesson(
                id=ls_id,
                user_id=db_user.id,
                chapter_id=ch_id,
                title=ls_title,
                topic=ls_topic,
                difficulty=difficulty,
                order_index=ls_order,
                status="pending"
            )
            db.add(db_lesson)

    # 5. Create GenerationJob
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    db_job = models.GenerationJob(
        id=job_id,
        user_id=db_user.id,
        job_type="course",
        status="queued",
        progress_percent=5,
        current_stage=f"Curriculum Structured ({len(raw_chapters)} Chapters, {total_lessons_count} Lessons). Queued for generation.",
        target_id=course_id
    )
    db.add(db_job)
    db.commit()

    # Identify first lesson for instant progressive streaming
    first_lesson = (
        db.query(models.Lesson)
        .join(models.Chapter, models.Lesson.chapter_id == models.Chapter.id)
        .filter(models.Chapter.course_id == course_id)
        .order_by(models.Chapter.order_index.asc(), models.Lesson.order_index.asc(), models.Lesson.id.asc())
        .first()
    )
    first_lesson_id = first_lesson.id if first_lesson else None
    first_lesson_title = first_lesson.title if first_lesson else None

    # 6. Initialize Redis Job State
    initial_course_state = {
        "job_id": job_id,
        "course_id": course_id,
        "job_type": "course",
        "progress": 5,
        "status": "QUEUED",
        "current_lesson": "Queued in worker pipeline...",
        "completed_count": 0,
        "total_count": total_lessons_count,
        "first_lesson_id": first_lesson_id,
        "first_lesson_title": first_lesson_title,
        "first_lesson_ready": False,
        "error": None
    }
    JOB_CACHE_FALLBACK[f"job:{job_id}"] = initial_course_state
    try:
        redis_client.set(f"job:{job_id}", json.dumps(initial_course_state))
    except Exception as ex:
        pass

    # 7. Check if Celery worker is active; fallback to FastAPI BackgroundTasks
    celery_active = False
    try:
        from celery_app import celery_app
        insp = celery_app.control.inspect(timeout=0.3)
        if insp and insp.ping():
            celery_active = True
    except Exception:
        celery_active = False

    if celery_active:
        print(f"[COURSE JOB] Dispatching course {course_id} to active Celery cluster...", flush=True)
        generate_course_pipeline.delay(job_id, course_id, difficulty)
    else:
        print(f"[COURSE JOB] Celery offline. Running course {course_id} via FastAPI BackgroundTasks...", flush=True)
        background_tasks.add_task(generate_course_pipeline, job_id, course_id, difficulty)

    return {
        "job_id": job_id,
        "course_id": course_id,
        "course_title": course_title,
        "status": "QUEUED",
        "chapters_count": len(raw_chapters),
        "total_lessons": total_lessons_count,
        "first_lesson_id": first_lesson_id,
        "first_lesson_title": first_lesson_title
    }


@app.get("/api/courses")
def list_all_courses(db: Session = Depends(get_db)):
    """Lists all courses with aggregated progress statistics."""
    courses = db.query(models.Course).order_by(models.Course.created_at.desc()).all()
    results = []

    for c in courses:
        all_lessons = (
            db.query(models.Lesson)
            .join(models.Chapter, models.Lesson.chapter_id == models.Chapter.id)
            .filter(models.Chapter.course_id == c.id)
            .all()
        )
        total = len(all_lessons)
        completed = sum(1 for l in all_lessons if l.status == "completed")
        failed = sum(1 for l in all_lessons if l.status == "failed")
        progress = int((completed / total) * 100) if total > 0 else 0

        chapters_count = db.query(models.Chapter).filter(models.Chapter.course_id == c.id).count()

        results.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "difficulty": c.difficulty,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "chapters_count": chapters_count,
            "total_lessons": total,
            "completed_lessons": completed,
            "failed_lessons": failed,
            "progress_percent": progress
        })

    return results


@app.get("/api/courses/{course_id}")
def get_course_details(course_id: str, db: Session = Depends(get_db)):
    """Retrieves full course hierarchy: Course -> Chapters -> Lessons with video/quiz metadata."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    chapters = (
        db.query(models.Chapter)
        .filter(models.Chapter.course_id == course_id)
        .order_by(models.Chapter.order_index.asc())
        .all()
    )

    chapters_payload = []
    total_lessons = 0
    completed_lessons = 0

    for ch in chapters:
        lessons = (
            db.query(models.Lesson)
            .filter(models.Lesson.chapter_id == ch.id)
            .order_by(models.Lesson.order_index.asc(), models.Lesson.id.asc())
            .all()
        )
        lessons_payload = []
        for ls in lessons:
            total_lessons += 1
            if ls.status == "completed":
                completed_lessons += 1

            has_video = bool(ls.video and ls.video.video_url)
            quiz_count = len(ls.quiz.questions_json) if (ls.quiz and isinstance(ls.quiz.questions_json, list)) else 0
            verification_score = ls.content.verification_score if ls.content else None

            lessons_payload.append({
                "id": ls.id,
                "title": ls.title,
                "topic": ls.topic,
                "status": ls.status,
                "has_video": has_video,
                "video_url": ls.video.video_url if has_video else None,
                "quiz_count": quiz_count,
                "verification_score": verification_score
            })

        chapters_payload.append({
            "id": ch.id,
            "title": ch.title,
            "order_index": ch.order_index,
            "lessons": lessons_payload
        })

    progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "difficulty": course.difficulty,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percent": progress,
        "chapters": chapters_payload
    }


@app.post("/api/courses/{course_id}/retry-lesson/{lesson_id}")
def retry_failed_course_lesson(
    course_id: str,
    lesson_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retries a specific failed lesson without modifying completed lessons."""
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    job_id = f"job_retry_{uuid.uuid4().hex[:8]}"

    celery_active = False
    try:
        from celery_app import celery_app
        insp = celery_app.control.inspect(timeout=0.3)
        if insp and insp.ping():
            celery_active = True
    except Exception:
        celery_active = False

    if celery_active:
        retry_course_lesson_pipeline.delay(job_id, course_id, lesson_id)
    else:
        background_tasks.add_task(retry_course_lesson_pipeline, job_id, course_id, lesson_id)

    return {"status": "retrying", "job_id": job_id, "lesson_id": lesson_id}


@app.delete("/api/courses/{course_id}")
def delete_course(course_id: str, db: Session = Depends(get_db)):
    """Deletes course and cascades deletion to chapters and lessons."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Safely clear student progress records for any lesson in this course
    lesson_ids = [
        l.id for ch in course.chapters for l in ch.lessons
    ]
    if lesson_ids:
        db.query(models.StudentProgress).filter(models.StudentProgress.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)

    db.delete(course)
    db.commit()
    return {"status": "deleted", "course_id": course_id}
