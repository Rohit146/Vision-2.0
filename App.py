import streamlit as st
from io import StringIO
from data_handler import load_excel, generate_data_profile
from mockup_generator import generate_bi_mockup
from visualizer import render_pages

st.set_page_config(page_title="AI BI Mockup Builder", layout="wide")
st.title("📊 AI BI Mockup Builder (Power BI / MicroStrategy)")

st.sidebar.header("Data")
uploaded = st.sidebar.file_uploader("Upload Excel", type=["xlsx","xls"])
profile = None
df_by_sheet = None

if uploaded:
    df_by_sheet = load_excel(uploaded)
    profile = generate_data_profile(df_by_sheet)
    st.sidebar.success(f"Loaded {len(df_by_sheet)} sheet(s)")

st.sidebar.header("Spec")
spec_file = st.sidebar.file_uploader("Load Spec (JSON)", type=["json"])
if spec_file:
    st.session_state["mockup_spec"] = spec_file.read().decode("utf-8")

colA, colB = st.columns([3,2])
with colA:
    st.subheader("Design")
    goal = st.text_input("Objective", placeholder="e.g., Build quarterly sales & margin dashboard by region/product")
    role = st.selectbox("Role", ["BI Developer","Data Analyst","Finance Planner"], index=0)
    gen_btn = st.button("Generate Mockup Spec", disabled=not (uploaded and goal))

    if gen_btn:
        with st.spinner("Generating compact JSON spec..."):
            spec = generate_bi_mockup(goal, profile or {}, role)
        st.session_state["mockup_spec"] = spec

    spec_text = st.text_area("Mockup Spec (editable JSON)", value=st.session_state.get("mockup_spec",""), height=380)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Download Spec (JSON)", data=spec_text, file_name="mockup_spec.json")
    with c2:
        if "mockup_spec" in st.session_state:
            st.success("Spec ready. Edit above and switch to Preview tab ➜")

with colB:
    st.subheader("Data Preview")
    if df_by_sheet:
        sheet = st.selectbox("Preview Sheet", list(df_by_sheet.keys()))
        st.dataframe(df_by_sheet[sheet].head(100), use_container_width=True)

st.divider()
preview_tab, spec_tab = st.tabs(["▶️ Preview Dashboard", "🧾 Raw Spec"])
with preview_tab:
    if not uploaded:
        st.info("Upload an Excel file to preview.")
    elif not st.session_state.get("mockup_spec"):
        st.info("Generate or load a mockup spec to preview.")
    else:
        render_pages(df_by_sheet, st.session_state["mockup_spec"])

with spec_tab:
    st.code(st.session_state.get("mockup_spec",""), language="json")
