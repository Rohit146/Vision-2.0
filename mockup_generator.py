from openai import OpenAI
import os, re, json
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SCHEMA_HINT = """
Return ONLY valid JSON matching this schema:
{
 "Pages":[
   {"name":"string","Filters":[{"field":"string"}],
    "KPIs":[{"title":"string","agg":"sum|avg|min|max|count|distinct","field":"string"}],
    "Layout":[
      {"section":"string","elements":[{"type":"Bar|Line|Pie|Table","x":"string","y":"string"}]}
    ]
   }
 ]
}
"""

def extract_clean_json(text: str) -> str:
    """Remove ```json fences, markdown, and extra notes."""
    text = re.sub(r"```(json)?", "", text)
    text = re.sub(r"```", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return "{}"
    json_str = match.group(0).strip()
    json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)
    return json_str

def generate_bi_mockup(user_goal: str, data_profile: dict, role="BI Developer") -> str:
    """Generate clean, valid BI mockup JSON."""
    profile_text = "\n".join(
        [f"Sheet {s}: numeric={p['numeric']} categorical={p['categorical']}" for s,p in data_profile.items()]
    )
    prompt = f"""
You are a {role}.
Generate a compact Power BI / MicroStrategy dashboard spec.
Be precise, minimal, use only fields present in the data.
Respond with valid JSON only.

Data Summary:
{profile_text}

User Goal:
{user_goal}

{SCHEMA_HINT}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content
    cleaned = extract_clean_json(raw)
    try:
        json.loads(cleaned)
    except Exception:
        cleaned = "{}"
    return cleaned
