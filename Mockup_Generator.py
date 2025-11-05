from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SCHEMA_HINT = """
Return ONLY valid JSON (no prose) with this schema:
{
  "Pages": [
    {
      "name": "string",
      "Filters": [{"field":"string"}],
      "KPIs": [
        {"title":"string","agg":"sum|avg|min|max|count|distinct","field":"string","format":"auto|#,##0.00|₹#,##0"}
      ],
      "Layout": [
        {"section":"string","elements":[
          {"type":"Bar|Line|Area|Pie|Scatter|Histogram|Box|Table",
           "x":"string(optional)","y":"string(optional)","color":"string(optional)",
           "agg":"sum|avg|min|max|count|distinct(optional)",
           "columns":["colA","colB"](for Table),
           "groupby":["dimA","dimB"](for Table),
           "metrics":[{"field":"string","agg":"sum|avg|min|max|count|distinct"}](for Table)
          }
        ]}
      ]
    }
  ]
}
"""

def generate_bi_mockup(user_goal: str, data_profile: dict, role="BI Developer") -> str:
    profile_text = "\n".join(
        [f"Sheet {s}: numeric={p['numeric']} categorical={p['categorical']}" for s,p in data_profile.items()]
    )
    prompt = f"""
You are a {role}. Produce a compact, development-ready BI dashboard specification for Power BI / MicroStrategy.
Use only fields that plausibly exist from the data summary. Prefer clear, implementable visuals and KPIs.
Be precise and minimal. No explanations. Output must be JSON per schema.

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
    return resp.choices[0].message.content.strip()
