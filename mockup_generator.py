from openai import OpenAI
import os, re, json
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SCHEMA_HINT = """
Return ONLY valid JSON (no prose, no markdown fences) matching this structure:
{ "Pages": [ { "name": "...", "Filters": [...], "KPIs": [...], "Layout": [...] } ] }
"""

def extract_clean_json(text: str) -> str:
    """Remove ```json fences and extra commentary from GPT output."""
    text = re.sub(r"```(json)?", "", text)       # remove code fences
    text = re.sub(r"```", "", text)
    match = re.search(r"\{[\s\S]*\}", text)      # find first { ... }
    if not match:
        return "{}"
    return match.group(0).strip()

def generate_bi_mockup(user_goal: str, data_profile: dict, role="BI Developer") -> str:
    """Generate compact, valid JSON spec automatically cleaned."""
    profile_text = "\n".join(
        [f"Sheet {s}: numeric={p['numeric']} categorical={p['categorical']}" for s,p in data_profile.items()]
    )
    prompt = f"""
You are a {role}. Produce a Power BI / MicroStrategy dashboard specification.
Use only fields from the data summary. Follow the schema strictly. No explanations.

Data Summary:
{profile_text}

User Goal:
{user_goal}

{SCHEMA_HINT}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2,
    )
    raw_text = resp.choices[0].message.content
    clean_json = extract_clean_json(raw_text)
    # final sanity check
    try:
        json.loads(clean_json)
    except Exception:
        # attempt to fix common commas/trailing issues
        clean_json = re.sub(r",(\s*[}\]])", r"\1", clean_json)
    return clean_json
