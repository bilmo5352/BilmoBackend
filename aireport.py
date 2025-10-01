# pip install google-genai
# export GENAI_API_KEY="YOUR_API_KEY"

from typing import Any, Dict, List
from datetime import datetime, timezone
from google import genai
from google.genai import types
import re
import json
result=dict()

def format_grounding_citations(resp):
    md = getattr(resp.candidates[0], "grounding_metadata", None) or {}
    sources = []
    # Try common locations for web search results
    for k in ["search_queries", "web_results", "grounding_chunks", "sources", "citations"]:
        v = md.get(k)
        if isinstance(v, list):
            for item in v:
                url = item.get("url") or item.get("uri") or item.get("source") or ""
                title = item.get("title") or item.get("name") or ""
                if url or title:
                    sources.append((title, url))
    # Fallback: walk any dicts that look like web result entries
    if not sources:
        for k, v in md.items():
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        url = item.get("url") or item.get("uri") or ""
                        title = item.get("title") or item.get("name") or ""
                        if url or title:
                            sources.append((title, url))
    # De-duplicate
    seen = set()
    dedup = []
    for t, u in sources:
        key = (t.strip(), u.strip())
        if key not in seen and (t or u):
            seen.add(key)
            dedup.append(key)
    return dedup

def parse_response_to_json(response_text):
    """
    Parse the LLM response text into JSON format using regular expressions.
    Extracts Reports and News sections with their titles, snippets, and URLs.
    """
    result = {
        "reports": [],
        "news": []
    }
    
    # Regular expression patterns
    # Pattern for Reports: Report1:, Report2:, etc.
    report_pattern = r'Report(\d+):\s*([^\n]+)\nsnippet(\d+):\s*([^\n]+)\nurl(\d+):\s*([^\n]+)'
    # Pattern for News: News1:, News2:, etc.
    news_pattern = r'News(\d+):\s*([^\n]+)\nsnippet(\d+):\s*([^\n]+)\nurl(\d+):\s*([^\n]+)'
    
    # Find all report matches
    report_matches = re.findall(report_pattern, response_text, re.MULTILINE)
    for match in report_matches:
        report_num, title, snippet_num, snippet, url_num, url = match
        result["reports"].append({
            "id": f"Report{report_num}",
            "title": title.strip(),
            "snippet": snippet.strip(),
            "url": url.strip()
        })
    
    # Find all news matches
    news_matches = re.findall(news_pattern, response_text, re.MULTILINE)
    for match in news_matches:
        news_num, title, snippet_num, snippet, url_num, url = match
        result["news"].append({
            "id": f"News{news_num}",
            "title": title.strip(),
            "snippet": snippet.strip(),
            "url": url.strip()
        })
    
    return result

client = genai.Client(api_key="AIzaSyC2Rb7z7HTqOjmPWCN7ZmyVW3HQ1TOtPqQ")

config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0,
)
def ReportProducts(product):
    global result
    query = f"""Tell about the Top deals about {product} available in internet, there should be no examples about the search , it should be really from the internet , the real cost ,  real deal , everything should be true data.\
        response format should be like this:
        Report1: name of the report 
        snippet1: snippet of the report
        url1: url of the report

        Report2:....... 3 Reports 

        News1:name of the News1
        snippet1: snippet of the News1
        url1: url of the News1

        News2:....... 3 News
        
        """
    resp = client.models.generate_content(
        model="gemini-2.5-flash",  # or gemini-2.5-pro
        contents=query,
        config=config,
    )
    
    # Parse the response text into JSON format
    result = parse_response_to_json(resp.text)
    return result


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Parse JSON strictly; try best-effort extraction if model adds extra text."""
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}$", text.strip())
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {}


def SuggestRepurchase(product_name: str) -> Dict[str, Any]:
    """Suggest related products (name + description) via association rule mining prompt.

    Returns dict:
    {
        "product": str,
        "related": [ { "name": str, "description": str } ],
        "generated_at": iso8601 str
    }
    """
    instruction = (
        "You are a retail recommendations engine applying association rule mining (market basket analysis). "
        "Infer items frequently bought together, sequential purchases, and cross-sells by category. "
        "Each related item's description must explain WHY it complements the input product, referencing patterns such as protection, capacity, connectivity, power, ergonomics, or maintenance. "
        "Descriptions must be specific and product-aware, not generic. Do not output SKUs or brand hallucinations; use general item names. "
        "Return STRICT JSON only with this schema: {\\n  \\\"product\\\": string,\\n  \\\"related\\\": [ { \\\"name\\\": string, \\\"description\\\": string } ]\\n}. No markdown, no commentary."
    )

    prompt = (
        f"Product: {product_name}\n"
        "Find 6-10 related items using association rule mining logic."
    )

    repurchase_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "product": types.Schema(type=types.Type.STRING),
                "related": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "name": types.Schema(type=types.Type.STRING),
                            "description": types.Schema(type=types.Type.STRING),
                        },
                        required=["name", "description"],
                    ),
                ),
            },
            required=["product", "related"],
        ),
        temperature=0,
    )

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[instruction, prompt],
        config=repurchase_config,
    )

    data = _safe_parse_json(resp.text or "")
    if not isinstance(data, dict):
        data = {}

    # Normalize and validate
    product_value = data.get("product") if isinstance(data.get("product"), str) else product_name
    related_raw = data.get("related") if isinstance(data.get("related"), list) else []

    normalized: List[Dict[str, str]] = []
    seen_names = set()
    for item in related_raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name") if isinstance(item.get("name"), str) else ""
        desc = item.get("description") if isinstance(item.get("description"), str) else ""
        name = name.strip()
        desc = desc.strip()
        if not name:
            continue
        key = name.lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        normalized.append({"name": name, "description": desc})

    # Enforce unique, product-specific descriptions
    def _keywords(text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [t for t in tokens if len(t) >= 3]

    product_keywords = _keywords(product_value or product_name)
    generic_markers = [
        "useful accessory",
        "commonly used",
        "great for",
        "enhances experience",
        "improves performance",
        "ideal for",
        "helps with",
        "good choice",
    ]

    filtered: List[Dict[str, str]] = []
    seen_pairs = set()
    for it in normalized:
        desc = (it.get("description") or "").strip()
        name = it.get("name") or ""
        if len(desc) < 30:
            continue
        low = desc.lower()
        if any(g in low for g in generic_markers):
            continue
        if product_keywords and not any(k in low for k in product_keywords):
            desc = f"{desc} Complementary to {product_value}."
        pair_key = (name.lower(), desc.lower())
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        filtered.append({"name": name, "description": desc})

    normalized_final = filtered

    result_repurchase: Dict[str, Any] = {
        "product": product_value,
        "related": normalized_final,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return result_repurchase

def productai(product_name: str) -> Dict[str, Any]:
    """Return combined JSON with reports, news, repurchase for a product."""
    news_reports = ReportProducts(product_name)
    repurchase = SuggestRepurchase(product_name)
    combined_output = {
        "product": product_name,
        "reports": news_reports.get("reports", []),
        "news": news_reports.get("news", []),
        "repurchase": repurchase.get("related", []),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return combined_output


if __name__ == "__main__":
    product_input = input("Enter product name: ").strip()
    if not product_input:
        raise ValueError("Product name is required")

    print(json.dumps(productai(product_input), indent=2, ensure_ascii=False))