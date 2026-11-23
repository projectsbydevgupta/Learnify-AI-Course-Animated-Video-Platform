"""
Master Academic Curriculum Index Registry
Provides textbook-grade, pre-verified course and module hierarchies
for Computer Science core subjects: DSA, DBMS, Computer Networks, and Machine Learning.
References: CLRS, Silberschatz, Kurose & Ross, Stanford CS 229, Goodfellow.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any

_INDEX_PATH = os.path.join(os.path.dirname(__file__), "curriculum_index_data.json")

# In-memory cached index
_CURRICULUM_DATA: Optional[Dict[str, Any]] = None

SUBJECT_METADATA = {
    "dsa": {
        "icon": "💻",
        "name": "Data Structures & Algorithms",
        "code": "CS-201",
        "textbook": "Introduction to Algorithms (Cormen, Leiserson, Rivest, Stein - CLRS) & MIT 6.006",
        "description": "Foundational programming primitives, linear & hierarchical data structures, sorting, recursion, dynamic programming, and complexity bounds."
    },
    "dbms": {
        "icon": "🗄️",
        "name": "Database Management Systems",
        "code": "CS-302",
        "textbook": "Database System Concepts (Silberschatz, Korth, Sudarshan) & Stanford CS 145",
        "description": "Relational algebra, SQL, normalization (1NF-BCNF), B+ tree storage, ACID transactions, and write-ahead log recovery."
    },
    "networks": {
        "icon": "🌐",
        "name": "Computer Networks",
        "code": "CS-305",
        "textbook": "Computer Networking: A Top-Down Approach (Kurose & Ross)",
        "description": "5-layer protocol stack, socket programming, TCP flow/congestion control, IP routing algorithms, Ethernet switching, and network security."
    },
    "machine_learning": {
        "icon": "🧠",
        "name": "Machine Learning & Deep Learning",
        "code": "CS-421",
        "textbook": "Pattern Recognition (Bishop), Stanford CS 229 & Deep Learning (Goodfellow)",
        "description": "Supervised regression & classification, tree ensembles, unsupervised dimensionality reduction, neural backpropagation, CNNs, and Transformers."
    }
}

def load_curriculum_index() -> Dict[str, Any]:
    global _CURRICULUM_DATA
    if _CURRICULUM_DATA is not None:
        return _CURRICULUM_DATA

    if not os.path.exists(_INDEX_PATH):
        raise FileNotFoundError(f"Curriculum data file not found at {_INDEX_PATH}")

    with open(_INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Attach rich metadata
    for sub in data.get("subjects", []):
        sub_id = sub.get("id")
        meta = SUBJECT_METADATA.get(sub_id, {})
        sub["icon"] = meta.get("icon", "📚")
        sub["name"] = meta.get("name", sub.get("title", ""))
        sub["code"] = meta.get("code", "CS-101")
        sub["textbook"] = meta.get("textbook", "Standard Academic Reference")
        sub["description"] = meta.get("description", sub.get("title", ""))
        
        # Calculate totals
        total_chapters = 0
        total_lessons = 0
        for part in sub.get("parts", []):
            part_chapters = len(part.get("chapters", []))
            part_lessons = sum(len(ch.get("lessons", [])) for ch in part.get("chapters", []))
            part["total_chapters"] = part_chapters
            part["total_lessons"] = part_lessons
            total_chapters += part_chapters
            total_lessons += part_lessons

        sub["total_chapters"] = total_chapters
        sub["total_lessons"] = total_lessons

    _CURRICULUM_DATA = data
    return _CURRICULUM_DATA


def get_all_subjects() -> List[Dict[str, Any]]:
    """Returns all 4 subjects with parts, chapters, and summary stats."""
    return load_curriculum_index().get("subjects", [])


def get_subject_by_id(subject_id: str) -> Optional[Dict[str, Any]]:
    """Finds subject by ID (dsa, dbms, networks, machine_learning)."""
    subjects = get_all_subjects()
    norm = subject_id.lower().strip()
    for s in subjects:
        if s["id"] == norm:
            return s
    return None


def get_part_by_id(subject_id: str, part_id: str) -> Optional[Dict[str, Any]]:
    """Finds a specific part/module within a subject."""
    sub = get_subject_by_id(subject_id)
    if not sub:
        return None
    for part in sub.get("parts", []):
        if part["id"] == part_id:
            return part
    return None


def find_best_index_match(query: str) -> Optional[Dict[str, Any]]:
    """
    Intelligently matches a search query to a Subject, Part, or Chapter in the index.
    Allows students to type e.g. "Linked Lists" or "B+ Tree" or "TCP" and instantly match
    the authoritative textbook module.
    """
    if not query:
        return None

    q_lower = query.lower().strip()
    words = [w for w in re.split(r"\W+", q_lower) if len(w) > 2]
    subjects = get_all_subjects()

    best_match = None
    highest_score = 0

    for sub in subjects:
        # Match subject
        if q_lower in sub["title"].lower() or q_lower in sub["id"]:
            score = 10
            if score > highest_score:
                highest_score = score
                best_match = {
                    "type": "subject",
                    "subject": sub,
                    "matched_item": sub
                }

        for part in sub.get("parts", []):
            part_title_lower = part["title"].lower()
            # Direct part title match
            if q_lower in part_title_lower:
                score = 30
                if score > highest_score:
                    highest_score = score
                    best_match = {
                        "type": "part",
                        "subject": sub,
                        "part": part,
                        "matched_item": part
                    }

            # Check individual chapters
            for ch in part.get("chapters", []):
                ch_title_lower = ch["title"].lower()
                clean_title_lower = ch.get("clean_title", "").lower()

                if q_lower in clean_title_lower or q_lower in ch_title_lower:
                    score = 50
                    if score > highest_score:
                        highest_score = score
                        best_match = {
                            "type": "chapter",
                            "subject": sub,
                            "part": part,
                            "chapter": ch,
                            "matched_item": ch
                        }

                # Word overlap in chapter clean title
                overlap = sum(1 for w in words if w in clean_title_lower)
                if overlap > 0:
                    score = 20 + (overlap * 5)
                    if score > highest_score:
                        highest_score = score
                        best_match = {
                            "type": "chapter",
                            "subject": sub,
                            "part": part,
                            "chapter": ch,
                            "matched_item": ch
                        }

                # Check lesson titles
                for ls in ch.get("lessons", []):
                    ls_title_lower = ls["title"].lower()
                    if q_lower in ls_title_lower:
                        score = 45
                        if score > highest_score:
                            highest_score = score
                            best_match = {
                                "type": "lesson",
                                "subject": sub,
                                "part": part,
                                "chapter": ch,
                                "lesson": ls,
                                "matched_item": ls
                            }

    return best_match


def build_curriculum_from_part(
    subject: Dict[str, Any],
    part: Dict[str, Any],
    difficulty: str = "Advanced",
    target_audience: str = "Computer Science Students & Developers"
) -> Dict[str, Any]:
    """
    Constructs a deterministic, complete course syllabus from an academic Part/Module.
    Chapters and lessons are 100% faithful to the textbook index.
    """
    # Clean up part title, e.g. "PART TWO ■ LINEAR DATA STRUCTURES" -> "Linear Data Structures"
    clean_part_name = re.sub(r"^PART\s+[A-Z]+\s*[■\-–:]*\s*", "", part.get("title", "")).strip().title()
    course_title = f"{subject['name']}: {clean_part_name}"
    description = (
        f"A master-level course covering {clean_part_name} from {subject['name']}. "
        f"Curriculum follows {subject.get('textbook', 'standard academic benchmarks')}."
    )

    chapters = []
    for c_idx, ch in enumerate(part.get("chapters", []), start=1):
        ch_title = f"Chapter {c_idx}: {ch.get('clean_title', ch.get('title'))}"
        lessons = []
        for l_idx, ls in enumerate(ch.get("lessons", []), start=1):
            ls_title = ls.get("title")
            lessons.append({
                "title": ls_title,
                "order_index": l_idx,
                "topic": f"{ls_title} in {ch.get('clean_title')} ({subject['name']})"
            })
        chapters.append({
            "title": ch_title,
            "order_index": c_idx,
            "lessons": lessons
        })

    return {
        "course_title": course_title,
        "description": description,
        "difficulty": difficulty,
        "target_audience": target_audience,
        "source": "master_curriculum_index",
        "subject_id": subject["id"],
        "part_id": part["id"],
        "chapters": chapters
    }


def build_curriculum_from_chapter(
    subject: Dict[str, Any],
    chapter: Dict[str, Any],
    difficulty: str = "Advanced",
    target_audience: str = "Computer Science Students & Developers"
) -> Dict[str, Any]:
    """
    Constructs a specialized course focused on a single extensive textbook Chapter.
    Breaks the lessons logically into sub-units.
    """
    clean_title = chapter.get("clean_title", chapter.get("title"))
    course_title = f"Mastery of {clean_title} ({subject['name']})"
    description = (
        f"In-depth academic module on {clean_title}. "
        f"Grounded in {subject.get('textbook', 'university curriculum standards')}."
    )

    lessons = chapter.get("lessons", [])
    # If a chapter has many lessons (e.g. 5 lessons), we can present it as a cohesive multi-part chapter
    formatted_lessons = [
        {
            "title": ls.get("title"),
            "order_index": idx,
            "topic": f"{ls.get('title')} ({clean_title}, {subject['name']})"
        }
        for idx, ls in enumerate(lessons, start=1)
    ]

    chapters = [
        {
            "title": f"Chapter 1: {clean_title} Core Principles & Implementation",
            "order_index": 1,
            "lessons": formatted_lessons
        }
    ]

    return {
        "course_title": course_title,
        "description": description,
        "difficulty": difficulty,
        "target_audience": target_audience,
        "source": "master_curriculum_index",
        "subject_id": subject["id"],
        "chapter_number": chapter.get("chapter_number"),
        "chapters": chapters
    }
