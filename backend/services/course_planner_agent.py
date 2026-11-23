import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(dotenv_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")

from services.topic_agent import extract_json_from_response
from knowledge_data.curriculum_index import (
    get_all_subjects,
    get_subject_by_id,
    get_part_by_id,
    find_best_index_match,
    build_curriculum_from_part,
    build_curriculum_from_chapter
)

def _generate_fallback_curriculum(topic: str, difficulty: str, target_audience: str) -> dict:
    """Deterministic academic syllabus fallback if LLM APIs encounter network/quota limits."""
    clean_topic = topic.strip().title()
    return {
        "course_title": f"Mastery of {clean_topic}: Principles and Practice",
        "description": f"A comprehensive curriculum covering the core principles, practical mechanics, and foundational trade-offs of {clean_topic}.",
        "difficulty": difficulty,
        "target_audience": target_audience,
        "chapters": [
            {
                "title": f"Chapter 1: Foundations & Core Intuition of {clean_topic}",
                "order_index": 1,
                "lessons": [
                    {"title": f"Introduction to {clean_topic}", "order_index": 1, "topic": f"Introduction and Core Motivation of {clean_topic}"},
                    {"title": f"Fundamental Architecture & Building Blocks", "order_index": 2, "topic": f"Core Architectural Components of {clean_topic}"}
                ]
            },
            {
                "title": f"Chapter 2: Step-by-Step Mechanics & Deep Dive",
                "order_index": 2,
                "lessons": [
                    {"title": f"How {clean_topic} Executes Under the Hood", "order_index": 1, "topic": f"Execution Mechanics of {clean_topic}"},
                    {"title": f"Key Algorithms & State Transformations", "order_index": 2, "topic": f"Algorithmic Flow of {clean_topic}"}
                ]
            },
            {
                "title": f"Chapter 3: Edge Cases, Optimization & Best Practices",
                "order_index": 3,
                "lessons": [
                    {"title": f"Common Pitfalls and Performance Bottlenecks", "order_index": 1, "topic": f"Common Pitfalls and Edge Cases in {clean_topic}"},
                    {"title": f"Synthesis, Trade-offs & Production Standards", "order_index": 2, "topic": f"Production Best Practices for {clean_topic}"}
                ]
            }
        ]
    }

from typing import Optional

def generate_course_curriculum(
    topic: str, 
    difficulty: str = "Advanced", 
    target_audience: str = "General Learners",
    num_chapters: Optional[int] = None,
    lessons_per_chapter: int = 2,
    subject_id: Optional[str] = None,
    part_id: Optional[str] = None,
    chapter_number: Optional[int] = None
) -> dict:
    """
    AGENT 1 — COURSE PLANNER AGENT
    Grounded primarily in the Master Academic Curriculum Index (DSA, DBMS, Networks, ML).
    If subject/module identifiers or an index match are found, extracts the authoritative
    textbook syllabus deterministically.
    Otherwise, leverages Groq 120B / Gemini to dynamically architect an optimal academic syllabus
    based on domain content requirements.
    """
    # 1. Direct Master Index Chapter selection (most specific)
    if subject_id and chapter_number:
        sub = get_subject_by_id(subject_id)
        if sub:
            for p in sub.get("parts", []):
                for ch in p.get("chapters", []):
                    if ch.get("chapter_number") == chapter_number:
                        print(f"\n[COURSE PLANNER] Using Master Curriculum Index for '{sub['name']}' Chapter {chapter_number}: '{ch.get('clean_title')}'", flush=True)
                        return build_curriculum_from_chapter(sub, ch, difficulty=difficulty, target_audience=target_audience)

    # 2. Direct Master Index Part/Module selection (multi-chapter module)
    if subject_id and part_id:
        sub = get_subject_by_id(subject_id)
        part = get_part_by_id(subject_id, part_id)
        if sub and part:
            print(f"\n[COURSE PLANNER] Using Master Curriculum Index for '{sub['name']}' -> '{part['title']}'", flush=True)
            return build_curriculum_from_part(sub, part, difficulty=difficulty, target_audience=target_audience)

    # 3. Fuzzy query search in Master Curriculum Index
    if topic and topic.strip():
        match = find_best_index_match(topic.strip())
        if match and match.get("matched_item"):
            match_type = match["type"]
            sub = match["subject"]
            print(f"\n[COURSE PLANNER] Grounded topic '{topic}' in Master Index ({match_type}): {match['matched_item'].get('title')}", flush=True)
            if match_type == "part":
                return build_curriculum_from_part(sub, match["part"], difficulty=difficulty, target_audience=target_audience)
            elif match_type in ("chapter", "lesson"):
                return build_curriculum_from_chapter(sub, match["chapter"], difficulty=difficulty, target_audience=target_audience)
            elif match_type == "subject":
                parts = sub.get("parts", [])
                if parts:
                    return build_curriculum_from_part(sub, parts[0], difficulty=difficulty, target_audience=target_audience)

    # 4. Fallback: Custom Topic Autonomous Curriculum Planner via Groq LPU (openai/gpt-oss-120b)
    scope_clause = (
        f"Target Scope: Exactly {num_chapters} Chapters, with {lessons_per_chapter} focused lessons per chapter."
        if num_chapters
        else "Target Scope: Dynamically determine the optimal pedagogical scope and exact number of chapters (e.g. 2, 3, 4, 5, or more chapters, with focused lessons per chapter) based strictly on the content depth required to master this topic thoroughly."
    )

    print(f"\n[COURSE PLANNER] Designing autonomous dynamic curriculum for '{topic}' ({difficulty} level)...", flush=True)

    system_instruction = (
        "You are a Chief Academic Curriculum Architect and University Professor. "
        "Your task is to design a pedagogically structured, non-redundant course syllabus. "
        "Every chapter must logically build on the preceding one: foundations first, followed by internal mechanics, then optimizations and real-world synthesis. "
        "Determine the exact number of chapters required by the topic's true academic scope. "
        "Return strictly valid JSON adhering exactly to the requested schema."
    )

    prompt = f"""
    Design a comprehensive, professional-grade course curriculum for the topic: "{topic}".
    Target Audience: {target_audience}
    {scope_clause}

    GUIDELINES:
    1. Lesson titles must be specific, conceptual, and distinct (avoid vague or duplicate titles).
    2. The progression must be linear: Chapter 1 introduces core intuition; subsequent chapters dive deeper into mechanics, algorithms, and real-world synthesis.
    3. Each lesson will be passed to a specialized AI lecture, video, and quiz generation pipeline, so specify a descriptive 'topic' for each lesson.
    4. Do NOT prepend words like "Advanced", "Beginner", or "Intermediate" to the course_title or lesson titles unless explicitly requested in the user's topic name. Keep titles clean and domain-focused.

    SCHEMA FORMAT (Return ONLY this JSON, no preamble, no markdown wrappers):
    {{
      "course_title": "Comprehensive Title for {topic}",
      "description": "2-3 sentence overview of what students will achieve in this course.",
      "difficulty": "{difficulty}",
      "target_audience": "{target_audience}",
      "chapters": [
        {{
          "title": "Chapter 1: [Descriptive Chapter Title]",
          "order_index": 1,
          "lessons": [
            {{
              "title": "Specific Lesson 1 Title",
              "order_index": 1,
              "topic": "Clear pedagogical focus for Lesson 1"
            }},
            {{
              "title": "Specific Lesson 2 Title",
              "order_index": 2,
              "topic": "Clear pedagogical focus for Lesson 2"
            }}
          ]
        }}
      ]
    }}
    """

    # Strategy 1: Groq LPU (Primary ultra-fast model)
    if GROQ_API_KEY:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2500
            )
            raw_text = resp.choices[0].message.content or ""
            data = extract_json_from_response(raw_text)
            validated = _validate_and_sanitize_curriculum(data, topic, difficulty, target_audience)
            print(f"[COURSE PLANNER] Successfully generated syllabus with {len(validated.get('chapters', []))} chapters via Groq.", flush=True)
            return validated
        except Exception as e:
            print(f"[COURSE PLANNER Warning] Groq curriculum generation failed ({e}). Attempting Gemini fallback...", flush=True)

    # Strategy 2: Google Gemini (Secondary high-capacity model)
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            gemini_resp = model.generate_content(
                f"{system_instruction}\n\n{prompt}",
                generation_config={"temperature": 0.2, "response_mime_type": "application/json"}
            )
            raw_text = gemini_resp.text
            data = extract_json_from_response(raw_text)
            validated = _validate_and_sanitize_curriculum(data, topic, difficulty, target_audience)
            print(f"[COURSE PLANNER] Successfully generated syllabus with {len(validated.get('chapters', []))} chapters via Gemini.", flush=True)
            return validated
        except Exception as e:
            print(f"[COURSE PLANNER Warning] Gemini curriculum generation failed ({e}).", flush=True)

    # Strategy 3: Deterministic fallback
    print(f"[COURSE PLANNER] Using deterministic curriculum fallback for '{topic}'.", flush=True)
    return _generate_fallback_curriculum(topic, difficulty, target_audience)

def _validate_and_sanitize_curriculum(data: dict, topic: str, difficulty: str, target_audience: str) -> dict:
    """Ensures curriculum structure conforms strictly to database relationships."""
    if not isinstance(data, dict):
        return _generate_fallback_curriculum(topic, difficulty, target_audience)

    course_title = data.get("course_title") or f"{topic.title()} Course"
    description = data.get("description") or f"Complete educational course on {topic}."
    raw_chapters = data.get("chapters", [])

    if not isinstance(raw_chapters, list) or len(raw_chapters) == 0:
        return _generate_fallback_curriculum(topic, difficulty, target_audience)

    sanitized_chapters = []
    for c_idx, ch in enumerate(raw_chapters, start=1):
        ch_title = ch.get("title") or f"Chapter {c_idx}"
        ch_order = ch.get("order_index", c_idx)
        raw_lessons = ch.get("lessons", [])
        
        sanitized_lessons = []
        for l_idx, ls in enumerate(raw_lessons, start=1):
            ls_title = ls.get("title") or f"Lesson {l_idx}"
            ls_topic = ls.get("topic") or ls_title
            ls_order = ls.get("order_index", l_idx)
            sanitized_lessons.append({
                "title": ls_title.strip(),
                "topic": ls_topic.strip(),
                "order_index": ls_order
            })
            
        if not sanitized_lessons:
            sanitized_lessons.append({
                "title": f"Overview of {ch_title}",
                "topic": f"{ch_title} principles",
                "order_index": 1
            })

        sanitized_chapters.append({
            "title": ch_title.strip(),
            "order_index": ch_order,
            "lessons": sanitized_lessons
        })

    return {
        "course_title": course_title.strip(),
        "description": description.strip(),
        "difficulty": difficulty,
        "target_audience": target_audience,
        "chapters": sanitized_chapters
    }

