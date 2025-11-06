from openai import OpenAI
import os, re, json
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_clean_json(text: str) -> str:
    text = re.sub(r"```(json)?", "", text)
    text = re.sub(r"```", "", text)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m: return "{}"
    return re.sub(r",(\s*[}\]])", r"\1", m.group(0)).strip()

ROLE_CONTEXT = {
    "Finance Analyst":
        "Focus on revenue, margin, cost, and profitability trends; show risks and cashflow insights.",
    "Sales Leader":
        "Focus on pipeline, win-loss, top regions/products, YoY growth and customer trends.",
    "Operations Manager":
        "Focus on efficiency, utilization, lead time, supplier or production metrics.",
    "BI Developer":
        "Focus on balanced visuals and technical KPIs useful for BI deployment readiness."
}

def generate_bi_mockup(goal, data_profile, role):
    profile = "\n".join(
        [f"Sheet {s}: numeric={p['numeric']} categorical={p['categorical']}"
         for s,p in data_profile.items()]
    )
    prompt = f"""
You are acting as a {role}. {ROLE_CONTEXT.get(role,'')}

Using this data:
{profile}

Business goal:
{goal}

Create a realistic Power BI-style dashboard spec in JSON.
Include five story sections: Overview, Performance, Trends, Risks, Recommendations.
Include relevant KPIs and visuals.

Return **only JSON** with this structure:
{{
 "Pages":[{{"name":"string",
   "Story":[{{"section":"string","text":"string"}}],
   "KPIs":[{{"title":"string","agg":"sum|avg|min|max|count","field":"string"}}],
   "Layout":[{{"section":"string","elements":[{{"type":"Bar|Line|Pie|Table","x":"string","y":"string"}}]}}]
 }}]
}}
"""
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3,
    )
    return extract_clean_json(r.choices[0].message.content)
