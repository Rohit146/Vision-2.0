import streamlit as st
from data_handler import load_excel, generate_data_profile
from mockup_generator import generate_bi_mockup
from visualizer import render_pages

st.set_page_config(page_title="AI BI Mockup Builder", layout="wide")

st.title("📊 AI BI Mockup Builder")

# ---- Sidebar ----
with st.sidebar:
    uploaded = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    role = st.selectbox("Role", ["BI Developer", "Data Analyst", "Finance Planner"], index=0)
    goal = st.text_area("Objective", placeholder="e.g., Create sales dashboard by region & category.")
    gen = st.button("✨ Generate Mockup")
    reset = st.button("🧹 Reset")

if reset:
    st.session_state.clear()
    st.experimental_rerun()

# ---- Load Data ----
if uploaded:
    df_by_sheet = load_excel(uploaded)
    profile = generate_data_profile(df_by_sheet)
    st.session_state["df_by_sheet"] = df_by_sheet
    st.success(f"Loaded {len(df_by_sheet)} sheet(s).")
else:
    df_by_sheet = st.session_state.get("df_by_sheet")

# ---- Generate Spec ----
if gen and df_by_sheet:
    with st.spinner("Generating JSON spec..."):
        spec = generate_bi_mockup(goal, profile, role)
    st.session_state["mockup_spec"] = spec

# ---- Editor ----
mockup_spec = st.session_state.get("mockup_spec", "")
st.text_area(
    "🧩 BI Mockup JSON (editable)",
    value=mockup_spec,
    key="mockup_edit",
    height=300,
)

# ---- Auto-validation ----
import json
try:
    json.loads(st.session_state.get("mockup_edit",""))
    st.success("✅ JSON is valid.")
except Exception as e:
    st.error(f"❌ Invalid JSON: {e}")

# ---- Preview ----
if df_by_sheet and st.session_state.get("mockup_edit"):
    st.divider()
    st.subheader("📈 Live Dashboard Preview")
    render_pages(df_by_sheet, st.session_state["mockup_edit"])
else:
    st.info("Upload data and generate a mockup to preview.")
