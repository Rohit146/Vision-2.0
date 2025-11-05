import streamlit as st
import plotly.express as px
import pandas as pd
import json, re, os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clean_json_text(text: str) -> str:
    """
    Clean text output from GPT to extract valid JSON block.
    Removes code fences, commentary, and stray markdown.
    """
    # remove markdown fences
    cleaned = re.sub(r"```(json)?", "", text)
    # find first { ... } block
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        return match.group(0)
    return cleaned.strip()


def try_parse_json(text: str):
    """
    Try parsing cleaned JSON, fallback to GPT repair if available.
    """
    cleaned = clean_json_text(text)
    try:
        data = json.loads(cleaned)
        return data, None
    except json.JSONDecodeError as e:
        # optional: try GPT-based repair if available
        if client:
            try:
                fix_prompt = f"Fix the following text into valid JSON only (no extra commentary):\n\n{cleaned}"
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": fix_prompt}],
                    temperature=0
                )
                fixed = clean_json_text(resp.choices[0].message.content)
                data = json.loads(fixed)
                st.toast("🔧 JSON auto-repaired by AI", icon="🤖")
                return data, None
            except Exception as e2:
                return None, f"JSON repair failed: {e2}"
        return None, f"JSON parse error: {e}"
