import streamlit as st
import plotly.express as px
import pandas as pd
import json, re

# ---------------- JSON PARSER ----------------
def try_parse_json(text: str):
    """Tolerant JSON extractor & validator."""
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

# ---------------- MAIN DASHBOARD RENDERER ----------------
def render_pages(df_by_sheet: dict, mockup_text: str):
    """Render dashboard (KPIs, filters, charts) from the BI mockup spec."""
    spec, err = try_parse_json(mockup_text)
    if err:
        st.error(f"Spec issue: {err}")
        return

    pages = spec.get("Pages") or []
    if not pages:
        st.warning("No 'Pages' found in spec.")
        return

    for page in pages:
        st.subheader(f"📄 {page.get('name', 'Dashboard')}")
        sheet = st.selectbox("Data Sheet", list(df_by_sheet.keys()), key=f"sheet_{page.get('name', 'default')}")
        df = df_by_sheet[sheet]

        # ------------- Filters -------------
        filters = page.get("Filters", [])
        if filters:
            with st.expander("🔎 Filters", expanded=False):
                for f in filters:
                    field = f.get("field")
                    if field and field in df.columns:
                        vals = sorted(df[field].dropna().unique())
                        selected = st.multiselect(f"Filter by {field}", vals, default=vals[:min(5, len(vals))])
                        if selected:
                            df = df[df[field].isin(selected)]

        # ------------- KPIs -------------
        kpis = page.get("KPIs", [])
        if kpis:
            st.markdown("### 📈 KPIs")
            cols = st.columns(min(len(kpis), 4))
            for i, k in enumerate(kpis):
                f = k.get("field")
                title = k.get("title", f)
                agg = k.get("agg", "sum")
                if f in df.columns and pd.api.types.is_numeric_dtype(df[f]):
                    val = compute_agg(df[f], agg)
                    cols[i % 4].metric(title, f"{val:,.2f}")
                else:
                    cols[i % 4].metric(title, "N/A")

        # ------------- Charts -------------
        layouts = page.get("Layout", [])
        for sec in layouts:
            section_title = sec.get("section", "Visuals")
            st.markdown(f"#### 📊 {section_title}")
            for el in sec.get("elements", []):
                typ = (el.get("type") or "").lower()
                x, y = el.get("x"), el.get("y")
                if not (x and y) or x not in df.columns or y not in df.columns:
                    continue
                try:
                    if typ == "bar":
                        fig = px.bar(df, x=x, y=y, title=f"{y} by {x}")
                    elif typ == "line":
                        fig = px.line(df, x=x, y=y, title=f"{y} trend by {x}")
                    elif typ == "pie":
                        fig = px.pie(df, names=x, values=y, title=f"{y} by {x}")
                    elif typ == "table":
                        st.dataframe(df[[x, y]].head(50), use_container_width=True)
                        continue
                    else:
                        continue
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"⚠️ Could not render {typ} chart ({e})")
