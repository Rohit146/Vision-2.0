import streamlit as st
import json, re
from data_handler import load_excel, generate_data_profile
from mockup_generator import generate_bi_mockup
from visualizer import render_story_dashboard

st.set_page_config(page_title="AI BI Story Dashboard", layout="wide")
st.markdown(
    """
    <style>
    .main, .block-container { max-width: 1500px; margin: auto; }
    .element-container { padding: 0.3rem 0.8rem; }
    .stMetric { text-align: center; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 AI BI Story Dashboard Builder")

# ---------------- SESSION ----------------
if "mockup_edit" not in st.session_state:
    st.session_state["mockup_edit"] = ""
if "df_by_sheet" not in st.session_state:
    st.session_state["df_by_sheet"] = None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    role = st.selectbox("Role", ["BI Developer", "Finance Analyst", "Sales Leader", "Operations Manager"], index=0)
    goal = st.text_area("Business Goal", placeholder="e.g., Analyze quarterly sales performance by region and category.")
    gen = st.button("✨ Generate Story Dashboard")
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
def clean_json_output(text: str):
    text = re.sub(r"```(json)?", "", text)
    text = re.sub(r"```", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return "{}"
    cleaned = re.sub(r",(\s*[}\]])", r"\1", match.group(0))
    return cleaned.strip()

if gen and df_by_sheet:
    with st.spinner("Generating corporate-style BI Story Dashboard..."):
        spec = generate_bi_mockup(goal, profile, role)
        st.session_state["mockup_edit"] = clean_json_output(spec)

# ---------------- JSON VALIDATION ----------------
spec_text = st.session_state.get("mockup_edit", "").strip()
if not spec_text:
    st.warning("No valid mockup spec found. Please generate one.")
else:
    try:
        json.loads(spec_text)
        st.success("✅ JSON spec valid.")
    except Exception:
        st.warning("⚠️ Invalid JSON detected. Using fallback layout.")
        fallback = json.dumps({
            "Pages": [{
                "name": "Corporate Story Dashboard",
                "Story": [
                    {"section": "Overview", "text": "Summarize key business highlights and metrics."},
                    {"section": "Performance", "text": "Show KPI cards for sales, profit, growth."},
                    {"section": "Trends", "text": "Display charts for region and product performance."},
                    {"section": "Risks", "text": "Identify areas underperforming or declining."},
                    {"section": "Recommendations", "text": "Suggest strategic actions."}
                ],
                "KPIs": [
                    {"title": "Total Sales", "agg": "sum", "field": "Sales"},
                    {"title": "Profit Margin", "agg": "avg", "field": "Profit"},
                    {"title": "YoY Growth", "agg": "avg", "field": "Growth"}
                ],
                "Layout": [
                    {"section": "Performance", "elements": [{"type": "Bar", "x": "Region", "y": "Sales"}]},
                    {"section": "Trends", "elements": [{"type": "Line", "x": "Month", "y": "Profit"}]}
                ]
            }]
        }, indent=2)
        st.session_state["mockup_edit"] = fallback

# ---------------- EDITOR ----------------
st.text_area(
    "🧩 BI Story Mockup JSON (Editable)",
    value=st.session_state["mockup_edit"],
    key="mockup_edit",
    height=300,
)

# ---------------- DASHBOARD PREVIEW ----------------
if df_by_sheet and st.session_state["mockup_edit"]:
    st.divider()
    st.subheader("📈 16:9 Story Dashboard Preview")
    render_story_dashboard(df_by_sheet, st.session_state["mockup_edit"])
else:
    st.info("Upload data and generate a mockup to preview.")
