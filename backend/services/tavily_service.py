import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

def search_tavily(query: str, max_results: int = 4) -> dict:
    """
    Searches the web using Tavily API and returns:
    - 'context': Clean aggregated text content from top authoritative web sources.
    - 'citations': List of formatted markdown links [Title](URL) for academic references.
    """
    api_key = os.getenv("TAVILY_API_KEY") or TAVILY_API_KEY
    if not api_key:
        print("[Tavily] Notice: TAVILY_API_KEY not configured. Skipping web fallback.", flush=True)
        return {"context": "", "citations": []}

    url = "https://api.tavily.com/search"
    academic_domains = [
        "mit.edu", "stanford.edu", "berkeley.edu", "openstax.org",
        "libretexts.org", "geeksforgeeks.org", "arxiv.org"
    ]
    
    # Attempt 1: Target authorized academic and university textbook portals
    payload_dict = {
        "api_key": api_key,
        "query": f"{query} computer science curriculum textbook lecture notes",
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
        "include_domains": academic_domains
    }

    def execute_tavily_request(req_payload: dict):
        p_bytes = json.dumps(req_payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=p_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "AICoursePlatform/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        print(f"[Tavily] Searching authorized academic domains for: '{query}'...", flush=True)
        data = execute_tavily_request(payload_dict)
        results = data.get("results", [])
        
        # Fallback to broader web if academic domains returned empty
        if not results:
            print("[Tavily] Academic domain search returned empty. Falling back to broad technical web...", flush=True)
            payload_dict.pop("include_domains", None)
            payload_dict["query"] = query
            data = execute_tavily_request(payload_dict)
            results = data.get("results", [])

        context_parts = []
        citations = []

        for r in results:
            title = r.get("title", "Web Reference")
            content = r.get("content", "")
            link = r.get("url", "")
            if content:
                context_parts.append(f"Web Source: {title}\nURL: {link}\nContent:\n{content}")
            if link:
                citations.append(f"🌐 [{title}]({link})")

        joined_context = "\n\n---\n\n".join(context_parts)
        print(f"[Tavily] Successfully retrieved {len(results)} authoritative web sources.", flush=True)
        return {
            "context": joined_context,
            "citations": citations
        }
    except Exception as e:
        print(f"[Tavily Error]: Failed to fetch web research: {e}", flush=True)
        return {"context": "", "citations": []}
