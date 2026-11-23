import os
import json
from groq import Groq
from services.topic_agent import extract_json_from_response

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def generate_adaptive_quiz(
    topic: str,
    difficulty: str = "Intermediate",
    missed_questions: list[dict] = None,
    lesson_summary: str = ""
) -> list[dict]:
    """
    Generates 2 targeted, fresh multiple-choice practice questions
    tailored specifically to the student's misconceptions and missed questions.
    Runs fast on Groq (~1-2 seconds) without touching video or reading text.
    """
    if not missed_questions:
        missed_questions = []

    print(f"\n[ADAPTIVE QUIZ] Generating targeted practice for topic: '{topic}' ({difficulty})")
    print(f"[ADAPTIVE QUIZ] Analyzing {len(missed_questions)} missed question(s)...")

    # Format the student's errors into a diagnostic brief
    diagnostic_lines = []
    for idx, item in enumerate(missed_questions, 1):
        q_text = item.get("question", "N/A")
        chosen = item.get("user_answer", "Incorrect choice")
        correct = item.get("correct_answer", "Correct principle")
        diag = item.get("explanation", "") or item.get("misconception_diagnosis", "")
        diagnostic_lines.append(
            f"Missed Concept #{idx}:\n"
            f"- Question Asked: {q_text}\n"
            f"- Student's Mistake (Chosen): {chosen}\n"
            f"- Actual Correct Principle: {correct}\n"
            f"- Context: {diag}\n"
        )

    diagnostic_context = "\n".join(diagnostic_lines) if diagnostic_lines else "General reinforcement on core topic mechanics."

    system_instruction = f"""You are an elite Adaptive Learning AI Tutor.
Your goal is to help a student overcome specific conceptual traps and misconceptions in '{topic}'.
You must generate exactly 2 brand-new, targeted multiple-choice questions (Round 2 Adaptive Practice).
The questions must NOT be identical to the ones the student missed; they must test the same underlying principles from fresh angles.

LEARNING OBJECTIVES FOR THESE 2 ADAPTIVE QUESTIONS:
1. Question 1 (Intuition Rebuild): Clarify the fundamental difference between the student's misconception and the true concept using a clear, relatable scenario.
2. Question 2 (Applied Verification): Present a practical engineering scenario to verify they can now apply the principle correctly under pressure.

STRICT JSON SCHEMA:
Return ONLY a valid JSON list containing exactly 2 question objects:
[
  {{
    "question": "Engaging, clear question directly addressing the weak concept?",
    "options": ["Accurate Answer", "Plausible Misconception A", "Plausible Misconception B", "Plausible Misconception C"],
    "correct_answer": "Accurate Answer",
    "explanation": "Clear explanation of why this is correct and how it resolves the previous misconception.",
    "misconception_diagnosis": "Why students easily confuse this and the trap to watch out for."
  }},
  {{
    "question": "Scenario-based question testing the application of the principle?",
    "options": ["Correct Approach", "Distractor Option", "Common Mistake", "Irrelevant Choice"],
    "correct_answer": "Correct Approach",
    "explanation": "Detailed breakdown of the practical mechanics.",
    "misconception_diagnosis": "The specific flawed assumption that leads to the incorrect options."
  }}
]
"""

    user_prompt = f"""Topic: {topic}
Difficulty Level: {difficulty}
Lesson Summary: {lesson_summary[:400] if lesson_summary else 'Core computer science theory and mechanics.'}

STUDENT DIAGNOSTIC PROFILE (MISSED QUESTIONS):
{diagnostic_context}

Generate exactly 2 targeted adaptive questions now in the specified JSON format. Return ONLY the JSON list."""

    if not GROQ_API_KEY:
        print("[ADAPTIVE QUIZ] GROQ_API_KEY not configured. Falling back to default adaptive questions.")
        return get_fallback_adaptive_quiz(topic)

    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        raw = response.choices[0].message.content or ""
        parsed = extract_json_from_response(raw)

        if isinstance(parsed, dict) and "quiz" in parsed:
            parsed = parsed["quiz"]

        if isinstance(parsed, list) and len(parsed) >= 1:
            print(f"[ADAPTIVE QUIZ] Successfully generated {len(parsed)} adaptive practice questions.")
            return parsed[:2]

        print("[ADAPTIVE QUIZ] Parsed JSON was not a list. Using fallback.")
        return get_fallback_adaptive_quiz(topic)

    except Exception as e:
        print(f"[ADAPTIVE QUIZ] Error during generation: {e}")
        return get_fallback_adaptive_quiz(topic)


def get_fallback_adaptive_quiz(topic: str) -> list[dict]:
    """Fallback 2-question adaptive practice if LLM call fails."""
    return [
        {
            "question": f"When applying {topic}, what is the fundamental guarantee that distinguishes its core behavior?",
            "options": [
                f"It maintains formal invariant contracts and expected state semantics.",
                f"It directly hardcodes memory allocation without an abstraction layer.",
                f"It trades off algorithmic correctness for faster compilation.",
                f"It bypasses all interface restrictions for raw pointer access."
            ],
            "correct_answer": f"It maintains formal invariant contracts and expected state semantics.",
            "explanation": f"{topic} is built upon clear contractual invariants that guarantee predictable behavior regardless of implementation.",
            "misconception_diagnosis": "Do not confuse implementation-specific details with the abstract behavioral contract."
        },
        {
            "question": f"In a real-world scenario involving {topic}, what is the best practice to prevent unexpected edge-case errors?",
            "options": [
                "Explicitly validate pre-conditions and invariant bounds before executing mutations.",
                "Assume underlying memory is infinite and ignore empty-state handling.",
                "Couple algorithm logic tightly to a single hardware architecture.",
                "Rely solely on compiler optimizations without runtime checks."
            ],
            "correct_answer": "Explicitly validate pre-conditions and invariant bounds before executing mutations.",
            "explanation": "Defensive invariant checks prevent boundary violations and ensure predictable program state.",
            "misconception_diagnosis": "Assuming the environment will silently fix boundary conditions is a common trap."
        }
    ]
