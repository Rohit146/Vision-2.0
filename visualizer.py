import streamlit as st
import plotly.express as px
import pandas as pd
import json, re

# ---------- parsing / validation ----------
def try_parse_json(text: str):
    try:
        match = re.search(r"\{[\s\S]*\}\s*$", text.strip())
        if not match:
            return None, "No JSON object found."
        return json.loads(match.group(0)), None
    except Exception as e:
        return None, f"JSON parse error: {e}"

def list_missing_fields(spec_page: dict, df: pd.DataFrame):
    missing = set()
    cols = set(df.columns)
    # KPIs
    for k in spec_page.get("KPIs", []):
        f = k.get("field")
        if f and f not in cols:
            missing.add(f)
    # Filters
    for flt in spec_page.get("Filters", []):
        f = flt.get("field")
        if f and f not in cols:
            missing.add(f)
    # Charts
    for sec in spec_page.get("Layout", []):
        for el in sec.get("elements", []):
            for key in ("x","y","color"):
                f = el.get(key)
                if f and f not in cols:
                    missing.add(f)
            for f in el.get("columns", []) or []:
                if f not in cols: missing.add(f)
            for f in el.get("groupby", []) or []:
                if f not in cols: missing.add(f)
            for m in el.get("metrics", []) or []:
                f = m.get("field")
                if f and f not in cols:
                    missing.add(f)
    return sorted(list(missing))

def apply_mapping_to_spec(spec_page: dict, mapping: dict):
    js = json.dumps(spec_page)
    for k,v in mapping.items():
        if v:  # only replace if user mapped something
            js = re.sub(rf'("{re.escape(k)}")', f'"{v}"', js)
    return json.loads(js)

# ---------- filters ----------
def apply_slicers(df: pd.DataFrame, spec_page: dict):
    filter_fields = [f.get("field") for f in spec_page.get("Filters", []) if f.get("field") in df.columns]
    selected = {}
    with st.sidebar:
        if filter_fields:
            st.markdown("### 🔎 Filters")
        for f in filter_fields:
            vals = sorted(df[f].dropna().unique().tolist())
            pick = st.multiselect(f, vals, default=vals[:min(5,len(vals))])
            if pick:
                selected[f] = set(pick)
    if selected:
        mask = pd.Series([True]*len(df))
        for col, allowed in selected.items():
            mask &= df[col].isin(list(allowed))
        df = df[mask]
    return df

# ---------- KPIs ----------
def compute_agg(series: pd.Series, agg: str):
    agg = (agg or "sum").lower()
    if agg == "sum":   return series.sum()
    if agg == "avg":   return series.mean()
    if agg == "min":   return series.min()
    if agg == "max":   return series.max()
    if agg == "count": return series.count()
    if agg == "distinct": return series.nunique()
    return series.sum()

def fmt(val, fmt_str):
    try:
        if fmt_str and fmt_str not in ("auto", ""):
            # naive formatter; for currencies use as-is
            return f"{val:,.2f}" if "0.00" in fmt_str else f"{val:,.0f}"
        if isinstance(val, float):
            return f"{val:,.2f}"
        return f"{val:,}"
    except Exception:
        return str(val)

def render_kpis(df: pd.DataFrame, spec_page: dict):
    kpis = spec_page.get("KPIs", []) or []
    if not kpis: return
    st.markdown("### 📌 KPIs")
    cols = st.columns(max(1, min(4, len(kpis))))
    for i,k in enumerate(kpis):
        title = k.get("title","KPI")
        field = k.get("field")
        agg = k.get("agg","sum")
        fmt_str = k.get("format","auto")
        if field in df.columns and pd.api.types.is_numeric_dtype(df[field]):
            val = compute_agg(df[field], agg)
            cols[i % len(cols)].metric(label=title, value=fmt(val, fmt_str))
        else:
            cols[i % len(cols)].metric(label=title, value="N/A")

# ---------- charts ----------
def render_chart(df: pd.DataFrame, el: dict):
    ctype = (el.get("type") or "").lower()
    if ctype == "table":
        cols = el.get("columns") or list(df.columns)[:8]
        if any(c not in df.columns for c in cols):
            return
        view = df[cols]
        # groupby + metrics
        if el.get("groupby") and el.get("metrics"):
            gcols = [g for g in el["groupby"] if g in view.columns]
            if gcols:
                agg_map = {}
                for m in el["metrics"]:
                    f = m.get("field")
                    a = (m.get("agg") or "sum").lower()
                    if f in view.columns:
                        agg_map[f] = a
                if agg_map:
                    view = view.groupby(gcols, dropna=False).agg(agg_map).reset_index()
        st.dataframe(view, use_container_width=True, hide_index=True)
        return

    x, y, color = el.get("x"), el.get("y"), el.get("color")
    agg = (el.get("agg") or "sum").lower()

    if not x or not y or x not in df.columns or y not in df.columns:
        return

    # aggregate if needed
    if pd.api.types.is_numeric_dtype(df[y]):
        gcols = [x] + ([color] if color and color in df.columns else [])
        grouped = df.groupby(gcols, dropna=False)[y]
        if   agg == "avg": data = grouped.mean().reset_index()
        elif agg == "min": data = grouped.min().reset_index()
        elif agg == "max": data = grouped.max().reset_index()
        elif agg == "count": data = grouped.count().reset_index(name=y)
        elif agg == "distinct": data = df.groupby(gcols, dropna=False)[y].nunique().reset_index(name=y)
        else: data = grouped.sum().reset_index()
    else:
        data = df

    title = f"{(el.get('y') or '').title()} by {(el.get('x') or '').title()}"

    if ctype == "bar":
        fig = px.bar(data, x=x, y=y, color=color, title=title)
    elif ctype == "line":
        fig = px.line(data, x=x, y=y, color=color, title=title, markers=True)
    elif ctype == "area":
        fig = px.area(data, x=x, y=y, color=color, title=title)
    elif ctype == "pie":
        fig = px.pie(data, names=x, values=y, color=color, title=title)
    elif ctype == "scatter":
        fig = px.scatter(data, x=x, y=y, color=color, title=title)
    elif ctype == "histogram":
        fig = px.histogram(data, x=x, y=y, color=color, title=title, barmode="overlay")
    elif ctype == "box":
        fig = px.box(data, x=x, y=y, color=color, title=title)
    else:
        return
    st.plotly_chart(fig, use_container_width=True)

# ---------- main renderer ----------
def render_pages(df_by_sheet: dict, mockup_text: str):
    spec, err = try_parse_json(mockup_text)
    if err:
        st.error(f"Spec issue: {err}")
        return

    pages = spec.get("Pages") or []
    if not pages:
        st.warning("No 'Pages' in spec.")
        return

    tab_titles = [p.get("name","Page") for p in pages]
    tabs = st.tabs(tab_titles)
    for tab, page in zip(tabs, pages):
        with tab:
            # sheet selection per page
            sheet = st.selectbox("Data sheet", list(df_by_sheet.keys()), key=f"sheet_{page.get('name','p')}")
            df = df_by_sheet[sheet].copy()

            # validate columns and offer mapping
            missing = list_missing_fields(page, df)
            mapping = {}
            if missing:
                st.warning(f"Missing fields: {', '.join(missing)}")
                with st.expander("Map missing fields to available columns"):
                    for m in missing:
                        mapping[m] = st.selectbox(f"Map '{m}' to:", [""] + list(df.columns), key=f"map_{page.get('name')}_{m}")
                if st.button("Apply Mapping", key=f"apply_{page.get('name')}"):
                    page = apply_mapping_to_spec(page, mapping)
                    st.experimental_rerun()

            # filters (sidebar)
            df_f = apply_slicers(df, page)

            # KPIs
            render_kpis(df_f, page)

            # sections -> charts/tables
            for sec in page.get("Layout", []):
                if sec.get("section"):
                    st.markdown(f"### 📂 {sec['section']}")
                for el in sec.get("elements", []):
                    render_chart(df_f, el)
