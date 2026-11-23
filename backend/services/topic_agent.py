import os
import re
import json
from groq import Groq
from services.rag_engine import query_knowledge_base

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def is_knowledge_base_relevant(topic: str, chunks: list[dict]) -> bool:
    """
    Evaluates whether the retrieved ChromaDB chunks actually provide substantial coverage
    of the requested topic, preventing irrelevant closest-neighbor fallbacks
    (e.g., returning Quicksort for Merge Sort, or Random Forests for Neural Networks).
    """
    if not chunks:
        return False

    clean_topic = re.sub(r'^(explain\s+(me\s+)?|what\s+is\s+|how\s+does\s+|tell\s+me\s+about\s+)', '', topic.strip(), flags=re.IGNORECASE)
    clean_topic = clean_topic.rstrip('?').strip().lower()

    # 1. Fast Strict Rejections: Prevent textbook mismatch when documents are topic-specific
    doc_names = " ".join([c.get("document", "").lower() for c in chunks])
    
    if "quicksort" in doc_names and "quicksort" not in clean_topic:
        print(f"[RAG Engine] Topic mismatch: Retrieved 'Quicksort' textbook chunks for requested topic '{topic}'. Rejecting local KB.")
        return False

    if "binary_search" in doc_names and ("binary" not in clean_topic and "search" not in clean_topic):
        print(f"[RAG Engine] Topic mismatch: Retrieved 'Binary Search' textbook chunks for requested topic '{topic}'. Rejecting local KB.")
        return False

    if "snmp" in doc_names and "snmp" not in clean_topic:
        print(f"[RAG Engine] Topic mismatch: Retrieved 'SNMP' textbook chunks for requested topic '{topic}'. Rejecting local KB.")
        return False

    # 2. Strict LLM Verification via Groq
    if GROQ_API_KEY:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            sample_excerpts = "\n\n".join([
                f"Document: {c.get('document', '')} (Page {c.get('page', '')})\nExcerpt: {c.get('text', '')[:350]}..."
                for c in chunks[:2]
            ])
            
            prompt = f"""You are a strict academic curriculum auditor.
Determine if the following textbook excerpts genuinely explain and teach the requested topic '{topic}'.
If the excerpts primarily teach a DIFFERENT topic (such as teaching Quicksort when asked about Merge Sort) or only mention '{topic}' in passing as a comparison, set 'covered' to false.
Set 'covered' to true ONLY if the textbook excerpt provides authentic pedagogical coverage of '{topic}'.

Topic: {topic}

Textbook Excerpts:
{sample_excerpts}

Return ONLY this JSON object (no markdown, no extra text):
{{"covered": false, "reason": "Explanation"}}
"""
            res = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                timeout=10.0
            )
            raw = res.choices[0].message.content or ""
            # Extract JSON block robustly (model may wrap in markdown)
            json_match = re.search(r'\{[^{}]+\}', raw, re.DOTALL)
            audit = json.loads(json_match.group(0)) if json_match else {}
            is_covered = bool(audit.get("covered", False))
            reason = audit.get("reason", "")
            print(f"[RAG Engine] Knowledge Base Audit for '{topic}': covered={is_covered} ({reason})")
            return is_covered
        except Exception as e:
            print(f"[RAG Engine] Audit notice ({e}). Falling back to token frequency check.")

    # 3. Fallback Heuristic
    stop_words = {
        "explain", "me", "what", "is", "how", "does", "work", "algorithm", "algorithms",
        "in", "the", "a", "an", "and", "or", "to", "for", "of", "with", "tutorial", "guide",
        "concept", "principles", "introduction", "basics", "overview", "deep", "dive",
        "lecture", "code", "implementation", "data", "structures", "computer", "science"
    }

    tokens = [w for w in re.findall(r'[a-z0-9]+', clean_topic) if len(w) > 2 and w not in stop_words]
    if not tokens:
        tokens = [w for w in re.findall(r'[a-z0-9]+', clean_topic) if len(w) > 2]

    if not tokens:
        return False

    text_corpus = " ".join([
        f"{c.get('document', '')} {c.get('section', '')} {c.get('text', '')}".lower()
        for c in chunks
    ])

    matched_tokens = [t for t in tokens if t in text_corpus]
    match_ratio = len(matched_tokens) / len(tokens)
    primary_token = tokens[0]
    count_primary = text_corpus.count(primary_token)

    return count_primary >= 3 and match_ratio >= 0.7

def extract_json_from_response(raw_text: str):
    """
    Robustly extracts and parses a JSON object or array from an LLM response.
    Handles:
    - Pure raw JSON output
    - <think>...</think> reasoning tags
    - Whole-response markdown fences (```json ... ``` or ``` ... ```)
    - Code blocks appearing *inside* JSON string fields without truncating
    - Outermost JSON braces/brackets extraction
    - Trailing commas before closing braces/brackets
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Model returned empty response content.")

    text = raw_text.strip()
    text = re.sub(r'<think>[\s\S]*?</think>', '', text).strip()

    # Strategy 1: Direct JSON parse (fastest & cleanest when model returns raw JSON)
    try:
        return json.loads(text, strict=False)
    except Exception:
        pass

    # Strategy 2: Whole-output markdown code fence (```json ... ``` or ``` ... ```)
    fence_match = re.match(r'^```(?:json)?\s*([\s\S]*?)\s*```$', text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip(), strict=False)
        except Exception:
            text = fence_match.group(1).strip()

    # Strategy 3: Extract from first '{' to last '}' (for JSON objects)
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate, strict=False)
        except Exception:
            pass

        # Strategy 3b: Strip trailing commas and premature double-closing braces before scene/lesson keys
        fixed = re.sub(r',\s*([\}\]])', r'\1', candidate)
        fixed = re.sub(
            r'(\]\s*\})\s*\}\s*,\s*"(text|transition|narration|visual_type|start_time|end_time|scene_id)"',
            r'\1, "\2"',
            fixed
        )
        fixed = re.sub(
            r'\}\s*\}\s*,\s*"(text|transition|narration|visual_type|start_time|end_time|scene_id)"',
            r'}, "\1"',
            fixed
        )
        try:
            return json.loads(fixed, strict=False)
        except Exception:
            pass

    # Strategy 4: Extract from first '[' to last ']' (for JSON lists)
    first_bracket = text.find('[')
    last_bracket = text.rfind(']')
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = text[first_bracket:last_bracket + 1]
        try:
            return json.loads(candidate, strict=False)
        except Exception:
            pass

        # Strategy 4b: Strip trailing commas inside list
        fixed = re.sub(r',\s*([\}\]])', r'\1', candidate)
        try:
            return json.loads(fixed, strict=False)
        except Exception:
            pass

    # Strategy 5: Resilient auto-repair for unterminated strings or unbalanced braces
    try:
        candidate_obj = text[first_brace:last_brace + 1] if (first_brace != -1 and last_brace != -1 and last_brace > first_brace) else text
        repaired = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', candidate_obj)
        if repaired.count('"') % 2 != 0:
            repaired += '"'
        open_b = repaired.count('{') - repaired.count('}')
        if open_b > 0:
            repaired += '}' * open_b
        return json.loads(repaired, strict=False)
    except Exception:
        pass

    # Strategy 6: Robust Regex Field Fallback (only for lesson draft payloads containing "explanation")
    if '"explanation"' in text and '"scenes"' not in text:
        try:
            result = {}
            title_m = re.search(r'"title"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            if title_m:
                result["title"] = title_m.group(1)

            exp_m = re.search(r'"explanation"\s*:\s*"([\s\S]*?)(?="\s*,\s*"(?:summary|video_script|quiz|learning_objectives|prerequisites)")', text)
            if exp_m:
                result["explanation"] = exp_m.group(1).encode('utf-8').decode('unicode_escape', errors='ignore')
            else:
                result["explanation"] = text[:3500]

            sum_m = re.search(r'"summary"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            result["summary"] = sum_m.group(1) if sum_m else "Key concept summary and algorithmic takeaways."

            script_m = re.search(r'"video_script"\s*:\s*"([\s\S]*?)(?="\s*,\s*"(?:quiz|learning_objectives|prerequisites|summary)")', text)
            result["video_script"] = script_m.group(1).encode('utf-8').decode('unicode_escape', errors='ignore') if script_m else "Authoritative educational lecture narration."

            result["prerequisites"] = ["Fundamental Programming Concepts"]
            result["learning_objectives"] = ["Explain core intuition and invariants", "Trace execution mechanics step-by-step", "Analyze asymptotic time and space bounds"]
            result["quiz"] = []
            if result.get("explanation"):
                return result
        except Exception:
            pass

    # Final attempt to surface the underlying error
    return json.loads(text, strict=False)

def enforce_three_quiz_questions(draft_data: dict, topic: str, difficulty: str = "Intermediate", client = None) -> list:
    """
    Guarantees that the quiz in draft_data has EXACTLY 3 questions.
    If the LLM returned only 1 or 2, synthesizes the missing question(s)
    targeting edge cases and boundary conditions so the count is strictly 3.
    """
    quiz = draft_data.get("quiz", [])
    if not isinstance(quiz, list):
        quiz = []

    valid_quiz = []
    for q in quiz:
        if isinstance(q, dict) and q.get("question") and isinstance(q.get("options"), list) and len(q.get("options")) >= 2:
            correct_ans = q.get("correct_answer")
            options = [str(opt) for opt in q["options"]]
            if correct_ans not in options:
                options[0] = str(correct_ans)
            while len(options) < 4:
                options.append(f"Plausible alternative approach {len(options) + 1}")
            q["options"] = options[:4]
            if not q.get("misconception_diagnosis"):
                q["misconception_diagnosis"] = "Common error: confusing abstract behavioral requirements with concrete implementation details."
            valid_quiz.append(q)

    # If already 3 or more, retain exactly the first 3
    if len(valid_quiz) >= 3:
        draft_data["quiz"] = valid_quiz[:3]
        return draft_data["quiz"]

    needed = 3 - len(valid_quiz)
    print(f"[QUIZ ENFORCER] Quiz only had {len(valid_quiz)} question(s). Synthesizing {needed} missing question(s) for '{topic}'...")

    if client and GROQ_API_KEY:
        try:
            existing_questions = "\n".join([f"- {item.get('question')}" for item in valid_quiz])
            supplement_prompt = f"""You are an elite Computer Science educator.
For the topic '{topic}' ({difficulty} level), the following questions already exist:
{existing_questions if existing_questions else 'None'}

TASK: Generate EXACTLY {needed} additional multiple-choice question(s) focusing on boundary conditions, subtle edge cases, or common misconceptions.
Each question MUST have exactly 4 options, a correct_answer matching one of the options, an explanation, and a misconception_diagnosis.

Return ONLY a valid JSON list matching this schema:
[
  {{
    "question": "Clear edge-case or misconception question?",
    "options": ["Accurate insight", "Plausible trap A", "Plausible trap B", "Common misconception C"],
    "correct_answer": "Accurate insight",
    "explanation": "Detailed explanation of the boundary condition or edge case.",
    "misconception_diagnosis": "Why students commonly choose the trap option."
  }}
]"""
            supp_resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You generate high-quality educational quiz questions. Output JSON list only."},
                    {"role": "user", "content": supplement_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            raw_supp = supp_resp.choices[0].message.content or ""
            parsed_supp = extract_json_from_response(raw_supp)
            if isinstance(parsed_supp, dict) and "quiz" in parsed_supp:
                parsed_supp = parsed_supp["quiz"]
            if isinstance(parsed_supp, list):
                for sq in parsed_supp:
                    if isinstance(sq, dict) and sq.get("question") and isinstance(sq.get("options"), list) and sq.get("correct_answer"):
                        s_correct = str(sq["correct_answer"])
                        s_options = [str(o) for o in sq["options"]]
                        if s_correct not in s_options:
                            s_options[0] = s_correct
                        while len(s_options) < 4:
                            s_options.append(f"Alternative choice {len(s_options) + 1}")
                        sq["options"] = s_options[:4]
                        if not sq.get("misconception_diagnosis"):
                            sq["misconception_diagnosis"] = "Common error: confusing boundary invariants with normal execution states."
                        valid_quiz.append(sq)
                        if len(valid_quiz) == 3:
                            break
        except Exception as supp_err:
            print(f"[QUIZ ENFORCER] Supplement request notice: {supp_err}")

    # Fallback if still under 3
    fallback_templates = [
        {
            "question": f"What is a critical boundary edge case or constraint to verify when implementing {topic}?",
            "options": [
                f"Handling empty, uninitialized, or extreme boundary states safely.",
                f"Assuming infinite system memory and omitting all capacity checks.",
                f"Ignoring return values and exception states from internal sub-calls.",
                f"Hardcoding constant array offsets without checking dynamic lengths."
            ],
            "correct_answer": f"Handling empty, uninitialized, or extreme boundary states safely.",
            "explanation": f"In {topic}, boundary cases such as null/empty states or upper capacity bounds are the most frequent source of runtime errors.",
            "misconception_diagnosis": "Overlooking empty-state preconditions leads to fatal null-pointer dereferences or boundary faults."
        },
        {
            "question": f"When evaluating the algorithmic trade-offs of {topic}, which statement is technically accurate?",
            "options": [
                "It prioritizes formal behavioral guarantees and invariant safety over unsafe micro-optimizations.",
                "It eliminates all time complexity bottlenecks by removing execution checks.",
                "It always requires O(1) memory overhead regardless of data scale.",
                "It can bypass CPU cache hierarchy constraints automatically."
            ],
            "correct_answer": "It prioritizes formal behavioral guarantees and invariant safety over unsafe micro-optimizations.",
            "explanation": "Algorithmic correctness relies on strict invariant preservation, balancing execution throughput with safety guarantees.",
            "misconception_diagnosis": "Believing that algorithms can bypass memory hierarchy or theoretical complexity limits is a common myth."
        }
    ]

    for fb in fallback_templates:
        if len(valid_quiz) >= 3:
            break
        valid_quiz.append(fb)

    draft_data["quiz"] = valid_quiz[:3]
    print(f"[QUIZ ENFORCER] Strictly guaranteed 3 questions for '{topic}'. Final count: {len(draft_data['quiz'])}")
    return draft_data["quiz"]

def generate_topic_content(topic: str, difficulty: str = "Beginner", revision_feedback: dict = None) -> dict:
    if not GROQ_API_KEY:
        print("[AGENT] API Key missing. Returning mock data.")
        return {
            "title": f"Introduction to {topic}",
            "explanation": f"This is an educational micro-lesson covering {topic}.",
            "summary": f"Mastered core concepts of {topic}.",
            "prerequisites": ["Curiosity to learn and basic problem-solving"],
            "learning_objectives": [f"Understand how {topic} works through simple intuition"],
            "video_script": f"Welcome to this lesson on {topic}...",
            "quiz": []
        }

    print(f"\n[AGENT] Starting generation for topic: '{topic}' (Target: {difficulty})")
    
    # 1. Hybrid 3-Tier Knowledge Formulation:
    # Tier 1: Local Academic Knowledge Base (ChromaDB)
    # Tier 2: Real-time Web Research (Tavily API)
    # Tier 3: Groq LPU Expert Knowledge Base
    context = ""
    sources_citation = []
    knowledge_source = "groq_knowledge"
    source_label = "Groq LPU Expert Knowledge Base"
    
    # Step A: Check local ChromaDB Knowledge Base
    try:
        chunks = query_knowledge_base(topic, n_results=3)
        if chunks and len(chunks) > 0 and is_knowledge_base_relevant(topic, chunks):
            print(f"[RAG Engine] Confirmed: '{topic}' is authentically covered in local ChromaDB ({len(chunks)} chunks).")
            knowledge_source = "knowledge_base"
            source_label = "Local Academic Knowledge Base (ChromaDB)"
            context = "\n\n".join([f"Source: {c.get('document', 'Textbook')} (Page {c.get('page', 1)}):\n{c.get('text')}" for c in chunks])
            for c in chunks:
                sources_citation.append(f"📖 {c.get('document', 'Textbook')} (Page {c.get('page', 1)})")
        else:
            print(f"[RAG Engine] Notice: Topic '{topic}' is NOT covered in local ChromaDB corpus. Proceeding to Tier 2 (Tavily Web Search)...")
    except Exception as e:
        print(f"[RAG Engine] Local ChromaDB check note: {e}")

    # Step B: If not in local ChromaDB, Fallback to Tavily Web Search
    if not context or knowledge_source != "knowledge_base":
        try:
            from services.tavily_service import search_tavily
            tavily_res = search_tavily(topic, max_results=4)
            if tavily_res and tavily_res.get("context") and len(tavily_res["context"].strip()) > 80:
                knowledge_source = "tavily_web"
                source_label = "Live Web Research (Tavily Search API)"
                context = tavily_res["context"]
                sources_citation = tavily_res.get("citations", [])
                print(f"[RAG Engine] Tavily Web Research succeeded for '{topic}'! Retrieved {len(sources_citation)} web sources.")
            else:
                print(f"[RAG Engine] Tavily Web Search returned insufficient data. Proceeding to Tier 3 (Groq Model)...")
        except Exception as te:
            print(f"[RAG Engine] Tavily search notice: {te}")

    # Step C: Fallback to Groq LPU Expert Curriculum Model
    if not context or knowledge_source == "groq_knowledge":
        knowledge_source = "groq_knowledge"
        source_label = "Groq LPU Expert Curriculum Model (openai/gpt-oss-120b)"
        context = f"Authoritative domain knowledge and standard computer science curriculum for {topic} targeting {difficulty} level."
        sources_citation = [
            "🧠 Groq LPU Expert Curriculum Engine (`openai/gpt-oss-120b`)",
            "🏛️ Standard Computer Science Curriculum & Algorithmic Specifications"
        ]
        print(f"[RAG Engine] Using Groq LPU authoritative internal curriculum knowledge.")

    # 2. Configure Groq API Request with Pedagogical Excellence
    client = Groq(api_key=GROQ_API_KEY)
    
    from services.visual_planner_agent import detect_domain
    domain = detect_domain(topic, context)
    print(f"[AGENT] Detected topic subject domain: '{domain}' (Source: {knowledge_source})")

    # Domain-specific section names and guidance
    if domain in ["ml_trees", "ml_regression", "ml_deep_learning"]:
        subject_name = "Machine Learning"
        section_4_title = "4. **Mathematical Formulation & Model Architecture Breakdown**"
        section_4_guide = "Detail mathematical formulations, loss/impurity metrics (e.g. Gini Impurity, Entropy, MSE), feature splitting rules, and ensemble aggregation."
        section_6_title = "6. **Clean Python / Scikit-Learn Code Implementation**"
        analogy_focus = "decision-making committees, trend fitting, or sensory pattern recognition"
    elif domain in ["dbms_normalization", "dbms_transactions"]:
        subject_name = "Database Management Systems"
        section_4_title = "4. **Relational Decomposition & Schema/Transaction Lifecycle Breakdown**"
        section_4_guide = "Detail functional dependencies, normal forms (1NF, 2NF, 3NF, BCNF) and anomalies, OR ACID states, Write-Ahead Logging (WAL), and lock isolation levels."
        section_6_title = "6. **Production SQL Schema / Transaction Script**"
        analogy_focus = "organized multi-table filing systems, student-department records, or banking balance transfers"
    elif domain in [
        "dsa_arrays", "dsa_linked_lists", "dsa_stacks", "dsa_queues", "dsa_heaps",
        "dsa_graphs", "dsa_hashing", "dsa_dp", "dsa_linear_search",
        "dsa_binary_search", "dsa_sorting", "dsa_recursion", "dsa_tree_graph",
        "dsa_memory_pointers", "dsa_bitwise", "dsa_complexity"
    ]:
        subject_name = "Data Structures & Algorithms"
        section_4_title = "4. **Algorithmic Invariants & State Transition Breakdown**"
        section_4_guide = "Detail data structure contracts (LIFO, FIFO, complete tree, DAG), pointer movements (top, head, tail, rear, low, mid, high, pivot), recurrence relations, or collision chains."
        section_6_title = "6. **Clean Algorithmic Python Code (with Boundary Guards)**"
        analogy_focus = "a physical stack of plates, people waiting in a queue line, a priority emergency triage, navigating a city map, or carriages connected in a train"
    elif domain == "networking":
        subject_name = "Computer Networks"
        section_4_title = "4. **The Complete Breakdown of Each Network Layer**"
        section_4_guide = "Detail each protocol layer (Application, Transport, Network, Data Link, Physical), encapsulation headers, and data flow."
        section_6_title = "6. **Concrete Packet Walkthrough & Network Flow Trace**"
        analogy_focus = "a global postal courier service shipping sealed, addressed envelopes across transport routes"
    else:
        subject_name = "Computer Science"
        section_4_title = "4. **Detailed Architecture & Component Breakdown**"
        section_4_guide = "Detail the core components, their architectural roles, interfaces, and responsibilities."
        section_6_title = "6. **Practical Implementation / Data Flow Trace**"
        analogy_focus = "modular engineering blueprints and real-world system pipelines"

    # All difficulties produce complete 8-scene narrated video lectures
    if difficulty.lower() == "beginner":
        pedagogy_guide = f"""
        TARGET AUDIENCE: A complete beginner with zero prior experience in {subject_name}.
        GOAL: Make the concept instantly click through plain-English intuition and everyday analogies ({analogy_focus}).
        
        RULES FOR BEGINNERS:
        1. Never dump unparsed jargon. If you introduce a specialized term, define it immediately with a simple analogy.
        2. {section_4_title}:
           {section_4_guide}
        3. SECTION 6 FORMAT:
           Provide {section_6_title} tailored strictly to {subject_name}.
        """
        video_script_words = "220 to 260 words (friendly, intuitive 8-scene educational lecture, ~2 minutes duration)"
    elif difficulty.lower() == "intermediate":
        pedagogy_guide = f"""
        TARGET AUDIENCE: A software developer or computer science student learning {subject_name}.
        GOAL: Clear operational mechanics, execution pipelines, data structures, and practical trade-offs.
        
        RULES FOR INTERMEDIATE:
        1. Focus on operational logic, data flows, validation boundaries, and comparative performance in {subject_name}.
        2. {section_4_title}:
           {section_4_guide}
        3. SECTION 6 FORMAT:
           Provide {section_6_title} with comments on edge cases and performance.
        """
        video_script_words = "250 to 290 words (thorough 8-scene lecture with mechanics and logic, ~2 minutes duration)"
    else:
        pedagogy_guide = f"""
        TARGET AUDIENCE: An advanced engineer, systems architect, or researcher seeking master-level technical depth in {subject_name}.
        GOAL: Exhaustive technical rigor, architectural trade-offs, internal state transitions, bit-level mechanics, invariants, and failure modes.
        
        RULES FOR ADVANCED:
        1. Dive deeply into theoretical invariants, mathematical foundations, memory layout, and boundary edge cases.
        2. {section_4_title}:
           {section_4_guide}
        3. SECTION 6 FORMAT:
           Provide production-grade {section_6_title} with error handling, boundary guards, and performance notes.
        4. Provide deep comparative discussion on real-world engineering trade-offs, scalability bottlenecks, and failure modes.
        """
        video_script_words = "280 to 350 words (comprehensive 8-scene masterclass lecture, deep technical breakdown, ~2:00 to 2:15 minutes duration)"

    system_instruction = (
        f"You are an elite educational director and curriculum architect creating an authoritative, comprehensive {subject_name} course module. "
        "Your priority is pedagogical precision, rigorous technical depth, and an extensive conversational video script. "
        "MANDATORY ASSESSMENT POLICY: The 'quiz' array MUST contain EXACTLY 3 multiple-choice questions (1: Core Intuition, 2: Mechanics & Execution Trace, 3: Boundary Condition & Misconception). "
        "CRITICAL JSON FORMATTING: In text fields (like 'explanation' and 'video_script'), NEVER use nested double quotes. Use single quotes (') for speech or dialogue (e.g. Scene 1: 'Welcome to this lesson' instead of \"Welcome\"). "
        "Return ONLY a valid JSON object matching the requested schema."
    )
    
    prompt = f"""
    TOPIC: {topic}
    SUBJECT DOMAIN: {subject_name}

    RETRIEVED KNOWLEDGE BASE CONTEXT:
    {context}

    {pedagogy_guide}

    REQUIRED EXPLANATION STRUCTURE (in clean GitHub-Flavored Markdown):
    1. **Core Intuition & Everyday Metaphor**: Relatable real-world framing ({analogy_focus}).
    2. **Why It Matters**: The fundamental bottleneck or challenge it solves.
    3. **How It Works (Step-by-Step)**: Clear numbered execution flow.
    {section_4_title}: {section_4_guide}
    5. **Concept Comparison Table**: Markdown table comparing naive vs optimal, or component vs component.
    {section_6_title}: Concrete practical code/trace without fluff.
    7. **Common Pitfalls & Pro Tips**: Misconceptions, boundary traps, and senior rules of thumb.

    Your "video_script" MUST be {video_script_words} structured in conversational spoken narrative for an animated video.

    SCHEMA FORMAT (Return ONLY this JSON):
    {{
      "title": "{topic}",
      "explanation": "Full markdown lesson with headings, analogy, tables, breakdown, and tips.",
      "summary": "3-4 punchy key takeaways that stick in memory.",
      "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
      "learning_objectives": [
        "Explain the core purpose of {topic} clearly",
        "Trace the mechanism step-by-step from start to finish",
        "Identify key components and their individual responsibilities"
      ],
      "video_script": "Engaging narration script for animated video.",
      "quiz": [
        {{
          "question": "Intuition & Metaphor question testing core concept at {difficulty} level?",
          "options": ["Accurate explanation", "Common misconception A", "Common misconception B", "Irrelevant choice"],
          "correct_answer": "Accurate explanation",
          "explanation": "Detailed explanation of why this answer is correct.",
          "misconception_diagnosis": "Why students often confuse this concept and why the distractor options are traps."
        }},
        {{
          "question": "Step-by-step mechanics or execution trace question?",
          "options": ["Correct mechanical step", "Suboptimal choice", "Incorrect sequence", "Fatal mistake"],
          "correct_answer": "Correct mechanical step",
          "explanation": "Detailed breakdown of the operational sequence and mechanics.",
          "misconception_diagnosis": "Common error in tracing the step-by-step logic."
        }},
        {{
          "question": "Boundary condition, edge case, or common misconception question?",
          "options": ["Correct handling/insight", "Common trap option", "Naive assumption", "Invalid claim"],
          "correct_answer": "Correct handling/insight",
          "explanation": "Deep dive into the edge case nuance and correct boundary handling.",
          "misconception_diagnosis": "The subtle misconception that leads developers or students to choose the wrong approach."
        }}
      ]
    }}
    """

    if revision_feedback:
        critique = revision_feedback.get("critique_summary", "")
        issues = "\n".join([f"- {issue}" for issue in revision_feedback.get("identified_issues", [])])
        revision_directive = f"""
        CRITICAL REVISION & QUALITY DIRECTIVE:
        A previous draft scored below the academic threshold. The LLM-as-a-Judge flagged the following issues:
        Judge Critique: {critique}
        Identified Issues to Fix:
        {issues}

        You MUST address every single identified issue above, rectify all factual inaccuracies or weak explanations, ensure perfect algorithmic correctness, and strengthen the pedagogical intuition.
        """
        prompt += f"\n\n{revision_directive}"

    # 3. Generate Draft Content
    print("[AGENT] Sending drafting request to Groq...")
    draft_data = None
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=6000
        )
        
        raw_content = response.choices[0].message.content or ""
        print(f"[AGENT] Generation successful! Response length: {len(raw_content)} chars")
        draft_data = extract_json_from_response(raw_content)

    except Exception as e:
        print(f"[AGENT] Groq constrained decoding note: {e}")
        # Self-Healing 1: Extract failed_generation from Groq error body if present
        failed_gen = None
        if hasattr(e, "body") and isinstance(e.body, dict):
            failed_gen = e.body.get("error", {}).get("failed_generation")
        if not failed_gen and hasattr(e, "response"):
            try:
                err_json = e.response.json()
                failed_gen = err_json.get("error", {}).get("failed_generation")
            except Exception:
                pass

        if failed_gen:
            print("[AGENT] Auto-recovering draft content from Groq failed_generation payload...")
            try:
                draft_data = extract_json_from_response(failed_gen)
                print("[AGENT] Successfully auto-recovered draft content from Groq payload!")
            except Exception as rec_err:
                print(f"[AGENT] Could not recover from failed_gen: {rec_err}")

        # Self-Healing 2: Fallback non-constrained call if recovery did not succeed
        if not draft_data:
            print("[AGENT] Executing resilient unconstrained fallback call...")
            try:
                retry_resp = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": system_instruction + " Return ONLY a valid JSON object."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=6000
                )
                raw_retry = retry_resp.choices[0].message.content or ""
                draft_data = extract_json_from_response(raw_retry)
            except Exception as retry_err:
                print(f"[AGENT] Retry call encountered: {retry_err}")
                raise retry_err

    # 3b. Strictly enforce that the quiz has exactly 3 questions
    draft_data["quiz"] = enforce_three_quiz_questions(draft_data, topic, difficulty, client)

    # 4. Append Authoritative Knowledge Source & Citations Section at the end
    if sources_citation or source_label:
        if knowledge_source == "knowledge_base":
            source_badge_title = "📚 Knowledge Source & Citations (Local Academic Knowledge Base)"
            source_origin = "**Grounding Origin:** Local ChromaDB Vector Store — retrieved directly from indexed curriculum textbook chapters."
        elif knowledge_source == "tavily_web":
            source_badge_title = "🌐 Knowledge Source & Citations (Real-Time Web Research)"
            source_origin = "**Grounding Origin:** Tavily Search API — live authoritative technical documentation & academic references."
        else:
            source_badge_title = "🧠 Knowledge Source & Citations (Groq LPU Expert Curriculum Model)"
            source_origin = "**Grounding Origin:** Groq LPU Curriculum Knowledge Engine (`openai/gpt-oss-120b`) — standard computer science curriculum."

        references_section = f"\n\n---\n\n### {source_badge_title}\n"
        references_section += f"{source_origin}\n\n"
        references_section += "**Referenced Citations:**\n"
        for ref in sources_citation:
            references_section += f"- {ref}\n"

        draft_data["explanation"] += references_section
        print(f"[AGENT] Appended {len(sources_citation)} {knowledge_source} source citations to lesson.")

    draft_data["grounding_context"] = context
    draft_data["knowledge_source"] = knowledge_source
    return draft_data