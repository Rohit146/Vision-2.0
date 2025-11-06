import streamlit as st
import json, re
from data_handler import load_excel, generate_data_profile
from mockup_generator import generate_bi_mockup
from visualizer import render_story_dashboard

# ---- Streamlit Setup ----
st.set_page_config(page_title="AI BI Story Dashboard", layout="wide")
st.title("📊 AI BI Story Dashboard Builder")

# ---- Session Initialization ----
if "mockup_edit" not in st.session_state:
    st.session_state["mockup_edit"] = ""
if "df_by_sheet" not in st.session_state:
    st.session_state["df_by_sheet"] = None
if "data_profile" not in st.session_state:
    st.session_state["data_profile"] = None

# ---- Sidebar ----
with st.sidebar:
    st.header("⚙️ Setup")
    uploaded = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    role = st.selectbox("Role", ["BI Developer", "Finance Analyst", "Sales Leader", "Operations Manager"])
    goal = st.text_area("Business Goal", placeholder="e.g., Analyze quarterly sales performance by region and category.")
    generate = st.button("✨ Generate Dashboard Spec")
    reset = st.button("🧹 Reset Session")

if reset:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# ---- Load Excel ----
if uploaded:
    df_by_sheet = load_excel(uploaded)
    st.session_state["df_by_sheet"] = df_by_sheet
    st.session_state["data_profile"] = generate_data_profile(df_by_sheet)
    st.success(f"✅ Loaded {len(df_by_sheet)} sheet(s).")
else:
    df_by_sheet = st.session_state.get("df_by_sheet")

# ---- Utility ----
def extract_json_block(text: str):
    text = re.sub(r"```(json)?", "", text)
    text = re.sub(r"```", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return "{}"
    return re.sub(r",(\s*[}\]])", r"\1", match.group(0)).strip()

# ---- Generate Spec ----
if generate and df_by_sheet:
    with st.spinner("🧠 Generating BI Story Dashboard..."):
        try:
            spec = generate_bi_mockup(goal, st.session_state["data_profile"], role)
            st.session_state["mockup_edit"] = extract_json_block(spec)
        except Exception as e:
            st.error(f"Generation failed: {e}")

# ---- Editor ----
st.markdown("### 🧩 Dashboard Specification (Editable JSON)")
st.session_state["mockup_edit"] = st.text_area(
    label="Mockup JSON",
    value=st.session_state.get("mockup_edit", ""),
    height=300,
)

# ---- JSON Validation ----
try:
    json.loads(st.session_state["mockup_edit"])
    st.success("✅ JSON is valid.")
except Exception:
    st.warning("⚠️ Invalid or empty JSON. Using fallback spec.")
    st.session_state["mockup_edit"] = json.dumps({
        "Pages": [{
            "name": "Corporate Story Dashboard",
            "Story": [
                {"section": "Overview", "text": "Executive summary of company performance."},
                {"section": "Performance", "text": "Key KPIs across regions and categories."},
                {"section": "Trends", "text": "Sales and profit trends over time."},
                {"section": "Risks", "text": "Highlight underperforming regions or products."},
                {"section": "Recommendations", "text": "Strategic next steps for improvement."}
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

# ---- Dashboard ----
if st.session_state["df_by_sheet"] and st.session_state["mockup_edit"]:
    st.divider()
    st.subheader("📈 Dashboard Preview (16:9 Story Layout)")
    render_story_dashboard(st.session_state["df_by_sheet"], st.session_state["mockup_edit"])
else:
    st.info("Upload data and generate a dashboard to preview.")
