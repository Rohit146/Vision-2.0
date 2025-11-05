import streamlit as st
import pandas as pd
from data_handler import load_excel, generate_data_profile
from mockup_generator import generate_bi_mockup
from visualizer import render_dashboard
from report_exporter import export_pdf

st.set_page_config(page_title="AI BI Mockup Builder", layout="wide")
st.title("📊 AI BI Mockup Builder")

st.sidebar.header("⚙️ Settings")
role = st.sidebar.selectbox("Role", ["BI Developer","Data Analyst","Finance Planner"])
uploaded_file = st.sidebar.file_uploader("Upload Excel", type=["xlsx","xls"])

if uploaded_file:
    excel_data = load_excel(uploaded_file)
    profile = generate_data_profile(excel_data)
    st.success(f"Loaded {len(excel_data)} sheet(s).")

    prompt = st.text_area("Objective", placeholder="e.g., Build quarterly sales KPI dashboard.")
    if st.button("Generate BI Mockup"):
        with st.spinner("Generating BI-ready mockup..."):
            mockup = generate_bi_mockup(prompt, profile, role)
        st.subheader("🧩 Mockup Specification (Editable)")
        mockup_edit = st.text_area("Edit Mockup", value=mockup, height=300)
        st.session_state["mockup_edit"] = mockup_edit

    if "mockup_edit" in st.session_state:
        edited = st.session_state["mockup_edit"]
        st.download_button("⬇️ Export Spec", edited, "mockup_spec.txt")
        if st.button("Export PDF"):
            pdf = export_pdf(edited)
            with open(pdf, "rb") as f:
                st.download_button("⬇️ Download PDF", f, "mockup_spec.pdf")

        st.divider()
        st.subheader("📈 Interactive Dashboard")
        sheet = st.selectbox("Choose Sheet", list(excel_data.keys()))
        render_dashboard(excel_data[sheet], edited)
else:
    st.info("Upload an Excel file to start.")
