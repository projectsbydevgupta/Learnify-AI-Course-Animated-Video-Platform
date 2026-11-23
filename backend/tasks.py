import time
import json
import redis
import os
from celery_app import celery_app
from services.topic_agent import generate_topic_content
from services.judge_agent import evaluate_lesson_with_judge
from services.visual_planner_agent import generate_video_plan
from services.remotion_service import render_remotion_from_synced_scenes
from services.tts_service import process_tts_and_sync_scenes

# Database imports matching models.py schema
from database import SessionLocal
from models import Lesson, LessonContent, Video, Quiz, User, Course, Chapter, GenerationJob
from sqlalchemy.sql import func

# Connect to Redis to send progress updates
r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# In-memory job state cache used when Redis/Docker is not running
JOB_CACHE_FALLBACK: dict[str, dict] = {}

def update_job_status(job_id: str, progress: int, status: str, steps: dict, video_url: str = None, error: str = None):
    """Saves the current progress percentage and step status to Redis with safe in-memory fallback."""
    payload = {
        "job_id": job_id,
        "progress": progress,
        "status": status,
        "steps": steps,
        "video_url": video_url,
        "error": error
    }
    JOB_CACHE_FALLBACK[f"job:{job_id}"] = payload
    try:
        r.set(f"job:{job_id}", json.dumps(payload))
    except Exception as ex:
        pass

def update_course_job_status(job_id: str, course_id: str, progress: int, status: str, current_lesson: str, completed_count: int, total_count: int, first_lesson_id: str = None, first_lesson_ready: bool = False, latest_completed_lesson_id: str = None, error: str = None):
    """Saves course-level generation progress and lesson checkpoints to Redis with safe in-memory fallback."""
    payload = {
        "job_id": job_id,
        "course_id": course_id,
        "job_type": "course",
        "progress": progress,
        "status": status,
        "current_lesson": current_lesson,
        "completed_count": completed_count,
        "total_count": total_count,
        "first_lesson_id": first_lesson_id,
        "first_lesson_ready": first_lesson_ready,
        "latest_completed_lesson_id": latest_completed_lesson_id,
        "error": error
    }
    JOB_CACHE_FALLBACK[f"job:{job_id}"] = payload
    try:
        r.set(f"job:{job_id}", json.dumps(payload))
    except Exception as ex:
        pass


# =========================================================================
# CORE REUSABLE LESSON SUB-PIPELINE (SHARED BY SINGLE TOPIC & FULL COURSE)
# =========================================================================
def execute_single_lesson_subpipeline(topic_id: str, title: str, difficulty: str = "Beginner", raw_content: str = None, step_callback=None) -> dict:
    """
    The unified core lesson generation pipeline:
    1. Research & Content Generation (Groq / RAG / Web)
    2. Academic Quality Gate Verification (LLM-as-a-Judge Gemini with auto-refine)
    3. Visual Scene Planning (Remotion scene blueprints)
    4. Neural TTS Synthesis & Millisecond Audio Cadence Synchronization
    5. Headless Remotion 1080p Video Rendering
    6. Relational PostgreSQL Persistence (Lesson, LessonContent, Video, Quiz)
    """
    def notify_step(step_name: str, status_msg: str):
        if step_callback:
            step_callback(step_name, status_msg)

    # 1. Research & Content Generation
    notify_step("content", f"Drafting Comprehensive Lesson for '{title}'...")
    content_data = generate_topic_content(title, difficulty)

    # 2. LLM-as-a-Judge Academic Verification
    notify_step("verification", "Auditing lesson with LLM-as-a-Judge (Gemini)...")
    grounding_ctx = content_data.get("grounding_context", "")
    judge_report = evaluate_lesson_with_judge(title, difficulty, grounding_ctx, content_data)
    judge_score = judge_report.get("overall_percentage", 90)
    judge_verdict = judge_report.get("verdict", "PASSED")

    # Quality Gate: Auto-refine if score is below 75%
    if judge_score < 75 or judge_verdict == "NEEDS_REVISION":
        print(f"[Quality Gate] Score {judge_score}% below threshold ({judge_verdict}) for '{title}'. Refining...", flush=True)
        notify_step("verification", f"Score {judge_score}% below threshold. Refining lesson with Judge critique...")
        content_data = generate_topic_content(title, difficulty, revision_feedback=judge_report)
        grounding_ctx = content_data.get("grounding_context", "")
        judge_report = evaluate_lesson_with_judge(title, difficulty, grounding_ctx, content_data)
        judge_score = judge_report.get("overall_percentage", 90)
        judge_verdict = judge_report.get("verdict", "PASSED")

    # 3. Script & Visual Scene Planning
    notify_step("script", "Formulating 8-Scene Educational Narration & Timing Scripts...")
    video_script_text = content_data.get("video_script", raw_content or title)
    
    notify_step("visuals", "Planning Interactive Visual Scene Blueprints...")
    scene_plan = generate_video_plan(title, video_script_text, difficulty=difficulty)

    # 4. Neural Voiceover Synthesis & Audio Cadence Synchronization
    notify_step("tts", "Synthesizing Neural Voiceovers & Measuring Audio Cadence...")
    synced_scenes = process_tts_and_sync_scenes(topic_id, scene_plan)

    # 5. Remotion 1080p Video Rendering
    notify_step("rendering", "Rendering 1080p Animated Video in Remotion...")
    output_mp4 = render_remotion_from_synced_scenes(topic_id, synced_scenes)
    video_relative_url = f"/static/videos/narrated_video_{topic_id}.mp4"

    # 6. Save complete entities to PostgreSQL database
    db = SessionLocal()
    try:
        default_user = db.query(User).first()
        user_id = default_user.id if default_user else "system_generated"

        # Create or Update Lesson
        db_lesson = db.query(Lesson).filter(Lesson.id == topic_id).first()
        if not db_lesson:
            db_lesson = Lesson(
                id=topic_id,
                title=content_data.get("title", title),
                topic=title,
                difficulty=difficulty,
                user_id=user_id,
                status="completed"
            )
            db.add(db_lesson)
        else:
            db_lesson.title = content_data.get("title", title)
            db_lesson.topic = title
            db_lesson.difficulty = difficulty
            db_lesson.status = "completed"
            db_lesson.created_at = func.now()
        db.commit()

        # Create or Update Lesson Content
        db_content = db.query(LessonContent).filter(LessonContent.lesson_id == topic_id).first()
        explanation_text = content_data.get("explanation", "")
        summary_text = content_data.get("summary", "")
        objectives = content_data.get("learning_objectives", [])
        prerequisites = content_data.get("prerequisites", [])

        if not db_content:
            db_content = LessonContent(
                lesson_id=topic_id,
                explanation=explanation_text,
                summary=summary_text,
                learning_objectives_json=objectives,
                prerequisites_json=prerequisites,
                verification_score=judge_score,
                verification_report_json=judge_report,
                judge_model=judge_report.get("judge_model", "Google Gemini")
            )
            db.add(db_content)
        else:
            db_content.explanation = explanation_text
            db_content.summary = summary_text
            db_content.learning_objectives_json = objectives
            db_content.prerequisites_json = prerequisites
            db_content.verification_score = judge_score
            db_content.verification_report_json = judge_report
            db_content.judge_model = judge_report.get("judge_model", "Google Gemini")

        # Create or Update Video
        db_video = db.query(Video).filter(Video.lesson_id == topic_id).first()
        if not db_video:
            db_video = Video(
                lesson_id=topic_id,
                video_url=video_relative_url,
                script_text=video_script_text,
                scene_plan_json=synced_scenes,
                render_status="completed"
            )
            db.add(db_video)
        else:
            db_video.video_url = video_relative_url
            db_video.script_text = video_script_text
            db_video.scene_plan_json = synced_scenes
            db_video.render_status = "completed"

        # Create or Update Quiz
        db_quiz = db.query(Quiz).filter(Quiz.lesson_id == topic_id).first()
        quiz_questions = content_data.get("quiz", [])
        if not db_quiz:
            db_quiz = Quiz(
                lesson_id=topic_id,
                questions_json=quiz_questions
            )
            db.add(db_quiz)
        else:
            db_quiz.questions_json = quiz_questions

        db.commit()
    finally:
        db.close()

    return {
        "topic_id": topic_id,
        "video_url": video_relative_url,
        "judge_score": judge_score,
        "output_mp4": output_mp4
    }


# =========================================================================
# MODE 1: SINGLE TOPIC PIPELINE (UNCHANGED BEHAVIOR & INTERFACE)
# =========================================================================
@celery_app.task(name="tasks.generate_topic_video_pipeline")
def generate_topic_video_pipeline(job_id: str, topic_id: str, title: str, raw_content: str, difficulty: str = "Beginner"):
    """Background task running single topic generation."""
    steps = {
        "research": "pending",
        "content": "pending",
        "verification": "pending",
        "script": "pending",
        "visuals": "pending",
        "tts": "pending",
        "rendering": "pending"
    }

    step_order = ["research", "content", "verification", "script", "visuals", "tts", "rendering"]

    def step_cb(step_name: str, msg: str):
        if step_name in step_order:
            idx = step_order.index(step_name)
            for i in range(idx):
                steps[step_order[i]] = "completed"
            steps[step_name] = "in_progress"
            for i in range(idx + 1, len(step_order)):
                steps[step_order[i]] = "pending"
        progress_map = {
            "content": 25,
            "verification": 48,
            "visuals": 65,
            "tts": 75,
            "rendering": 88
        }
        update_job_status(job_id, progress_map.get(step_name, 50), msg, steps)

    try:
        steps["research"] = "in_progress"
        update_job_status(job_id, 15, "Formulating Topic Curriculum & Knowledge Base...", steps)
        steps["research"] = "completed"

        res = execute_single_lesson_subpipeline(
            topic_id=topic_id,
            title=title,
            difficulty=difficulty,
            raw_content=raw_content,
            step_callback=step_cb
        )

        for s in steps:
            steps[s] = "completed"

        update_job_status(job_id, 100, "COMPLETED", steps, video_url=res.get("video_url"))
    except Exception as e:
        update_job_status(job_id, 0, "FAILED", steps, error=str(e))
        raise e


# =========================================================================
# MODE 2: FULL COURSE GENERATION PIPELINE (LEVEL 12)
# =========================================================================
@celery_app.task(name="tasks.generate_course_pipeline")
def generate_course_pipeline(job_id: str, course_id: str, difficulty: str = "Beginner"):
    """
    Executes the full course generation workflow:
    1. Loads the Course, Chapters, and pre-allocated Lessons from PostgreSQL.
    2. Sequentially executes the CORE lesson sub-pipeline for each pending lesson.
    3. Preserves completed lessons on partial failure (Resume & Fault Tolerance).
    """
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            update_course_job_status(job_id, course_id, 0, "FAILED", "", 0, 0, error="Course not found in database.")
            return

        # Fetch all lessons ordered by chapter and order index
        lessons = (
            db.query(Lesson)
            .join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(Chapter.course_id == course_id)
            .order_by(Chapter.order_index.asc(), Lesson.order_index.asc(), Lesson.id.asc())
            .all()
        )
        total_lessons = len(lessons)
        first_lesson = lessons[0] if lessons else None
        first_lesson_id = first_lesson.id if first_lesson else None
        first_lesson_ready = (first_lesson.status == "completed") if first_lesson else False

        if total_lessons == 0:
            update_course_job_status(job_id, course_id, 100, "COMPLETED", "No lessons to generate", 0, 0)
            return

        print(f"\n[COURSE WORKER] Commencing course pipeline for '{course.title}' ({total_lessons} total lessons)...", flush=True)

        failed_lessons = []
        completed_count = sum(1 for l in lessons if l.status == "completed")

        for idx, lesson in enumerate(lessons, start=1):
            # Checkpoint recovery: skip lessons that are already completed
            if lesson.status == "completed":
                print(f"[COURSE WORKER] Lesson {idx}/{total_lessons} ('{lesson.title}') is already completed. Skipping.", flush=True)
                if lesson.id == first_lesson_id:
                    first_lesson_ready = True
                continue

            lesson_progress = int(((idx - 1) / total_lessons) * 100)
            update_course_job_status(
                job_id, course_id, lesson_progress, "PROCESSING", 
                f"Generating Lesson {idx}/{total_lessons}: '{lesson.title}'", 
                completed_count, total_lessons,
                first_lesson_id=first_lesson_id,
                first_lesson_ready=first_lesson_ready
            )

            # Mark lesson in progress
            lesson.status = "processing"
            db.commit()

            try:
                print(f"\n[COURSE WORKER] Executing Lesson {idx}/{total_lessons}: '{lesson.title}' ({lesson.id})...", flush=True)
                execute_single_lesson_subpipeline(
                    topic_id=lesson.id,
                    title=lesson.title,
                    difficulty=difficulty or course.difficulty or "Advanced"
                )
                lesson.status = "completed"
                db.commit()
                completed_count += 1
                if lesson.id == first_lesson_id or idx == 1:
                    first_lesson_ready = True

                # Immediately notify Redis that this lesson is completed!
                current_prog = int((completed_count / total_lessons) * 100)
                update_course_job_status(
                    job_id, course_id, current_prog, "PROCESSING",
                    f"Completed Lesson {idx}/{total_lessons}: '{lesson.title}'. Preparing next module...",
                    completed_count, total_lessons,
                    first_lesson_id=first_lesson_id,
                    first_lesson_ready=first_lesson_ready,
                    latest_completed_lesson_id=lesson.id
                )
                print(f"[COURSE WORKER] Lesson {idx}/{total_lessons} ('{lesson.title}') finished successfully! (first_ready={first_lesson_ready})", flush=True)
            except Exception as ex:
                print(f"[COURSE WORKER ERROR] Lesson {idx}/{total_lessons} ('{lesson.title}') failed: {ex}", flush=True)
                lesson.status = "failed"
                db.commit()
                failed_lessons.append({"lesson_id": lesson.id, "title": lesson.title, "error": str(ex)})

        # Update Job in PostgreSQL
        gen_job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if gen_job:
            gen_job.progress_percent = 100
            if failed_lessons:
                gen_job.status = "completed_with_errors"
                gen_job.error_message = json.dumps(failed_lessons)
                gen_job.current_stage = f"Completed {completed_count}/{total_lessons} lessons ({len(failed_lessons)} failed - retry available)"
            else:
                gen_job.status = "completed"
                gen_job.current_stage = "All lessons and videos generated successfully!"
            db.commit()

        final_status = "COMPLETED" if not failed_lessons else "PARTIAL_FAILURE"
        update_course_job_status(
            job_id, course_id, 100, final_status, 
            "Course generation complete!" if not failed_lessons else f"{len(failed_lessons)} lessons require retry.",
            completed_count, total_lessons,
            first_lesson_id=first_lesson_id,
            first_lesson_ready=True if completed_count > 0 else False,
            error=json.dumps(failed_lessons) if failed_lessons else None
        )
        print(f"[COURSE WORKER] Course '{course.title}' execution finished. Status: {final_status} ({completed_count}/{total_lessons} completed).", flush=True)

    finally:
        db.close()


# =========================================================================
# MODE 2: RETRY SINGLE FAILED COURSE LESSON (LEVEL 11 & 12 RESILIENCE)
# =========================================================================
@celery_app.task(name="tasks.retry_course_lesson_pipeline")
def retry_course_lesson_pipeline(job_id: str, course_id: str, lesson_id: str):
    """Retries a specific failed lesson without re-running completed lessons."""
    db = SessionLocal()
    try:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            update_course_job_status(job_id, course_id, 0, "FAILED", "", 0, 0, error="Lesson not found.")
            return

        course = db.query(Course).filter(Course.id == course_id).first()
        difficulty = course.difficulty if course else "Beginner"

        lesson.status = "processing"
        db.commit()

        update_course_job_status(job_id, course_id, 50, "RETRYING", f"Retrying lesson '{lesson.title}'...", 0, 1)

        execute_single_lesson_subpipeline(
            topic_id=lesson.id,
            title=lesson.title,
            difficulty=difficulty
        )

        lesson.status = "completed"
        db.commit()

        update_course_job_status(job_id, course_id, 100, "COMPLETED", f"Lesson '{lesson.title}' successfully recovered!", 1, 1)
        print(f"[COURSE WORKER] Successfully recovered failed lesson '{lesson.title}' ({lesson.id})!", flush=True)
    except Exception as e:
        lesson.status = "failed"
        db.commit()
        update_course_job_status(job_id, course_id, 0, "FAILED", "", 0, 1, error=str(e))
        raise e
    finally:
        db.close()
