import streamlit as st
import json, re
from data_handler import load_excel, generate_data_profile
from mockup_generator import generate_bi_mockup
from visualizer import render_pages

st.set_page_config(page_title="AI BI Mockup Builder", layout="wide")
st.title("📊 AI BI Mockup Builder")

# ---------------- SESSION ----------------
if "mockup_edit" not in st.session_state:
    st.session_state["mockup_edit"] = ""
if "df_by_sheet" not in st.session_state:
    st.session_state["df_by_sheet"] = None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Controls")
    uploaded = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    role = st.selectbox("Role", ["BI Developer", "Data Analyst", "Finance Planner"], index=0)
    goal = st.text_area("Objective", placeholder="e.g., Create sales dashboard by region and category.")
    gen = st.button("✨ Generate Mockup")
    reset = st.button("🧹 Reset Session")

if reset:
    st.session_state.clear()
    st.experimental_rerun()

# ---------------- LOAD DATA ----------------
if uploaded:
    df_by_sheet = load_excel(uploaded)
    profile = generate_data_profile(df_by_sheet)
    st.session_state["df_by_sheet"] = df_by_sheet
    st.success(f"✅ Loaded {len(df_by_sheet)} sheet(s).")
else:
    df_by_sheet = st.session_state.get("df_by_sheet")

# ---------------- GENERATE MOCKUP ----------------
if gen and df_by_sheet:
    with st.spinner("Generating compact BI JSON spec..."):
        spec = generate_bi_mockup(goal, profile, role)
    st.session_state["mockup_edit"] = spec

# ---------------- JSON CLEANER ----------------
def extract_first_json_block(text: str) -> str:
    """Extract and sanitize first JSON object from GPT or user text."""
    if not text or not text.strip():
        return "{}"
    text = re.sub(r"```(json)?", "", text)
    text = re.sub(r"```", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return "{}"
    cleaned = re.sub(r",(\s*[}\]])", r"\1", match.group(0))
    return cleaned.strip()

# ---------------- JSON VALIDATION ----------------
raw_spec = st.session_state.get("mockup_edit", "")
clean_spec = extract_first_json_block(raw_spec)

try:
    json.loads(clean_spec)
    st.session_state["mockup_edit"] = clean_spec
    st.success("✅ JSON is valid and ready.")
except Exception:
    st.warning("⚠️ Invalid or empty JSON. Using fallback spec.")
    fallback = json.dumps({
        "Pages": [{
            "name": "Default Dashboard",
            "Filters": [{"field": "Region"}],
            "KPIs": [{"title": "Total Sales", "agg": "sum", "field": "Sales"}],
            "Layout": [
                {"section": "Charts", "elements": [
                    {"type": "Bar", "x": "Region", "y": "Sales"}
                ]}
            ]
        }]
    }, indent=2)
    st.session_state["mockup_edit"] = fallback

# ---------------- EDITOR ----------------
st.text_area(
    "🧩 BI Mockup JSON (Editable)",
    value=st.session_state["mockup_edit"],
    key="mockup_edit",
    height=300,
)

# ---------------- DASHBOARD PREVIEW ----------------
if df_by_sheet and st.session_state["mockup_edit"]:
    st.divider()
    st.subheader("📈 Live Dashboard Preview")
    render_pages(df_by_sheet, st.session_state["mockup_edit"])
else:
    st.info("Upload data and generate a mockup to preview.")
