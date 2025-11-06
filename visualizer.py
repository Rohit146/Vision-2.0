import streamlit as st
import plotly.express as px
import pandas as pd
import json, re

# ---------------- JSON PARSER ----------------
def try_parse_json(text: str):
    if not text:
        return None, "Empty spec"
    text = re.sub(r"```(json)?", "", text)
    text = re.sub(r"```", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None, "No JSON block found"
    candidate = re.sub(r",(\s*[}\]])", r"\1", match.group(0))
    try:
        return json.loads(candidate), None
    except Exception as e:
        return None, f"JSON error: {e}"

# ---------------- AGGREGATION ----------------
def compute_agg(series, agg):
    agg = (agg or "sum").lower()
    if agg == "sum": return series.sum()
    if agg == "avg": return series.mean()
    if agg == "min": return series.min()
    if agg == "max": return series.max()
    if agg == "count": return series.count()
    if agg == "distinct": return series.nunique()
    return series.sum()

# ---------------- MAIN STORY RENDERER ----------------
def render_story_dashboard(df_by_sheet: dict, mockup_text: str):
    spec, err = try_parse_json(mockup_text)
    if err:
        st.error(f"Spec issue: {err}")
        return

    pages = spec.get("Pages") or []
    if not pages:
        st.warning("No 'Pages' found in spec.")
        return

    for page in pages:
        st.markdown(f"## 🏢 {page.get('name', 'Dashboard')}")
        sheet = st.selectbox("📊 Select Data Sheet", list(df_by_sheet.keys()), key=f"sheet_{page.get('name', 'default')}")
        df = df_by_sheet[sheet]

        # ---- STORY SECTIONS ----
        story = page.get("Story", [])
        if story:
            for s in story:
                st.markdown(f"### 🧭 {s.get('section')}")
                st.caption(s.get("text", ""))

        # ---- KPI Section ----
        kpis = page.get("KPIs", [])
        if kpis:
            st.markdown("### 📈 Key Metrics")
            cols = st.columns(min(len(kpis), 4))
            for i, k in enumerate(kpis):
                field = k.get("field")
                title = k.get("title", field)
                agg = k.get("agg", "sum")
                if field in df.columns and pd.api.types.is_numeric_dtype(df[field]):
                    val = compute_agg(df[field], agg)
                    cols[i % 4].metric(title, f"{val:,.2f}")
                else:
                    cols[i % 4].metric(title, "N/A")

        # ---- Visual Layout ----
        layouts = page.get("Layout", [])
        st.markdown("### 📊 Visuals & Trends")
        for sec in layouts:
            section_title = sec.get("section", "Visuals")
            st.markdown(f"#### {section_title}")
            for el in sec.get("elements", []):
                typ = (el.get("type") or "").lower()
                x, y = el.get("x"), el.get("y")
                if not (x and y) or x not in df.columns or y not in df.columns:
                    continue
                try:
                    if typ == "bar":
                        fig = px.bar(df, x=x, y=y, title=f"{y} by {x}", height=500, width=900)
                    elif typ == "line":
                        fig = px.line(df, x=x, y=y, title=f"{y} trend over {x}", height=500, width=900)
                    elif typ == "pie":
                        fig = px.pie(df, names=x, values=y, title=f"{y} distribution by {x}", height=500, width=900)
                    else:
                        continue
                    fig.update_layout(margin=dict(l=30, r=30, t=50, b=30))
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"⚠️ Could not render {typ} chart ({e})")

        # ---- Recommendations / Insights ----
        if any(s.get("section", "").lower() == "recommendations" for s in story):
            st.markdown("---")
            st.markdown("### 💡 Executive Summary & Next Steps")
            st.info("This section summarizes insights and suggests strategic actions based on the trends observed.")
