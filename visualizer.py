import streamlit as st
import plotly.express as px
import pandas as pd
import json, re

def try_parse_json(text: str):
    """Tolerant JSON extractor."""
    if not text: return None, "Empty spec"
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

def compute_agg(series, agg):
    agg = (agg or "sum").lower()
    if agg=="sum": return series.sum()
    if agg=="avg": return series.mean()
    if agg=="min": return series.min()
    if agg=="max": return series.max()
    if agg=="count": return series.count()
    if agg=="distinct": return series.nunique()
    return series.sum()

def render_pages(df_by_sheet: dict, mockup_text: str):
    spec, err = try_parse_json(mockup_text)
    if err:
        st.error(f"Spec issue: {err}")
        return
    pages = spec.get("Pages") or []
    if not pages:
        st.warning("No 'Pages' in spec.")
        return
    for page in pages:
        st.subheader(f"📄 {page.get('name','Dashboard')}")
        sheet = st.selectbox("Data sheet", list(df_by_sheet.keys()), key=f"sheet_{page.get('name')}")
        df = df_by_sheet[sheet]

        # Filters (as sidebar multiselects)
        for f in page.get("Filters", []):
            col = f.get("field")
            if col and col in df.columns:
                vals = sorted(df[col].dropna().unique())
                sel = st.multiselect(f"Filter: {col}", vals, default=vals[:min(5,len(vals))])
                if sel:
                    df = df[df[col].isin(sel)]

        # KPIs
        kpis = page.get("KPIs", [])
        if kpis:
            st.markdown("### 📈 KPIs")
            cols = st.columns(min(len(kpis),4))
            for i,k in enumerate(kpis):
                f = k.get("field")
                if f in df.columns and pd.api.types.is_numeric_dtype(df[f]):
                    val = compute_agg(df[f], k.get("agg"))
                    cols[i % 4].metric(k.get("title", f), f"{val:,.2f}")
                else:
                    cols[i % 4].metric(k.get("title", f), "N/A")

        # Charts
        for sec in page.get("Layout", []):
            st.markdown(f"#### 📊 {sec.get('section','Visuals')}")
            for el in sec.get("elements", []):
                typ = (el.get("type") or "").lower()
                x, y = el.get("x"), el.get("y")
                if not (x and y) or x not in df.columns or y not in df.columns:
                    continue
                if typ == "bar":
                    fig = px.bar(df, x=x, y=y)
                elif typ == "line":
                    fig = px.line(df, x=x, y=y)
                elif typ == "pie":
                    fig = px.pie(df, names=x, values=y)
                elif typ == "table":
                    st.dataframe(df[[x,y]], use_container_width=True)
                    continue
                else:
                    continue
                st.plotly_chart(fig, use_container_width=True)
