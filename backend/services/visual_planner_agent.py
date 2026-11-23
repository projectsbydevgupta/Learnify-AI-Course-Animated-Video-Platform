import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(dotenv_path)
api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=api_key) if api_key else None
from services.topic_agent import extract_json_from_response

def clean_lesson_title(raw_title: str) -> str:
    """
    Cleans conversational search prefixes and trailing punctuation
    e.g. 'explain me random forest algorithm?' -> 'Random Forest Algorithm'
    """
    cleaned = re.sub(r'^(explain\s+(me\s+)?|what\s+is\s+|how\s+does\s+|tell\s+me\s+about\s+)', '', raw_title.strip(), flags=re.IGNORECASE)
    cleaned = cleaned.rstrip('?').strip()
    return cleaned.title() if cleaned else raw_title.title()

STOP_WORDS = {
    "what", "is", "how", "does", "the", "and", "for", "with", "from", "into", "over",
    "after", "explain", "basics", "introduction", "intro", "guide", "overview", "deep",
    "dive", "lecture", "tutorial", "algorithm", "algorithms", "data", "structure",
    "structures", "system", "systems", "core", "concept", "concepts", "part", "step"
}

def verify_scene_plan_integrity(lesson_title: str, domain: str, scenes: list[dict]) -> tuple[bool, str]:
    """
    Guarantees video plan integrity across two strict dimensions:
    1. Semantic Relevance: Key terms from the user's title MUST appear in scene narrations/titles.
    2. Multi-Directional Anti-Contamination: Detects and rejects cross-domain hallucinations
       (e.g., DBMS terms in DSA, ML training in Networks, or packet headers in ML).
    """
    clean_title = clean_lesson_title(lesson_title).lower()
    raw_tokens = re.findall(r'[a-zA-Z0-9]+', clean_title)
    keywords = [w for w in raw_tokens if len(w) >= 3 and w not in STOP_WORDS]

    # Assemble full text dump across all scenes
    scene_dumps = []
    for s in scenes:
        scene_dumps.append(str(s.get("title", "")))
        scene_dumps.append(str(s.get("text", "")))
        scene_dumps.append(str(s.get("narration", "")))
        vd = s.get("visual_data", {})
        if isinstance(vd, dict):
            try:
                scene_dumps.append(json.dumps(vd))
            except Exception:
                pass
    all_plan_text = " ".join(scene_dumps).lower()

    # 1. Semantic Relevance Verification
    if keywords:
        has_relevant_keyword = any(kw in all_plan_text for kw in keywords)
        if not has_relevant_keyword:
            return False, f"Semantic drift: None of the core topic keywords {keywords} found in generated scenes."

    # 2. Multi-Directional Anti-Contamination Guardrails
    # DSA topics must not contain DBMS transaction terms or ML model training
    dsa_domains = [
        "dsa_arrays", "dsa_linked_lists", "dsa_stacks", "dsa_queues", "dsa_heaps",
        "dsa_graphs", "dsa_hashing", "dsa_dp", "dsa_tree_graph", "dsa_binary_search",
        "dsa_linear_search", "dsa_sorting", "dsa_recursion", "dsa_memory_pointers",
        "dsa_bitwise", "dsa_complexity"
    ]
    if domain in dsa_domains:
        forbidden_dbms = re.compile(r'\b(acid|atomicity|serializability|write-ahead|wal\b|isolation\s*levels?|dirty\s*reads?|phantom\s*reads?|schema\.sql|begin\s*transaction)\b', re.IGNORECASE)
        forbidden_ml = re.compile(r'\b(gradient\s*descent|backpropagation|scikit-learn|random\s*forest|gini\s*(index|impurity)|transformer\s*attention|epoch\s*training)\b', re.IGNORECASE)
        if forbidden_dbms.search(all_plan_text):
            return False, "Detected DBMS transaction contamination in DSA video plan."
        if forbidden_ml.search(all_plan_text):
            return False, "Detected ML model training contamination in DSA video plan."

    # Networking topics must not contain DBMS transactions or ML training
    elif domain == "networking":
        forbidden_dbms = re.compile(r'\b(acid|atomicity|serializability|write-ahead\s*log|dirty\s*reads?|phantom\s*reads?|1nf|2nf|3nf|bcnf|boyce[\s-]*codd)\b', re.IGNORECASE)
        forbidden_ml = re.compile(r'\b(gradient\s*descent|backpropagation|scikit-learn|random\s*forest|gini\s*index|transformer\s*attention)\b', re.IGNORECASE)
        if forbidden_dbms.search(all_plan_text):
            return False, "Detected DBMS transaction contamination in Computer Networking video plan."
        if forbidden_ml.search(all_plan_text):
            return False, "Detected ML training contamination in Computer Networking video plan."

    # Machine Learning topics must not contain DBMS transactions or low-level packet switching terms
    elif domain in ["ml_trees", "ml_regression", "ml_deep_learning"]:
        forbidden_dbms = re.compile(r'\b(acid|atomicity|serializability|write-ahead\s*log|two-phase\s*locking|dirty\s*reads?|phantom\s*reads?|1nf|2nf|3nf|bcnf)\b', re.IGNORECASE)
        forbidden_net = re.compile(r'\b(syn\s*packet|3-way\s*handshake|sliding\s*window\s*flow\s*control|wireshark\s*capture|snmp\s*manager)\b', re.IGNORECASE)
        if forbidden_dbms.search(all_plan_text):
            return False, "Detected DBMS transaction contamination in Machine Learning video plan."
        if forbidden_net.search(all_plan_text):
            return False, "Detected Computer Networking packet contamination in Machine Learning video plan."

    # Operating Systems topics must not contain ML training or DBMS normalization
    elif domain == "os_systems":
        forbidden_dbms = re.compile(r'\b(1nf|2nf|3nf|bcnf|boyce[\s-]*codd|lossless\s*decomposition|functional\s*dependenc(y|ies))\b', re.IGNORECASE)
        forbidden_ml = re.compile(r'\b(gradient\s*descent|backpropagation|scikit-learn|random\s*forest|gini\s*index|transformer\s*attention)\b', re.IGNORECASE)
        if forbidden_dbms.search(all_plan_text):
            return False, "Detected DBMS normalization contamination in Operating Systems video plan."
        if forbidden_ml.search(all_plan_text):
            return False, "Detected ML training contamination in Operating Systems video plan."

    # Database Systems topics must not contain ML model training
    elif domain in ["dbms_normalization", "dbms_transactions"]:
        forbidden_ml = re.compile(r'\b(gradient\s*descent|backpropagation|scikit-learn|random\s*forest|gini\s*index|transformer\s*attention)\b', re.IGNORECASE)
        if forbidden_ml.search(all_plan_text):
            return False, "Detected ML model training contamination in Database Systems video plan."

    return True, "Plan verified successfully."

def detect_domain(title: str, content: str) -> str:
    """
    Robust regex-based topic domain detection distinguishing core subjects:
    1. Machine Learning (ml_trees, ml_regression, ml_deep_learning)
    2. Computer Networks (networking)
    3. Database Management Systems (dbms_normalization, dbms_transactions)
    4. Data Structures & Algorithms (dsa_binary_search, dsa_sorting, dsa_recursion, dsa_tree_graph)
    5. Operating Systems (os_systems)
    6. System Design & Scalable Architecture (system_design)

    STAGE 1: High-Priority Title Matching (User Intent)
    STAGE 2: Content Matching (when title is ambiguous)
    """
    clean_title = re.sub(r'^(explain\s+(me\s+)?|what\s+is\s+|how\s+does\s+|tell\s+me\s+about\s+)', '', title.strip(), flags=re.IGNORECASE).lower().strip()
    text = f"{title} {content[:1500]}".lower()

    # --- STAGE 1: High-Priority Title Intent ---
    # 0.1 DSA: Memory Model, Pointers, Memory Addresses, Stack vs Heap, Pass-by-Value vs Pass-by-Reference
    if re.search(r'\b(pointers?|memory\s*addresses?|dereferenc(ing|e)|stack\s*memory|heap\s*memory|stack\s*(vs|and)\s*heap|stack\s*memory\s*allocation|heap\s*allocation|pass[\s-]*by[\s-]*value|pass[\s-]*by[\s-]*reference|memory\s*footprint|primitive\s*data\s*types?|dynamic\s*heap\s*allocation|memory\s*model)\b', clean_title):
        return "dsa_memory_pointers"

    # 0.2 DSA: Bitwise Operations & Bitmasks
    if re.search(r'\b(bitwise|bitmasks?|bit\s*manipulation|bit\s*shifts?|two\'?s\s*complement|binary\s*representation)\b', clean_title):
        return "dsa_bitwise"

    # 0.3 DSA: Asymptotic Analysis & Algorithmic Complexity (Big-O, Master Theorem)
    if re.search(r'\b(asymptotic\s*analysis|algorithmic\s*complexity|big[\s-]*o\b|big[\s-]*omega|big[\s-]*theta|time\s*and\s*space\s*bounds|time\s*bounds?|space\s*bounds?|recurrence\s*tree|master\s*theorem|(best|worst|average)[\s-]*case(\s*analysis)?|best.*average.*worst|in[\s-]*place\s*invariants?)\b', clean_title):
        return "dsa_complexity"

    # 1. DSA: Trees & Binary Search Trees (Check before binary search, handle singular and plural)
    if re.search(r'\b(binary\s*search\s*trees?|bsts?|binary\s*trees?|tries?|avl|red[\s-]*black|tree\s*traversals?)\b', clean_title):
        return "dsa_tree_graph"

    # 1.1 DSA: Graphs & Graph Optimization Algorithms
    if re.search(r'\b(graphs?|directed\s*graph|undirected\s*graph|dag\b|adjacency\s*list|adjacency\s*matrix|topological\s*sort|dijkstra|bellman[\s-]*ford|kruskal|prim\'?s|floyd[\s-]*warshall|bfs|dfs|breadth[\s-]*first|depth[\s-]*first|disjoint\s*set|dsu\b|union[\s-]*find|minimum\s*spanning\s*tree|mst\b)\b', clean_title) and not re.search(r'\btrees?\b', clean_title):
        return "dsa_graphs"

    # 1.2 DSA: Heaps & Priority Queues
    if re.search(r'\b(heaps?|min[\s-]*heap|max[\s-]*heap|priority\s*queues?|heapify|binary\s*heaps?|heapsort)\b', clean_title):
        return "dsa_heaps"

    # 2. DSA: Binary Search (Must not be a tree)
    if re.search(r'\b(binary\s*search|bisect|logarithmic\s*search)\b', clean_title) and not re.search(r'\btrees?\b', clean_title):
        return "dsa_binary_search"

    # 2.1 DSA: Linear Search (Sequential search on arrays / lists)
    if re.search(r'\b(linear\s*search|sequential\s*search)\b', clean_title):
        return "dsa_linear_search"

    # 3. DSA: Sorting
    if re.search(r'\b(quicksort|lomuto|mergesort|merge\s*sort|bubble\s*sort|insertion\s*sort|selection\s*sort|sorting)\b', clean_title):
        return "dsa_sorting"

    # 4. DSA: Recursion & Call Stacks
    if re.search(r'\b(recursion|recursive|call\s*stack|activation\s*record|backtracking)\b', clean_title):
        return "dsa_recursion"

    # 4.1 DSA: Stacks & LIFO Data Structures
    if re.search(r'\b(stacks?|stack\s*data\s*structure|lifo|push[\s-]*pop|monotonic\s*stack|postfix\s*evaluation|infix\s*to\s*postfix|bracket\s*matching|parenthes(is|es)\s*validation)\b', clean_title):
        return "dsa_stacks"

    # 4.2 DSA: Queues & FIFO Data Structures
    if re.search(r'\b(queues?|queue\s*data\s*structure|fifo|enqueue|dequeue|circular\s*queue|circular\s*ring\s*buffer|double[\s-]*ended\s*queue|deque)\b', clean_title) and not re.search(r'\b(heaps?|min[\s-]*heap|max[\s-]*heap|message\s*queues?|kafka|rabbitmq)\b', clean_title):
        return "dsa_queues"

    # 4.3 DSA: Hashing & Hash Tables
    if re.search(r'\b(hash\s*tables?|hash\s*maps?|hash\s*sets?|hashing|hash\s*functions?|collision\s*resolution|chaining|open\s*addressing|linear\s*probing|hash\s*bucket)\b', clean_title):
        return "dsa_hashing"

    # 4.4 DSA: Dynamic Programming
    if re.search(r'\b(dynamic\s*programming|dp\b|memoization|tabulation|optimal\s*substructure|overlapping\s*subproblems|0[\/-]1\s*knapsack|knapsack|longest\s*common\s*subsequence|lcs\b|coin\s*change|climbing\s*stairs)\b', clean_title):
        return "dsa_dp"

    # 4.5 DSA: Arrays, Dynamic Arrays, Vectors, Contiguous Memory, Two Pointers
    if re.search(r'\b(arrays?|dynamic\s*arrays?|vectors?|contiguous\s*memory|two[\s-]*pointers?|sliding\s*window|prefix\s*sums?|subarrays?|static\s*arrays?)\b', clean_title):
        return "dsa_arrays"

    # 4.6 DSA: Linked Lists (Singly, Doubly, Circular, Sentinel Nodes)
    if re.search(r'\b(linked\s*lists?|singly\s*linked|doubly\s*linked|circular\s*linked|sentinel\s*node|list\s*nodes?)\b', clean_title):
        return "dsa_linked_lists"

    # 5. ML: Decision Trees & Random Forest Ensembles
    if re.search(r'\b(random\s*forest|decision\s*trees?|ensemble|bagging|boosting|id3|cart|gini\s*index)\b', clean_title):
        return "ml_trees"

    # 6. ML: Deep Learning & Transformers
    if re.search(r'\b(transformer|self[\s-]*attention|attention\s*mechanism|multi[\s-]*head\s*attention|neural\s*network|backprop|deep\s*learning|pytorch|llm)\b', clean_title):
        return "ml_deep_learning"

    # 7. ML: Regression & Optimization
    if re.search(r'\b(linear\s*regression|logistic\s*regression|least\s*squares|ols|gradient\s*descent|bias[\s-]*variance)\b', clean_title):
        return "ml_regression"

    # 8. DBMS: Normalization
    if re.search(r'\b(normalization|normal\s*forms?|1nf|2nf|3nf|bcnf|boyce[\s-]*codd|functional\s*dependenc(y|ies))\b', clean_title):
        return "dbms_normalization"

    # 9. DBMS: ACID Transactions & Concurrency (Specific compound terms)
    if re.search(r'\b(acid|transactions?|wal|write-ahead|serializability|two-phase\s*locking|concurrency\s*control|isolation\s*levels?|phantom\s*reads?|dirty\s*reads?)\b', clean_title):
        return "dbms_transactions"

    # 10. Networking
    if re.search(r'\b(tcp|udp|ip\b|osi\b|handshake|snmp|packet\s*capture|wireshark|socket|sliding\s*window|dns|http|ethernet|icmp)\b', clean_title):
        return "networking"

    # 11. OS: Operating Systems & Kernel Engineering
    if re.search(r'\b(operating\s*systems?|cpu\s*scheduling|round[\s-]*robin|shortest\s*job|sjf|banker\'?s\s*algorithm|deadlocks?|virtual\s*memory|paging|page\s*replacement|lru\s*cache|tlb|semaphores?|mutex|process\s*synchronization|fork|ipc\b|context\s*switch)\b', clean_title):
        return "os_systems"

    # 12. System Design: Distributed Systems & Scalable Architecture
    if re.search(r'\b(system\s*design|distributed\s*systems?|microservices?|load\s*balanc(er|ing)|caching\s*strateg(y|ies)|redis\s*cache|cdn\b|content\s*delivery|api\s*gateway|message\s*queues?|kafka|rabbitmq|database\s*sharding|cap\s*theorem|rate\s*limit(er|ing)|consistent\s*hashing)\b', clean_title):
        return "system_design"

    # --- STAGE 2: Content Matching (when title is ambiguous) ---
    # DSA Memory Model & Pointers
    if re.search(r'\b(pointer\s*arithmetic|dereferenc(ing|e)|stack\s*memory\s*allocation|dynamic\s*heap\s*allocation|pass[\s-]*by[\s-]*value|pass[\s-]*by[\s-]*reference|memory\s*footprint|stack\s*vs\s*heap)\b', text):
        return "dsa_memory_pointers"

    elif re.search(r'\b(bitwise\s*operations?|bitmask(ing|s)?|bit\s*shifts?|two\'?s\s*complement)\b', text):
        return "dsa_bitwise"

    elif re.search(r'\b(asymptotic\s*analysis|algorithmic\s*complexity|big[\s-]*o\s*notation|master\s*theorem|recurrence\s*tree|(best|worst|average)[\s-]*case(\s*analysis)?|best.*average.*worst)\b', text):
        return "dsa_complexity"

    # DSA Trees & BST FIRST before database
    elif re.search(r'\b(binary\s*search\s*trees?|bsts?\b|binary\s*trees?|avl\s*trees?|red[\s-]*black\s*trees?|tries?\b|in-order\s*successor|tree\s*traversals?)\b', text):
        return "dsa_tree_graph"

    elif re.search(r'\b(adjacency\s*list|adjacency\s*matrix|topological\s*sort|dijkstra|bellman[\s-]*ford|kruskal|prim\'?s|floyd[\s-]*warshall|shortest\s*path|graph\s*traversals?|minimum\s*spanning\s*tree|dsu\b|union[\s-]*find)\b', text) and not re.search(r'\btrees?\b', text):
        return "dsa_graphs"

    elif re.search(r'\b(min[\s-]*heap|max[\s-]*heap|priority\s*queue|heapify|binary\s*heap|sift[\s-]*up|sift[\s-]*down)\b', text):
        return "dsa_heaps"

    elif re.search(r'\b(stack\s*adt|lifo\s*order|push\s*and\s*pop|monotonic\s*stack|stack\s*underflow|stack\s*overflow)\b', text):
        return "dsa_stacks"

    elif re.search(r'\b(queue\s*adt|fifo\s*order|enqueue\s*and\s*dequeue|circular\s*ring\s*buffer|double[\s-]*ended\s*queue|deque)\b', text):
        return "dsa_queues"

    elif re.search(r'\b(hash\s*table|hash\s*map|hash\s*set|hash\s*function|collision\s*resolution|chaining|open\s*addressing|linear\s*probing|hash\s*bucket)\b', text):
        return "dsa_hashing"

    elif re.search(r'\b(dynamic\s*programming|memoization|tabulation|optimal\s*substructure|overlapping\s*subproblems|knapsack|longest\s*common\s*subsequence)\b', text):
        return "dsa_dp"

    elif re.search(r'\b(binary\s*search|bisect|logarithmic\s*search|search\s*space\s*halv|midpoint\s*calculation)\b', text) and not re.search(r'\b(binary\s*search\s*trees?|bsts?\b)\b', text):
        return "dsa_binary_search"

    elif re.search(r'\b(linear\s*search|sequential\s*search|sequential\s*scan|array\s*traversal\s*search)\b', text):
        return "dsa_linear_search"

    elif re.search(r'\b(quicksort|lomuto|partition\s*scheme|mergesort|heapsort|in-place\s*sorting)\b', text):
        return "dsa_sorting"

    elif re.search(r'\b(recursion|recursive\s*call|call\s*stack|activation\s*record|base\s*case)\b', text):
        return "dsa_recursion"

    elif re.search(r'\b(linked\s*lists?|singly\s*linked|doubly\s*linked|circular\s*linked|sentinel\s*node|node\.next|head\s*node)\b', text):
        return "dsa_linked_lists"

    elif re.search(r'\b(arrays?|dynamic\s*arrays?|vectors?|contiguous\s*memory|base\s*address|two[\s-]*pointers?|sliding\s*window|prefix\s*sums?|subarrays?)\b', text):
        return "dsa_arrays"

    elif re.search(r'\b(random\s*forest|decision\s*trees?|ensemble|bagging|gini\s*index|information\s*gain)\b', text):
        return "ml_trees"

    elif re.search(r'\b(transformer|self[\s-]*attention|multi[\s-]*head\s*attention|query\s*key\s*value|neural\s*network|backprop)\b', text):
        return "ml_deep_learning"

    elif re.search(r'\b(linear\s*regression|logistic\s*regression|least\s*squares|gradient\s*descent|bias[\s-]*variance)\b', text):
        return "ml_regression"

    elif re.search(r'\b(normalization|normal\s*forms?|1nf|2nf|3nf|bcnf|boyce[\s-]*codd|functional\s*dependenc(y|ies)|lossless\s*decomposition)\b', text):
        return "dbms_normalization"

    # Notice: Specific compound terms, NO bare "database" or "indexing" words that hijack DSA!
    elif re.search(r'\b(acid\s*(guarantees|properties)?|atomicity|serializability|two-phase\s*locking|write-ahead\s*log|wal\b|isolation\s*levels?|dirty\s*reads?|phantom\s*reads?|repeatable\s*read|database\s+transactions?|sql\s+transactions?|concurrency\s*control|buffer\s*pool\s*manager|rollback\s*segment)\b', text):
        return "dbms_transactions"

    elif re.search(r'\b(tcp|udp|ip\b|osi\b|handshake|syn\s*packet|snmp|packet\s*capture|wireshark|sliding\s*window|socket|ethernet|icmp)\b', text):
        return "networking"

    elif re.search(r'\b(operating\s*systems?|cpu\s*scheduling|round[\s-]*robin|shortest\s*job|deadlocks?|banker\'?s\s*algorithm|virtual\s*memory|page\s*replacement|page\s*table|tlb|semaphores?|mutex|context\s*switch)\b', text):
        return "os_systems"

    elif re.search(r'\b(system\s*design|distributed\s*systems?|microservices?|load\s*balanc(er|ing)|caching\s*strateg(y|ies)|redis|api\s*gateway|message\s*queue|kafka|cap\s*theorem|rate\s*limit(er|ing)|consistent\s*hashing)\b', text):
        return "system_design"

    else:
        return "general_cs"


VALID_VISUAL_TYPES = {
    "title_card", "flow_steps", "array_memory", "queue_structure",
    "tree_structure", "genai_transformer", "agentic_loop", "system_pipeline",
    "concept_network", "layer_stack", "cycle_loop", "comparison",
    "comparison_matrix", "code_snippet", "text_bullets", "graph_chart"
}

def sanitize_visual_type(raw_type: str, visual_data: dict) -> str:
    vt = (raw_type or "").lower().strip()
    if vt in VALID_VISUAL_TYPES:
        return vt
    # Map common aliases or LLM deviations to valid Remotion visuals
    if any(k in vt for k in ["queue", "fifo", "ring_buffer", "deque"]):
        return "queue_structure"
    if any(k in vt for k in ["code", "snippet", "implementation", "program", "syntax"]):
        return "code_snippet"
    if any(k in vt for k in ["matrix", "grid", "table"]):
        return "comparison_matrix"
    if any(k in vt for k in ["compare", "vs", "versus", "difference", "tradeoff"]):
        return "comparison"
    if any(k in vt for k in ["step", "flow", "transition", "phase", "lifecycle"]):
        return "flow_steps"
    if any(k in vt for k in ["bullet", "item", "list", "takeaway", "edge", "invariant"]):
        return "text_bullets"
    if any(k in vt for k in ["tree", "hierarchy", "decision_tree", "bst", "heap"]):
        return "tree_structure"
    if any(k in vt for k in ["array", "memory", "address", "pointer", "register", "bitwise"]):
        return "array_memory"
    if any(k in vt for k in ["stack", "layer", "tier", "frame"]):
        return "layer_stack"
    if any(k in vt for k in ["loop", "cycle", "circular"]):
        return "cycle_loop"
    if any(k in vt for k in ["network", "graph", "topology"]):
        return "concept_network"
    if any(k in vt for k in ["pipeline", "stream"]):
        return "system_pipeline"

    # Infer from data shape
    if not isinstance(visual_data, dict):
        return "flow_steps"
    if "rows" in visual_data:
        return "comparison_matrix"
    if "steps" in visual_data:
        return "flow_steps"
    if "items" in visual_data:
        return "text_bullets"
    if "left_title" in visual_data or "right_title" in visual_data:
        return "comparison"
    if "stages" in visual_data:
        return "system_pipeline"
    if "layers" in visual_data:
        return "layer_stack"
    if "nodes" in visual_data:
        return "concept_network"
    if "code" in visual_data:
        return "code_snippet"
    return "flow_steps"

def generate_video_plan(lesson_title: str, lesson_content: str, difficulty: str = "Advanced") -> list[dict]:
    """
    Transforms lesson content into high-retention, 8-scene animated video blueprints (~2 minutes)
    tailored dynamically to the topic's true subject domain.
    """
    lesson_title = clean_lesson_title(lesson_title)
    domain = detect_domain(lesson_title, lesson_content)
    scene_count = 8
    duration_desc = "~2:00-2:15 minutes across 8 comprehensive scenes"

    if domain == "ml_trees":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Machine Learning - Decision Trees & Random Forest Ensembles ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Decision Trees & Ensembles:
        - Scene 1: "title_card" -> Foundational Problem Framing: From Single Decision Trees to Random Forest Ensembles.
        - Scene 2: "flow_steps" -> 3-Stage Splitting Strategy: 1. Feature Cutoff Search, 2. Gini Impurity / Entropy Minimization, 3. Tree Halting & Pruning.
        - Scene 3: "tree_structure" -> Tree Node Splitting visualization showing Parent Node, decision cutoff (e.g. Age < 60), and Left/Right daughter nodes with purity.
        - Scene 4: "code_snippet" -> Clean Python / Scikit-Learn code (RandomForestClassifier, n_estimators=100, max_depth, fit/predict).
        - Scene 5: "system_pipeline" -> Concrete Ensemble Voting Pipeline: Bootstrap Sampling -> Parallel Tree Classifications -> Majority Voting Aggregation.
        - Scene 6: "comparison" -> Single Decision Tree (High Variance, Overfitting to Noise) vs. Random Forest Ensemble (Averaged Low Variance, Stable).
        - Scene 7: "comparison_matrix" -> Performance Profile Matrix: Bias vs Variance, Overfitting Risk, Interpretability, Training Speed.
        - Scene 8: "text_bullets" -> Senior ML Production Invariants: Feature Subsampling (sqrt(p)), Hyperparameter Tuning, Out-of-Bag (OOB) Generalization.
        """
    elif domain == "ml_regression":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Machine Learning - Regression & Optimization Theory ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Regression & Optimization:
        - Scene 1: "title_card" -> Problem Space: Quantitative Continuous Prediction vs Qualitative Probability Modeling.
        - Scene 2: "flow_steps" -> 3-Stage Mathematical Learning Flow: 1. Hypothesis Formulation, 2. Loss Function Definition (RSS / Log-Loss), 3. Optimization via Normal Equations or Gradient Descent.
        - Scene 3: "graph_chart" -> Dynamic Loss Curve or Scatter Plot with Fitted Regression Line and Residual Error stems.
        - Scene 4: "code_snippet" -> Clean Python / Scikit-Learn code (LinearRegression / LogisticRegression, normal equations solution, evaluation metrics).
        - Scene 5: "cycle_loop" -> Iterative Optimization Loop: Forward Prediction -> Residual Error Loss -> Gradient Step -> Parameter Update Convergence.
        - Scene 6: "comparison" -> High Bias Underfitting (Overly Rigid Model) vs High Variance Overfitting (Complex Polynomial Fitting Noise).
        - Scene 7: "comparison_matrix" -> Statistical Metric Matrix: R-squared, Residual Standard Error (RSE), Confusion Matrix (Precision, Recall, ROC-AUC).
        - Scene 8: "text_bullets" -> Senior ML Production Invariants: Collinearity Detection, L1/L2 Regularization, Outlier Leverage, and Strict Train/Val/Test Splits.
        """
    elif domain == "ml_deep_learning":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Machine Learning - Deep Learning & Attention Mechanisms ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Deep Learning & Transformers:
        - Scene 1: "title_card" -> AI Model Architecture & Latent Representation Vision.
        - Scene 2: "system_pipeline" -> Forward Pass Pipeline: Tokenization -> Embedding Space -> Multi-Head Attention -> Output Logits.
        - Scene 3: "genai_transformer" -> Scaled Dot-Product Attention Heatmap Matrix (Query-Key-Value interactions).
        - Scene 4: "code_snippet" -> Clean PyTorch code implementing the Scaled Dot-Product Attention layer.
        - Scene 5: "agentic_loop" -> Backpropagation & Residual Gradient Stream Flow through deep layers.
        - Scene 6: "comparison" -> Recurrent Architectures (Sequential Latency Bottleneck) vs Transformer Attention (Parallel Matrix Execution).
        - Scene 7: "comparison_matrix" -> Attention Scaling Matrix: Vanilla Quadratic O(N^2) Attention vs FlashAttention Kernel Fusion.
        - Scene 8: "text_bullets" -> Production AI Deployment: KV Caching, 4-bit Weight Quantization, and Memory-Bound Kernel Fusion.
        """
    elif domain == "dbms_normalization":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Database Management Systems - Normalization & Schema Design ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Database Normalization:
        - Scene 1: "title_card" -> Relational Schema Design: Eliminating Data Redundancy & Insertion/Update/Delete Anomalies.
        - Scene 2: "flow_steps" -> The 4 Stages of Normalization: 1. 1NF (Atomic Cells), 2. 2NF (Eliminate Partial Dependencies), 3. 3NF (Eliminate Transitive Dependencies), 4. BCNF (Superkey Invariant).
        - Scene 3: "comparison" -> Unnormalized Anomaly-Ridden Table (Redundant Duplication, Update Inconsistency) vs Decomposed Clean Normalized Relations.
        - Scene 4: "code_snippet" -> Clean SQL DDL Schema with Normalized Relations, Primary Keys, and Foreign Key References.
        - Scene 5: "system_pipeline" -> Functional Dependency Decomposition Pipeline: Candidate Key Discovery -> Non-Key Isolation -> Schema Partitioning.
        - Scene 6: "concept_network" -> Entity-Relationship & Functional Dependency Graph: Visualizing Functional Dependencies (X -> Y) and Prime Keys.
        - Scene 7: "comparison_matrix" -> Normal Form Anomaly Elimination Matrix: 1NF vs 2NF vs 3NF vs BCNF comparing Redundancy, Dependency Preservation, and Anomaly Protection.
        - Scene 8: "text_bullets" -> Senior Database Engineering Invariants: Lossless Decomposition, Dependency Preservation, and Intentional Denormalization for OLAP Reads.
        """
    elif domain == "dbms_transactions":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Database Management Systems - Transactions, ACID & Storage Engines ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Database Transactions & Indexing:
        - Scene 1: "title_card" -> Database Transaction Architecture: Atomicity, Consistency, Isolation, and Durability Guarantees.
        - Scene 2: "flow_steps" -> The 4 Pillars of ACID: 1. Atomicity (All-or-Nothing Rollback), 2. Consistency (Integrity Invariants), 3. Isolation (Serializability), 4. Durability (Crash Recovery).
        - Scene 3: "tree_structure" -> Multi-Level B-Tree / B+ Tree Indexing Hierarchy: Root Node -> Internal Index Pages -> Leaf Record Pointers.
        - Scene 4: "code_snippet" -> Production SQL Transaction with Explicit Isolation Level (BEGIN TRANSACTION; SET ISOLATION LEVEL SERIALIZABLE; COMMIT;).
        - Scene 5: "system_pipeline" -> Durability & Write-Ahead Logging (WAL) Pipeline: Application SQL -> In-Memory Buffer Pool -> WAL Disk Flush -> Checkpoint Persistence.
        - Scene 6: "comparison" -> Pessimistic Concurrency (Row Locks, Resource Contention) vs Optimistic Concurrency Control (Validation at Commit, Abort-and-Retry).
        - Scene 7: "comparison_matrix" -> Transaction Isolation Level Matrix: Read Uncommitted vs Read Committed vs Repeatable Read vs Serializable against Dirty, Non-Repeatable, and Phantom Reads.
        - Scene 8: "text_bullets" -> Senior Database Engineering Invariants: Deadlock Prevention via Uniform Lock Acquisition, WAL Checkpointing, and Sharding Consistency.
        """
    elif domain == "dsa_arrays":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Arrays & Contiguous Memory Architecture ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Arrays and Contiguous Memory:
        - Scene 1: "title_card" -> Foundational Problem Framing: Contiguous Memory Layout, Indexing Invariant & O(1) Random Access.
        - Scene 2: "array_memory" -> In-Memory Array Ribbon showing contiguous memory cells with indices [0, 1, 2, 3, 4], values, hexadecimal RAM byte addresses (0x1000, 0x1004, 0x1008...), and active Low/Mid/arr[i] pointer indicators.
        - Scene 3: "flow_steps" -> 3-Stage Memory Access Mechanics: 1. Base Pointer Acquisition (&arr[0]), 2. Offset Arithmetic (addr = base + i * sizeof(T)), 3. Direct O(1) Memory Dereference.
        - Scene 4: "code_snippet" -> Clean C/C++ or Python code demonstrating array allocation (malloc/vector), indexing, and pointer arithmetic.
        - Scene 5: "system_pipeline" -> Dynamic Resizing Pipeline: Capacity Check -> Double Buffer Allocation (2x N) -> Deep Element Copy -> Old Buffer Free.
        - Scene 6: "comparison" -> Contiguous Array (O(1) Direct Access, CPU Cache Spatial Locality, O(N) Insertion Shift) vs Linked List (O(N) Traversal, Scattered Heap Nodes, O(1) Pointer Splice).
        - Scene 7: "comparison_matrix" -> Comprehensive Architectural Matrix comparing "Contiguous Array" vs "Linked List":
          Accurately evaluate:
          1. "Random Access": left: "O(1) Direct Offset", right: "O(N) Pointer Traversal", winner: "left".
          2. "Insert at Head": left: "O(N) Element Shift", right: "O(1) Pointer Splice", winner: "right".
          3. "Insert in Middle": left: "O(N) Element Shift", right: "O(N) Traversal to Node", winner: "left". (Note: Linked List requires O(N) traversal to reach the middle node).
          4. "CPU Cache Locality": left: "Optimal (L1/L2 Spatial Locality)", right: "Poor (Heap Cache Misses)", winner: "left".
          5. "Memory Overhead": left: "Minimal (Contiguous Data)", right: "High (+8B to 16B Pointers/Node)", winner: "left".
        - Scene 8: "text_bullets" -> Senior Systems & DSA Invariants: CPU L1/L2 Cache Line Locality, Spatial Locality prefetching, Zero-based index arithmetic, and Buffer Overflow boundary guards.
        """
    elif domain == "dsa_linked_lists":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Linked Lists & Dynamic Node Pointer Architecture ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Linked Lists:
        - Scene 1: "title_card" -> Foundational Problem Framing: Dynamic Heap Allocation, Disjoint Memory & Pointer Linking Invariants.
        - Scene 2: "system_pipeline" -> Sequential Node Chain Trace: Head Pointer -> Node(10) -> Node(20) -> Node(30) -> NULL.
        - Scene 3: "flow_steps" -> 3-Stage Head Insertion Invariant: 1. Allocate New Node on Heap, 2. Wire new_node.next = head, 3. Reassign head = new_node in O(1) time.
        - Scene 4: "code_snippet" -> Clean Python / C++ SinglyLinkedList implementation with Node struct, head insertion, and boundary guards.
        - Scene 5: "cycle_loop" -> Traversal & Deletion Cycle: Advance prev & cur pointers -> Rewire prev.next = cur.next -> Free discarded node.
        - Scene 6: "comparison" -> Singly Linked List (O(1) Head Insertion, Non-Contiguous Growth) vs Contiguous Array (O(1) Random Access, Cache Locality, O(N) Head Insert).
        - Scene 7: "comparison_matrix" -> Linked List vs Dynamic Array Architecture Matrix:
          leftHeader: "Linked List", rightHeader: "Dynamic Array".
          1. "Insert at Head": left: "O(1) Pointer Update", right: "O(N) Shift", winner: "left".
          2. "Random Access": left: "O(N) Traversal", right: "O(1) Direct Offset", winner: "right".
          3. "Insert in Middle": left: "O(N) Traversal to Node", right: "O(N) Element Shift", winner: "tie".
          4. "Memory Locality": left: "Poor (Heap Pointer Chasing)", right: "Optimal (CPU Cache Lines)", winner: "right".
          5. "Capacity Flexibility": left: "Infinite Dynamic Growth", right: "Requires 2x Reallocation", winner: "left".
        - Scene 8: "text_bullets" -> Senior Algorithmic Invariants: Sentinel/Dummy Head Node to eliminate null edge cases, Fast & Slow Pointers (Floyd's Cycle Finding), and Memory Leak Prevention.
        """
    elif domain == "dsa_binary_search":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Binary Search & Logarithmic Partitioning ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Binary Search:
        - Scene 1: "title_card" -> Foundational Problem Framing & Asymptotic Logarithmic Efficiency O(log N).
        - Scene 2: "array_memory" -> Interactive Memory Ribbon showing array cells, address offsets, and active Low, Mid, High pointers.
        - Scene 3: "flow_steps" -> 3-Stage Algorithmic Invariant: 1. Boundary Initialization, 2. Midpoint Inspection, 3. Deterministic Search Space Halving.
        - Scene 4: "code_snippet" -> Clean Python/C++ code preventing integer overflow (mid = beg + (end - beg) // 2).
        - Scene 5: "system_pipeline" -> Iterative Convergence Trace: Step-by-Step Halving Trace from N -> N/2 -> 1.
        - Scene 6: "comparison" -> Naive Linear Scan O(N) vs Logarithmic Binary Search O(log N).
        - Scene 7: "comparison_matrix" -> Asymptotic Complexity Analysis Matrix: Best, Average, Worst Case Time, and Auxiliary Space.
        - Scene 8: "text_bullets" -> Senior Algorithmic Invariants: Monotonic Pre-sorting prerequisite, Off-by-one boundary guards, and Binary Search on the Answer Space.
        """
    elif domain == "dsa_linear_search":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Linear Search & Sequential Traversal ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Linear Search:
        - Scene 1: "title_card" -> Foundational Problem Framing: Sequential Search Space & Unsorted Data Invariant O(N).
        - Scene 2: "array_memory" -> In-Memory Array Ribbon showing array cells, elements, target value, and the active scanning pointer i checking elements sequentially from index 0.
        - Scene 3: "flow_steps" -> 3-Stage Algorithmic Invariant: 1. Pointer Initialization (i=0), 2. Element Comparison (arr[i] == target), 3. Early Termination on Match or Array Exhaustion.
        - Scene 4: "code_snippet" -> Clean Python/C++ code implementing Linear Search with early termination and sentinel search variant.
        - Scene 5: "system_pipeline" -> Sequential Traversal Trace: Step-by-Step Scan from Index 0 -> 1 -> 2 until Target is located.
        - Scene 6: "comparison" -> Linear Search (Unsorted, O(N), Works on streams and linked lists) vs Binary Search (Requires sorted array, O(log N)).
        - Scene 7: "comparison_matrix" -> Asymptotic Complexity Analysis Matrix: Best Case O(1), Average Case O(N), Worst Case O(N), Space O(1).
        - Scene 8: "text_bullets" -> Senior Algorithmic Invariants: Cache line prefetching advantages, Sentinel search optimization, and Practical threshold rules (N < 30).
        """
    elif domain == "dsa_sorting":
        # Dynamically detect the specific sorting algorithm from the title
        title_lower = lesson_title.lower()
        if "merge" in title_lower:
            sort_algo = "Merge Sort"
            sort_steps = "1. Divide array into halves, 2. Recursively sort each half, 3. Merge sorted halves back"
            sort_code_desc = "Clean Python/C++ code implementing Merge Sort with the Merge subroutine (two-pointer merge)."
            sort_ptr_desc = "In-Memory Array Ribbon showing left and right sub-arrays, merge pointers i, j, and k."
            sort_worst = "Guaranteed O(N log N) time in all cases — best, average, and worst."
            sort_compare = "In-Place O(1) Quicksort (Cache-friendly) vs Merge Sort (O(N) auxiliary, always stable, guaranteed O(N log N))."
        elif "heap" in title_lower:
            sort_algo = "Heap Sort"
            sort_steps = "1. Build Max-Heap (Heapify), 2. Extract-Max root to sorted end, 3. Restore heap property"
            sort_code_desc = "Clean Python/C++ code implementing Heap Sort with heapify-down subroutine."
            sort_ptr_desc = "In-Memory Array Ribbon showing heap region vs sorted region boundary."
            sort_worst = "Guaranteed O(N log N) worst-case, in-place O(1) auxiliary space."
            sort_compare = "Quicksort (Cache-friendly, avg O(N log N)) vs Heap Sort (Guaranteed O(N log N), poor cache locality)."
        elif "bubble" in title_lower:
            sort_algo = "Bubble Sort"
            sort_steps = "1. Compare adjacent pairs, 2. Swap if out of order, 3. Repeat N-1 passes"
            sort_code_desc = "Clean Python/C++ code implementing optimized Bubble Sort with early-exit flag."
            sort_ptr_desc = "In-Memory Array Ribbon showing comparison pointer sweeping and bubble propagation."
            sort_worst = "O(N^2) worst case — practical only for nearly-sorted small arrays."
            sort_compare = "Naive Bubble Sort O(N^2) vs Optimized Early-Exit Bubble Sort vs Insertion Sort O(N) best case."
        elif "insertion" in title_lower:
            sort_algo = "Insertion Sort"
            sort_steps = "1. Pick next key element, 2. Shift larger elements right, 3. Insert key at correct position"
            sort_code_desc = "Clean Python/C++ code implementing Insertion Sort with binary search optimization variant."
            sort_ptr_desc = "In-Memory Array Ribbon showing sorted prefix region, key element, and shift pointers."
            sort_worst = "O(N^2) worst case but O(N) on nearly-sorted — adaptive and stable."
            sort_compare = "Insertion Sort (Adaptive, O(N) best) vs Merge Sort (Always O(N log N)) vs Quick Sort (In-place, fast cache)."
        elif "selection" in title_lower:
            sort_algo = "Selection Sort"
            sort_steps = "1. Find minimum in unsorted region, 2. Swap with leftmost unsorted, 3. Advance sorted boundary"
            sort_code_desc = "Clean Python/C++ code implementing Selection Sort with minimum tracking."
            sort_ptr_desc = "In-Memory Array Ribbon showing sorted prefix, current minimum pointer, and scan pointer."
            sort_worst = "O(N^2) in all cases — minimal swaps (O(N)) but no early termination."
            sort_compare = "Selection Sort (O(N) swaps, always O(N^2)) vs Bubble Sort (O(N^2) swaps, adaptive) vs Insertion Sort."
        else:  # Default: Quicksort
            sort_algo = "Quicksort"
            sort_steps = "1. Divide via Lomuto/Hoare Partition, 2. Conquer via Subarray Recursion, 3. In-Place Combine"
            sort_code_desc = "Clean Python/C++ code implementing Quicksort and the Lomuto Partition subroutine."
            sort_ptr_desc = "In-Memory Array Ribbon showing active Pivot element, scanning pointers i and j, and swap regions."
            sort_worst = "Pathological Worst-Case O(N^2) (Pre-sorted with fixed pivot) vs Balanced Expected O(N log N) (Randomized pivot)."
            sort_compare = "Pathological Worst-Case O(N^2) (Pre-sorted, fixed pivot) vs Balanced Expected O(N log N) (Randomized pivot)."

        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - {sort_algo} ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for {sort_algo}:
        - Scene 1: "title_card" -> Divide-and-Conquer Paradigm: {sort_algo} — Core algorithm framing for {lesson_title}.
        - Scene 2: "array_memory" -> {sort_ptr_desc}
        - Scene 3: "flow_steps" -> {sort_algo} 3-Step Strategy: {sort_steps}.
        - Scene 4: "code_snippet" -> {sort_code_desc}
        - Scene 5: "system_pipeline" -> Execution & Recursion Tree Trace: Dynamic Subarray processing for {lesson_title}.
        - Scene 6: "comparison" -> {sort_compare}
        - Scene 7: "comparison_matrix" -> Sorting Algorithm Comparison Matrix: {sort_algo} vs MergeSort vs HeapSort across Time, Auxiliary Space, Cache Locality, and Stability.
        - Scene 8: "text_bullets" -> Senior Algorithmic Invariants: Loop Invariant Correctness, Complexity analysis, and production tips for {sort_algo}.
        """
    elif domain == "dsa_recursion":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Recursion & Call Stack Mechanics ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Recursion:
        - Scene 1: "title_card" -> Foundational Problem Framing: Divide-and-Conquer & Mathematical Induction Hook.
        - Scene 2: "flow_steps" -> The 3 Golden Rules of Recursion: 1. Base Case Guard, 2. State Reduction, 3. Call Stack Unwinding.
        - Scene 3: "layer_stack" -> In-Memory Call Stack Layout showing activation records (stack frames) pushed and popped in LIFO order.
        - Scene 4: "code_snippet" -> Clean C++/Python recursive code implementing explicit base case guards.
        - Scene 5: "system_pipeline" -> Concrete Execution Trace stepping through recursive descent and ascent.
        - Scene 6: "comparison" -> Recursive Paradigm (Call Stack elegance) vs Iterative Paradigm (Explicit loop, O(1) auxiliary space).
        - Scene 7: "comparison_matrix" -> Asymptotic Profile & Memory Footprint (Time Complexity, Stack Depth O(N), Stack Overflow risk).
        - Scene 8: "text_bullets" -> Senior Engineering Invariants: Preventing Stack Overflow, Tail Call Optimization, Memoization.
        """
    elif domain == "dsa_tree_graph":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Binary Search Trees & Tree Invariants ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Binary Search Trees:
        - Scene 1: "title_card" -> Foundational Problem Framing: Hierarchical Search Space & The BST Invariant (Left < Root < Right).
        - Scene 2: "flow_steps" -> 3 Core BST Operations: 1. Root Key Inspection, 2. Directional Branch Decision (Left if Key < Node, Right if Key > Node), 3. Terminal Insertion / Search Halving.
        - Scene 3: "tree_structure" -> Interactive Binary Search Tree Visual showing Root Node (Key 50), Left Subtree (< 50, Node: 25, Leaves: 12, 37), Right Subtree (> 50, Node: 75, Leaves: 62, 87) demonstrating the invariant.
        - Scene 4: "code_snippet" -> Clean Python/C++ code implementing recursive BST Search and Insert with Left/Right pointer transitions.
        - Scene 5: "system_pipeline" -> Concrete Key Search Traversal: Step 1: Root Comparison -> Step 2: Branch Halving Traversal -> Step 3: Target Node Located in O(log N).
        - Scene 6: "comparison" -> Degenerate Skewed BST (Worst-Case O(N) Unbalanced Linear Chain) vs Self-Balancing AVL/Red-Black Tree (Guaranteed O(log N) Depth).
        - Scene 7: "comparison_matrix" -> Asymptotic Profile Matrix: Average Case O(log N) vs Degenerate Worst Case O(N) across Search, Insert, and Delete operations, plus O(H) Call Stack Auxiliary Space.
        - Scene 8: "text_bullets" -> Senior Algorithmic Invariants: In-Order Traversal yields strictly sorted output, Deletion via In-Order Successor / Predecessor, and Self-Balancing tree rotations.
        """
    elif domain == "dsa_stacks":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Stacks & LIFO Data Structures ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Stacks:
        - Scene 1: "title_card" -> Foundational Problem Framing: Last-In-First-Out (LIFO) Contract & Abstract Data Type Foundations.
        - Scene 2: "flow_steps" -> 3 Core Stack Operations: 1. Push (Allocate top slot & insert element), 2. Pop (Retrieve top element & decrement pointer), 3. Peek / Top (Inspect current top value without mutation).
        - Scene 3: "layer_stack" -> In-Memory Stack Visual showing vertical stack layers: Top Element (Top Pointer, status: 'top', tag: 'TOP'), Middle Elements, Base Element (tag: 'BASE'), showing strictly O(1) top access.
        - Scene 4: "code_snippet" -> Clean Python Stack class implementation using dynamic array with push(), pop(), peek(), and is_empty() boundary guards.
        - Scene 5: "system_pipeline" -> Concrete Real-World Trace: Validating Balanced Parentheses or Infix-to-Postfix conversion stepping through token evaluations.
        - Scene 6: "comparison" -> Stack (LIFO: Push & Pop only at Top, O(1)) vs Queue (FIFO: Enqueue at Rear, Dequeue at Front, O(1)).
        - Scene 7: "comparison_matrix" -> Stack Operations Matrix: Array-based Stack vs Linked-List-based Stack across Push, Pop, Peek, Dynamic Resizing Overhead, and Cache Locality.
        - Scene 8: "text_bullets" -> Senior Algorithmic Invariants: Preventing Stack Underflow & Overflow, Call Stack Trace frames, and Monotonic Stack for Next Greater Element in O(N) linear time.
        """
    elif domain == "dsa_queues":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Queues & FIFO Data Structures ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Queues:
        - Scene 1: "title_card" -> Foundational Problem Framing: First-In-First-Out (FIFO) Contract & Sequential Stream Processing.
        - Scene 2: "flow_steps" -> 3 Core Queue Operations: 1. Enqueue (Append item to rear), 2. Dequeue (Extract item from front), 3. Front / Peek (Inspect line head).
        - Scene 3: "queue_structure" -> Horizontal FIFO Queue Structure: Front Pointer pointing to head element (ready for Dequeue), intermediate queued items, and Rear Pointer pointing to tail element (ready for Enqueue), showing strict FIFO order.
        - Scene 4: "code_snippet" -> Clean Python Queue implementation using collections.deque or circular array buffer.
        - Scene 5: "cycle_loop" -> Circular Ring Buffer: Modulo Pointer Math (rear + 1) % capacity eliminating O(N) array shifting.
        - Scene 6: "comparison" -> Naive Array Queue (O(N) Dequeue shift bottleneck) vs Circular Ring Buffer / Linked List (O(1) constant time dequeue).
        - Scene 7: "comparison_matrix" -> Queue Complexity Matrix: Array Shift vs Circular Ring Buffer vs Doubly-Linked Deque across Enqueue, Dequeue, Peek, and Memory Locality.
        - Scene 8: "text_bullets" -> Senior Systems Invariants: BFS Graph Frontier Queue, Asynchronous Message Broker Buffers, Rate Limiting Leaky Buckets, and Underflow/Overflow Guards.
        """
    elif domain == "dsa_heaps":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Heaps & Priority Queues ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Heaps:
        - Scene 1: "title_card" -> Foundational Problem Framing: Priority Queues & Complete Binary Heap Invariants.
        - Scene 2: "tree_structure" -> Complete Binary Tree Visual: Min-Heap / Max-Heap showing Root Node (Min/Max Key), Left Subtree, Right Subtree, demonstrating Parent <= Children property.
        - Scene 3: "array_memory" -> Zero-Indexed Array Representation: Contiguous memory ribbon showing explicit math indices (Left = 2i + 1, Right = 2i + 2, Parent = (i - 1) // 2).
        - Scene 4: "code_snippet" -> Clean Python Min-Heap implementation with sift_up and sift_down methods.
        - Scene 5: "flow_steps" -> 3-Stage Heapify Mechanics: 1. Insert at end of array, 2. Compare key with parent, 3. Sift-Up swap until heap invariant is restored.
        - Scene 6: "comparison" -> Min-Heap (Root is Minimum, O(1) peek) vs Max-Heap (Root is Maximum, O(1) peek) vs Unsorted Array for Priority Queue.
        - Scene 7: "comparison_matrix" -> Priority Queue Complexity Matrix: Binary Heap vs Unsorted Array vs Sorted Array across Insert, Extract-Min, Find-Min, and Build-Heap (O(N) linear time).
        - Scene 8: "text_bullets" -> Senior Algorithmic Invariants: Complete Binary Tree compact array storage with zero pointer overhead, Dijkstra's algorithm acceleration, and Top-K Streaming Elements.
        """
    elif domain == "dsa_graphs":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Graph Theory & Traversals ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Graphs:
        - Scene 1: "title_card" -> Foundational Problem Framing: Vertices, Edges, Directed Acyclic Graphs (DAG), and Network Connectivity.
        - Scene 2: "concept_network" -> Graph Topological Network: Central Vertex Hub connected to neighbor nodes with directional paths and edge weights.
        - Scene 3: "system_pipeline" -> Shortest Path / Traversal Pipeline: Source Vertex -> Frontier Queue / Priority Heap -> Edge Relaxation -> Shortest Path Tree.
        - Scene 4: "code_snippet" -> Clean Python Graph representation using Adjacency Lists and BFS / Dijkstra traversal.
        - Scene 5: "flow_steps" -> 3-Stage Traversal Mechanics: 1. Initialize Distance & Visited Set, 2. Pop next node from frontier, 3. Relax all adjacent unvisited edges.
        - Scene 6: "comparison" -> Adjacency Matrix (O(V^2) Space, O(1) Edge Check) vs Adjacency List (O(V + E) Space, Optimal for Sparse Graphs).
        - Scene 7: "comparison_matrix" -> Graph Algorithm Matrix: BFS vs DFS vs Dijkstra vs Bellman-Ford across Time Complexity, Space Complexity, and Negative Weight support.
        - Scene 8: "text_bullets" -> Senior Engineering Invariants: Cycle detection in DAGs via Topological Sorting, Disjoint Set Union (DSU) path compression for Kruskal MST, and Network Routing.
        """
    elif domain == "dsa_hashing":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Hash Tables & Collision Resolution ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Hash Tables:
        - Scene 1: "title_card" -> Foundational Problem Framing: O(1) Average-Time Key-Value Mapping & Direct Memory Addressing.
        - Scene 2: "system_pipeline" -> Hash Function Execution Pipeline: Raw Key -> Hash Function Computation -> Modulo Capacity Compression -> Bucket Index.
        - Scene 3: "array_memory" -> Hash Bucket Array Memory: Array of buckets demonstrating indexed slots (Slot 0, Slot 1, Slot 2...) holding resolved key-value pairs.
        - Scene 4: "code_snippet" -> Clean Python Hash Map implementation with Separate Chaining collision handling.
        - Scene 5: "flow_steps" -> 3 Collision Resolution Stages: 1. Hash Code Generation, 2. Bucket Collision Detection, 3. Chaining / Open Addressing Resolution.
        - Scene 6: "comparison" -> Separate Chaining (Linked Lists per bucket, graceful degradation) vs Open Addressing (Linear Probing, cache-friendly, clustering risk).
        - Scene 7: "comparison_matrix" -> Hash Table vs Balanced BST vs Array Matrix across Lookup, Insert, Delete, and Sorted Order Invariants.
        - Scene 8: "text_bullets" -> Senior Engineering Invariants: Load Factor threshold (0.75) triggering dynamic table doubling and rehashing, uniform distribution, and avoiding hash flooding vulnerabilities.
        """
    elif domain == "dsa_dp":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Dynamic Programming & Recurrence ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Dynamic Programming:
        - Scene 1: "title_card" -> Foundational Problem Framing: Optimal Substructure & Overlapping Subproblems.
        - Scene 2: "flow_steps" -> The 4 Pillars of Dynamic Programming: 1. State Space Definition, 2. Recurrence Relation Formulation, 3. Base Case Initialization, 4. Computation Order (Top-Down / Bottom-Up).
        - Scene 3: "tree_structure" -> Recursion Tree with Subproblem Pruning: Showing exponential duplicate function calls (fib(3) computed multiple times) pruned into polynomial work via memoization.
        - Scene 4: "code_snippet" -> Clean Python DP implementation demonstrating Top-Down @lru_cache vs Bottom-Up Tabulation table.
        - Scene 5: "comparison_matrix" -> DP State Transition Table: 2D Grid / 1D Array showing subproblem values filled systematically row by row (e.g. Knapsack / LCS).
        - Scene 6: "comparison" -> Top-Down Memoization (Recursive, Intuitive, Stack Overhead) vs Bottom-Up Tabulation (Iterative, Cache-Friendly, Space-Optimizable).
        - Scene 7: "comparison_matrix" -> Complexity Profile Matrix: Naive Exponential Recursion O(2^N) vs Dynamic Programming O(N * W) Time and O(W) Space.
        - Scene 8: "text_bullets" -> Senior Algorithmic Invariants: State space reduction using rolling arrays (1D DP optimization), DAG topological ordering, and identifying subproblem recurrence relations.
        """
    elif domain == "dsa_memory_pointers":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Programming Primitives, Memory Model & Pointers ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Memory Architecture and Pointers:
        - Scene 1: "title_card" -> Foundational Problem Framing: Memory Architecture, Virtual Addresses, and Pointer Indirection.
        - Scene 2: "flow_steps" -> 3-Stage Memory Lifecycle: 1. Variable Address Allocation, 2. Pointer Storing Target Address (0x1004), 3. Dereferencing Operator (*ptr) / Frame Deallocation.
        - Scene 3: "array_memory" -> Contiguous Memory Layout: Cells showing explicit Hex Memory Addresses (0x1000, 0x1004, 0x1008), Variable Values, and Pointer labels (ptr -> 0x1000).
        - Scene 4: "code_snippet" -> Clean C/C++ code demonstrating pointer declaration, address-of (&x), dereferencing (*ptr), or Stack (int a = 10;) vs Dynamic Heap (int* b = new int(20); delete b;).
        - Scene 5: "system_pipeline" -> Memory Resolution Pipeline: Pointer Variable -> CPU Memory Management Unit (MMU) -> Physical RAM Bus -> Value Read.
        - Scene 6: "comparison" -> Stack Memory (Fast, Auto LIFO Deallocation, Fixed Frame Size) vs Dynamic Heap Memory (Flexible Runtime Size, Manual malloc/free, Fragmentation Risk) OR Pass-by-Value vs Pass-by-Reference.
        - Scene 7: "comparison_matrix" -> Memory Profile Matrix: Stack Allocation vs Heap Allocation across Speed, Scope, Lifetime, Overhead, and Safety (Stack Overflow vs Memory Leaks).
        - Scene 8: "text_bullets" -> Senior Systems Invariants: Dangling Pointer Elimination, Double Free Safeguards, Memory Alignment & Cache Lines, and RAII Smart Pointers (std::unique_ptr).
        """
    elif domain == "dsa_bitwise":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Bitwise Operations & Bitmasks ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Bitwise Logic:
        - Scene 1: "title_card" -> Foundational Problem Framing: Low-Level Binary Logic, Two's Complement & Bitmasking.
        - Scene 2: "flow_steps" -> 3 Bitmasking Primitives: 1. Set Bit (x | (1 << k)), 2. Clear Bit (x & ~(1 << k)), 3. Toggle Bit (x ^ (1 << k)).
        - Scene 3: "array_memory" -> Binary Register Ribbon: Memory array showing bit positions [b7 down to b0] with binary values [0, 1, 0, 1, 1, 0, 0, 1].
        - Scene 4: "code_snippet" -> Clean C++/Python bit manipulation helper functions for bitmask checks and bitwise counting.
        - Scene 5: "system_pipeline" -> ALU Execution Pipeline: Input Operands -> Bitwise Logic Gate (AND/OR/XOR) -> Shift Register -> Single-Cycle Hardware Result.
        - Scene 6: "comparison" -> Arithmetic Multiplication/Division vs High-Speed Hardware Bitwise Shifts (x << 1 vs x * 2).
        - Scene 7: "comparison_matrix" -> Bitwise Operators Matrix: AND, OR, XOR, NOT, Left Shift, and Right Shift truth tables.
        - Scene 8: "text_bullets" -> Senior Systems Invariants: Power of two check (x & (x - 1)) == 0, Brian Kernighan's bit count, and avoiding signed right shift arithmetic traps.
        """
    elif domain == "dsa_complexity":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Data Structures & Algorithms - Asymptotic Analysis & Algorithmic Complexity ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Algorithmic Complexity:
        - Scene 1: "title_card" -> Foundational Problem Framing: Asymptotic Growth Rates & Computational Resource Bounds.
        - Scene 2: "flow_steps" -> 3 Steps of Complexity Analysis: 1. Identify Input Size N, 2. Count Dominating Primitive Operations, 3. Discard Constants & Lower-Order Terms.
        - Scene 3: "comparison_matrix" -> The Big-O Hierarchy Matrix: O(1) Constant < O(log N) < O(N) < O(N log N) < O(N^2) < O(2^N) with runtime growth benchmarks.
        - Scene 4: "code_snippet" -> Clean Python comparative code demonstrating O(1) direct access, O(N) single loop, and O(N^2) nested loop algorithms.
        - Scene 5: "system_pipeline" -> Recurrence Relation Solving Pipeline: Recurrence T(N) = aT(N/b) + f(N) -> Master Theorem Case Identification -> Tight Asymptotic Bound.
        - Scene 6: "comparison" -> Big-O (Tight Upper Bound / Worst Case) vs Big-Omega (Lower Bound) vs Big-Theta (Tight Order).
        - Scene 7: "comparison_matrix" -> Case Complexity Analysis Matrix: Best Case vs Average Case vs Worst Case across Linear Search, QuickSort, and Binary Search.
        - Scene 8: "text_bullets" -> Senior Complexity Invariants: Space-Time trade-offs, In-Place auxiliary space vs input space, and avoiding hidden high constant factors.
        """
    elif domain == "networking":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Computer Networking & Communication Protocols ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Computer Networks:
        - Scene 1: "title_card" -> High-Throughput Architectural Vision & Protocol Foundation.
        - Scene 2: "layer_stack" -> Multi-layer abstraction (OSI 7 layers or TCP/IP 4 layers) showing vertical encapsulation.
        - Scene 3: "system_pipeline" -> Protocol Header Specification & Bit-level Fields (Ports, Sequence/ACK numbers, Flags, Checksum).
        - Scene 4: "cycle_loop" -> State Machine & Handshake Lifecycle (SYN -> SYN-ACK -> ACK) or SNMP Manager-Agent request/trap cycle.
        - Scene 5: "flow_steps" -> Dynamic Sliding Window Flow Control & Buffer Management preventing packet drops.
        - Scene 6: "comparison" -> Connection-Oriented Reliable (TCP: Handshake, Order, Retransmit) vs Connectionless Datagram (UDP: 8-byte Minimal Header, Fast, Unchecked).
        - Scene 7: "comparison_matrix" -> Protocol Feature Matrix: Reliability, Latency, Header Overhead, Flow Control.
        - Scene 8: "text_bullets" -> Production Network Hardening: TIME-WAIT Socket Draining (2MSL), SYN Flood Defense (SYN Cookies), Promiscuous Sniffing & Port Mirroring.
        """
    elif domain == "os_systems":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Operating Systems & Kernel Engineering ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Operating Systems:
        - Scene 1: "title_card" -> Kernel & OS Foundations: Process Scheduling, Virtual Memory & Concurrency Primitives.
        - Scene 2: "flow_steps" -> 3-Stage Process Lifecycle: 1. Admission & Scheduling, 2. Execution & Quantum Expiration, 3. Kernel Interrupt / Context Switch.
        - Scene 3: "layer_stack" -> OS Layer Hierarchy: User Space (Ring 3) -> System Call Traps -> Kernel Mode (Ring 0) -> Physical Silicon (CPU/MMU/RAM).
        - Scene 4: "code_snippet" -> Clean C / POSIX Synchronization code (Semaphores, Mutex locks, or Inter-Process Shared Memory).
        - Scene 5: "system_pipeline" -> Operational Hardware Translation: Virtual Address -> TLB Cache Check -> Page Table Walk -> Physical RAM Frame.
        - Scene 6: "comparison" -> Preemptive Scheduling (Timer Interrupts, Starvation Free) vs Cooperative Scheduling (Voluntary Yield, Low Overhead).
        - Scene 7: "comparison_matrix" -> OS Trade-Off Matrix: Round Robin vs Shortest Job First (SJF) across Response Time, Turnaround, and Overhead.
        - Scene 8: "text_bullets" -> Senior Systems Engineering Invariants: Coffman Deadlock Conditions, Thrashing Working Sets, and Priority Inheritance.
        """
    elif domain == "system_design":
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: System Design & Distributed Systems ({lesson_title}).
        Produce EXACTLY 8 distinct scenes structured specifically for Distributed Architecture:
        - Scene 1: "title_card" -> Distributed Systems Foundations: Horizontal Scaling, Fault-Tolerance & Microservice Mesh.
        - Scene 2: "flow_steps" -> 3-Stage Request Lifecycle: 1. Edge DNS & CDN Routing, 2. Reverse Proxy Load Balancing, 3. Decoupled Service Mesh Dispatch.
        - Scene 3: "concept_network" -> High-Availability Topology: Clients -> Layer 7 Load Balancer -> Stateless Compute Tier -> Distributed Cache -> Sharded DB.
        - Scene 4: "code_snippet" -> Production Implementation (Distributed Cache-Aside with Redis, or Token Bucket Rate Limiting).
        - Scene 5: "system_pipeline" -> Asynchronous Event-Driven Pipeline: API Write Ingest -> Kafka Partitioned Log -> Async Consumer Pool -> Read Store.
        - Scene 6: "comparison" -> Monolithic Architecture (Tight Coupling, Single Failure Domain) vs Microservices (Decoupled, Horizontally Scalable).
        - Scene 7: "comparison_matrix" -> CAP Theorem & Consistency Matrix: Strong Consistency (CP) vs High Availability (AP) across Latency and Partition Tolerance.
        - Scene 8: "text_bullets" -> Senior Distributed Engineering Invariants: Idempotency Keys, Circuit Breakers, and Exponential Backoff with Jitter.
        """
    else:
        prompt_scenes_guide = f"""
        TOPIC DOMAIN: Software Engineering & Computer Science ({lesson_title}).
        Produce EXACTLY 8 distinct scenes tailored to {lesson_title}:
        - Scene 1: "title_card" -> Architectural Vision & Problem Definition.
        - Scene 2: "flow_steps" -> 3-Stage Foundational Execution Flow.
        - Scene 3: "concept_network" -> System Architecture & Component Interaction.
        - Scene 4: "code_snippet" -> Clean Implementation / Data Structure Walkthrough.
        - Scene 5: "system_pipeline" -> Operational Execution Trace & State Transitions.
        - Scene 6: "comparison" -> Traditional Approach vs Modern {lesson_title} Architecture.
        - Scene 7: "comparison_matrix" -> Architectural Trade-offs & Efficiency Matrix.
        - Scene 8: "text_bullets" -> Senior Engineering Principles & Production Hardening.
        """

    prompt = f"""
    You are an award-winning Educational Video Director (think 3Blue1Brown, Khan Academy, Fireship).
    Convert the following lesson into an engaging 8-scene animated video ({duration_desc}).

    LESSON TITLE: {lesson_title}
    LESSON CONTENT:
    {lesson_content}

    RULES FOR PEDAGOGICAL EXCELLENCE:
    1. {prompt_scenes_guide}

    2. TIMING & PACING:
       - EXACTLY 8 scenes.
       - NARRATION: 40 to 50 words per scene (~14-16 seconds per scene, total video ~2 minutes).
       - Narration MUST explicitly teach {lesson_title} with precision, clarity, and natural conversational cadence.

    3. STRICT ANTI-HALLUCINATION & TOPIC RELEVANCE INVARIANTS:
       - Focus 100% on directly teaching '{lesson_title}'. Every scene must explicitly teach '{lesson_title}'.
       - Under NO circumstances include irrelevant concepts from disjoint computer science disciplines:
         * If this is an algorithm or data structure, NEVER mention SQL, ACID transactions, database tables, or neural networks.
         * If this is a machine learning topic, NEVER mention database normalization forms, network packet captures, or sorting algorithms.
         * If this is a networking topic, NEVER mention scikit-learn, relational schemas, or binary tree rotations.
         * If this is an operating systems topic, NEVER mention database normalization or machine learning loss functions.
       - The narration must use clear spoken sentences without markdown formatting.

    4. STRICT VISUAL_DATA JSON SCHEMAS:
       - For "title_card":
         "visual_data": {{"title": "{lesson_title}", "subtitle": "Clear, intuitive subtitle"}}
       - For "flow_steps":
         "visual_data": {{
           "steps": [
             {{"title": "Step 1", "desc": "Detailed description"}},
             {{"title": "Step 2", "desc": "Detailed description"}},
             {{"title": "Step 3", "desc": "Detailed description"}}
           ]
         }}
       - For "layer_stack":
         "visual_data": {{
           "title": "Stack Layer Visualization",
           "direction_label": "Direction of execution / growth",
           "layers": [
             {{"title": "Top Layer", "description": "Details", "tag": "L3", "status": "normal"}},
             {{"title": "Middle Layer", "description": "Details", "tag": "L2", "status": "normal"}},
             {{"title": "Base Layer", "description": "Details", "tag": "L1", "status": "normal"}}
           ]
         }}
       - For "tree_structure":
         "visual_data": {{
           "title": "{lesson_title} Hierarchy",
           "root_label": "Root Condition",
           "left_label": "Branch True",
           "right_label": "Branch False",
           "left_leaf_1": "Class A",
           "left_leaf_2": "Class B",
           "right_leaf_1": "Class C",
           "right_leaf_2": "Class D",
           "status": "Optimal Decision Boundary"
         }}
       - For "array_memory":
         "visual_data": {{
           "title": "{lesson_title} Memory Ribbon",
           "items": [
             {{"index": 0, "value": 11, "address": "0x1000", "status": "eliminated"}},
             {{"index": 1, "value": 24, "address": "0x1004", "status": "normal"}},
             {{"index": 2, "value": 37, "address": "0x1008", "status": "target"}},
             {{"index": 3, "value": 55, "address": "0x100C", "status": "normal"}}
           ],
           "pointers": [
             {{"label": "Low", "index": 0, "color": "#38bdf8"}},
             {{"label": "Mid", "index": 2, "color": "#f59e0b"}},
             {{"label": "High", "index": 3, "color": "#ec4899"}}
           ]
         }}
       - For "queue_structure":
         "visual_data": {{
           "title": "FIFO Queue Structure",
           "items": [
             {{"value": "Item [10]", "label": "Front / Dequeue", "status": "front", "index": 0}},
             {{"value": "Item [20]", "label": "Slot 1 (Waiting)", "status": "normal", "index": 1}},
             {{"value": "Item [30]", "label": "Slot 2 (Waiting)", "status": "normal", "index": 2}},
             {{"value": "Item [40]", "label": "Rear / Enqueue", "status": "rear", "index": 3}}
           ],
           "status": "FIFO Contract: First-In, First-Out • O(1) Dequeue at Front, O(1) Enqueue at Rear"
         }}
       - For "comparison":
         "visual_data": {{
           "left_title": "Approach A",
           "left_desc": "Explanation of Approach A",
           "right_title": "Approach B",
           "right_desc": "Explanation of Approach B"
         }}
       - For "comparison_matrix":
         "visual_data": {{
           "title": "Comparative Analysis",
           "leftHeader": "Option A",
           "rightHeader": "Option B",
           "rows": [
             {{"feature": "Feature 1", "left": "Value A", "right": "Value B"}},
             {{"feature": "Feature 2", "left": "Value A", "right": "Value B"}}
           ]
         }}
       - For "system_pipeline":
         "visual_data": {{
           "title": "Execution Pipeline",
           "stages": [
             {{"label": "1. Init", "subtitle": "Details", "badge": "Step 1", "icon": "🔍", "status": "normal"}},
             {{"label": "2. Process", "subtitle": "Details", "badge": "Step 2", "icon": "⚙️", "status": "normal"}},
             {{"label": "3. Output", "subtitle": "Details", "badge": "Step 3", "icon": "✅", "status": "normal"}}
           ],
           "highlight_label": "Key takeaway"
         }}
       - For "cycle_loop":
         "visual_data": {{
           "title": "State Machine Transitions",
           "stages": [
             {{"title": "1. Step A", "desc": "Detail A", "icon": "📤"}},
             {{"title": "2. Step B", "desc": "Detail B", "icon": "📥"}},
             {{"title": "3. Step C", "desc": "Detail C", "icon": "✅"}}
           ]
         }}
       - For "concept_network":
         "visual_data": {{
           "title": "Entity Relationship & Dependencies"
         }}
       - For "code_snippet":
         "visual_data": {{
           "code": "// Implementation code matching topic language"
         }}
       - For "text_bullets":
         "visual_data": {{
           "items": [
             "Core invariant 1",
             "Edge case safeguard 2",
             "Production engineering rule 3"
           ]
         }}

    5. JSON FORMAT:
       - Return a JSON object with a "scenes" array containing EXACTLY {scene_count} scene objects.
       - CRITICAL BRACE BALANCE: Close "visual_data" with a SINGLE '}}' before writing "text" and "transition". Do NOT double-close "visual_data" with '}}}}'.
       - Each scene must follow this exact structure:
         {{
           "scene_id": 1,
           "start_time": 0,
           "end_time": 15,
           "narration": "40 to 50 words of spoken educational narration...",
           "visual_type": "title_card",
           "visual_data": {{"title": "{lesson_title}", "subtitle": "Core architectural intuition"}},
           "text": "Lower-third caption banner",
           "transition": "fade"
         }}
    """

    parsed_json = None
    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": f"You are a specialized educational JSON video planner. You return strictly a JSON object with a 'scenes' array of {scene_count} comprehensive scenes about '{lesson_title}'. Do NOT wrap in markdown. In narration, use single quotes (') for any dialogue or quotes. Return raw JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=6000
        )

        raw_output = response.choices[0].message.content or ""
        parsed_json = extract_json_from_response(raw_output)
        print(f"[VISUAL PLANNER] Primary Groq constrained JSON decode succeeded for '{lesson_title}'!")

    except Exception as e:
        print(f"[VISUAL PLANNER] Groq constrained call notice: {e}")
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
            try:
                parsed_json = extract_json_from_response(failed_gen)
                if isinstance(parsed_json, dict) and "scenes" in parsed_json:
                    print(f"[VISUAL PLANNER] Auto-recovered {len(parsed_json['scenes'])} dynamic scenes from Groq failed_generation!")
            except Exception as rec_err:
                print(f"[VISUAL PLANNER] Recovery parse error: {rec_err}")

        # Self-Healing 2: Unconstrained Groq call if constrained decoding failed and could not be repaired
        if not parsed_json or not (isinstance(parsed_json, list) or (isinstance(parsed_json, dict) and "scenes" in parsed_json)):
            try:
                print(f"[VISUAL PLANNER] Retrying dynamic scene generation via unconstrained Groq decoding...")
                retry_resp = groq_client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": f"You are a specialized educational JSON video planner. Return ONLY a raw JSON object with a 'scenes' array of {scene_count} scenes about '{lesson_title}'. Never double-close visual_data braces."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=6000
                )
                raw_retry = retry_resp.choices[0].message.content or ""
                parsed_json = extract_json_from_response(raw_retry)
                if isinstance(parsed_json, dict) and "scenes" in parsed_json:
                    print(f"[VISUAL PLANNER] Unconstrained Groq decoding succeeded ({len(parsed_json['scenes'])} scenes)!")
            except Exception as retry_err:
                print(f"[VISUAL PLANNER] Unconstrained Groq retry notice: {retry_err}")

        if not parsed_json or not isinstance(parsed_json, (dict, list)):
            print(f"[VISUAL PLANNER] Auto-activating authoritative domain fallback for '{lesson_title}' ({domain}).")
            return get_domain_fallback(lesson_title, domain)

    try:
        if isinstance(parsed_json, dict) and "scenes" in parsed_json and isinstance(parsed_json["scenes"], list):
            raw_scenes = parsed_json["scenes"]
        elif isinstance(parsed_json, list):
            raw_scenes = parsed_json
        else:
            print(f"[VISUAL PLANNER] Unexpected JSON structure, activating domain fallback.")
            return get_domain_fallback(lesson_title, domain)

        sanitized_scenes = []
        for item in raw_scenes:
            if isinstance(item, dict) and "visual_type" in item:
                item["scene_id"] = len(sanitized_scenes) + 1
                if not item.get("narration"):
                    item["narration"] = f"Continuing our detailed walkthrough on {lesson_title}."
                if not item.get("text"):
                    item["text"] = f"Scene {item['scene_id']}"
                if not item.get("visual_data"):
                    item["visual_data"] = {}
                item["visual_type"] = sanitize_visual_type(item.get("visual_type"), item.get("visual_data", {}))
                sanitized_scenes.append(item)

        if len(sanitized_scenes) >= 6:
            # Universal Semantic Relevance & Multi-Directional Anti-Contamination Verification
            is_valid, validation_msg = verify_scene_plan_integrity(lesson_title, domain, sanitized_scenes)
            if not is_valid:
                print(f"[Visual Planner] Integrity Verification Failed for '{lesson_title}' ({domain}): {validation_msg}. Rejecting hallucinated plan and using domain fallback.")
                return get_domain_fallback(lesson_title, domain)

            if len(sanitized_scenes) < scene_count:
                fallback_scenes = get_domain_fallback(lesson_title, domain)
                for missing_id in range(len(sanitized_scenes) + 1, scene_count + 1):
                    fb = fallback_scenes[missing_id - 1].copy()
                    fb["scene_id"] = missing_id
                    sanitized_scenes.append(fb)
            return sanitized_scenes
        else:
            raise ValueError(f"Insufficient valid scenes returned: {len(sanitized_scenes)}")

    except Exception as e:
        print(f"[Visual Planner] Notice/Fallback for {lesson_title} (domain={domain}): {e}")
        return get_domain_fallback(lesson_title, domain)

def get_domain_fallback(lesson_title: str, domain: str) -> list[dict]:
    """
    Dedicated fallback 8-scene plans with 100% distinct architecture per domain.
    """
    # -------------------------------------------------------------
    # 1. MACHINE LEARNING: DECISION TREES & RANDOM FOREST
    # -------------------------------------------------------------
    if domain == "ml_trees":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this comprehensive machine learning masterclass on {lesson_title}. Decision trees offer intuitive rule-based splits, but by combining hundreds of de-correlated trees into an ensemble, we transform brittle high-variance classifiers into robust predictive powerhouses.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Decision Trees, Gini Impurity & Random Forest Ensembles"},
                "text": "Core Ensemble Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Building a decision tree follows three iterative phases: searching every feature cutoff to maximize partition purity, calculating impurity drop using the Gini Index or Information Gain, and applying stopping thresholds or pruning to prevent memorizing data noise.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Cutoff Search", "desc": "Evaluate all candidate feature split thresholds"},
                        {"title": "2. Purity Optimization", "desc": "Maximize Gini purity drop: 1 - sum(p_i^2)"},
                        {"title": "3. Pruning Guard", "desc": "Halt tree expansion or prune subtrees to curb overfitting"}
                    ]
                },
                "text": "3-Stage Tree Splitting Logic",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Examining the tree architecture illustrates recursive partitioning in action. Notice how the parent node evaluates an optimal decision threshold, routing samples into two homogeneous daughter nodes that maximize classification certainty.",
                "visual_type": "tree_structure",
                "visual_data": {
                    "title": f"{lesson_title} Decision Hierarchy",
                    "root_label": "Feature Split: Age < 60",
                    "left_label": "Left: Age < 60",
                    "right_label": "Right: Age >= 60",
                    "left_leaf_1": "Class A (Purity 83%)",
                    "left_leaf_2": "Class B (17%)",
                    "right_leaf_1": "Class A (21%)",
                    "right_leaf_2": "Class B (Purity 79%)",
                    "status": "Gini Impurity Drop = 0.319 (Purer than Parent 0.48)"
                },
                "text": "Recursive Node Partitioning Substrate",
                "transition": "fade"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation using Scikit-Learn. Notice how we specify n estimators to build a forest of diverse trees, while controlling maximum depth and minimum samples per leaf to preserve generalization.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "from sklearn.ensemble import RandomForestClassifier\nfrom sklearn.model_selection import train_test_split\n\n# 1. Instantiate Random Forest with 100 de-correlated trees\nrf = RandomForestClassifier(\n    n_estimators=100,\n    max_features='sqrt',      # Random predictor subsampling\n    oob_score=True,           # Out-of-bag validation\n    random_state=42\n)\n\n# 2. Fit ensemble on bootstrapped samples\nrf.fit(X_train, y_train)\nprint(f'OOB Generalization Score: {rf.oob_score_:.4f}')"
                },
                "text": "Scikit-Learn Random Forest Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing the ensemble lifecycle highlights the dual mechanisms of bagging: bootstrapping creates perturbed training sets with replacement, each tree votes independently on test inputs, and majority voting collapses predictions into a stable consensus.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Random Forest Voting Pipeline",
                    "stages": [
                        {"label": "1. Bootstrap", "subtitle": "Sample N with replacement", "badge": "Data", "icon": "🎲", "status": "normal"},
                        {"label": "2. Subsample", "subtitle": "Random subset of features", "badge": "Split", "icon": "✂️", "status": "normal"},
                        {"label": "3. Grow Forest", "subtitle": "Train 500-1000 trees", "badge": "Model", "icon": "🌲", "status": "normal"},
                        {"label": "4. Consensus", "subtitle": "Majority vote aggregation", "badge": "Output", "icon": "🗳️", "status": "normal"}
                    ],
                    "highlight_label": "Averaging across de-correlated trees smooths out individual variance without increasing bias."
                },
                "text": "Bootstrap Aggregation & Voting Trace",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing a solitary decision tree against a Random Forest exposes fundamental bias-variance trade-offs: while a single deep tree overfits to spurious noise and suffers high variance, an ensemble smooths predictions just as repeated measurements stabilize a clinical reading.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Single Decision Tree (High Variance)",
                    "left_desc": "Grows overly complex branches fitting sample noise; highly sensitive to training data perturbations; prone to severe overfitting.",
                    "right_title": "Random Forest Ensemble (Low Variance)",
                    "right_desc": "Averages hundreds of de-correlated trees; reduces variance by the square root of tree count; yields stable, generalized decision boundaries."
                },
                "text": "Single Tree Overfitting vs Ensemble Stability",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "From a metric perspective, Random Forest achieves superior test accuracy and out-of-bag validation at the expense of interpretability and inference latency, making it the premier choice for tabular predictive tasks.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Classifier Architecture Trade-Offs",
                    "leftHeader": "Decision Tree",
                    "rightHeader": "Random Forest Ensemble",
                    "rows": [
                        {"feature": "Variance Profile", "left": "High (Sample sensitive)", "right": "Low (Averaged stability)"},
                        {"feature": "Overfitting Risk", "left": "Severe without pruning", "right": "Naturally bounded"},
                        {"feature": "Interpretability", "left": "Direct rule inspection", "right": "Feature importance scores"},
                        {"feature": "Inference Speed", "left": "O(depth) single tree seek", "right": "O(N * depth) parallel vote"}
                    ]
                },
                "text": "Model Performance & Bias-Variance Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To master ensemble models in production, always validate against out-of-bag error, tune max features to decorrelate individual trees, and extract feature importances to verify the model captures genuine physical relationships rather than spurious noise.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Feature Subsampling Invariant: Evaluate sqrt(p) random features at each split to strictly de-correlate trees",
                        "Out-of-Bag (OOB) Validation: Leverage the ~36.8% unselected bootstrap samples for free cross-validation",
                        "Generalization Rule: Increasing tree count (n_estimators) never causes overfitting, only marginal compute cost"
                    ]
                },
                "text": "Senior ML Engineering Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 2. MACHINE LEARNING: REGRESSION & OPTIMIZATION THEORY
    # -------------------------------------------------------------
    elif domain == "ml_regression":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this advanced statistical learning masterclass on {lesson_title}. Whether predicting quantitative continuous targets through Ordinary Least Squares or estimating qualitative event probabilities via logistic Sigmoids, understanding mathematical risk minimization is central to machine learning.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Linear & Logistic Regression, Normal Equations & Risk Minimization"},
                "text": "Statistical Learning Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Statistical estimation executes across three rigorous mathematical steps: defining our parametric hypothesis space, formulating an explicit convex loss function such as Residual Sum of Squares, and deriving optimal coefficients via normal equations or gradient descent.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Hypothesis Modeling", "desc": "Formulate Y = X * beta + epsilon or p(X) = 1 / (1 + e^-z)"},
                        {"title": "2. Loss Formulation", "desc": "Define Residual Sum of Squares (RSS) or Maximum Likelihood log-loss"},
                        {"title": "3. Optimization", "desc": "Solve beta = (X^T * X)^-1 * X^T * Y via analytical normal equations"}
                    ]
                },
                "text": "3-Stage Optimization Lifecycle",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Examining the fitted regression substrate reveals how Ordinary Least Squares minimizes the sum of squared vertical residuals. Notice how the linear model balances intercept and slope parameters to capture underlying data variance.",
                "visual_type": "graph_chart",
                "visual_data": {
                    "title": f"{lesson_title} Residual Fit Curve",
                    "description": "Ordinary Least Squares minimizes sum of squared residuals: RSS = sum(y_i - y_hat_i)^2"
                },
                "text": "Ordinary Least Squares Substrate",
                "transition": "fade"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation using Scikit-Learn. Notice line five: we compute the coefficient of determination, R squared, to measure the exact proportion of target variability explained by our input predictors.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "from sklearn.linear_model import LinearRegression\nfrom sklearn.metrics import r2_score, mean_squared_error\n\n# 1. Fit Ordinary Least Squares model\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\n\n# 2. Analytical Normal Equation: beta = inv(X.T @ X) @ X.T @ y\ny_pred = model.predict(X_test)\nr2 = r2_score(y_test, y_pred)\nmse = mean_squared_error(y_test, y_pred)\nprint(f'R^2 Score: {r2:.3f} | Test MSE: {mse:.3f}')"
                },
                "text": "Scikit-Learn Regression Implementation",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "In logistic classification, parameters cannot be solved analytically. Instead, the algorithm iterates through Maximum Likelihood Estimation: computing predicted probabilities through the Sigmoid link, evaluating gradient loss, and updating weights until convergence.",
                "visual_type": "cycle_loop",
                "visual_data": {
                    "title": "Iterative Optimization & Gradient Loop",
                    "stages": [
                        {"title": "1. Forward Prob", "desc": "Pass z through Sigmoid sigma(z)", "icon": "📐"},
                        {"title": "2. Compute Loss", "desc": "Evaluate cross-entropy residual error", "icon": "📊"},
                        {"title": "3. Gradient Step", "desc": "Calculate gradient vector w.r.t weights", "icon": "⚡"},
                        {"title": "4. Weight Update", "desc": "Adjust beta along negative gradient", "icon": "✅"}
                    ]
                },
                "text": "Maximum Likelihood Optimization Cycle",
                "transition": "fade"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing high bias against high variance reveals the fundamental dilemma of machine learning: an overly simplistic linear fit underfits the true function, while an unregularized high-degree polynomial overfits to sample noise, leading to catastrophic test error.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "High Bias (Underfitting)",
                    "left_desc": "Excessively rigid assumptions; cannot capture non-linear patterns; exhibits high error on both training and test data.",
                    "right_title": "High Variance (Overfitting)",
                    "right_desc": "Excessive model flexibility; memorizes sample idiosyncrasies; achieves near-zero training loss but explodes in test error."
                },
                "text": "Underfitting (Bias) vs Overfitting (Variance)",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "In formal evaluation, regression performance is quantified by R squared and Residual Standard Error, while classification performance is mapped across a Confusion Matrix balancing Precision, Recall, and the Area Under the ROC Curve.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Model Evaluation Metrics Matrix",
                    "leftHeader": "Continuous Regression",
                    "rightHeader": "Binary Classification",
                    "rows": [
                        {"feature": "Primary Metric", "left": "R^2 (Explained Variance)", "right": "ROC-AUC / F1-Score"},
                        {"feature": "Loss Function", "left": "Mean Squared Error (MSE)", "right": "Binary Cross-Entropy (Log-Loss)"},
                        {"feature": "Residual Measure", "left": "Residual Standard Error (RSE)", "right": "Confusion Matrix (TP, FP, FN, TN)"},
                        {"feature": "Optimization", "left": "Closed-Form Normal Equations", "right": "Iterative Gradient Ascent (MLE)"}
                    ]
                },
                "text": "Statistical Evaluation Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To master regression in production, always inspect residual plots for non-linearity or heteroscedasticity, apply L2 Ridge or L1 Lasso regularization to penalize large coefficients, and preserve a strictly held-out test set for unbiased validation.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Residual Diagnostic Invariant: Funnel shapes in residuals signal non-constant variance (heteroscedasticity)",
                        "Collinearity Guard: Highly correlated inputs inflate coefficient variance; verify Variance Inflation Factors (VIF)",
                        "Data Hygiene Rule: Never touch the test set during hyperparameter tuning; rely strictly on K-Fold Cross-Validation"
                    ]
                },
                "text": "Senior ML Engineering Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 3. DATABASE MANAGEMENT SYSTEMS: NORMALIZATION
    # -------------------------------------------------------------
    elif domain == "dbms_normalization":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this advanced relational database masterclass on {lesson_title}. Designing robust database schemas requires decomposing unnormalized tables to systematically eliminate data redundancy, avoid update anomalies, and guarantee referential integrity.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Relational Design, Normal Forms (1NF, 2NF, 3NF, BCNF) & Anomaly Elimination"},
                "text": "Relational Design Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Relational normalization progresses through four rigorous stages: First Normal Form enforces atomic values; Second Normal Form eliminates partial key dependencies; Third Normal Form removes transitive dependencies; and Boyce-Codd Normal Form ensures all determinants are superkeys.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. First Normal Form (1NF)", "desc": "Atomic column values; unique records without repeating groups"},
                        {"title": "2. Second Normal Form (2NF)", "desc": "Eliminate partial functional dependencies on composite keys"},
                        {"title": "3. Third Normal Form (3NF)", "desc": "Eliminate transitive dependencies: Non-key attributes depend only on Primary Key"},
                        {"title": "4. Boyce-Codd (BCNF)", "desc": "Every determinant X in functional dependency X -> Y must be a Superkey"}
                    ]
                },
                "text": "The 4 Stages of Relational Normalization",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Examining bad relational design exposes three catastrophic anomalies: updating redundant rows causes partial inconsistencies; inserting new entities is blocked without complete composite keys; and deleting a row inadvertently deletes unrelated essential entities.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Unnormalized Schema (Anomalies)",
                    "left_desc": "Redundant data stored across multiple rows; updating address in one row leaves others inconsistent; deleting an employee destroys department records.",
                    "right_title": "Normalized Schema (Clean Relations)",
                    "right_desc": "Decomposed into focused tables linked by foreign keys; single point of truth per entity; zero insertion, update, or deletion side effects."
                },
                "text": "Unnormalized Anomalies vs Normalized Integrity",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production SQL implementation demonstrating 3NF decomposition. Notice how the employee entity is decoupled from geographical locations, referencing ZIP through an explicit foreign key to guarantee integrity.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "-- 3NF Normalized Schema Decomposition\nCREATE TABLE Locations (\n    zip_code VARCHAR(10) PRIMARY KEY,\n    city VARCHAR(50) NOT NULL,\n    state VARCHAR(50) NOT NULL\n);\n\nCREATE TABLE Employees (\n    emp_id INT PRIMARY KEY,\n    emp_name VARCHAR(100) NOT NULL,\n    dept_id INT NOT NULL,\n    zip_code VARCHAR(10) REFERENCES Locations(zip_code)\n);"
                },
                "text": "Production SQL Normalized DDL",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing the decomposition pipeline illustrates how functional dependencies govern table splits: we isolate candidate keys, identify partial and transitive determinants, and partition tables while guaranteeing lossless joins and dependency preservation.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Schema Decomposition Pipeline",
                    "stages": [
                        {"label": "1. Identify Keys", "subtitle": "Compute candidate superkeys", "badge": "Keys", "icon": "🔑", "status": "normal"},
                        {"label": "2. Detect Violations", "subtitle": "Find X -> Y where X not key", "badge": "Audit", "icon": "⚠️", "status": "normal"},
                        {"label": "3. Decompose", "subtitle": "Split into R1(X, Y) and R2(R - Y)", "badge": "Split", "icon": "✂️", "status": "normal"},
                        {"label": "4. Verify Join", "subtitle": "Confirm lossless join property", "badge": "Check", "icon": "✅", "status": "normal"}
                    ],
                    "highlight_label": "Every attribute must depend on the key, the whole key, and nothing but the key."
                },
                "text": "Lossless Decomposition Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Visualizing functional dependencies demonstrates the root cause of transitive anomalies: employee ID determines ZIP code, which in turn determines City. By separating these into distinct relations, we break the transitive chain.",
                "visual_type": "concept_network",
                "visual_data": {
                    "title": "Functional Dependency & Key Mappings"
                },
                "text": "Functional Dependency Graph",
                "transition": "fade"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Comparing the normal forms illustrates the architectural progression: while 1NF provides basic structure, 3NF and BCNF achieve complete anomaly elimination, balancing storage efficiency against query join overhead.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Normal Form Architectural Profile",
                    "leftHeader": "Lower Forms (1NF & 2NF)",
                    "rightHeader": "Higher Forms (3NF & BCNF)",
                    "rows": [
                        {"feature": "Redundancy Level", "left": "Moderate to High", "right": "Near Zero (Minimal)"},
                        {"feature": "Update Anomalies", "left": "Still possible in non-keys", "right": "Completely eliminated"},
                        {"feature": "Dependency Rule", "left": "No partial dependencies", "right": "Every determinant is a superkey"},
                        {"feature": "Join Overhead", "left": "Few joins required", "right": "Requires multi-table JOINs"}
                    ]
                },
                "text": "Normal Form Anomaly Elimination Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To master schema design in production, ensure decompositions are strictly lossless, maintain foreign key indexes to prevent join bottlenecks, and consider intentional denormalization only for read-heavy analytical data warehouses.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Lossless Join Invariant: R1 intersect R2 must form a candidate key of at least one decomposed relation",
                        "Index Foreign Keys: Always place B-Tree indexes on foreign key columns to avoid expensive table scans on JOINs",
                        "OLTP vs OLAP Rule: Maintain strict 3NF/BCNF for transactional writes; denormalize into star schemas for analytics"
                    ]
                },
                "text": "Senior Database Engineering Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 4. DATABASE MANAGEMENT SYSTEMS: ACID TRANSACTIONS
    # -------------------------------------------------------------
    elif domain == "dbms_transactions":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this comprehensive database systems masterclass on {lesson_title}. In high-concurrency environments, maintaining data integrity requires absolute adherence to the ACID guarantees: Atomicity, Consistency, Isolation, and Durability.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "ACID Guarantees, Concurrency Control & Write-Ahead Logging"},
                "text": "Transaction & Concurrency Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "The four pillars of ACID govern every modification: Atomicity enforces all-or-nothing completion; Consistency enforces domain invariants; Isolation guarantees serializable concurrency; and Durability ensures committed updates survive server power loss.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Atomicity", "desc": "All operations commit successfully or the transaction completely rolls back"},
                        {"title": "2. Consistency", "desc": "Database transitions strictly between valid states preserving schema constraints"},
                        {"title": "3. Isolation", "desc": "Concurrent transactions execute as if they occurred serially without interference"},
                        {"title": "4. Durability", "desc": "Committed modifications are written to non-volatile disk via Write-Ahead Logs"}
                    ]
                },
                "text": "The 4 Pillars of ACID Transactions",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Under the hood, database indexing relies on balanced B-Tree hierarchies. Notice how internal nodes store search keys that guide logarithmic traversals down to leaf record pages, minimizing expensive disk input-output operations.",
                "visual_type": "tree_structure",
                "visual_data": {
                    "title": "B-Tree Multi-Level Storage Index",
                    "root_label": "Root Page: Key 50",
                    "left_label": "Internal Page: Keys 20, 35",
                    "right_label": "Internal Page: Keys 65, 80",
                    "left_leaf_1": "Leaf: Records [10..20]",
                    "left_leaf_2": "Leaf: Records [21..35]",
                    "right_leaf_1": "Leaf: Records [51..65]",
                    "right_leaf_2": "Leaf: Records [66..80]",
                    "status": "Logarithmic O(log N) Multi-Level Page Seek"
                },
                "text": "B-Tree Multi-Level Index Hierarchy",
                "transition": "fade"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of an ACID transaction. Notice how we wrap multiple balance operations in an atomic block, ensuring that an unexpected failure triggers an immediate rollback to prevent lost funds.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "BEGIN TRANSACTION;\nSET TRANSACTION ISOLATION LEVEL SERIALIZABLE;\n\n-- Deduct from Source Account\nUPDATE Accounts SET balance = balance - 500 WHERE id = 101;\n\n-- Credit to Target Account\nUPDATE Accounts SET balance = balance + 500 WHERE id = 202;\n\n-- Explicit integrity check before permanent persistence\nCOMMIT;"
                },
                "text": "Production SQL Transaction Block",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Durability is achieved through Write-Ahead Logging: before modifying pages in the in-memory buffer pool, log records are flushed sequentially to non-volatile disk, enabling full crash recovery during sudden hardware outages.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Durability & Write-Ahead Log (WAL) Pipeline",
                    "stages": [
                        {"label": "1. Client SQL", "subtitle": "Execute DML modification", "badge": "Query", "icon": "📥", "status": "completed"},
                        {"label": "2. WAL Append", "subtitle": "Flush log record to disk", "badge": "WAL", "icon": "📝", "status": "active"},
                        {"label": "3. Buffer Pool", "subtitle": "Dirty page in memory", "badge": "RAM", "icon": "⚡", "status": "normal"},
                        {"label": "4. Checkpoint", "subtitle": "Sync dirty pages to tables", "badge": "Disk", "icon": "💾", "status": "highlight"}
                    ],
                    "highlight_label": "WAL protocol guarantees committed transactions survive system crashes without data loss."
                },
                "text": "Write-Ahead Logging (WAL) Trace",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing pessimistic locking against optimistic concurrency control reveals essential architectural trade-offs: pessimistic locks prevent conflicts up front by queuing transactions, while optimistic concurrency executes without locks, validating and retrying at commit.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Pessimistic Locking (Strict)",
                    "left_desc": "Acquires shared and exclusive locks up front; guarantees zero conflict aborts; risks thread contention, lock waiting, and deadlocks.",
                    "right_title": "Optimistic Concurrency Control",
                    "right_desc": "Executes without locks, checking record version numbers at commit time; excels in low-contention reads; aborts and retries on collision."
                },
                "text": "Pessimistic Locking vs Optimistic Concurrency",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "SQL isolation levels establish the continuum between speed and consistency: Read Committed prevents dirty reads, Repeatable Read eliminates non-repeatable reads, while Serializable eliminates phantom reads at the cost of concurrency.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Transaction Isolation Levels Matrix",
                    "leftHeader": "Lower Isolation (Read Committed)",
                    "rightHeader": "Strict Isolation (Serializable)",
                    "rows": [
                        {"feature": "Dirty Reads", "left": "Prevented", "right": "Prevented"},
                        {"feature": "Non-Repeatable Reads", "left": "Possible", "right": "Prevented"},
                        {"feature": "Phantom Reads", "left": "Possible", "right": "Completely Prevented"},
                        {"feature": "Throughput Scaling", "left": "High Concurrency", "right": "Constrained by Serial Locks"}
                    ]
                },
                "text": "Transaction Isolation Level Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To maintain transactional integrity at scale, always access tables in uniform global order to prevent deadlocks, keep transaction durations minimal to avoid holding lock buffers, and configure automated WAL checkpointing.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Deadlock Prevention: Always acquire row locks in deterministic primary key order to eliminate circular waits",
                        "Short Transaction Rule: Never perform external network calls or user waits inside an open transaction block",
                        "Durability Invariant: Ensure synchronous commit flush settings are active for high-value financial accounts"
                    ]
                },
                "text": "Senior Database Engineering Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 4.9 DATA STRUCTURES & ALGORITHMS: ARRAYS & CONTIGUOUS MEMORY
    # -------------------------------------------------------------
    elif domain == "dsa_arrays":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this fundamental systems and algorithms masterclass on {lesson_title}. In computer memory, arrays are the bedrock of efficient computation, organizing elements in contiguous memory to enable instantaneous constant-time random access.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Contiguous Memory, Pointer Invariants & Constant Time O(1) Indexing"},
                "text": "Contiguous Memory Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "In physical RAM, an array is allocated as an unbroken contiguous ribbon of memory cells. Each element occupies a fixed number of bytes, allowing instant translation from an index to a physical memory address using base plus offset arithmetic.",
                "visual_type": "array_memory",
                "visual_data": {
                    "title": f"{lesson_title} Contiguous Memory Layout",
                    "items": [
                        {"index": 0, "value": 10, "address": "0x1000", "status": "active"},
                        {"index": 1, "value": 20, "address": "0x1004", "status": "normal"},
                        {"index": 2, "value": 30, "address": "0x1008", "status": "normal"},
                        {"index": 3, "value": 40, "address": "0x100C", "status": "target"},
                        {"index": 4, "value": 50, "address": "0x1010", "status": "normal"},
                        {"index": 5, "value": 60, "address": "0x1014", "status": "normal"}
                    ],
                    "pointers": [
                        {"label": "Base", "index": 0, "color": "#38bdf8"},
                        {"label": "arr[3]", "index": 3, "color": "#10b981"}
                    ]
                },
                "text": "Contiguous RAM Allocation & Index Pointers",
                "transition": "fade"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Constant-time O of one random access is powered by three mathematical steps: first, acquiring the starting base address in memory; second, computing the exact byte offset by multiplying the index by element size; and third, performing a direct memory dereference.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Base Pointer", "desc": "Acquire starting address in RAM: base_addr = &arr[0]"},
                        {"title": "2. Offset Arithmetic", "desc": "Compute byte offset: target_addr = base_addr + i * sizeof(T)"},
                        {"title": "3. Direct O(1) Access", "desc": "Dereference physical memory slot instantly without traversing"}
                    ]
                },
                "text": "3-Stage Direct Addressing Mechanics",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is how arrays operate at the hardware level in C. When we allocate dynamic memory with malloc, the pointer points to the base cell. Indexing brackets are pure syntactic sugar for pointer arithmetic.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "#include <stdio.h>\n#include <stdlib.h>\n\nint main() {\n    // Allocate contiguous block for 5 integers\n    int *arr = (int *)malloc(5 * sizeof(int));\n    \n    for (int i = 0; i < 5; i++) {\n        arr[i] = (i + 1) * 10;\n    }\n    \n    // Direct O(1) addressing: *(arr + 3)\n    int val = arr[3]; // Exactly 40\n    printf(\"arr[3] = %d\\n\", val);\n    \n    free(arr);\n    return 0;\n}"
                },
                "text": "Contiguous Allocation & Pointer Arithmetic",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "When a dynamic array or vector exceeds its capacity, geometric doubling preserves amortized constant time: checking full capacity, allocating a new block of double size on the heap, copying elements, and freeing old memory.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Dynamic Array Geometric Resizing",
                    "stages": [
                        {"label": "1. Capacity Check", "subtitle": "size == capacity reached", "badge": "Guard", "icon": "⚠️", "status": "completed"},
                        {"label": "2. Double Allocation", "subtitle": "Allocate new buffer (2x N)", "badge": "Heap", "icon": "📦", "status": "active"},
                        {"label": "3. Element Migration", "subtitle": "Copy N elements to new RAM", "badge": "Transfer", "icon": "🔄", "status": "normal"},
                        {"label": "4. Amortized O(1)", "subtitle": "Free old buffer & update ptr", "badge": "Ready", "icon": "✅", "status": "highlight"}
                    ],
                    "highlight_label": "Geometric 2x doubling guarantees O(1) amortized insertion over infinite appends."
                },
                "text": "Geometric Doubling & Capacity Growth",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing arrays to linked lists reveals fundamental architectural trade-offs: arrays excel at instantaneous indexed lookups and hardware cache locality, whereas linked lists allow O of one insertions anywhere once a node pointer is held.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Contiguous Array",
                    "left_desc": "O(1) random access via index arithmetic. Consecutive elements reside in the same CPU cache line, maximizing hardware throughput.",
                    "right_title": "Linked List",
                    "right_desc": "O(N) sequential traversal to access index i. Scattered heap nodes cause CPU cache misses, but insertion requires no element shifting."
                },
                "text": "Contiguous Array vs Linked List",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Analyzing the time complexity matrix shows random access is always O of one. Appending at the end is amortized O of one, while insertion or deletion at the beginning requires shifting elements in O of N linear time.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Array Operations Complexity Matrix",
                    "leftHeader": "Static Array",
                    "rightHeader": "Dynamic Vector",
                    "rows": [
                        {"feature": "Indexed Access", "left": "O(1)", "right": "O(1)"},
                        {"feature": "Append at End", "left": "N/A (Fixed)", "right": "O(1) Amortized"},
                        {"feature": "Insert at Head / Middle", "left": "O(N) Shift", "right": "O(N) Shift"},
                        {"feature": "Space Overhead", "left": "O(N) Exact", "right": "O(N) 2x Capacity"}
                    ]
                },
                "text": "Asymptotic Complexity Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To master array engineering in production: leverage CPU cache lines for high-speed linear traversals, enforce strict bounds checks to avoid buffer overflow vulnerabilities, and use two-pointer or sliding window techniques for optimal space complexity.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "CPU Cache Line Locality: Contiguous layouts trigger hardware prefetching for 10x-100x faster iterations",
                        "Boundary Invariants: Always enforce 0 <= index < size to prevent catastrophic memory corruption or CVEs",
                        "Two-Pointer & Sliding Window: Solve sub-array search and partition problems in O(N) time with O(1) space"
                    ]
                },
                "text": "Senior Algorithmic Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 4.95 DATA STRUCTURES & ALGORITHMS: LINKED LISTS
    # -------------------------------------------------------------
    elif domain == "dsa_linked_lists":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this comprehensive data structures masterclass on {lesson_title}. Unlike contiguous arrays, linked lists allocate memory dynamically on the heap, linking disparate nodes via pointer addresses to achieve instantaneous constant-time insertions.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Dynamic Heap Nodes, Pointer Wiring & Constant-Time O(1) Splicing"},
                "text": "Linked List Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "In physical memory, a linked list consists of self-contained node records. Each node houses its payload data and a pointer reference directing the program to the next node in the heap, terminating at NULL.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Disjoint Node & Pointer Sequence",
                    "stages": [
                        {"label": "Head Pointer", "subtitle": "Entry Reference", "badge": "Ptr", "icon": "🎯", "status": "completed"},
                        {"label": "Node [10 | *]", "subtitle": "Addr: 0x2A40", "badge": "Data", "icon": "📦", "status": "active"},
                        {"label": "Node [20 | *]", "subtitle": "Addr: 0x5F10", "badge": "Data", "icon": "📦", "status": "normal"},
                        {"label": "Node [30 | NULL]", "subtitle": "Tail Node", "badge": "End", "icon": "🛑", "status": "highlight"}
                    ],
                    "highlight_label": "Nodes reside anywhere across heap memory, connected exclusively through pointers."
                },
                "text": "Dynamic Node Allocation & Pointer Chains",
                "transition": "fade"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Inserting an element at the head of a linked list is a guaranteed O of one operation executing in three steps: allocating the new node, pointing its next pointer to the current head, and swinging the head pointer to the new node.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Heap Allocation", "desc": "Instantiate new Node(val) with payload and null link"},
                        {"title": "2. Wire Next Pointer", "desc": "Set new_node.next = head to preserve remaining list"},
                        {"title": "3. Reassign Head", "desc": "Set head = new_node in instant O(1) pointer assignment"}
                    ]
                },
                "text": "3-Stage O(1) Head Insertion Invariant",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation. Notice how Python slots eliminate dictionary overhead, and the prepend method accepts the new value, instantiating the node and redirecting head in a single clean expression.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "class Node:\n    __slots__ = ('data', 'next')\n    def __init__(self, data, next_node=None):\n        self.data = data\n        self.next = next_node\n\nclass SinglyLinkedList:\n    def __init__(self):\n        self.head = None\n\n    def insert_head(self, data):\n        # Instant O(1) prepend\n        self.head = Node(data, self.head)\n\n    def delete(self, key):\n        prev, curr = None, self.head\n        while curr and curr.data != key:\n            prev, curr = curr, curr.next\n        if curr:\n            if prev is None:\n                self.head = curr.next\n            else:\n                prev.next = curr.next"
                },
                "text": "Clean Python Linked List Implementation",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Deleting a node requires navigating with trailing pointers: prev trails curr until the target matches. Rewiring prev next to curr next cleanly bypasses the node, allowing garbage collection without moving other elements.",
                "visual_type": "cycle_loop",
                "visual_data": {
                    "title": "Two-Pointer Traversal & Deletion Cycle",
                    "stages": [
                        {"title": "Inspect Node", "desc": "Check curr.data == target", "icon": "🔍"},
                        {"title": "Advance Pointers", "desc": "prev = curr, curr = curr.next", "icon": "➡️"},
                        {"title": "Rewire Pointer", "desc": "prev.next = curr.next bypass", "icon": "✂️"},
                        {"title": "Free Memory", "desc": "Node unlinked & collected", "icon": "🗑️"}
                    ]
                },
                "text": "Two-Pointer Deletion & Node Reclaim",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Contrasting linked lists with arrays highlights the trade-off between insertion speed and memory locality: linked lists excel at prepend and splice operations, whereas arrays dominate random indexing and CPU cache prefetching.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Singly Linked List",
                    "left_desc": "O(1) head insertion and deletion without shifting. Memory grows incrementally on the heap, but traversal is strictly sequential O(N).",
                    "right_title": "Contiguous Array",
                    "right_desc": "O(1) direct index arithmetic and superior CPU cache locality, but inserting at the head requires shifting all N elements in O(N) time."
                },
                "text": "Linked List vs Contiguous Array",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "In the architectural comparison matrix, notice that linked lists achieve O of one insertion at the head, but arbitrary middle insertion requires O of N traversal. Arrays win decisively on random access and memory efficiency.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Linked List vs Dynamic Array Matrix",
                    "leftHeader": "Linked List",
                    "rightHeader": "Dynamic Array",
                    "rows": [
                        {"feature": "Insert at Head", "left": "O(1) Direct Splice", "right": "O(N) Element Shift", "winner": "left"},
                        {"feature": "Random Access", "left": "O(N) Sequential", "right": "O(1) Direct Offset", "winner": "right"},
                        {"feature": "Insert in Middle", "left": "O(N) Traversal to Node", "right": "O(N) Shift", "winner": "tie"},
                        {"feature": "CPU Cache Locality", "left": "Poor (Heap Chasing)", "right": "Optimal (Cache Lines)", "winner": "right"},
                        {"feature": "Memory Overhead", "left": "High (+8B to 16B Ptrs)", "right": "Minimal (Raw Elements)", "winner": "right"}
                    ]
                },
                "text": "Architectural Trade-Off Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To write senior-grade linked list code: use dummy sentinel nodes to eliminate special cases for the head, deploy Floyd's cycle detection algorithm with fast and slow pointers, and always free unlinked nodes in manual memory environments.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Dummy Sentinel Head: Eliminates separate conditional branches for inserting or deleting the head node",
                        "Floyd Cycle Invariant: Advance slow by 1 and fast by 2 to detect cycles in O(N) time with O(1) space",
                        "Pointer Reversal Guard: Always preserve curr.next in a temp variable before reassigning pointers"
                    ]
                },
                "text": "Senior Algorithmic Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 5. DATA STRUCTURES & ALGORITHMS: BINARY SEARCH
    # -------------------------------------------------------------
    elif domain == "dsa_binary_search":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this fundamental algorithmic masterclass on {lesson_title}. Searching and ordering data is central to computer science, and understanding how logarithmic divide-and-conquer strategies operate unlocks instantaneous lookups across millions of records.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Divide-and-Conquer, Pointer Invariants & Logarithmic O(log N) Efficiency"},
                "text": "Logarithmic Search Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Visualizing binary search directly in memory reveals contiguous cells with strict address offsets. Notice how our Low and High pointers bound the active search window, while the Mid pointer evaluates the candidate, immediately greying out eliminated partitions.",
                "visual_type": "array_memory",
                "visual_data": {
                    "title": f"{lesson_title} In-Memory Ribbon",
                    "items": [
                        {"index": 0, "value": 12, "address": "0x1000", "status": "eliminated"},
                        {"index": 1, "value": 15, "address": "0x1004", "status": "eliminated"},
                        {"index": 2, "value": 19, "address": "0x1008", "status": "active"},
                        {"index": 3, "value": 24, "address": "0x100C", "status": "active"},
                        {"index": 4, "value": 31, "address": "0x1010", "status": "target"},
                        {"index": 5, "value": 53, "address": "0x1014", "status": "normal"},
                        {"index": 6, "value": 59, "address": "0x1018", "status": "normal"},
                        {"index": 7, "value": 60, "address": "0x101C", "status": "normal"}
                    ],
                    "pointers": [
                        {"label": "Low", "index": 2, "color": "#38bdf8"},
                        {"label": "Mid", "index": 4, "color": "#f59e0b"},
                        {"label": "High", "index": 7, "color": "#ec4899"}
                    ]
                },
                "text": "Contiguous Memory & Pointer Dynamics",
                "transition": "fade"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "The mechanics of binary search rely on three non-negotiable stages: first, establishing boundary pointers across the sorted array; second, inspecting the midpoint element; and third, deterministically eliminating an entire half of candidate values in every iteration.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Initialize Bounds", "desc": "Establish Low = 0 and High = N - 1 across sorted array"},
                        {"title": "2. Midpoint Probe", "desc": "Inspect element at mid = low + (high - low) // 2"},
                        {"title": "3. Search Space Halving", "desc": "Discard the half that cannot contain target, repeating until found"}
                    ]
                },
                "text": "3-Stage Algorithmic Strategy",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the idiomatic implementation. Notice line four: to prevent catastrophic integer overflow in lower-level languages, we compute mid as beginning plus end minus beginning divided by two, guaranteeing numerical safety on massive arrays.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "def binary_search(arr, target):\n    beg, end = 0, len(arr) - 1\n    result = -1\n    while beg <= end:\n        # Safe midpoint computation preventing integer overflow\n        mid = beg + (end - beg) // 2\n        if arr[mid] == target:\n            return mid  # Target found\n        elif arr[mid] < target:\n            beg = mid + 1  # Discard left half\n        else:\n            end = mid - 1  # Discard right half\n    return -1  # Target absent"
                },
                "text": "Python Implementation with Overflow Guard",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing a live execution walkthrough demonstrates how rapidly search space collapses: sixteen candidates halve to eight, then four, two, and one, locating any item in at most logarithmic time.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Search Space Halving Lifecycle",
                    "stages": [
                        {"label": "1. N Items", "subtitle": "Full array range [0..N-1]", "badge": "Input", "icon": "📍", "status": "completed"},
                        {"label": "2. N/2 Items", "subtitle": "First partition discard", "badge": "Halve", "icon": "✂️", "status": "active"},
                        {"label": "3. N/4 Items", "subtitle": "Second partition discard", "badge": "Zoom", "icon": "🔍", "status": "normal"},
                        {"label": "4. Target Found", "subtitle": "Converged in log2(N) steps", "badge": "Done", "icon": "🎯", "status": "highlight"}
                    ],
                    "highlight_label": "Every comparison cuts remaining candidates by exactly fifty percent."
                },
                "text": "Logarithmic Search Space Halving",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Contrasting naive linear search against binary search demonstrates an immense computational leap: while linear search checks every item in O of N time, binary search evaluates a billion items in roughly thirty CPU operations.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Linear Brute Force O(N)",
                    "left_desc": "Scans every element sequentially; execution time grows proportionally with data size, degrading drastically at scale.",
                    "right_title": "Logarithmic Binary Search O(log N)",
                    "right_desc": "Repeatedly partitions the search range in half; searches millions of records in only a few dozen CPU cycles."
                },
                "text": "Linear Scan vs Logarithmic Division",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "In formal complexity terms, the best case is O of one when our target resides at the initial midpoint. Average and worst cases are strictly bounded by O of log N, requiring negligible auxiliary memory.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Search Complexity Analysis Matrix",
                    "leftHeader": "Linear Search",
                    "rightHeader": "Binary Search",
                    "rows": [
                        {"feature": "Best Case Time", "left": "O(1)", "right": "O(1)"},
                        {"feature": "Average Case Time", "left": "O(N)", "right": "O(log N)"},
                        {"feature": "Worst Case Time", "left": "O(N)", "right": "O(log N)"},
                        {"feature": "Auxiliary Space", "left": "O(1)", "right": "O(1)"}
                    ]
                },
                "text": "Asymptotic Complexity Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To master binary search, always verify that your data is strictly sorted, guard against off-by-one errors in while conditions, and remember that binary search can be applied across continuous solution spaces to solve monotonic optimization problems.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Prerequisite Invariant: Elements must be strictly monotonic or pre-sorted",
                        "Overflow Guard: Always compute mid using beg + (end - beg) // 2",
                        "Binary Search on Answer: Apply logarithmic search to guess and verify monotonic solution bounds"
                    ]
                },
                "text": "Senior Algorithmic Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 5.5 DATA STRUCTURES & ALGORITHMS: LINEAR SEARCH (SEQUENTIAL)
    # -------------------------------------------------------------
    elif domain == "dsa_linear_search":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this comprehensive computer science masterclass on {lesson_title}. Linear search is the foundational searching strategy in software engineering: it scans contiguous elements sequentially from the first index to the last, finding targets on raw data without requiring sorting or preprocessing.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Sequential Scan, Unsorted Arrays & Asymptotic O(N) Complexity"},
                "text": "Linear Search Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Examining the array directly in memory illustrates how sequential traversal functions. Notice the active index pointer advancing steadily across memory cells: each stored element is compared against our target value until a match is confirmed or the boundary of the array is reached.",
                "visual_type": "array_memory",
                "visual_data": {
                    "title": "In-Memory Sequential Array Traversal",
                    "items": [
                        {"index": 0, "value": 14, "address": "0x1000", "status": "eliminated"},
                        {"index": 1, "value": 29, "address": "0x1004", "status": "eliminated"},
                        {"index": 2, "value": 42, "address": "0x1008", "status": "target"},
                        {"index": 3, "value": 87, "address": "0x100C", "status": "normal"},
                        {"index": 4, "value": 63, "address": "0x1010", "status": "normal"}
                    ],
                    "pointers": [
                        {"label": "Current (i)", "index": 2, "color": "#38bdf8"},
                        {"label": "Target (42)", "index": 2, "color": "#10b981"}
                    ]
                },
                "text": "Sequential Memory Ribbon Mechanics",
                "transition": "fade"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Linear search executes across three deterministic algorithmic phases: first, initialize an index pointer at index zero; second, compare the current array element against the target key; and third, return the matching index immediately, or advance the pointer until exhaustion returns negative one.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Pointer Initialization", "desc": "Initialize index pointer i = 0 pointing to the start of the collection"},
                        {"title": "2. Element Comparison", "desc": "Compare array element at index i against the target search key"},
                        {"title": "3. Match or Advance", "desc": "Return index i upon matching, or advance i until array exhaustion returns -1"}
                    ]
                },
                "text": "3-Stage Sequential Execution Flow",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of linear search in Python and C++. Notice how early termination optimizes the search: the moment the target value is matched, the loop exits immediately without examining remaining elements, saving valuable CPU cycles on early hits.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "def linear_search(arr: list, target: int) -> int:\n    # 1. Sequentially scan each element\n    for index, value in enumerate(arr):\n        # 2. Early termination on match\n        if value == target:\n            return index  # Target located\n            \n    # 3. Target not found in entire collection\n    return -1"
                },
                "text": "Clean Implementation & Early Termination",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing a live execution walkthrough highlights state transitions across each iteration: the search begins at index zero, detects a mismatch, advances to index one, and upon inspecting index two, asserts equality, records the target position, and terminates cleanly.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Linear Search State Execution Trace",
                    "stages": [
                        {"label": "1. Index 0", "subtitle": "A[0] != Target", "badge": "Mismatch", "icon": "🔍", "status": "completed"},
                        {"label": "2. Index 1", "subtitle": "A[1] != Target", "badge": "Mismatch", "icon": "⏩", "status": "completed"},
                        {"label": "3. Index 2", "subtitle": "A[2] == Target", "badge": "Match Found", "icon": "🎯", "status": "active"},
                        {"label": "4. Return Index", "subtitle": "Halt and return 2", "badge": "Done", "icon": "✅", "status": "highlight"}
                    ],
                    "highlight_label": "Early termination stops the loop the instant the target element is encountered."
                },
                "text": "Step-by-Step Traversal Trace",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Contrasting linear search against binary search exposes fundamental design trade-offs: while binary search achieves logarithmic speed, it strictly requires pre-sorted random-access arrays. Linear search handles raw unsorted data, single-pass streaming pipes, and dynamically linked lists with zero sorting overhead.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Linear Search (Sequential Scan)",
                    "left_desc": "Operates on completely unsorted collections; works on streams and linked lists; zero preprocessing; O(N) linear time.",
                    "right_title": "Binary Search (Logarithmic Divide)",
                    "right_desc": "Requires pre-sorted random-access array; halves search space iteratively; O(log N) time, but sorting costs O(N log N) upfront."
                },
                "text": "Linear Search vs Binary Search",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "From a metric perspective, linear search achieves constant time O of one in the best case when the target resides at index zero. In the worst and average cases, runtime scales linearly with input size N, maintaining optimal O of one auxiliary memory.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Search Complexity & Profile Matrix",
                    "leftHeader": "Linear Search",
                    "rightHeader": "Binary Search",
                    "rows": [
                        {"feature": "Best-Case Time", "left": "O(1) [First element match]", "right": "O(1) [Midpoint match]"},
                        {"feature": "Average-Case Time", "left": "O(N) [~N/2 comparisons]", "right": "O(log N) [Logarithmic halving]"},
                        {"feature": "Worst-Case Time", "left": "O(N) [Target at end or missing]", "right": "O(log N) [Guaranteed logarithmic]"},
                        {"feature": "Data Prerequisite", "left": "None (Works on unsorted arrays)", "right": "Strictly sorted array required"},
                        {"feature": "Auxiliary Space", "left": "O(1) Constant Space", "right": "O(1) Iterative Space"}
                    ]
                },
                "text": "Asymptotic Complexity & Profile Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To master linear search in production systems, exploit CPU cache line prefetching on contiguous memory, consider sentinel keys to eliminate loop bounds checks on hot paths, and choose linear search for small or unindexed collections where sorting would waste compute resources.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Cache Locality Advantage: Contiguous array traversal maximizes CPU L1/L2 hardware prefetch throughput.",
                        "Sentinel Search Optimization: Placing the target key at the array boundary eliminates bound comparisons per loop.",
                        "Small-N Threshold Rule: For small collections (N < 32), linear search beats binary search due to zero sorting overhead."
                    ]
                },
                "text": "Senior Algorithmic Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6. DATA STRUCTURES & ALGORITHMS: SORTING (TOPIC-AWARE FALLBACK)
    # -------------------------------------------------------------
    elif domain == "dsa_sorting":
        title_lower = lesson_title.lower()
        # Merge Sort fallback
        if "merge" in title_lower:
            return [
                {
                    "scene_id": 1, "start_time": 0.0, "end_time": 15.0,
                    "narration": f"Welcome to this comprehensive algorithms masterclass on {lesson_title}. Merge Sort is a classic divide-and-conquer algorithm that guarantees O of N log N performance in every case by splitting, recursively sorting, and merging subarrays.",
                    "visual_type": "title_card",
                    "visual_data": {"title": lesson_title, "subtitle": "Divide-and-Conquer, Stable Sorting & O(N log N) Guaranteed"},
                    "text": "Merge Sort Algorithmic Foundations", "transition": "fade"
                },
                {
                    "scene_id": 2, "start_time": 15.0, "end_time": 30.0,
                    "narration": "Visualizing Merge Sort in memory shows two sorted sub-arrays being merged by advancing pointers i, j, and k through the left half, right half, and output buffer simultaneously until all elements are placed in sorted order.",
                    "visual_type": "array_memory",
                    "visual_data": {
                        "title": f"{lesson_title} Merge Memory Ribbon",
                        "items": [
                            {"index": 0, "value": 3, "address": "0x1000", "status": "active"},
                            {"index": 1, "value": 7, "address": "0x1004", "status": "active"},
                            {"index": 2, "value": 12, "address": "0x1008", "status": "eliminated"},
                            {"index": 3, "value": 5, "address": "0x100C", "status": "target"},
                            {"index": 4, "value": 9, "address": "0x1010", "status": "normal"},
                            {"index": 5, "value": 14, "address": "0x1014", "status": "normal"}
                        ],
                        "pointers": [
                            {"label": "i (Left)", "index": 0, "color": "#38bdf8"},
                            {"label": "j (Right)", "index": 3, "color": "#f59e0b"},
                            {"label": "k (Output)", "index": 2, "color": "#ec4899"}
                        ]
                    },
                    "text": "Two-Pointer Merge Mechanics", "transition": "fade"
                },
                {
                    "scene_id": 3, "start_time": 30.0, "end_time": 45.0,
                    "narration": "Merge Sort executes three clean divide-and-conquer stages: first divide the array into two equal halves at the midpoint; second recursively sort each half until base case arrays of size one; third merge sorted halves back into a single fully-sorted output.",
                    "visual_type": "flow_steps",
                    "visual_data": {
                        "steps": [
                            {"title": "1. Divide", "desc": "Split array at mid = (low + high) // 2 into two equal halves"},
                            {"title": "2. Conquer (Recurse)", "desc": "Recursively merge_sort(left) and merge_sort(right) until single elements"},
                            {"title": "3. Merge & Combine", "desc": "Two-pointer merge of sorted left and right halves into output buffer"}
                        ]
                    },
                    "text": "3-Stage Divide-and-Conquer Strategy", "transition": "slide"
                },
                {
                    "scene_id": 4, "start_time": 45.0, "end_time": 60.0,
                    "narration": "Here is the clean Merge Sort implementation. Notice the merge function uses three pointers advancing through left and right sub-arrays, copying the smaller element to the output at each step until both halves are fully exhausted.",
                    "visual_type": "code_snippet",
                    "visual_data": {
                        "code": "def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(left, right):\n    result, i, j = [], 0, 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i]); i += 1\n        else:\n            result.append(right[j]); j += 1\n    return result + left[i:] + right[j:]"
                    },
                    "text": "Python Merge Sort Implementation", "transition": "slide"
                },
                {
                    "scene_id": 5, "start_time": 60.0, "end_time": 75.0,
                    "narration": "Tracing the recursion tree shows Merge Sort's systematic decomposition: an array of 8 elements splits into 4, then 2, then 1-element base cases, and merges back layer by layer — each level doing O of N work across O of log N levels.",
                    "visual_type": "system_pipeline",
                    "visual_data": {
                        "title": "Merge Sort Recursion Trace",
                        "stages": [
                            {"label": "1. Split to Halves", "subtitle": "Divide at midpoint", "badge": "Divide", "icon": "✂️", "status": "completed"},
                            {"label": "2. Recurse Left", "subtitle": "Sort left sub-array", "badge": "Left", "icon": "⬅️", "status": "active"},
                            {"label": "3. Recurse Right", "subtitle": "Sort right sub-array", "badge": "Right", "icon": "➡️", "status": "normal"},
                            {"label": "4. Merge Back", "subtitle": "Two-pointer merge into output", "badge": "Merge", "icon": "🔀", "status": "highlight"}
                        ],
                        "highlight_label": "Each merge level performs exactly O(N) work. With O(log N) levels, total is O(N log N)."
                    },
                    "text": "Recursion Tree & Merge Trace", "transition": "slide"
                },
                {
                    "scene_id": 6, "start_time": 75.0, "end_time": 90.0,
                    "narration": "Comparing Merge Sort against Quicksort highlights a fundamental trade-off: Merge Sort guarantees O of N log N in every case and is stable, at the cost of O of N auxiliary memory; while Quicksort sorts in-place with superior cache locality but degrades to O of N squared without randomization.",
                    "visual_type": "comparison",
                    "visual_data": {
                        "left_title": "Merge Sort (Stable, Guaranteed)",
                        "left_desc": "Always O(N log N); stable sort preserves equal-element order; requires O(N) auxiliary buffer for merging.",
                        "right_title": "Quicksort (In-Place, Fast Cache)",
                        "right_desc": "Average O(N log N) with O(1) auxiliary; in-place with great cache locality; O(N^2) worst-case without randomized pivot."
                    },
                    "text": "Merge Sort vs Quicksort Trade-Offs", "transition": "slide"
                },
                {
                    "scene_id": 7, "start_time": 90.0, "end_time": 105.0,
                    "narration": "Examining the sorting algorithm matrix confirms Merge Sort's guaranteed O of N log N in all cases, making it the preferred choice for linked lists and external sorting, while Quicksort excels for in-memory random-access arrays.",
                    "visual_type": "comparison_matrix",
                    "visual_data": {
                        "title": "Sorting Algorithm Complexity Matrix",
                        "leftHeader": "Merge Sort",
                        "rightHeader": "Quicksort (Randomized)",
                        "rows": [
                            {"feature": "Best Case Time", "left": "O(N log N)", "right": "O(N log N)"},
                            {"feature": "Worst Case Time", "left": "Guaranteed O(N log N)", "right": "O(N^2) [expected O(N log N)]"},
                            {"feature": "Auxiliary Space", "left": "O(N) merge buffer", "right": "O(log N) call stack"},
                            {"feature": "Stability", "left": "✅ Stable", "right": "❌ Not stable (in-place)"}
                        ]
                    },
                    "text": "Asymptotic Sorting Algorithm Matrix", "transition": "fade"
                },
                {
                    "scene_id": 8, "start_time": 105.0, "end_time": 120.0,
                    "narration": "To master Merge Sort like a senior engineer, always leverage its stability guarantee for multi-key sort chains, apply it to linked list sorting where random access is impossible, and use bottom-up iterative Merge Sort to eliminate recursive call stack overhead entirely.",
                    "visual_type": "text_bullets",
                    "visual_data": {
                        "items": [
                            "Stability Invariant: Merge Sort preserves relative order of equal elements — critical for multi-key stable sorting",
                            "External Sort Application: Used in database engines for sorting datasets exceeding RAM capacity (external merge sort)",
                            "Iterative Bottom-Up: Eliminate recursion overhead by iteratively merging pairs of size 1 → 2 → 4 → N"
                        ]
                    },
                    "text": "Senior Algorithmic Invariants", "transition": "fade"
                }
            ]
        # Selection Sort fallback
        if "selection" in title_lower:
            return [
                {
                    "scene_id": 1, "start_time": 0.0, "end_time": 15.0,
                    "narration": f"Welcome to this comprehensive algorithms masterclass on {lesson_title}. Selection Sort is a fundamental comparison-based sorting algorithm that systematically partitions an array into sorted and unsorted regions, finding the minimum element in each pass.",
                    "visual_type": "title_card",
                    "visual_data": {"title": lesson_title, "subtitle": "In-Place Comparison, Minimum Selection & O(N^2) Invariants"},
                    "text": "Selection Sort Algorithmic Foundations", "transition": "fade"
                },
                {
                    "scene_id": 2, "start_time": 15.0, "end_time": 30.0,
                    "narration": "Examining Selection Sort in memory shows the array divided into two parts: a sorted prefix on the left, and an unsorted region on the right. Pointers track the sorted boundary i and the current minimum element found during the pass.",
                    "visual_type": "array_memory",
                    "visual_data": {
                        "title": f"{lesson_title} Scan & Minimum Ribbon",
                        "items": [
                            {"index": 0, "value": 11, "address": "0x1000", "status": "active"},
                            {"index": 1, "value": 12, "address": "0x1004", "status": "active"},
                            {"index": 2, "value": 25, "address": "0x1008", "status": "normal"},
                            {"index": 3, "value": 22, "address": "0x100C", "status": "target"},
                            {"index": 4, "value": 64, "address": "0x1010", "status": "normal"}
                        ],
                        "pointers": [
                            {"label": "Sorted (i)", "index": 2, "color": "#10b981"},
                            {"label": "Min (min_idx)", "index": 3, "color": "#f59e0b"},
                            {"label": "Scan (j)", "index": 4, "color": "#38bdf8"}
                        ]
                    },
                    "text": "Sorted Prefix & Scanning Pointer Mechanics", "transition": "fade"
                },
                {
                    "scene_id": 3, "start_time": 30.0, "end_time": 45.0,
                    "narration": "Selection Sort executes across three consistent steps per pass: first, initialize min index at the first unsorted position; second, linearly scan remaining elements to find the smallest value; third, perform a single swap to place the minimum into the sorted prefix.",
                    "visual_type": "flow_steps",
                    "visual_data": {
                        "steps": [
                            {"title": "1. Set Search Boundary", "desc": "Initialize min_idx = i at the beginning of the unsorted subarray"},
                            {"title": "2. Scan for Minimum", "desc": "Iterate j from i+1 to N-1; update min_idx whenever arr[j] < arr[min_idx]"},
                            {"title": "3. Single In-Place Swap", "desc": "Swap arr[i] with arr[min_idx], expanding the sorted prefix by 1 element"}
                        ]
                    },
                    "text": "3-Stage Selection & Swap Strategy", "transition": "slide"
                },
                {
                    "scene_id": 4, "start_time": 45.0, "end_time": 60.0,
                    "narration": "Here is the clean, idiomatic Python implementation of Selection Sort. Notice the outer loop advances the sorted boundary, the inner loop identifies the minimum index, and exactly one swap occurs per outer pass.",
                    "visual_type": "code_snippet",
                    "visual_data": {
                        "code": "def selection_sort(arr):\n    n = len(arr)\n    for i in range(n - 1):\n        min_idx = i\n        for j in range(i + 1, n):\n            if arr[j] < arr[min_idx]:\n                min_idx = j\n        # In-place swap with leftmost unsorted element\n        if min_idx != i:\n            arr[i], arr[min_idx] = arr[min_idx], arr[i]\n    return arr"
                    },
                    "text": "Python Selection Sort Implementation", "transition": "slide"
                },
                {
                    "scene_id": 5, "start_time": 60.0, "end_time": 75.0,
                    "narration": "Tracing a live execution walkthrough demonstrates how the sorted prefix grows incrementally: pass 1 places the global minimum at index zero, pass 2 secures the second smallest, requiring exactly N minus 1 passes to guarantee full ordering.",
                    "visual_type": "system_pipeline",
                    "visual_data": {
                        "title": "Selection Sort Pass-by-Pass Pipeline",
                        "stages": [
                            {"label": "Pass 1: Min = 11", "subtitle": "Swap to index 0", "badge": "Step 1", "icon": "🔍", "status": "completed"},
                            {"label": "Pass 2: Min = 12", "subtitle": "Swap to index 1", "badge": "Step 2", "icon": "🔄", "status": "active"},
                            {"label": "Pass 3: Min = 22", "subtitle": "Swap to index 2", "badge": "Step 3", "icon": "⚡", "status": "normal"},
                            {"label": "Pass 4: Complete", "subtitle": "Array fully sorted", "badge": "Done", "icon": "✅", "status": "highlight"}
                        ],
                        "highlight_label": "Selection Sort performs at most O(N) swaps, making it exceptionally write-efficient."
                    },
                    "text": "Pass-by-Pass Execution Pipeline", "transition": "slide"
                },
                {
                    "scene_id": 6, "start_time": 75.0, "end_time": 90.0,
                    "narration": "Comparing Selection Sort against Bubble Sort highlights distinct mechanical trade-offs: while Bubble Sort performs continuous adjacent swaps, Selection Sort scans quietly and performs at most one swap per pass, dramatically reducing memory write operations.",
                    "visual_type": "comparison",
                    "visual_data": {
                        "left_title": "Selection Sort (Minimal Memory Writes)",
                        "left_desc": "Strictly O(N) memory writes; ideal for flash memory and EEPROM where write cycles degrade physical storage.",
                        "right_title": "Bubble Sort (Adaptive Adjacent Swaps)",
                        "right_desc": "Performs up to O(N^2) swaps; can detect early sortedness in O(N) time, whereas Selection Sort always scans fully."
                    },
                    "text": "Selection Sort vs Bubble Sort Trade-Offs", "transition": "slide"
                },
                {
                    "scene_id": 7, "start_time": 90.0, "end_time": 105.0,
                    "narration": "Examining the sorting algorithm matrix confirms Selection Sort's asymptotic profile: best, average, and worst case time are all Theta of N squared comparisons, with optimal O of one auxiliary space and at most N swaps.",
                    "visual_type": "comparison_matrix",
                    "visual_data": {
                        "title": "Sorting Algorithm Complexity Matrix",
                        "leftHeader": "Selection Sort",
                        "rightHeader": "Bubble Sort / Insertion Sort",
                        "rows": [
                            {"feature": "Best Case Time", "left": "Theta(N^2) [Always scans]", "right": "O(N) [When pre-sorted]"},
                            {"feature": "Worst Case Time", "left": "Theta(N^2) comparisons", "right": "O(N^2) comparisons"},
                            {"feature": "Auxiliary Space", "left": "O(1) strictly in-place", "right": "O(1) strictly in-place"},
                            {"feature": "Total Swaps", "left": "At most N - 1 swaps", "right": "Up to N*(N-1)/2 swaps"}
                        ]
                    },
                    "text": "Asymptotic Selection Sort Matrix", "transition": "fade"
                },
                {
                    "scene_id": 8, "start_time": 105.0, "end_time": 120.0,
                    "narration": "To master Selection Sort like a senior engineer, remember the loop invariant: the subarray A zero to i minus one is sorted and contains the smallest elements in the entire array. Use it when write operations are physically expensive.",
                    "visual_type": "text_bullets",
                    "visual_data": {
                        "items": [
                            "Loop Invariant: Subarray arr[0..i-1] consists of the i smallest elements in fully sorted order",
                            "Minimal Write Advantage: Exactly O(N) swaps make it ideal when memory write cycles are constrained (EEPROM / Flash)",
                            "Stability Warning: Standard Selection Sort is NOT stable due to long-distance swaps jumping over equal keys"
                        ]
                    },
                    "text": "Senior Algorithmic Invariants", "transition": "fade"
                }
            ]

        # Insertion Sort fallback
        if "insertion" in title_lower:
            return [
                {
                    "scene_id": 1, "start_time": 0.0, "end_time": 15.0,
                    "narration": f"Welcome to this comprehensive algorithms masterclass on {lesson_title}. Insertion Sort is an intuitive, adaptive comparison-based sorting algorithm that builds the final sorted array one element at a time.",
                    "visual_type": "title_card",
                    "visual_data": {"title": lesson_title, "subtitle": "Incremental Insertion, Adaptive Sorting & O(N) Best-Case"},
                    "text": "Insertion Sort Algorithmic Foundations", "transition": "fade"
                },
                {
                    "scene_id": 2, "start_time": 15.0, "end_time": 30.0,
                    "narration": "Examining Insertion Sort in memory shows a sorted subarray expanding from the left. Each pass takes the next unsorted element and shifts larger elements one position to the right to make room.",
                    "visual_type": "array_memory",
                    "visual_data": {
                        "title": f"{lesson_title} Key Element & Shift Ribbon",
                        "items": [
                            {"index": 0, "value": 5, "address": "0x1000", "status": "active"},
                            {"index": 1, "value": 8, "address": "0x1004", "status": "active"},
                            {"index": 2, "value": 12, "address": "0x1008", "status": "active"},
                            {"index": 3, "value": 7, "address": "0x100C", "status": "target"},
                            {"index": 4, "value": 19, "address": "0x1010", "status": "normal"}
                        ],
                        "pointers": [
                            {"label": "Key (arr[i])", "index": 3, "color": "#f59e0b"},
                            {"label": "Shift (j)", "index": 2, "color": "#38bdf8"}
                        ]
                    },
                    "text": "Shift & Insertion Mechanics", "transition": "fade"
                },
                {
                    "scene_id": 3, "start_time": 30.0, "end_time": 45.0,
                    "narration": "Insertion Sort proceeds through three simple steps: pick the key element at index i, shift all elements greater than key one position forward, and insert the key into its correct sorted position.",
                    "visual_type": "flow_steps",
                    "visual_data": {
                        "steps": [
                            {"title": "1. Select Key", "desc": "Store current element key = arr[i] starting at i = 1"},
                            {"title": "2. Shift Greater Elements", "desc": "Compare key backwards with arr[j]; shift arr[j] to j+1 while arr[j] > key"},
                            {"title": "3. Drop Key into Place", "desc": "Assign arr[j + 1] = key into the opened vacancy"}
                        ]
                    },
                    "text": "3-Stage Incremental Insertion Strategy", "transition": "slide"
                },
                {
                    "scene_id": 4, "start_time": 45.0, "end_time": 60.0,
                    "narration": "Here is the clean Python implementation of Insertion Sort. The while loop runs only as long as elements are out of order, granting Insertion Sort its famous linear O of N performance on nearly sorted data.",
                    "visual_type": "code_snippet",
                    "visual_data": {
                        "code": "def insertion_sort(arr):\n    for i in range(1, len(arr)):\n        key = arr[i]\n        j = i - 1\n        # Shift elements greater than key to the right\n        while j >= 0 and arr[j] > key:\n            arr[j + 1] = arr[j]\n            j -= 1\n        arr[j + 1] = key\n    return arr"
                    },
                    "text": "Python Insertion Sort Implementation", "transition": "slide"
                },
                {
                    "scene_id": 5, "start_time": 60.0, "end_time": 75.0,
                    "narration": "Tracing a live execution walkthrough demonstrates how each insertion preserves the invariant: after pass i, the first i plus one elements are strictly sorted among themselves.",
                    "visual_type": "system_pipeline",
                    "visual_data": {
                        "title": "Insertion Sort Step-by-Step Pipeline",
                        "stages": [
                            {"label": "Step 1: Key = arr[1]", "subtitle": "Insert into sorted arr[0]", "badge": "Step 1", "icon": "📥", "status": "completed"},
                            {"label": "Step 2: Key = arr[2]", "subtitle": "Shift and insert", "badge": "Step 2", "icon": "🔄", "status": "active"},
                            {"label": "Step 3: Key = arr[3]", "subtitle": "Adaptive shift scan", "badge": "Step 3", "icon": "⚡", "status": "normal"},
                            {"label": "Step 4: Fully Sorted", "subtitle": "O(N) best case achieved", "badge": "Done", "icon": "✅", "status": "highlight"}
                        ],
                        "highlight_label": "Insertion Sort is the algorithm of choice for hybrid sorts like Timsort on small arrays."
                    },
                    "text": "Incremental Insertion Pipeline", "transition": "slide"
                },
                {
                    "scene_id": 6, "start_time": 75.0, "end_time": 90.0,
                    "narration": "Comparing Insertion Sort against Selection Sort reveals why Insertion Sort is preferred for online streaming data: Insertion Sort adapts to incoming data in real time, running in linear time if data arrives mostly sorted.",
                    "visual_type": "comparison",
                    "visual_data": {
                        "left_title": "Insertion Sort (Adaptive & Stable)",
                        "left_desc": "O(N) best-case time; stable sort; excellent for small arrays (N < 32) and nearly-sorted live data streams.",
                        "right_title": "Selection Sort (Fixed Comparisons)",
                        "right_desc": "Always Theta(N^2) comparisons regardless of initial array order; not stable; but strictly bounded to O(N) swaps."
                    },
                    "text": "Insertion Sort vs Selection Sort Trade-Offs", "transition": "slide"
                },
                {
                    "scene_id": 7, "start_time": 90.0, "end_time": 105.0,
                    "narration": "Examining the sorting algorithm matrix confirms Insertion Sort's outstanding best-case profile: O of N time with O of one space, making it a foundational building block in production engines like Python's Timsort.",
                    "visual_type": "comparison_matrix",
                    "visual_data": {
                        "title": "Sorting Algorithm Complexity Matrix",
                        "leftHeader": "Insertion Sort",
                        "rightHeader": "Selection Sort",
                        "rows": [
                            {"feature": "Best Case Time", "left": "O(N) [Pre-sorted]", "right": "Theta(N^2) [Always scans]"},
                            {"feature": "Worst Case Time", "left": "O(N^2) [Reverse sorted]", "right": "Theta(N^2) comparisons"},
                            {"feature": "Auxiliary Space", "left": "O(1) in-place", "right": "O(1) in-place"},
                            {"feature": "Stability", "left": "✅ Stable", "right": "❌ Not stable"}
                        ]
                    },
                    "text": "Asymptotic Insertion Sort Matrix", "transition": "fade"
                },
                {
                    "scene_id": 8, "start_time": 105.0, "end_time": 120.0,
                    "narration": "To implement Insertion Sort like a senior engineer, leverage it inside hybrid algorithms like Introsort or Timsort when subarrays drop below 16 elements, maximizing CPU L1 cache locality and minimizing function call overhead.",
                    "visual_type": "text_bullets",
                    "visual_data": {
                        "items": [
                            "Adaptive Efficiency: Scales with the number of inversions in the array: O(N + I)",
                            "Hybrid Sorting Workhorse: Powers the base case of Python's Timsort and Java's Dual-Pivot Quicksort",
                            "Online Algorithm: Can sort a list as it receives it element-by-element in streaming pipelines"
                        ]
                    },
                    "text": "Senior Algorithmic Invariants", "transition": "fade"
                }
            ]

        # Default: Quicksort fallback (original behavior)

        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this comprehensive algorithms masterclass on {lesson_title}. Quicksort is one of the most efficient sorting algorithms ever developed, leveraging dynamic in-place partitioning to achieve blistering O of N log N performance.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Divide-and-Conquer, Lomuto Partitioning & Invariant Proofs"},
                "text": "Quicksort Algorithmic Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Examining the partition subroutine directly in memory reveals contiguous array cells undergoing in-place swaps. Notice how the pivot element establishes our comparison baseline, with pointer i tracking elements less than the pivot and pointer j scanning forward.",
                "visual_type": "array_memory",
                "visual_data": {
                    "title": "Quicksort Lomuto Partition Ribbon",
                    "items": [
                        {"index": 0, "value": 9, "address": "0x1000", "status": "active"},
                        {"index": 1, "value": 7, "address": "0x1004", "status": "active"},
                        {"index": 2, "value": 10, "address": "0x1008", "status": "active"},
                        {"index": 3, "value": 11, "address": "0x100C", "status": "target"},
                        {"index": 4, "value": 17, "address": "0x1010", "status": "normal"},
                        {"index": 5, "value": 22, "address": "0x1014", "status": "normal"},
                        {"index": 6, "value": 31, "address": "0x1018", "status": "normal"}
                    ],
                    "pointers": [
                        {"label": "i", "index": 2, "color": "#38bdf8"},
                        {"label": "Pivot", "index": 3, "color": "#f59e0b"},
                        {"label": "j", "index": 6, "color": "#ec4899"}
                    ]
                },
                "text": "In-Memory Partition & Pointer Mechanics",
                "transition": "fade"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Quicksort executes across three divide-and-conquer phases: Divide rearranges array elements in-place around a pivot; Conquer recursively sorts left and right subarrays; while Combine requires zero work because sorting occurs in-place.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Divide (Partition)", "desc": "Rearrange A[p..r] so elements <= pivot are left, and elements > pivot are right"},
                        {"title": "2. Conquer (Recursion)", "desc": "Recursively sort subarrays A[p..q-1] and A[q+1..r]"},
                        {"title": "3. Combine (Zero Cost)", "desc": "Entire array is sorted in-place without auxiliary buffers"}
                    ]
                },
                "text": "3-Stage Divide-and-Conquer Strategy",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of Quicksort with the Lomuto partition algorithm. Notice lines 5 through 7: whenever an element smaller than the pivot is encountered, index i increments and swaps elements to preserve the partition invariant.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "def partition(A, p, r):\n    x = A[r]         # Pivot element\n    i = p - 1        # Boundary of elements <= pivot\n    for j in range(p, r):\n        if A[j] <= x:\n            i += 1\n            A[i], A[j] = A[j], A[i]  # In-place swap\n    A[i + 1], A[r] = A[r], A[i + 1]\n    return i + 1     # Final pivot position"
                },
                "text": "Lomuto Partition Algorithm",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing a live execution walkthrough demonstrates the recursion tree: dynamic partitions divide subarrays into balanced subproblems, executing linear partitioning passes across logarithmic recursion depth.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Quicksort Partition & Recursion Trace",
                    "stages": [
                        {"label": "1. Pick Pivot", "subtitle": "Select A[r] as baseline", "badge": "Pivot", "icon": "📍", "status": "completed"},
                        {"label": "2. Scan & Swap", "subtitle": "Lomuto partition scan", "badge": "Scan", "icon": "🔄", "status": "active"},
                        {"label": "3. Place Pivot", "subtitle": "Final swap to index q", "badge": "Lock", "icon": "🔒", "status": "normal"},
                        {"label": "4. Recurse", "subtitle": "Sort left & right branches", "badge": "Branch", "icon": "🌲", "status": "highlight"}
                    ],
                    "highlight_label": "Partitioning takes strictly linear O(N) time with zero auxiliary memory."
                },
                "text": "Partition & Recursion Trace",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing worst-case and expected behavior highlights why pivot selection is critical: picking a fixed pivot on an already sorted array yields quadratic O of N squared runtime, while randomized pivot selection guarantees expected O of N log N performance.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Fixed Pivot (Pathological Worst-Case)",
                    "left_desc": "On pre-sorted arrays, partitions split as N-1 and 0; recurrence unrolls to quadratic O(N^2) comparisons.",
                    "right_title": "Randomized Pivot (Expected O(N log N))",
                    "right_desc": "Selects pivot uniformly at random; produces balanced subproblems; mathematically guaranteed expected Theta(N log N)."
                },
                "text": "Worst-Case O(N^2) vs Randomized Expected O(N log N)",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Comparing modern sorting algorithms reveals why Quicksort dominates practical libraries: although MergeSort guarantees worst-case O of N log N, Quicksort sorts in-place with superior CPU cache locality and lower constant factors.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Asymptotic Sorting Algorithm Matrix",
                    "leftHeader": "Quicksort (Randomized)",
                    "rightHeader": "MergeSort",
                    "rows": [
                        {"feature": "Average Time", "left": "O(N log N)", "right": "O(N log N)"},
                        {"feature": "Worst-Case Time", "left": "O(N^2) [O(N log N) expected]", "right": "Guaranteed O(N log N)"},
                        {"feature": "Auxiliary Space", "left": "O(log N) Call Stack", "right": "O(N) Auxiliary Buffer"},
                        {"feature": "Cache Performance", "left": "Superior (Contiguous locality)", "right": "Moderate (Buffer copying)"}
                    ]
                },
                "text": "Asymptotic Sorting Algorithm Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To implement Quicksort like a senior engineer, always randomize pivot selection, prove correctness using partition loop invariants, and implement tail-call recursion on the smaller partition to bound stack depth to O of log N.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Loop Invariant: At each loop step, elements A[p..i] <= pivot and elements A[i+1..j-1] > pivot",
                        "Tail Call Optimization: Recurse on the smaller partition first to guarantee maximum call stack depth of O(log N)",
                        "Hybrid Sorting: Switch to Insertion Sort for small subarrays (N < 16) to maximize L1 cache throughput"
                    ]
                },
                "text": "Senior Algorithmic Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.5 DATA STRUCTURES & ALGORITHMS: TREES & GRAPHS (BST)
    # -------------------------------------------------------------
    elif domain == "dsa_tree_graph":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this fundamental algorithmic masterclass on {lesson_title}. Today we unpack the binary search tree, the hierarchical data structure that enables fast logarithmic search, insertion, and deletion by strictly maintaining the ordering invariant: left keys are smaller, and right keys are larger.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Hierarchical Data, Invariants & Logarithmic O(log N) Search"},
                "text": "BST Architectural Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Every BST interaction hinges on three core operational phases. First, we inspect the root node key. Second, we compare our target value to make a deterministic directional branch: descending left if smaller, or right if larger. Finally, we reach our destination node or insert the new leaf pointer.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Key Comparison", "desc": "Compare target value with the current node key to determine the branch direction."},
                        {"title": "2. Directional Branch", "desc": "Descend strictly to the left child if target < key, or to the right child if target > key."},
                        {"title": "3. Terminal Resolution", "desc": "Locate the target element in O(log N) time or attach a new leaf node pointer."}
                    ]
                },
                "text": "Core BST Operations",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Observe the tree hierarchy in action. The root key is 50. All keys in the left subtree, such as 25, 12, and 37, are strictly less than 50. All keys in the right subtree, like 75, 62, and 87, are strictly greater. Each decision halves the search space.",
                "visual_type": "tree_structure",
                "visual_data": {
                    "title": "Binary Search Tree Invariant",
                    "root_label": "Root: 50",
                    "left_label": "Left: 25",
                    "right_label": "Right: 75",
                    "left_leaf_1": "Key 12",
                    "left_leaf_2": "Key 37",
                    "right_leaf_1": "Key 62",
                    "right_leaf_2": "Key 87",
                    "status": "Left < Root < Right Invariant"
                },
                "text": "Tree Structure & Invariant",
                "transition": "zoom"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of recursive search and insert in a BST. If the root is null or matches the key, we terminate immediately. Otherwise, the method calls itself on the appropriate subtree, delivering logarithmic time complexity without allocating extra memory buffers.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "BST Search & Insertion Implementation",
                    "language": "python",
                    "code": "class Node:\n    def __init__(self, key):\n        self.key = key\n        self.left = None\n        self.right = None\n\ndef search(root, key):\n    if not root or root.key == key:\n        return root\n    if key < root.key:\n        return search(root.left, key)\n    return search(root.right, key)\n\ndef insert(root, key):\n    if not root:\n        return Node(key)\n    if key < root.key:\n        root.left = insert(root.left, key)\n    elif key > root.key:\n        root.right = insert(root.right, key)\n    return root"
                },
                "text": "Recursive Traversal Code",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Trace a target search query from end to end. The algorithm starts at the root, evaluates the comparator guard, eliminates an entire half of the remaining nodes at each step, and terminates at the target key in O of log N operations.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Search Traversal Pipeline",
                    "stages": [
                        {"label": "1. Root Compare", "subtitle": "Evaluate target against root key", "badge": "Step 1", "icon": "🔍", "status": "normal"},
                        {"label": "2. Branch Halving", "subtitle": "Prune opposite subtree & descend", "badge": "Step 2", "icon": "⚙️", "status": "normal"},
                        {"label": "3. Target Located", "subtitle": "Found matching node or insert position", "badge": "Step 3", "icon": "✅", "status": "normal"}
                    ],
                    "highlight_label": "Search Complexity: O(log N)"
                },
                "text": "Execution Traversal Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "The primary vulnerability of a naive BST is tree degeneration. If keys are inserted in sorted order, the tree collapses into an unbalanced linked list with worst-case O of N time. Balanced structures like AVL and Red-Black trees fix this by rotating nodes to guarantee log N depth.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Degenerate Skewed BST",
                    "left_desc": "Sequential inputs collapse tree height into O(N). Search degrades into a linear scan like a linked list.",
                    "right_title": "Balanced AVL / Red-Black Tree",
                    "right_desc": "Self-balancing tree rotations maintain height <= 2 * log(N), guaranteeing O(log N) worst-case time."
                },
                "text": "Skewed Tree vs Balanced BST",
                "transition": "fade"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Review the asymptotic complexity profile across key operations. In a balanced BST, search, insert, and delete all execute in O of log N time. In a degenerate skewed tree, all operations degrade to linear O of N time, demonstrating why balance invariants matter.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "BST Complexity Profile: Balanced vs Degenerate",
                    "leftHeader": "Balanced BST (Average)",
                    "rightHeader": "Skewed BST (Worst Case)",
                    "rows": [
                        {"feature": "Search Time", "left": "O(log N)", "right": "O(N)"},
                        {"feature": "Insertion Time", "left": "O(log N)", "right": "O(N)"},
                        {"feature": "Deletion Time", "left": "O(log N)", "right": "O(N)"},
                        {"feature": "Auxiliary Space", "left": "O(log N) stack frames", "right": "O(N) stack frames"}
                    ]
                },
                "text": "Asymptotic Complexity Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior engineering invariants: an in-order traversal of any valid BST always yields a sorted sequence; deleting a node with two children requires replacing it with its in-order successor; and production systems rely on balanced trees like Red-Black trees for predictable latency.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "In-Order Traversal Invariant: Visiting Left -> Root -> Right yields keys in strictly ascending sorted order.",
                        "Two-Child Node Deletion: Replace target node with either the In-Order Successor (min of right subtree) or In-Order Predecessor (max of left subtree).",
                        "Balancing Guarantees: Use self-balancing tree rotations (AVL/Red-Black) to prevent O(N) pathological degradation on pre-sorted data streams."
                    ]
                },
                "text": "Senior Engineering Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.6 DATA STRUCTURES & ALGORITHMS: STACKS & LIFO DATA STRUCTURES
    # -------------------------------------------------------------
    elif domain == "dsa_stacks":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this fundamental algorithmic lecture on {lesson_title}. Today we dissect the stack data structure, governed strictly by the Last-In, First-Out or LIFO principle, where insertions and deletions occur exclusively at one designated end called the top.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Last-In, First-Out (LIFO) • O(1) Push, Pop & Peek Operations"},
                "text": "Stack Architectural Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Every stack provides three fundamental primitives. First, push appends an item to the top in constant time. Second, pop removes and returns the topmost element. Third, peek inspects the active top value without altering the underlying stack state.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Push Operation", "desc": "Allocate the next top slot, assign the element, and advance the top pointer in O(1) time."},
                        {"title": "2. Pop Operation", "desc": "Guard against underflow, retrieve the item at the top pointer, and decrement in O(1) time."},
                        {"title": "3. Peek / Top Query", "desc": "Directly read the current top element value without mutating or popping the stack."}
                    ]
                },
                "text": "Core Stack Primitives",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Observe the in-memory vertical stack architecture. Element 40 sits at the top with the active top pointer. Below it rest elements 30, 20, and base element 10. Any new push or pop operation interacts exclusively with the top in constant O of 1 time.",
                "visual_type": "layer_stack",
                "visual_data": {
                    "title": "In-Memory Stack Architecture (LIFO)",
                    "direction_label": "LIFO Contract: Push and Pop occur exclusively at the TOP element in O(1) time",
                    "layers": [
                        {"title": "Element [40] (Top of Stack)", "description": "Active element at top pointer. Next candidate for Pop operation in O(1) time.", "tag": "TOP", "pointer": "Top ->", "status": "top"},
                        {"title": "Element [30]", "description": "Intermediate stack frame waiting for upper elements to be popped.", "tag": "SLOT 2", "status": "normal"},
                        {"title": "Element [20]", "description": "Intermediate stack frame stored in contiguous or linked node memory.", "tag": "SLOT 1", "status": "normal"},
                        {"title": "Element [10] (Base of Stack)", "description": "First element pushed onto the stack. Last element to ever be popped.", "tag": "BASE", "pointer": "Base", "status": "accent"}
                    ]
                },
                "text": "In-Memory Stack Visual",
                "transition": "zoom"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of a clean Stack class in Python. Using an underlying dynamic array, append implements constant amortized push, while pop removes the terminal element. Boundary guards prevent underflow exceptions on empty reads.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "Python Stack Implementation",
                    "language": "python",
                    "code": "class Stack:\n    def __init__(self):\n        self._items = []\n\n    def push(self, item):\n        self._items.append(item)  # O(1) amortized\n\n    def pop(self):\n        if self.is_empty():\n            raise IndexError('pop from empty stack')\n        return self._items.pop()  # O(1)\n\n    def peek(self):\n        if self.is_empty():\n            raise IndexError('peek at empty stack')\n        return self._items[-1]    # O(1)\n\n    def is_empty(self):\n        return len(self._items) == 0"
                },
                "text": "Stack Class Implementation",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Stacks excel in nested syntax validation and expression parsing. As tokens stream through the pipeline, opening brackets push onto the stack. On each closing bracket, the top token pops and matches against its expected pair.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Expression Parsing Pipeline",
                    "stages": [
                        {"label": "1. Token Ingestion", "subtitle": "Scan syntax string character by character", "badge": "Scan", "icon": "📝", "status": "normal"},
                        {"label": "2. Push Operands", "subtitle": "Push opening brackets onto top of stack", "badge": "Push", "icon": "📥", "status": "normal"},
                        {"label": "3. Pop & Validate", "subtitle": "Pop top element on closing bracket match", "badge": "Pop", "icon": "⚙️", "status": "normal"},
                        {"label": "4. Balanced State", "subtitle": "Empty stack confirms syntax validity", "badge": "Result", "icon": "✅", "status": "normal"}
                    ],
                    "highlight_label": "Validation Complexity: O(N) Time, O(N) Space"
                },
                "text": "Bracket Validation Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Contrast the stack against the queue. A stack enforces Last-In, First-Out order with all mutations at the top, powering call stacks and backtracking. A queue enforces First-In, First-Out order with additions at the rear and removals at the front.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Stack (LIFO)",
                    "left_desc": "Last-In, First-Out. Push and pop occur exclusively at the single top pointer. Powers function call stacks, undo buffers, and depth-first search.",
                    "right_title": "Queue (FIFO)",
                    "right_desc": "First-In, First-Out. Elements enqueue at the rear and dequeue from the front. Powers process scheduling, print queues, and breadth-first search."
                },
                "text": "Stack LIFO vs Queue FIFO",
                "transition": "fade"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Review the trade-offs between array-based and linked-list-based stack implementations. Dynamic array stacks offer high CPU cache locality and amortized O of 1 time, while linked lists guarantee strict O of 1 time with higher pointer overhead.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Stack Implementation Trade-offs",
                    "leftHeader": "Dynamic Array Stack",
                    "rightHeader": "Linked List Stack",
                    "rows": [
                        {"feature": "Push Time", "left": "O(1) Amortized", "right": "O(1) Strict"},
                        {"feature": "Pop Time", "left": "O(1) Strict", "right": "O(1) Strict"},
                        {"feature": "Memory Overhead", "left": "Low (contiguous buffer)", "right": "High (pointer per node)"},
                        {"feature": "Cache Locality", "left": "High (L1/L2 friendly)", "right": "Low (heap allocated nodes)"}
                    ]
                },
                "text": "Implementation Complexity Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior engineering invariants: always guard against stack underflow before popping; monitor thread stack depth to avoid stack overflow crashes; and leverage monotonic stacks to solve next-greater-element queries in linear time.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Underflow Boundary Guard: Always verify is_empty() is False before popping or peeking to prevent runtime index exceptions.",
                        "Call Stack Frame Bounds: Keep recursion depth within limits or convert deep recursion to explicit heap-allocated stacks to avoid stack overflow.",
                        "Monotonic Stack Optimization: Maintain elements in strictly monotonic increasing or decreasing order to compute nearest greater/smaller values in O(N) time."
                    ]
                },
                "text": "Senior Stack Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.7 DATA STRUCTURES & ALGORITHMS: QUEUES & FIFO DATA STRUCTURES
    # -------------------------------------------------------------
    elif domain == "dsa_queues":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this comprehensive algorithmic lecture on {lesson_title}. Today we analyze the queue data structure, governed strictly by the First-In, First-Out or FIFO principle, where items enter at the rear and exit from the front.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "First-In, First-Out (FIFO) • O(1) Enqueue & Dequeue Primitives"},
                "text": "Queue Architectural Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Queue operations follow a strict two-pointer protocol. Enqueue appends an item to the rear pointer. Dequeue removes and returns the front item. Front queries allow peeking at the next eligible element without removing it.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Enqueue Operation", "desc": "Insert element at the rear pointer and advance rear index in O(1) time."},
                        {"title": "2. Dequeue Operation", "desc": "Retrieve element at the front pointer, advance front, and return in O(1) time."},
                        {"title": "3. Front / Peek Query", "desc": "Inspect the line leader at the front pointer without mutating queue state."}
                    ]
                },
                "text": "Core Queue Operations",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Observe the horizontal queue data structure in action. Item 10 sits at the front with the active front pointer, ready to dequeue. Incoming elements like item 40 enter at the rear pointer. The sequence moves strictly from rear to front in First-In, First-Out order.",
                "visual_type": "queue_structure",
                "visual_data": {
                    "title": "FIFO Queue Data Structure Architecture",
                    "items": [
                        {"value": "Item [10]", "label": "Front / Dequeue", "status": "front", "index": 0},
                        {"value": "Item [20]", "label": "Slot 1 (Waiting)", "status": "normal", "index": 1},
                        {"value": "Item [30]", "label": "Slot 2 (Waiting)", "status": "normal", "index": 2},
                        {"value": "Item [40]", "label": "Rear / Enqueue", "status": "rear", "index": 3}
                    ],
                    "status": "FIFO Contract: First-In, First-Out • O(1) Dequeue at Front, O(1) Enqueue at Rear"
                },
                "text": "FIFO Queue Structure",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of a Queue in Python. Using collections.deque provides an internal doubly-linked block array, guaranteeing true O of 1 push and pop on both ends without memory reallocation shifts.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "Python Queue Implementation",
                    "language": "python",
                    "code": "from collections import deque\n\nclass Queue:\n    def __init__(self):\n        self._items = deque()\n\n    def enqueue(self, item):\n        self._items.append(item)      # O(1) append to rear\n\n    def dequeue(self):\n        if self.is_empty():\n            raise IndexError('dequeue from empty queue')\n        return self._items.popleft()  # O(1) remove from front\n\n    def front(self):\n        if self.is_empty():\n            raise IndexError('front on empty queue')\n        return self._items[0]         # O(1) peek front\n\n    def is_empty(self):\n        return len(self._items) == 0"
                },
                "text": "Python Queue Implementation",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "To implement a queue in a fixed-size array without shifting elements, we use a circular ring buffer. Modulo arithmetic wraps rear and front pointers around the capacity boundary, maintaining constant time performance without memory waste.",
                "visual_type": "cycle_loop",
                "visual_data": {
                    "title": "Circular Ring Buffer Mechanics",
                    "center_label": "Modulo Math",
                    "stages": [
                        {"title": "1. Rear Advance", "desc": "rear = (rear + 1) % capacity on enqueue", "icon": "🔄"},
                        {"title": "2. Buffer Write", "desc": "Write element into ring slot array[rear]", "icon": "✍️"},
                        {"title": "3. Front Advance", "desc": "front = (front + 1) % capacity on dequeue", "icon": "⏩"},
                        {"title": "4. Wrap-Around", "desc": "Modulo math wraps pointers smoothly to index 0", "icon": "🔁"}
                    ]
                },
                "text": "Circular Buffer Wrap-Around",
                "transition": "zoom"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Compare naive array queues with circular buffers. A naive array requires shifting all N elements left upon dequeue, causing an O of N bottleneck. A circular ring buffer or linked list decouples front and rear, achieving true O of 1 dequeue.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Naive Array Queue",
                    "left_desc": "Popping from index 0 forces an O(N) element shift across the entire array, creating massive latency on large datasets.",
                    "right_title": "Circular Buffer / Deque",
                    "right_desc": "Front and rear pointers advance via modulo index math (index + 1) % N, guaranteeing O(1) operations with zero memory shifts."
                },
                "text": "Array Queue vs Circular Buffer",
                "transition": "fade"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Review the asymptotic complexity profile across queue architectures. While all implementations enqueue in O of 1 time, only circular buffers and linked lists achieve O of 1 dequeue without memory reallocation penalties.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Queue Architecture Complexity Matrix",
                    "leftHeader": "Linear Array Queue",
                    "rightHeader": "Circular Ring Buffer",
                    "rows": [
                        {"feature": "Enqueue Time", "left": "O(1) Amortized", "right": "O(1) Strict"},
                        {"feature": "Dequeue Time", "left": "O(N) Shift Bottleneck", "right": "O(1) Strict"},
                        {"feature": "Space Overhead", "left": "O(1) contiguous", "right": "O(1) fixed ring"},
                        {"feature": "Cache Locality", "left": "High", "right": "Maximum (fixed array)"}
                    ]
                },
                "text": "Queue Complexity Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior engineering invariants: breadth-first search relies strictly on FIFO queues for shortest paths; circular buffers prevent memory fragmentation in network IO; and rate limiters use leaky-bucket queues to smooth bursty traffic.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Breadth-First Search Invariant: FIFO queues guarantee nodes are visited in strict non-decreasing order of distance from the source.",
                        "Network Buffer Sizing: Fixed ring buffers prevent memory fragmentation and thread contention in high-throughput network packet drivers.",
                        "Concurrency Thread Safety: Use synchronized blocking queues with condition variables to safely coordinate producer-consumer workloads."
                    ]
                },
                "text": "Senior Queue Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.8 DATA STRUCTURES & ALGORITHMS: HEAPS & PRIORITY QUEUES
    # -------------------------------------------------------------
    elif domain == "dsa_heaps":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this advanced algorithmic lecture on {lesson_title}. Today we master the binary heap and priority queue, the complete binary tree structure where every parent node satisfies the heap property relative to its children.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Priority Queues • Complete Binary Heaps & O(log N) Heapify"},
                "text": "Heap Architectural Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Observe the complete binary tree invariant of a min-heap. The root node holds the minimum key 10. Each child is greater than or equal to its parent, guaranteeing instant O of 1 access to the extreme element without maintaining full sorted order.",
                "visual_type": "tree_structure",
                "visual_data": {
                    "title": "Min-Heap Complete Binary Tree",
                    "root_label": "Min: 10",
                    "left_label": "Node: 25",
                    "right_label": "Node: 30",
                    "left_leaf_1": "Key 40",
                    "left_leaf_2": "Key 50",
                    "right_leaf_1": "Key 60",
                    "right_leaf_2": "Key 70",
                    "status": "Parent <= Children Invariant • O(1) Min Access"
                },
                "text": "Heap Tree Structure",
                "transition": "zoom"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Heaps require zero pointer overhead because a complete binary tree maps directly into a flat contiguous array. For any index i, the left child lives at 2i plus 1, the right child at 2i plus 2, and the parent at i minus 1 integer-divided by 2.",
                "visual_type": "array_memory",
                "visual_data": {
                    "title": "Contiguous Array Memory Representation",
                    "items": [
                        {"index": 0, "value": 10, "address": "Root", "status": "target"},
                        {"index": 1, "value": 25, "address": "2i+1", "status": "active"},
                        {"index": 2, "value": 30, "address": "2i+2", "status": "active"},
                        {"index": 3, "value": 40, "address": "Leaf", "status": "normal"},
                        {"index": 4, "value": 50, "address": "Leaf", "status": "normal"},
                        {"index": 5, "value": 60, "address": "Leaf", "status": "normal"}
                    ],
                    "pointers": [
                        {"label": "Root", "index": 0, "color": "#10b981"},
                        {"label": "Left", "index": 1, "color": "#38bdf8"},
                        {"label": "Right", "index": 2, "color": "#818cf8"}
                    ]
                },
                "text": "Flat Array Index Math",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of sift-up and sift-down mechanics in Python. Sift-up restores the invariant after insertion by bubbling smaller keys upward, while sift-down sinks replacement elements after extract-min.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "Python Min-Heap Sift Mechanics",
                    "language": "python",
                    "code": "class MinHeap:\n    def __init__(self):\n        self.heap = []\n\n    def push(self, val):\n        self.heap.append(val)\n        self._sift_up(len(self.heap) - 1)\n\n    def _sift_up(self, idx):\n        parent = (idx - 1) // 2\n        while idx > 0 and self.heap[idx] < self.heap[parent]:\n            self.heap[idx], self.heap[parent] = self.heap[parent], self.heap[idx]\n            idx = parent\n            parent = (idx - 1) // 2\n\n    def pop_min(self):\n        if not self.heap:\n            raise IndexError('pop from empty heap')\n        min_val = self.heap[0]\n        last = self.heap.pop()\n        if self.heap:\n            self.heap[0] = last\n            self._sift_down(0)\n        return min_val"
                },
                "text": "Heap Push & Pop Implementation",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Follow the three stages of element insertion. The new value enters at the end of the array to preserve tree completeness, compares against its parent, and swaps upward in at most log N iterations.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Append to Leaf", "desc": "Insert element at the terminal array index, maintaining the complete tree shape."},
                        {"title": "2. Parent Key Compare", "desc": "Compare new value against parent at index (i - 1) // 2."},
                        {"title": "3. Sift-Up Swap", "desc": "Swap with parent until heap invariant holds or element reaches the root in O(log N)."}
                    ]
                },
                "text": "Heapify Sift-Up Protocol",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Compare min-heaps with max-heaps and unsorted arrays. While an unsorted array allows O of 1 insertion, finding or extracting the minimum costs linear O of N time. A binary heap balances both operations at O of log N.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Unsorted Array Queue",
                    "left_desc": "O(1) fast insertion at tail, but extracting the minimum requires a full O(N) linear scan over every element.",
                    "right_title": "Binary Heap Priority Queue",
                    "right_desc": "Maintains partial heap order in O(log N) insert and extract-min, enabling scalable priority scheduling."
                },
                "text": "Unsorted Array vs Binary Heap",
                "transition": "fade"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Examine the priority queue complexity profile. Notice that building a heap from an arbitrary array of N elements takes linear O of N time using bottom-up heapify, significantly faster than N repeated insertions.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Priority Queue Complexity Profile",
                    "leftHeader": "Binary Heap",
                    "rightHeader": "Unsorted Array",
                    "rows": [
                        {"feature": "Find-Min / Peek", "left": "O(1) Strict", "right": "O(N) Scan"},
                        {"feature": "Extract-Min", "left": "O(log N)", "right": "O(N) Scan & Shift"},
                        {"feature": "Insert Element", "left": "O(log N)", "right": "O(1) Append"},
                        {"feature": "Build-Heap (N items)", "left": "O(N) Linear Time", "right": "O(N) Copy"}
                    ]
                },
                "text": "Heap Complexity Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior engineering invariants: complete binary trees eliminate pointer memory overhead; Dijkstra's shortest path algorithm relies on min-heaps for fast vertex relaxation; and streaming top-K queries use fixed-size heaps.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Compact Array Efficiency: Binary heaps use zero pointer links, maximizing hardware CPU L1 cache line prefetching.",
                        "Linear Build Heap: Always construct heaps using bottom-up heapify in O(N) time instead of N repeated push calls.",
                        "Streaming Top-K Pattern: Maintain a min-heap of size K to identify the top K largest elements across an infinite data stream in O(N log K) time."
                    ]
                },
                "text": "Senior Heap Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.9 DATA STRUCTURES & ALGORITHMS: GRAPHS & GRAPH ALGORITHMS
    # -------------------------------------------------------------
    elif domain == "dsa_graphs":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this advanced algorithmic masterclass on {lesson_title}. Today we explore graph theory, the mathematical and computational framework modeling complex relationships between discrete vertices connected by directed or undirected edges.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Graph Theory • Vertices, Weighted Edges & Traversal Invariants"},
                "text": "Graph Architectural Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Observe the topological graph network. The central source vertex connects to neighboring vertices via weighted edges. Graph traversal systematically discovers reachable nodes while tracking visited states to prevent infinite cyclic loops.",
                "visual_type": "concept_network",
                "visual_data": {
                    "title": "Graph Network Topology & Edge Weights",
                    "central_hub": "Source Vertex [A]",
                    "nodes": [
                        {"name": "Vertex [B] (Weight: 4)", "role": "Adjacent Frontier Node", "tag": "Neighbor", "icon": "🔵"},
                        {"name": "Vertex [C] (Weight: 2)", "role": "Relaxed Shortest Path Node", "tag": "Active", "icon": "🟢"},
                        {"name": "Vertex [D] (Weight: 7)", "role": "Unvisited Distant Node", "tag": "Pending", "icon": "🟡"},
                        {"name": "Vertex [E] (Weight: 1)", "role": "Direct High-Priority Target", "tag": "Target", "icon": "⚡"}
                    ]
                },
                "text": "Graph Network Topology",
                "transition": "zoom"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Trace the execution pipeline of Dijkstra's algorithm. The source vertex initializes distances, pushes into a priority queue, pops the minimum-distance candidate, and relaxes all outgoing edges until the shortest path tree is finalized.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Shortest Path Relaxation Pipeline",
                    "stages": [
                        {"label": "1. Init Distances", "subtitle": "Set dist[source]=0, others=inf", "badge": "Init", "icon": "📍", "status": "normal"},
                        {"label": "2. Extract Min Node", "subtitle": "Pop lowest-distance vertex from min-heap", "badge": "Extract", "icon": "⚡", "status": "normal"},
                        {"label": "3. Edge Relaxation", "subtitle": "if dist[u] + w < dist[v]: update dist[v]", "badge": "Relax", "icon": "⚙️", "status": "normal"},
                        {"label": "4. Finalized Path", "subtitle": "Mark visited & record predecessor", "badge": "Done", "icon": "✅", "status": "normal"}
                    ],
                    "highlight_label": "Dijkstra Complexity: O((V + E) log V)"
                },
                "text": "Dijkstra Traversal Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of Breadth-First Search using an adjacency list. A FIFO queue maintains the search frontier, while a visited set guarantees each vertex and edge is evaluated exactly once.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "Python Graph BFS Implementation",
                    "language": "python",
                    "code": "from collections import deque\n\ndef bfs(graph, start_vertex):\n    visited = {start_vertex}\n    queue = deque([start_vertex])\n    traversal_order = []\n\n    while queue:\n        curr = queue.popleft()\n        traversal_order.append(curr)\n\n        for neighbor in graph.get(curr, []):\n            if neighbor not in visited:\n                visited.add(neighbor)\n                queue.append(neighbor)\n\n    return traversal_order"
                },
                "text": "Python Graph Traversal Code",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Graph exploration follows three deterministic phases. First, initialize the frontier data structure. Second, dequeue the next candidate vertex. Third, explore unvisited outgoing edges and update state properties.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Frontier Initialization", "desc": "Push start vertex into FIFO queue (BFS) or LIFO stack (DFS) with visited marker."},
                        {"title": "2. Node Extraction", "desc": "Pop the current vertex and record its visitation in the traversal tree."},
                        {"title": "3. Neighbor Exploration", "desc": "Inspect all adjacent edges; prune already visited nodes to prevent cycles."}
                    ]
                },
                "text": "Graph Traversal Mechanics",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Compare adjacency lists with adjacency matrices. An adjacency list uses O of V plus E memory, ideal for sparse graphs. An adjacency matrix consumes quadratic O of V squared memory, but checks edge existence in instant constant time.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Adjacency List (Sparse)",
                    "left_desc": "O(V + E) space. Iterating neighbors is optimal for real-world sparse networks like web pages and social graphs.",
                    "right_title": "Adjacency Matrix (Dense)",
                    "right_desc": "O(V^2) space. Allows O(1) edge existence queries, but wastes significant memory when graphs have few edges."
                },
                "text": "Adjacency List vs Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Review the algorithm complexity matrix across core graph algorithms. BFS and DFS operate in linear O of V plus E time, Dijkstra finds non-negative shortest paths in O of E log V, and Bellman-Ford detects negative weight cycles.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Graph Algorithm Complexity Profile",
                    "leftHeader": "Algorithm & Paradigm",
                    "rightHeader": "Time Complexity & Constraints",
                    "rows": [
                        {"feature": "Breadth-First Search (BFS)", "left": "Unweighted Shortest Path", "right": "O(V + E) with FIFO Queue"},
                        {"feature": "Depth-First Search (DFS)", "left": "Cycle Detection & TopoSort", "right": "O(V + E) with Call Stack"},
                        {"feature": "Dijkstra's Algorithm", "left": "Weighted Non-Negative Path", "right": "O((V + E) log V) with Min-Heap"},
                        {"feature": "Bellman-Ford Algorithm", "left": "Negative Weights & Cycles", "right": "O(V * E) Dynamic Programming"}
                    ]
                },
                "text": "Graph Algorithm Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior engineering invariants: topological sort requires a directed acyclic graph with no cycles; Disjoint Set Union with path compression achieves near-constant time in Kruskal's MST; and visited sets are mandatory to prevent infinite loops.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Topological Sort DAG Invariant: Build systems and task dependencies require a Directed Acyclic Graph (DAG); cycle detection prevents infinite build loops.",
                        "Union-Find Near-Constant Time: Disjoint Set Union (DSU) with union-by-rank and path compression runs in nearly O(1) inverse Ackermann time for Kruskal MST.",
                        "Visited Tracking Invariant: Always maintain an explicit visited hash set to guarantee traversal terminates on graphs containing cyclic back-edges."
                    ]
                },
                "text": "Senior Graph Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.10 DATA STRUCTURES & ALGORITHMS: HASHING & HASH TABLES
    # -------------------------------------------------------------
    elif domain == "dsa_hashing":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this core algorithmic lecture on {lesson_title}. Today we master the hash table, the foundational data structure providing average constant time O of 1 key-value lookups, insertions, and deletions via hash function address mapping.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Hash Tables • O(1) Key-Value Mapping & Collision Resolution"},
                "text": "Hash Table Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Observe the hash function execution pipeline. A string key passes into a hash function, producing a large integer hash code. Modulo compression maps that code into a valid bucket index within the physical array.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Hash Function Execution Pipeline",
                    "stages": [
                        {"label": "1. Key String", "subtitle": "Arbitrary key: 'user_102'", "badge": "Key", "icon": "🔑", "status": "normal"},
                        {"label": "2. Hash Computation", "subtitle": "hash('user_102') -> 8392104", "badge": "Hash", "icon": "⚙️", "status": "normal"},
                        {"label": "3. Modulo Capacity", "subtitle": "8392104 % TableSize(8) -> 4", "badge": "Compress", "icon": "📐", "status": "normal"},
                        {"label": "4. Bucket Array", "subtitle": "Write payload to Bucket[4]", "badge": "Storage", "icon": "💾", "status": "normal"}
                    ],
                    "highlight_label": "Direct Addressing: O(1) Average Lookup"
                },
                "text": "Hash Function Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Inspect the bucket array in memory. Each bucket represents an indexed memory slot. When different keys hash to the same bucket index, a collision occurs, requiring chaining or open addressing to resolve.",
                "visual_type": "array_memory",
                "visual_data": {
                    "title": "Hash Table Bucket Array Memory",
                    "items": [
                        {"index": 0, "value": "Empty", "address": "0x00", "status": "eliminated"},
                        {"index": 1, "value": "K: 'alice'", "address": "0x08", "status": "normal"},
                        {"index": 2, "value": "K: 'bob'", "address": "0x10", "status": "active"},
                        {"index": 3, "value": "Empty", "address": "0x18", "status": "eliminated"},
                        {"index": 4, "value": "Collision", "address": "0x20", "status": "target"},
                        {"index": 5, "value": "K: 'dave'", "address": "0x28", "status": "normal"}
                    ],
                    "pointers": [
                        {"label": "Slot 2", "index": 2, "color": "#38bdf8"},
                        {"label": "Collision", "index": 4, "color": "#f59e0b"}
                    ]
                },
                "text": "Bucket Array & Collision",
                "transition": "zoom"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of a Separate Chaining hash map in Python. Each bucket stores a list of key-value tuples. On lookup, we find the bucket via modulo math and linearly scan the short chain.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "Separate Chaining Hash Map Implementation",
                    "language": "python",
                    "code": "class HashMap:\n    def __init__(self, capacity=8):\n        self.capacity = capacity\n        self.buckets = [[] for _ in range(capacity)]\n        self.size = 0\n\n    def put(self, key, value):\n        idx = hash(key) % self.capacity\n        bucket = self.buckets[idx]\n        for i, (k, v) in enumerate(bucket):\n            if k == key:\n                bucket[i] = (key, value)\n                return\n        bucket.append((key, value))\n        self.size += 1\n\n    def get(self, key):\n        idx = hash(key) % self.capacity\n        for k, v in self.buckets[idx]:\n            if k == key:\n                return v\n        raise KeyError(key)"
                },
                "text": "Chaining Hash Map Code",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Follow the collision resolution workflow. First, compute the bucket index. If a key collision occurs, separate chaining links the new item, while open addressing probes consecutive slots. When the load factor exceeds threshold, the table rehashes.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Compute Hash Index", "desc": "Run hash(key) % capacity to identify the target bucket slot."},
                        {"title": "2. Collision Handling", "desc": "Separate chaining links nodes; linear probing scans next vacant index."},
                        {"title": "3. Load Factor Rehashing", "desc": "When size / capacity > 0.75, double capacity and rehash all keys."}
                    ]
                },
                "text": "Collision & Rehashing Flow",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Compare separate chaining with open addressing. Separate chaining handles high load factors gracefully without table degradation. Open addressing achieves superior CPU cache locality but suffers from clustering when load exceeds 70 percent.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Separate Chaining",
                    "left_desc": "Each bucket points to a linked list. Never runs out of slots, handles collisions gracefully, but incurs heap pointer overhead.",
                    "right_title": "Open Addressing (Linear Probing)",
                    "right_desc": "All keys reside directly in the flat bucket array. Maximizes CPU cache locality, but degrades rapidly if clustering occurs."
                },
                "text": "Chaining vs Open Addressing",
                "transition": "fade"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Review the comparative trade-offs between Hash Tables, Balanced Binary Search Trees, and Arrays. While hash tables deliver unmatched O of 1 average lookups, balanced trees guarantee O of log N worst-case times and maintain sorted key order.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Lookup Data Structure Comparison Matrix",
                    "leftHeader": "Hash Table (Average)",
                    "rightHeader": "Balanced BST (Worst Case)",
                    "rows": [
                        {"feature": "Search Time", "left": "O(1) Constant", "right": "O(log N) Guaranteed"},
                        {"feature": "Insertion Time", "left": "O(1) Amortized", "right": "O(log N)"},
                        {"feature": "Deletion Time", "left": "O(1) Constant", "right": "O(log N)"},
                        {"feature": "Sorted Order", "left": "Unordered (Hash dependent)", "right": "Strictly In-Order"}
                    ]
                },
                "text": "Hash Table Complexity Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior engineering invariants: maintain the load factor below 0.75 to prevent O of N chain degradation; use uniform hashing functions to prevent hash flooding attacks; and immutable keys are mandatory for consistent hash codes.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Load Factor Threshold (0.75): Dynamically double the bucket array and rehash all keys when the load factor reaches 0.75 to preserve O(1) time.",
                        "Key Immutability Invariant: Keys must never mutate their hash-dependent attributes while stored in a hash table, or lookups will fail.",
                        "Hash DoS Defense: Production web servers use randomized hash seeds (like SipHash) to defend against adversarial worst-case collision attacks."
                    ]
                },
                "text": "Senior Hashing Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.11 DATA STRUCTURES & ALGORITHMS: DYNAMIC PROGRAMMING (DP)
    # -------------------------------------------------------------
    elif domain == "dsa_dp":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this advanced algorithmic masterclass on {lesson_title}. Today we unpack Dynamic Programming, the optimization technique that transforms exponential brute-force algorithms into polynomial solutions by caching solutions to overlapping subproblems.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Dynamic Programming • Optimal Substructure & Overlapping Subproblems"},
                "text": "Dynamic Programming Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Every dynamic programming solution rests upon four foundational pillars. First, define the state representation. Second, derive the recurrence relation. Third, initialize base cases. Fourth, determine the computation order.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. State Space Definition", "desc": "Define dp[i] or dp[i][w] to represent the optimal answer for a subproblem of size i."},
                        {"title": "2. Recurrence Relation", "desc": "Express optimal answer dp[i] as a function of previously solved subproblems."},
                        {"title": "3. Base Cases & Order", "desc": "Initialize known terminal conditions and establish topological calculation order."}
                    ]
                },
                "text": "The 4 DP Pillars",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Observe the power of memoization in the recursion tree. Naive recursion repeatedly computes identical subproblems like fib of 3 across multiple branches, exploding into O of 2 to the N work. Memoization intercepts duplicate calls and returns stored results in O of 1 time.",
                "visual_type": "tree_structure",
                "visual_data": {
                    "title": "Recursion Tree with Subproblem Memoization",
                    "root_label": "fib(5)",
                    "left_label": "fib(4)",
                    "right_label": "fib(3) [Pruned]",
                    "left_leaf_1": "fib(3)",
                    "left_leaf_2": "fib(2) [Pruned]",
                    "right_leaf_1": "Cached",
                    "right_leaf_2": "Cached",
                    "status": "Overlapping Subproblems Pruned: O(2^N) -> O(N)"
                },
                "text": "Recursion Tree Pruning",
                "transition": "zoom"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of the 0/1 Knapsack problem in Python using bottom-up tabulation. For each item and weight capacity, we evaluate whether to exclude the item or include it to maximize total value.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "0/1 Knapsack Tabulation Implementation",
                    "language": "python",
                    "code": "def knapsack(weights, values, capacity):\n    n = len(weights)\n    dp = [[0] * (capacity + 1) for _ in range(n + 1)]\n\n    for i in range(1, n + 1):\n        w_i, v_i = weights[i - 1], values[i - 1]\n        for w in range(capacity + 1):\n            if w_i <= w:\n                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - w_i] + v_i)\n            else:\n                dp[i][w] = dp[i - 1][w]\n\n    return dp[n][capacity]"
                },
                "text": "Knapsack DP Implementation",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Examine the dynamic programming state grid. Each row builds strictly upon the previous row. By caching subproblem answers, we avoid all recomputation, solving the problem in pseudo-polynomial time proportional to N times capacity.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Knapsack State Transition Grid dp[i][w]",
                    "leftHeader": "Subproblem State",
                    "rightHeader": "Optimal Substructure Decision",
                    "rows": [
                        {"feature": "Capacity w = 1", "left": "Exclude item: dp[i-1][1]", "right": "Include: dp[i-1][1 - w_i] + v_i"},
                        {"feature": "Capacity w = 2", "left": "Exclude item: dp[i-1][2]", "right": "Include: dp[i-1][2 - w_i] + v_i"},
                        {"feature": "Capacity w = 3", "left": "Exclude item: dp[i-1][3]", "right": "Include: dp[i-1][3 - w_i] + v_i"},
                        {"feature": "Target w = W", "left": "Previous optimal prefix", "right": "Global Optimal Value at dp[N][W]"}
                    ]
                },
                "text": "DP State Grid & Recurrence",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Compare top-down memoization with bottom-up tabulation. Top-down recursion is intuitive and only solves reachable subproblems, but risks stack overflow. Bottom-up tabulation iteratively fills tables without call stack overhead, enabling rolling-array space optimization.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Top-Down Memoization",
                    "left_desc": "Recursive descent caching subproblem returns in a hash map. Solves only reachable states, but incurs function call stack frame overhead.",
                    "right_title": "Bottom-Up Tabulation",
                    "right_desc": "Iterative loop filling state tables in topological order. Zero recursion overhead, cache-friendly, and allows space reduction to O(W)."
                },
                "text": "Top-Down vs Bottom-Up DP",
                "transition": "fade"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Review the asymptotic complexity contrast. Brute-force exponential recursion demands O of 2 to the N operations, while dynamic programming condenses the solution into O of N times W polynomial time.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Algorithmic Efficiency Profile: Naive vs DP",
                    "leftHeader": "Naive Exponential Recursion",
                    "rightHeader": "Dynamic Programming (Tabulation)",
                    "rows": [
                        {"feature": "Time Complexity", "left": "O(2^N) Exponential", "right": "O(N * W) Polynomial"},
                        {"feature": "Subproblem Calls", "left": "Repeated Duplicate Branches", "right": "Evaluated Exactly Once"},
                        {"feature": "Space Footprint", "left": "O(N) Call Stack", "right": "O(W) with Rolling Array"},
                        {"feature": "Feasibility on N=50", "left": "Trillions of Years (Crash)", "right": "Less than 1 Millisecond"}
                    ]
                },
                "text": "Complexity Profile Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior engineering invariants: confirm optimal substructure before applying DP; optimize memory footprint from 2D grids to 1D rolling arrays when only previous states are needed; and recognize that all DP problems represent shortest paths in DAGs.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Optimal Substructure Invariant: An optimal solution to the problem must contain optimal solutions to its constituent subproblems.",
                        "Space Optimization via Rolling Arrays: If state dp[i] depends solely on row dp[i-1], reduce memory from O(N * W) to O(W) using a single 1D array.",
                        "DAG Formulation: Every dynamic programming problem is fundamentally finding the shortest or longest path in a Directed Acyclic Graph."
                    ]
                },
                "text": "Senior DP Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.12 DATA STRUCTURES & ALGORITHMS: MEMORY MODEL, POINTERS & ALLOCATION
    # -------------------------------------------------------------
    elif domain == "dsa_memory_pointers":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this systems programming masterclass on {lesson_title}. Today we examine how software maps directly onto physical silicon, contrasting the fast linear stack against dynamic heap allocation, and demystifying memory addresses and pointer dereferencing.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Memory Architecture • Stack Frames, Heap Pointers & Reference Semantics"},
                "text": "Memory Architecture Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Program execution manages memory through three coordinated mechanisms: allocating local stack frames for function scopes, requesting dynamic memory blocks from the runtime heap manager, and dereferencing pointer addresses to read or mutate underlying data.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Stack Frame Allocation", "desc": "Compiler pushes activation record containing local primitives and pointers onto the thread call stack."},
                        {"title": "2. Dynamic Heap Request", "desc": "Runtime allocator (malloc / new) finds free memory blocks and returns raw starting byte address."},
                        {"title": "3. Pointer Dereferencing", "desc": "CPU follows memory address held in pointer register to access or mutate the target data payload."}
                    ]
                },
                "text": "Memory Lifecycle & Dereferencing",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Observe the contiguous memory address space. At address 0x1000, pointer ptr stores value 0x1008. When our program dereferences ptr, the processor jumps directly to address 0x1008 to retrieve the integer payload 42. Notice each cell has an explicit hexadecimal address and byte offset.",
                "visual_type": "array_memory",
                "visual_data": {
                    "title": "Address Space & Pointer Dereference Trace",
                    "cells": [
                        {"index": "0x1000", "value": "0x1008", "label": "ptr (Address)", "status": "pivot"},
                        {"index": "0x1004", "value": "0x0000", "label": "Padding", "status": "normal"},
                        {"index": "0x1008", "value": "42", "label": "*ptr (Payload)", "status": "found"},
                        {"index": "0x100C", "value": "100", "label": "stack_var", "status": "normal"}
                    ],
                    "status": "Dereference Path: ptr holds address 0x1008 -> *ptr resolves to value 42 in O(1) memory cycle"
                },
                "text": "Contiguous Memory & Pointer Map",
                "transition": "zoom"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is clean implementation code demonstrating pointers and pass-by-reference semantics. Notice how passing by value creates a copied duplicate, while passing a pointer or reference mutates the original caller state in place without reallocation overhead.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "Pointers & Pass-by-Reference Implementation",
                    "language": "python",
                    "code": "# Python passes object references by value (call-by-object-reference)\ndef modify_state(primitive_val: int, container: list):\n    # 1. Primitives are immutable: rebinding creates new local reference\n    primitive_val = primitive_val + 10  # Does NOT affect caller\n\n    # 2. Containers are mutable: dereferencing mutates caller object\n    container.append(99)                # Caller state MUTATED\n\nval = 5\ndata = [1, 2, 3]\nmodify_state(val, data)\nprint(f'val: {val}, data: {data}')  # Output: val: 5, data: [1, 2, 3, 99]"
                },
                "text": "Reference Mutability Implementation",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing the execution pipeline reveals the lifetime transitions of memory management: stack variables allocate instantly via stack-pointer decrements, heap objects require allocator search, pointer indirection resolves addresses, and scope teardown reclaims stack frames automatically.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Memory Allocation & Dereference Pipeline",
                    "stages": [
                        {"label": "1. Stack Frame", "subtitle": "SP register bump", "badge": "O(1) Init", "icon": "⚡", "status": "normal"},
                        {"label": "2. Heap Alloc", "subtitle": "malloc / new block", "badge": "Runtime", "icon": "📦", "status": "normal"},
                        {"label": "3. Dereference", "subtitle": "Follow pointer address", "badge": "Lookup", "icon": "🎯", "status": "normal"},
                        {"label": "4. Scope Teardown", "subtitle": "RAII stack unwind / GC", "badge": "Cleanup", "icon": "🧹", "status": "normal"}
                    ],
                    "highlight_label": "Stack Allocation is instantaneous (single CPU instruction), Heap requires fragmentation management."
                },
                "text": "Memory Execution Lifecycle",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing stack memory against dynamic heap memory exposes architectural trade-offs: stack allocation is blazing fast and deterministic via RAII scope boundaries, whereas heap memory provides dynamic sizing and arbitrary lifetimes at the expense of fragmentation and pointer overhead.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Stack Memory Allocation",
                    "left_desc": "Fixed-size, contiguous frames allocated via single CPU pointer movement; automatic scope cleanup (RAII); blazing L1/L2 cache locality; risk of stack overflow on deep recursion.",
                    "right_title": "Dynamic Heap Allocation",
                    "right_desc": "Flexible, runtime-sized blocks with arbitrary lifetimes; requires manual deallocation or garbage collection; fragmentation risk; indirection overhead via pointer lookups."
                },
                "text": "Stack Allocation vs Dynamic Heap",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "This architectural comparison matrix contrasts the key performance dimensions. Stack allocations operate in O of 1 time with zero fragmentation, while heap management requires search overhead and introduces safety hazards like memory leaks and dangling pointers.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Memory Architecture Matrix",
                    "headers": ["Metric Dimension", "Stack Memory", "Heap Memory"],
                    "rows": [
                        {"label": "Allocation Speed", "val1": "O(1) CPU Instruction", "val2": "O(log N) to O(N) Allocator Search"},
                        {"label": "Lifetime & Scope", "val1": "Deterministic Scope (RAII)", "val2": "Manual (free) or Garbage Collector"},
                        {"label": "Memory Layout", "val1": "Contiguous (Optimal Cache)", "val2": "Fragmented Virtual Address Space"},
                        {"label": "Access Pattern", "val1": "Direct Stack Pointer Offset", "val2": "Indirect Pointer Dereference"},
                        {"label": "Primary Risk", "val1": "Stack Overflow", "val2": "Memory Leaks & Dangling Pointers"}
                    ]
                },
                "text": "Memory Architecture Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, master three senior engineering memory invariants: adhere to RAII to tie resource lifecycles strictly to stack scopes, guard against pointer aliasing in hot inner loops, and organize data contiguously to maximize CPU cache line prefetching.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "RAII Invariant: Always bind heap allocations, file handles, and locks to the lifetime of stack-allocated objects for deterministic cleanup.",
                        "Spatial Locality Principle: Contiguous array layouts saturate 64-byte L1 cache lines, whereas scattered pointer-chasing structures induce heavy cache miss penalties.",
                        "Pointer Safety Boundary: Never return raw pointer addresses of stack-allocated local variables after function scope teardown."
                    ]
                },
                "text": "Senior Memory Architecture Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.13 DATA STRUCTURES & ALGORITHMS: BITWISE OPERATIONS & BITMASKS
    # -------------------------------------------------------------
    elif domain == "dsa_bitwise":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this low-level computational masterclass on {lesson_title}. Today we delve beneath software abstractions into raw bits, exploring bitwise operators, masks, and how manipulating individual bits achieves single-cycle ALU execution speeds.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Bitwise Operations • Bitmasks, Shifting & Low-Level ALU Speed"},
                "text": "Bitwise & Bitmask Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Bitwise mastery is built upon three foundational primitives: inspecting state via bitwise AND, toggling or setting flags via bitwise OR and XOR, and multiplying or dividing powers of two instantaneously through arithmetic bit shifts.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Bitwise Masking (AND)", "desc": "Filter specific bits using a mask: (x & (1 << k)) isolates the k-th bit flag in O(1) time."},
                        {"title": "2. Flag Setting & Toggling", "desc": "Set bits using OR (x | mask); toggle bits using XOR (x ^ mask); clear bits using NOT (x & ~mask)."},
                        {"title": "3. Binary Bit Shifting", "desc": "Left shift (x << k) multiplies by 2^k; right shift (x >> k) divides by 2^k in a single clock cycle."}
                    ]
                },
                "text": "Core Bit Manipulation Primitives",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Observe the 8-bit register representation. Bits 7 down to 0 form an integer value. Applying mask 0000 0100 isolates bit 2 in constant time. Bit shifting aligns flags to the least significant bit for instant boolean evaluation without branching.",
                "visual_type": "array_memory",
                "visual_data": {
                    "title": "8-Bit Register Layout & Bitmask Evaluation",
                    "cells": [
                        {"index": "Bit 7", "value": "0", "label": "Sign / MSB", "status": "normal"},
                        {"index": "Bit 6", "value": "1", "label": "Flag 6", "status": "normal"},
                        {"index": "Bit 5", "value": "0", "label": "Flag 5", "status": "normal"},
                        {"index": "Bit 4", "value": "1", "label": "Flag 4", "status": "normal"},
                        {"index": "Bit 3", "value": "0", "label": "Flag 3", "status": "normal"},
                        {"index": "Bit 2", "value": "1", "label": "Target Flag", "status": "pivot"},
                        {"index": "Bit 1", "value": "0", "label": "Flag 1", "status": "normal"},
                        {"index": "Bit 0", "value": "1", "label": "LSB (2^0)", "status": "found"}
                    ],
                    "status": "Register Value: 0b01010101 (85) • Mask (1 << 2) isolates Bit 2 = 1 in 1 CPU cycle"
                },
                "text": "8-Bit Register & Bitmask Ribbon",
                "transition": "zoom"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of standard bit manipulation idioms. Notice Brian Kernighan's algorithm for counting set bits in O of K time, along with clean helper functions for setting, clearing, and testing arbitrary bit flags.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "Bitmask Utility Implementation",
                    "language": "python",
                    "code": "class Bitmask:\n    @staticmethod\n    def test_bit(x: int, k: int) -> bool:\n        return (x & (1 << k)) != 0\n\n    @staticmethod\n    def set_bit(x: int, k: int) -> int:\n        return x | (1 << k)\n\n    @staticmethod\n    def clear_bit(x: int, k: int) -> int:\n        return x & ~(1 << k)\n\n    @staticmethod\n    def count_set_bits(n: int) -> int:\n        # Brian Kernighan's Algorithm: runs in O(k) where k = set bits\n        count = 0\n        while n > 0:\n            n = n & (n - 1)  # Clears the lowest set bit\n            count += 1\n        return count"
                },
                "text": "Bit Manipulation Primitives Code",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing the bitwise execution pipeline illustrates how multi-flag states compress into an integer: raw status signals enter the ALU, apply bitwise masks in parallel, undergo single-cycle shift operations, and resolve complex permission matrices with zero branch misprediction penalties.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Bitwise ALU Execution Pipeline",
                    "stages": [
                        {"label": "1. Integer Input", "subtitle": "Compact 32/64-bit integer", "badge": "Input", "icon": "🔢", "status": "normal"},
                        {"label": "2. Mask AND / OR", "subtitle": "Single-cycle bitmask logic", "badge": "ALU", "icon": "⚡", "status": "normal"},
                        {"label": "3. Bit Shift", "subtitle": "Arith / Logical shift << >>", "badge": "Register", "icon": "⏩", "status": "normal"},
                        {"label": "4. State Resolve", "subtitle": "O(1) multi-flag evaluation", "badge": "Output", "icon": "✅", "status": "normal"}
                    ],
                    "highlight_label": "Zero branch misprediction: Bitwise logic executes completely in hardware ALU registers."
                },
                "text": "Bitwise Execution Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing arithmetic operations against bitwise operations demonstrates why high-performance systems rely on bitmasks: standard arithmetic requires multiple clock cycles and boolean arrays incur massive heap overhead, whereas bitwise flags pack 64 boolean states into a single 64-bit register.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Arithmetic & Boolean Arrays",
                    "left_desc": "Multi-cycle division/modulo operations; boolean arrays incur 1 byte per flag plus pointer overhead; introduces cache line eviction and branch misprediction.",
                    "right_title": "Bitwise Operations & Masks",
                    "right_desc": "Executes in a single CPU clock cycle; packs up to 64 flags into one register; zero memory allocation; branches eliminated via branchless bit tricks."
                },
                "text": "Arithmetic vs Bitwise Performance",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "This reference matrix summarizes standard bitwise operators, their formal logic truth tables, and their primary systems engineering applications. Notice how XOR acts as a toggle and self-inverting cipher, while bit shifts execute power-of-two arithmetic instantaneously.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Bitwise Operators & Logic Truth Matrix",
                    "headers": ["Operator", "Operation Name", "Formula / Effect", "Primary Use Case"],
                    "rows": [
                        {"label": "AND (&)", "val1": "Bitwise Intersection", "val2": "1 only if both bits are 1", "val3": "Masking & Bit Isolation"},
                        {"label": "OR (|)", "val1": "Bitwise Union", "val2": "1 if either bit is 1", "val3": "Setting Flags & Combining States"},
                        {"label": "XOR (^)", "val1": "Exclusive Difference", "val2": "1 if bits differ (x ^ x = 0)", "val3": "Toggling Bits & Finding Singles"},
                        {"label": "NOT (~)", "val1": "Bit Inversion", "val2": "~x = -(x + 1) in Two's Complement", "val3": "Inverting Bitmasks"},
                        {"label": "Left Shift (<<)", "val1": "Bit Multiplication", "val2": "x << k = x * 2^k", "val3": "Creating Bitmasks (1 << k)"},
                        {"label": "Right Shift (>>)", "val1": "Bit Division", "val2": "x >> k = floor(x / 2^k)", "val3": "Fast Power-of-Two Division"}
                    ]
                },
                "text": "Bitwise Operator Truth Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior bitwise invariants: Brian Kernighan's identity clears the lowest set bit in O of 1; XOR identity x XOR x equals zero unlocks space-free state tracking; and always account for two's complement sign extension on signed integer shifts.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Kernighan's Invariant: The expression x & (x - 1) always clears the lowest set bit of x, enabling set-bit counting in O(k) steps.",
                        "XOR Cancellation Law: Because x ^ x = 0 and x ^ 0 = x, duplicate elements cancel out entirely, enabling O(1) space deduplication.",
                        "Sign Extension Guard: In signed integers, right shift (>>) performs arithmetic shift preserving the sign bit; use unsigned types for logical bit shifting."
                    ]
                },
                "text": "Senior Bitwise Engineering Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 6.14 DATA STRUCTURES & ALGORITHMS: ASYMPTOTIC ANALYSIS & ALGORITHMIC COMPLEXITY
    # -------------------------------------------------------------
    elif domain == "dsa_complexity":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this foundational algorithmic lecture on {lesson_title}. Today we establish mathematical rigor in algorithm design, evaluating growth rates as input sizes scale to infinity using Big-O, Big-Omega, Big-Theta, and solving recurrence relations via the Master Theorem.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Algorithmic Complexity • Asymptotic Bounds, Master Theorem & Space Invariants"},
                "text": "Asymptotic Analysis Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Asymptotic analysis classifies algorithmic efficiency into three formal mathematical bounds: Big-O defines the asymptotic upper bound or worst-case ceiling; Big-Omega establishes the lower bound or best-case floor; and Big-Theta represents an asymptotically tight bound when both limits coincide.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Big-O: Asymptotic Upper Bound", "desc": "f(n) is O(g(n)) if there exist constants c > 0 and n_0 such that f(n) <= c * g(n) for all n >= n_0."},
                        {"title": "2. Big-Omega: Asymptotic Lower Bound", "desc": "f(n) is Omega(g(n)) if f(n) >= c * g(n) for all n >= n_0, establishing theoretical performance floor."},
                        {"title": "3. Big-Theta: Tight Asymptotic Bound", "desc": "f(n) is Theta(g(n)) if and only if f(n) is both O(g(n)) and Omega(g(n)), guaranteeing exact growth rate."}
                    ]
                },
                "text": "The 3 Asymptotic Bounds",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Examine the hierarchy of algorithmic growth rates. As N scales from one thousand to one million elements, an O of 1 operation remains instantaneous, O of log N takes just twenty operations, while an O of N squared algorithm explodes to one trillion operations, crashing production systems.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Algorithmic Growth Hierarchy & Scalability Impact",
                    "headers": ["Complexity Class", "Order of Growth", "Operations for N = 10^6", "Practical Engineering Limit"],
                    "rows": [
                        {"label": "O(1)", "val1": "Constant Time", "val2": "1 operation", "val3": "Infinite scale (Hash lookups, Stack pop)"},
                        {"label": "O(log N)", "val1": "Logarithmic", "val2": "20 operations", "val3": "Massive big-data scale (Binary Search)"},
                        {"label": "O(N)", "val1": "Linear Time", "val2": "1,000,000 operations", "val3": "Scales directly with dataset size"},
                        {"label": "O(N log N)", "val1": "Linearithmic", "val2": "20,000,000 operations", "val3": "Optimal comparison sorting limit"},
                        {"label": "O(N^2)", "val1": "Quadratic", "val2": "1,000,000,000,000 ops", "val3": "Unusable beyond N = 10,000"},
                        {"label": "O(2^N)", "val1": "Exponential", "val2": "Exceeds atoms in universe", "val3": "Brute-force combinatorial searches only"}
                    ]
                },
                "text": "Growth Hierarchy Matrix",
                "transition": "zoom"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is clean implementation code illustrating distinct complexity orders. Constant time hash access runs in O of 1; binary search achieves O of log N by halving the search space; linear scan checks every element in O of N; and nested loops compound into O of N squared.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "title": "Complexity Classes in Code",
                    "language": "python",
                    "code": "# 1. O(1) Constant Time Access\ndef get_first(arr: list):\n    return arr[0] if arr else None\n\n# 2. O(log N) Divide & Conquer (Binary Search)\ndef binary_search(arr: list, target: int) -> int:\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: low = mid + 1\n        else: high = mid - 1\n    return -1\n\n# 3. O(N^2) Quadratic Nested Loops\ndef count_pairs(arr: list) -> int:\n    return sum(1 for i in range(len(arr)) for j in range(i + 1, len(arr)))"
                },
                "text": "Complexity Implementations in Python",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Solving divide-and-conquer recurrences follows the Master Theorem pipeline: express problem T of N as a subproblems of size N over b plus combination cost O of N to the d. Compare log base b of a against d to immediately determine the closed-form complexity bound.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Master Theorem Recurrence Pipeline",
                    "stages": [
                        {"label": "1. Recurrence Form", "subtitle": "T(n) = a*T(n/b) + O(n^d)", "badge": "Input", "icon": "📐", "status": "normal"},
                        {"label": "2. Critical Exponent", "subtitle": "Compute c_crit = log_b(a)", "badge": "Evaluate", "icon": "🧮", "status": "normal"},
                        {"label": "3. Compare Exponents", "subtitle": "Test c_crit vs work cost d", "badge": "Compare", "icon": "⚖️", "status": "normal"},
                        {"label": "4. Closed Form", "subtitle": "Case 1, 2, or 3 Complexity", "badge": "Result", "icon": "🎯", "status": "normal"}
                    ],
                    "highlight_label": "Case 1: d < log_b(a) -> O(n^log_b(a)); Case 2: d = log_b(a) -> O(n^d log n); Case 3: d > log_b(a) -> O(n^d)"
                },
                "text": "Master Theorem Solving Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing asymptotic complexity against real-world wall-clock runtime reveals crucial engineering nuances: Big-O models scalability to infinity by discarding constant factors, but for small datasets, low-overhead algorithms with larger constants often outperform theoretical optimums.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Asymptotic Big-O Complexity",
                    "left_desc": "Hardware-agnostic theoretical bound; ignores machine constants c and low-order terms; governs how algorithms scale as inputs approach infinity.",
                    "right_title": "Physical Wall-Clock Runtime",
                    "right_desc": "Dictated by CPU cache line locality, SIMD vectorization, branch prediction, and constant overhead; O(N^2) insertion sort beats O(N log N) quicksort for N < 32."
                },
                "text": "Theoretical Big-O vs Wall-Clock Runtime",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "This reference matrix details how recurrence relations are solved across different algorithmic paradigms. The Master Theorem provides closed forms for balanced divide-and-conquer, while the Recursion Tree method visually computes total work across geometric levels.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Recurrence Solving Methods Matrix",
                    "headers": ["Solving Method", "Applicable Recurrence Structure", "Core Technique", "Benchmark Example"],
                    "rows": [
                        {"label": "Master Theorem (Case 1)", "val1": "T(n) = a*T(n/b) + O(n^d) where d < log_b(a)", "val2": "Leaf work dominates tree", "val3": "Strassen's Matrix Mult: O(n^2.81)"},
                        {"label": "Master Theorem (Case 2)", "val1": "T(n) = a*T(n/b) + O(n^d) where d = log_b(a)", "val2": "Work evenly distributed per level", "val3": "Merge Sort: O(n log n)"},
                        {"label": "Master Theorem (Case 3)", "val1": "T(n) = a*T(n/b) + O(n^d) where d > log_b(a)", "val2": "Root combination work dominates", "val3": "Binary Search: O(log n)"},
                        {"label": "Recursion Tree Method", "val1": "Unbalanced trees (e.g. T(n/3) + T(2n/3))", "val2": "Sum geometric series per level", "val3": "Quicksort worst/average cases"},
                        {"label": "Substitution Method", "val1": "Any recurrence relation", "val2": "Mathematical induction proof", "val3": "Proving strict asymptotic bounds"}
                    ]
                },
                "text": "Recurrence Solving Matrix",
                "transition": "slide"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To conclude, remember three senior algorithmic complexity invariants: always distinguish worst-case from amortized bounds, optimize for space-time trade-offs where memory caches save expensive recomputations, and benchmark small input sizes against cache locality realities.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Amortized vs Worst-Case Invariant: Dynamic array append is O(1) amortized across N operations despite occasional O(N) reallocation bursts.",
                        "Space-Time Duality: Space complexity and time complexity can often be traded off; memoization trades O(N) auxiliary space to reduce O(2^N) time to O(N).",
                        "Dominant Term Law: In asymptotic polynomials, as N scales towards infinity, the highest order term dominates completely; low-order terms and coefficients vanish."
                    ]
                },
                "text": "Senior Algorithmic Complexity Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 7. COMPUTER NETWORKS
    # -------------------------------------------------------------
    elif domain == "networking":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this advanced systems engineering masterclass on {lesson_title}. Today we dissect the architectural mechanics, state machines, bit-level protocol headers, and high-concurrency throughput trade-offs that govern mission-critical distributed communication.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Network Architecture & Protocol Engineering"},
                "text": "Architectural Foundation",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Examining the layered architecture reveals strict isolation boundaries. Each layer handles a distinct Protocol Data Unit: Application messages are encapsulated into Transport segments, wrapped into Internet packets with IP headers, and framed as MAC payloads for physical transmission.",
                "visual_type": "layer_stack",
                "visual_data": {
                    "title": "Layer Encapsulation Architecture",
                    "direction_label": "Encapsulation: Top-to-Bottom on send, Bottom-to-Top on receive",
                    "layers": [
                        {"title": "Application Layer (HTTP, DNS)", "description": "User requests & high-level application contracts (PDU: Data)", "tag": "L4", "status": "normal"},
                        {"title": "Transport Layer (TCP, UDP)", "description": "Port multiplexing, segmentation, and flow control (PDU: Segments)", "tag": "L3", "status": "highlight"},
                        {"title": "Internet Layer (IP)", "description": "Logical addressing and global packet routing (PDU: Packets)", "tag": "L2", "status": "normal"},
                        {"title": "Network Access Layer (Ethernet/Wi-Fi)", "description": "Physical frame addressing and bit signaling (PDU: Frames)", "tag": "L1", "status": "normal"}
                    ]
                },
                "text": "Deep Layer Encapsulation Substrate",
                "transition": "fade"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Inside the protocol header, precise bit fields govern communication: source and destination port numbers establish multiplexing, 32-bit sequence and acknowledgment numbers enforce absolute order, while explicit control flags like SYN, ACK, and FIN drive the state machine.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Protocol Header Bit-Level Layout",
                    "stages": [
                        {"label": "Ports (32-bit)", "subtitle": "Source & Dest Multiplex", "badge": "Addr", "icon": "🔌", "status": "completed"},
                        {"label": "Seq / ACK (64-bit)", "subtitle": "Total Byte Ordering", "badge": "Sync", "icon": "🔢", "status": "active"},
                        {"label": "Flags (9-bit)", "subtitle": "SYN, ACK, FIN, RST, PSH", "badge": "Control", "icon": "🚩", "status": "normal"},
                        {"label": "Window (16-bit)", "subtitle": "Receiver buffer size", "badge": "Flow", "icon": "📊", "status": "highlight"}
                    ],
                    "highlight_label": "Every byte is tracked deterministically through cumulative acknowledgment numbers."
                },
                "text": "Bit-Level Header Specification",
                "transition": "slide"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Reliability begins with connection synchronization: the initiator emits a SYN, the receiver responds with SYN-ACK validating its buffer capacity, and the final ACK transitions both sockets into the active established state.",
                "visual_type": "cycle_loop",
                "visual_data": {
                    "title": "Connection State Machine Transitions",
                    "stages": [
                        {"title": "1. SYN-SENT", "desc": "Client initiates sequence", "icon": "📤"},
                        {"title": "2. SYN-RECEIVED", "desc": "Server acknowledges and replies", "icon": "📥"},
                        {"title": "3. ESTABLISHED", "desc": "Full-duplex channel unlocked", "icon": "✅"},
                        {"title": "4. FIN-WAIT / TIME-WAIT", "desc": "Graceful socket draining", "icon": "⏳"}
                    ]
                },
                "text": "State Machine & Handshake Lifecycle",
                "transition": "fade"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Flow control protects the receiver from buffer saturation. The sliding window mechanism dynamically advertises how many bytes can be accepted, clamping the sender's transmission rate in direct response to system load.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Window Advertisement", "desc": "Receiver transmits advertised receive window (rwnd)"},
                        {"title": "2. Sliding Stream", "desc": "Sender streams unacknowledged bytes up to window capacity"},
                        {"title": "3. Cumulative Acknowledgment", "desc": "Receiver acknowledges contiguous bytes, sliding window forward"}
                    ]
                },
                "text": "Flow Control: Sliding Window Mechanics",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Comparing reliable stateful protocols like TCP against lightweight datagram protocols like UDP highlights fundamental design choices: TCP guarantees order and delivery at the cost of latency, while UDP maximizes raw transmission speed.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Connection-Oriented (TCP)",
                    "left_desc": "3-way handshake connection state; strict sequence reordering; dynamic flow and congestion control; retransmits lost packets.",
                    "right_title": "Datagram Protocol (UDP)",
                    "right_desc": "Connectionless best-effort delivery; minimal 8-byte header; no acknowledgment or retransmission overhead; ideal for real-time media."
                },
                "text": "Reliable TCP vs Lightweight UDP",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Comparing protocol features illustrates trade-offs: TCP delivers rock-solid reliability for web and transactional data, whereas UDP powers low-latency streaming, DNS queries, and SNMP network monitoring.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Protocol Feature & Trade-Off Matrix",
                    "leftHeader": "Transmission Control Protocol (TCP)",
                    "rightHeader": "User Datagram Protocol (UDP)",
                    "rows": [
                        {"feature": "Reliability", "left": "Guaranteed (Retransmission)", "right": "Best-Effort (No Ack)"},
                        {"feature": "Ordering", "left": "Strict Sequence Numbers", "right": "Out-of-Order Allowed"},
                        {"feature": "Header Overhead", "left": "20 to 60 Bytes", "right": "8 Bytes Minimal"},
                        {"feature": "Flow & Congestion", "left": "Active Sliding Window", "right": "None (Application Level)"}
                    ]
                },
                "text": "Protocol Feature & Trade-Off Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "Mastering network architecture requires understanding edge cases: handling connection reset attacks, tuning receive window scaling options, and mitigating SYN flood denial-of-service vulnerabilities with cryptographic cookies.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "TCP Window Scale: Enables high-bandwidth pipes exceeding legacy 64KB limits",
                        "SYN Flood Defense: Implement kernel SYN Cookies to eliminate half-open socket memory exhaustion",
                        "TIME-WAIT Tuning: Maintain adequate socket draining periods (2MSL) to avoid delayed packet corruption"
                    ]
                },
                "text": "Production Hardening & Synthesis",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 8. OPERATING SYSTEMS & KERNEL ENGINEERING
    # -------------------------------------------------------------
    elif domain == "os_systems":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this comprehensive systems architecture masterclass on {lesson_title}. Operating systems manage the vital boundary between physical silicon and application threads, multiplexing scarce CPU cycles, virtualizing physical memory, and coordinating concurrent access.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Process Scheduling, Virtual Memory & Concurrency Primitives"},
                "text": "Kernel & OS Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Process management cycles through three core operational stages: first, processes enter the Ready queue awaiting scheduling; second, the CPU scheduler dispatches execution within an allotted time quantum; and third, the kernel initiates a context switch upon timer interrupts or blocking I/O calls.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Admission & Scheduling", "desc": "Process enters Ready Queue awaiting CPU dispatch"},
                        {"title": "2. Execution & Quantum", "desc": "Runs on CPU core until timer interrupt or I/O request"},
                        {"title": "3. State Transition", "desc": "Transitions to Blocked on I/O, or returns to Ready on preemption"}
                    ]
                },
                "text": "Kernel Process Lifecycle",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Examining the operating system hierarchy exposes strict isolation between unprivileged Ring 3 User Space and privileged Ring 0 Kernel Mode. Applications request hardware resources only through guarded system calls, preventing errant user software from corrupting memory or hijacking devices.",
                "visual_type": "layer_stack",
                "visual_data": {
                    "title": "Operating System Privilege Hierarchy",
                    "direction_label": "Privilege Boundary: User Mode (Ring 3) to Kernel Mode (Ring 0)",
                    "layers": [
                        {"title": "User Space Applications", "description": "Unprivileged Ring 3 execution space protecting system memory", "tag": "Ring 3", "status": "normal"},
                        {"title": "System Call Interface (POSIX/Win32)", "description": "Controlled trap gates (syscall) transitioning to kernel mode", "tag": "Syscall", "status": "highlight"},
                        {"title": "OS Kernel (Scheduler, VMM, Drivers)", "description": "Privileged Ring 0 supervisor managing processes, paging tables, and devices", "tag": "Ring 0", "status": "normal"},
                        {"title": "Hardware Substrate (CPU, MMU, RAM)", "description": "Physical execution cores, memory management unit, and I/O controllers", "tag": "Silicon", "status": "normal"}
                    ]
                },
                "text": "Privilege Ring Architecture",
                "transition": "fade"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of a concurrency synchronization primitive using POSIX semaphores. Notice how the wait operation decrements the permit counter and atomically blocks the thread if resources are exhausted, guaranteeing mutual exclusion across shared state.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "// Synchronization Primitive: POSIX Counting Semaphore / Mutex\n#include <pthread.h>\n#include <semaphore.h>\n\nsem_t mutex;\n\nvoid* critical_section_worker(void* arg) {\n    // 1. Wait (P operation): Decrement and block if unavailable\n    sem_wait(&mutex);\n    \n    // 2. Protected Critical Section (Mutual Exclusion invariant)\n    shared_counter++;\n    \n    // 3. Post (V operation): Increment and wake waiting thread\n    sem_post(&mutex);\n    return NULL;\n}"
                },
                "text": "Concurrency & Synchronization Primitives",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing memory virtualization highlights how the CPU translates addresses: the Memory Management Unit checks the Translation Lookaside Buffer for cached entries, and upon a miss, traverses multi-level page tables to resolve physical RAM frames without application awareness.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Virtual Address Translation Pipeline",
                    "stages": [
                        {"label": "1. Virtual Addr", "subtitle": "Page number + Offset", "badge": "Virtual", "icon": "🔍", "status": "completed"},
                        {"label": "2. TLB Lookup", "subtitle": "Hardware cache hit/miss", "badge": "TLB", "icon": "⚡", "status": "active"},
                        {"label": "3. Page Walk", "subtitle": "Multi-level page table seek", "badge": "MMU", "icon": "📖", "status": "normal"},
                        {"label": "4. Physical RAM", "subtitle": "Frame address resolution", "badge": "DRAM", "icon": "💾", "status": "highlight"}
                    ],
                    "highlight_label": "Translation Lookaside Buffer (TLB) resolves virtual-to-physical mappings in sub-nanosecond hardware cycles."
                },
                "text": "Virtual Memory & MMU Translation",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Contrasting preemptive scheduling against cooperative systems illustrates the trade-off between control and throughput: preemptive schedulers use hardware timer interrupts to guarantee responsiveness and prevent CPU starvation, whereas cooperative systems risk complete lockup if a task hangs.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Preemptive Scheduling (e.g. Round Robin)",
                    "left_desc": "Timer interrupts force context switches; high responsiveness and starvation prevention; kernel maintains absolute CPU control.",
                    "right_title": "Non-Preemptive (Cooperative) Scheduling",
                    "right_desc": "Processes yield CPU voluntarily; low context switch overhead; vulnerable to rogue or infinite CPU-hogging processes."
                },
                "text": "Preemptive vs Cooperative CPU Scheduling",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "Comparing scheduling algorithms demonstrates distinct optimization goals: Round Robin prioritizes fair interactive response time at the cost of context-switching overhead, whereas Shortest Job First minimizes average turnaround time but risks starving resource-heavy background jobs.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "OS Scheduling Algorithm Trade-Off Matrix",
                    "leftHeader": "Round Robin (Preemptive)",
                    "rightHeader": "Shortest Job First (SJF)",
                    "rows": [
                        {"feature": "Response Time", "left": "Optimal & Bounded by Quantum", "right": "High for Long Jobs"},
                        {"feature": "Turnaround Time", "left": "Higher (Frequent Context Switches)", "right": "Mathematically Minimal Average"},
                        {"feature": "Starvation Risk", "left": "Zero (Fair Share Guarantee)", "right": "High (Long Jobs Starve)"},
                        {"feature": "Scheduling Overhead", "left": "Requires Timer Interrupts & Switches", "right": "Low (Runs to completion)"}
                    ]
                },
                "text": "Scheduling Metric & Trade-Off Matrix",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To master operating systems in production, eliminate deadlocks by breaking any of the four Coffman conditions, tune time quanta to exceed context-switch latency by an order of magnitude, and guard shared locks with priority inheritance.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Coffman Conditions: Deadlock requires Mutual Exclusion, Hold-and-Wait, No Preemption, and Circular Wait; breaking any single condition prevents deadlock entirely.",
                        "Thrashing Prevention: Ensure total allocated physical memory satisfies the working set size of active processes to avoid non-stop page fault thrashing.",
                        "Priority Inversion Guard: Implement Priority Inheritance protocols to prevent low-priority threads from indefinitely stalling critical high-priority tasks."
                    ]
                },
                "text": "Senior Systems Engineering Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 9. SYSTEM DESIGN & DISTRIBUTED SYSTEMS
    # -------------------------------------------------------------
    elif domain == "system_design":
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this advanced distributed systems masterclass on {lesson_title}. When scaling modern web applications to millions of concurrent users, single-node architectures fail. Today we dissect the architectural blueprints, caching topologies, and consistency trade-offs that power resilient global scale.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Distributed Systems, Horizontal Scale & Fault-Tolerant Architecture"},
                "text": "Distributed Systems Foundations",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": "Scaling a distributed application follows three critical tiers: first, users resolve requests through Anycast DNS and edge CDNs; second, Layer 7 load balancers terminate SSL and distribute traffic; and third, stateless service tiers orchestrate business logic backed by distributed data stores.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Edge Resolution & CDN", "desc": "Anycast DNS routing and static asset caching at edge points of presence"},
                        {"title": "2. Layer 7 Load Balancing", "desc": "Reverse proxy terminates SSL and distributes traffic across stateless pods"},
                        {"title": "3. Decoupled Service Mesh", "desc": "Microservices communicate via gRPC or asynchronous event buses"}
                    ]
                },
                "text": "Distributed Request Lifecycle",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": "Examining high-availability architecture illustrates how redundancy removes single points of failure. Stateless application instances scale out horizontally behind load balancers, while database clusters maintain primary-replica replication with automated failover.",
                "visual_type": "concept_network",
                "visual_data": {"title": f"{lesson_title} High-Availability Topology"},
                "text": "High-Availability System Topology",
                "transition": "fade"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production implementation of the Cache-Aside pattern. By checking an in-memory Redis cluster before hitting the primary database, read latency drops from tens of milliseconds to sub-millisecond times, shielding the persistent layer from query storms.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": "# Distributed Cache-Aside Pattern with Redis\nimport redis\nimport json\n\ncache = redis.Redis(host='cluster-cache', port=6379, decode_responses=True)\n\ndef get_entity(entity_id: str):\n    cache_key = f\"entity:{entity_id}\"\n    # 1. Attempt sub-millisecond in-memory cache lookup\n    cached = cache.get(cache_key)\n    if cached:\n        return json.loads(cached)\n    \n    # 2. Cache Miss: Fall back to primary database\n    record = database.query_by_id(entity_id)\n    if record:\n        # 3. Populate cache with TTL to prevent stale state\n        cache.setex(cache_key, 3600, json.dumps(record))\n    return record"
                },
                "text": "Resilient Caching & Data Access Pattern",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing an asynchronous event-driven workflow shows how message brokers like Kafka decouple write ingestion from heavy processing. Producers append events to partitioned logs in microseconds, allowing worker clusters to consume and persist changes independently.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": "Asynchronous Event-Driven Pipeline",
                    "stages": [
                        {"label": "1. Ingest", "subtitle": "API Gateway receives write", "badge": "Gateway", "icon": "📥", "status": "completed"},
                        {"label": "2. Event Bus", "subtitle": "Kafka partitioned topic", "badge": "Kafka", "icon": "📨", "status": "active"},
                        {"label": "3. Consumer Workers", "subtitle": "Async background worker pool", "badge": "Workers", "icon": "⚙️", "status": "normal"},
                        {"label": "4. Read Model", "subtitle": "Denormalized search replica", "badge": "Store", "icon": "⚡", "status": "highlight"}
                    ],
                    "highlight_label": "Partitioned event logs decouple producer throughput from slow downstream consumer processing."
                },
                "text": "Asynchronous Event-Driven Pipeline",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": "Contrasting monolithic setups against microservice architectures highlights operational trade-offs: monoliths offer simple local transactions and deployment, whereas microservices provide isolated failure domains and elastic horizontal scaling for distinct business capabilities.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Monolithic Architecture",
                    "left_desc": "Single codebase, shared database, simple initial deployment; tightly coupled, difficult to scale individual services, single blast radius.",
                    "right_title": "Microservices & Event Mesh",
                    "right_desc": "Independently deployable domain services, isolated databases, elastic scaling; higher operational complexity and eventual consistency."
                },
                "text": "Monolithic Simplicity vs Microservice Elasticity",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": "The CAP Theorem dictates that under network partitions, a distributed system must choose between Strong Consistency and High Availability: CP systems refuse writes to maintain strict correctness, while AP systems prioritize continuous uptime and accept eventual consistency.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Distributed Consensus & Trade-Off Matrix",
                    "leftHeader": "Strong Consistency (CP System)",
                    "rightHeader": "High Availability (AP System)",
                    "rows": [
                        {"feature": "CAP Theorem Stance", "left": "Prioritizes Absolute Correctness", "right": "Prioritizes 100% Uptime & Low Latency"},
                        {"feature": "Partition Behavior", "left": "Blocks or rejects writes during split", "right": "Accepts writes and reconciles later"},
                        {"feature": "Read Latency", "left": "Higher (Quorum verification required)", "right": "Sub-millisecond (Local node read)"},
                        {"feature": "Ideal Workloads", "left": "Financial ledger, inventory reservation", "right": "Social feeds, real-time analytics"}
                    ]
                },
                "text": "CAP Theorem & Consistency Trade-Offs",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": "To engineer rock-solid distributed systems, enforce idempotency keys on all state-mutating endpoints, wrap cross-service calls in circuit breakers to isolate cascading failures, and always apply randomized jitter to exponential retries.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Idempotency Invariant: Every mutation API must accept an Idempotency-Key so retried network requests never cause duplicate billing or double writes.",
                        "Circuit Breaker Pattern: Automatically trip open failed downstream calls to prevent cascading failures from exhausting connection pools.",
                        "Exponential Backoff with Jitter: Always randomize retry intervals to avoid the thundering herd problem when services recover from an outage."
                    ]
                },
                "text": "Senior Distributed Engineering Invariants",
                "transition": "fade"
            }
        ]

    # -------------------------------------------------------------
    # 10. GENERAL COMPUTER SCIENCE FALLBACK
    # -------------------------------------------------------------
    else:
        return [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "narration": f"Welcome to this comprehensive technical masterclass on {lesson_title}. Today we dissect the core mechanics, operational workflows, and rigorous algorithmic principles that make this concept essential in production software engineering and computational problem solving.",
                "visual_type": "title_card",
                "visual_data": {"title": lesson_title, "subtitle": "Core Principles, Algorithmic Invariants & Implementation"},
                "text": "Foundational Architecture",
                "transition": "fade"
            },
            {
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.0,
                "narration": f"Mastering {lesson_title} begins with three core operational phases: first, validating input constraints and initial preconditions; second, executing deterministic transformation logic through structured loop invariants; and third, returning verified outputs while releasing computational resources.",
                "visual_type": "flow_steps",
                "visual_data": {
                    "steps": [
                        {"title": "1. Precondition Guard", "desc": "Validating initial parameters and memory bounds"},
                        {"title": "2. Core Logic Execution", "desc": "Executing deterministic transformation algorithms"},
                        {"title": "3. Convergence & Output", "desc": "Returning verified results and releasing state"}
                    ]
                },
                "text": "3-Stage Execution Flow",
                "transition": "slide"
            },
            {
                "scene_id": 3,
                "start_time": 30.0,
                "end_time": 45.0,
                "narration": f"Examining the underlying data flow reveals how state transitions operate across explicit boundary contracts. Each processing unit maintains strict memory safety and encapsulation, minimizing unintended side effects while maximizing execution efficiency.",
                "visual_type": "concept_network",
                "visual_data": {"title": f"{lesson_title} State & Data Flow Architecture"},
                "text": "State Machine & Boundary Contracts",
                "transition": "fade"
            },
            {
                "scene_id": 4,
                "start_time": 45.0,
                "end_time": 60.0,
                "narration": "Here is the production-grade implementation. Notice how error boundaries and edge conditions are verified up front, ensuring predictable runtime behavior, zero out-of-bounds panics, and mathematically verified loop invariants even on adversarial input datasets.",
                "visual_type": "code_snippet",
                "visual_data": {
                    "code": f"// Production implementation of {lesson_title}\nclass Solution {{\npublic:\n    bool execute() {{\n        // 1. Guard against boundary and null edge cases\n        if (!is_valid()) return false;\n        \n        // 2. Core execution pipeline\n        process_pipeline();\n        return true;\n    }}\n}};"
                },
                "text": "Clean Implementation & Guard Rails",
                "transition": "slide"
            },
            {
                "scene_id": 5,
                "start_time": 60.0,
                "end_time": 75.0,
                "narration": "Tracing a live execution walkthrough highlights state transitions from start to finish. Each step asserts correctness before handing off data to downstream instructions, preventing silent logic corruption and guaranteeing deterministic termination.",
                "visual_type": "system_pipeline",
                "visual_data": {
                    "title": f"{lesson_title} Operational Lifecycle",
                    "stages": [
                        {"label": "1. Ingest", "subtitle": "Validate state", "badge": "Init", "icon": "📥", "status": "completed"},
                        {"label": "2. Compute", "subtitle": "Execute logic", "badge": "Run", "icon": "⚙️", "status": "active"},
                        {"label": "3. Verify", "subtitle": "Assert correctness", "badge": "Check", "icon": "🛡️", "status": "normal"},
                        {"label": "4. Output", "subtitle": "Final state", "badge": "Done", "icon": "✅", "status": "highlight"}
                    ],
                    "highlight_label": "Deterministic loop invariants ensure robust execution across edge conditions."
                },
                "text": "Execution Trace & State Transitions",
                "transition": "slide"
            },
            {
                "scene_id": 6,
                "start_time": 75.0,
                "end_time": 90.0,
                "narration": f"Contrasting naive brute-force implementations against modern {lesson_title} exposes critical trade-offs: naive routines incur unconstrained computational complexity and memory bloat, whereas optimized routines minimize overhead and guarantee bounded execution time.",
                "visual_type": "comparison",
                "visual_data": {
                    "left_title": "Naive / Brute-Force Approach",
                    "left_desc": "Suboptimal iterations with high CPU overhead; vulnerable to worst-case input degradation and uncontrolled memory allocations.",
                    "right_title": f"Optimized {lesson_title}",
                    "right_desc": "Carefully bounded execution flow; verified loop invariants, optimal cache locality, and minimal auxiliary memory consumption."
                },
                "text": "Algorithmic Trade-Off Comparison",
                "transition": "slide"
            },
            {
                "scene_id": 7,
                "start_time": 90.0,
                "end_time": 105.0,
                "narration": f"In terms of asymptotic metrics, balancing time complexity against auxiliary memory footprint ensures the design remains responsive and predictable under high-volume workloads and large dataset scales.",
                "visual_type": "comparison_matrix",
                "visual_data": {
                    "title": "Algorithmic Complexity & Efficiency Matrix",
                    "leftHeader": "Naive Implementation",
                    "rightHeader": f"Optimized {lesson_title}",
                    "rows": [
                        {"feature": "Time Complexity", "left": "Suboptimal / Quadratic O(N^2)", "right": "Bounded / Optimal O(N)"},
                        {"feature": "Auxiliary Space", "left": "Heavy Buffer Copying O(N)", "right": "In-Place / Minimal O(1)"},
                        {"feature": "Edge Case Safety", "left": "Unchecked Boundary Panics", "right": "Deterministic Preconditions"},
                        {"feature": "Memory Locality", "left": "Fragmented Pointer Chasing", "right": "Contiguous Cache Utilization"}
                    ]
                },
                "text": "Complexity & Efficiency Profile",
                "transition": "fade"
            },
            {
                "scene_id": 8,
                "start_time": 105.0,
                "end_time": 120.0,
                "narration": f"To master {lesson_title} in production systems, always defend preconditions up front, prove algorithmic correctness with inductive invariants, and optimize memory access patterns to take full advantage of hardware cache prefetching.",
                "visual_type": "text_bullets",
                "visual_data": {
                    "items": [
                        "Precondition Defense: Validate array boundaries and state integrity before executing core loops",
                        "Loop Invariant Correctness: Ensure states remain strictly valid across initialization, maintenance, and termination",
                        "Hardware Cache Efficiency: Prefer contiguous memory structures to maximize CPU L1 and L2 throughput"
                    ]
                },
                "text": "Senior Engineering Invariants",
                "transition": "fade"
            }
        ]
