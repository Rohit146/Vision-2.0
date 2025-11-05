import streamlit as st
import pandas as pd
from io import StringIO
from data_handler import load_excel, generate_data_profile
from mockup_generator import generate_bi_mockup
from visualizer import render_pages

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="AI BI Mockup Builder", layout="wide")
st.title("📊 AI BI Mockup Builder (Power BI / MicroStrategy)")

# Initialize session
if "mockup_spec" not in st.session_state:
    st.session_state["mockup_spec"] = ""
if "data_profile" not in st.session_state:
    st.session_state["data_profile"] = None
if "df_by_sheet" not in st.session_state:
    st.session_state["df_by_sheet"] = None

# ---------------- SIDEBAR ----------------
st.sidebar.header("📂 Data")
uploaded = st.sidebar.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded:
    st.session_state["df_by_sheet"] = load_excel(uploaded)
    st.session_state["data_profile"] = generate_data_profile(st.session_state["df_by_sheet"])
    st.sidebar.success(f"Loaded {len(st.session_state['df_by_sheet'])} sheet(s).")

# Controls
st.sidebar.header("⚙️ Session Controls")
if st.sidebar.button("🧹 Reset Session"):
    st.session_state.clear()
    st.experimental_rerun()

if st.sidebar.button("🗂 Duplicate Spec"):
    st.session_state["mockup_spec"] = st.session_state["mockup_spec"]

# ---------------- MAIN TABS ----------------
tab_data, tab_design, tab_preview = st.tabs(["📊 Data", "🧩 Design", "▶️ Preview Dashboard"])

# ---------------- TAB 1: DATA ----------------
with tab_data:
    st.subheader("📊 Uploaded Data Preview")
    if st.session_state["df_by_sheet"]:
        sheet = st.selectbox("Select Sheet", list(st.session_state["df_by_sheet"].keys()))
        st.dataframe(st.session_state["df_by_sheet"][sheet].head(100), use_container_width=True)
    else:
        st.info("Upload an Excel file to begin.")

# ---------------- TAB 2: DESIGN ----------------
with tab_design:
    st.subheader("🧠 BI Mockup Designer")

    goal = st.text_input("Objective", placeholder="e.g., Create quarterly sales dashboard with KPIs and charts.")
    role = st.selectbox("Role", ["BI Developer", "Data Analyst", "Finance Planner"], index=0)

    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("✨ Generate New Spec", disabled=not (goal and st.session_state["data_profile"])):
            with st.spinner("Generating compact JSON spec..."):
                spec = generate_bi_mockup(goal, st.session_state["data_profile"], role)
                st.session_state["mockup_spec"] = spec
    with colB:
        if st.button("♻️ Refresh Preview"):
            st.toast("Spec refreshed!", icon="🔄")

    # Editable text area (autosave)
    st.text_area(
        "Mockup Spec (editable JSON)",
        value=st.session_state.get("mockup_spec", ""),
        height=400,
        key="mockup_spec_editor",
        on_change=lambda: st.session_state.update({"mockup_spec": st.session_state.mockup_spec_editor})
    )

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download Spec JSON",
            st.session_state.get("mockup_spec", ""),
            file_name="mockup_spec.json"
        )
    with col2:
        st.success("💾 Changes saved automatically to memory.")

# ---------------- TAB 3: PREVIEW ----------------
with tab_preview:
    st.subheader("📈 Auto-Generated Dashboard")

    if not st.session_state["df_by_sheet"]:
        st.info("Upload an Excel file to visualize the dashboard.")
    elif not st.session_state.get("mockup_spec"):
        st.info("Generate or edit a mockup spec first.")
    else:
        render_pages(st.session_state["df_by_sheet"], st.session_state["mockup_spec"])
