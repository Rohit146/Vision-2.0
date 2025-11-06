import streamlit as st, plotly.express as px, json, re, pandas as pd

def parse_json(text):
    text = re.sub(r"```(json)?|```","",text)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m: return {}
    try: return json.loads(re.sub(r",(\s*[}\]])",r"\1",m.group(0)))
    except: return {}

def agg(series, op):
    op=(op or "sum").lower()
    return getattr(series, {"avg":"mean","sum":"sum",
                            "min":"min","max":"max",
                            "count":"count"}.get(op,"sum"))()

def render_story_dashboard(df_dict, spec_txt):
    spec = parse_json(spec_txt)
    for page in spec.get("Pages",[]):
        st.markdown(f"## 🏢 {page.get('name','Dashboard')}")
        sheet = st.selectbox("📊 Sheet", list(df_dict.keys()), key=f"s_{page.get('name','d')}")
        df = df_dict[sheet]

        # ---------- Story text ----------
        for s in page.get("Story",[]):
            st.markdown(f"### 🧭 {s['section']}")
            st.caption(s.get("text",""))

        # ---------- KPI row ----------
        kpis = page.get("KPIs",[])
        if kpis:
            cols = st.columns(min(4,len(kpis)))
            for i,k in enumerate(kpis):
                f=k.get("field"); 
                if f in df.columns and pd.api.types.is_numeric_dtype(df[f]):
                    v=agg(df[f],k.get("agg"))
                    cols[i%4].metric(k.get("title",f), f"{v:,.2f}")
                else:
                    cols[i%4].metric(k.get("title",f),"N/A")

        # ---------- Visuals (16:9) ----------
        st.markdown("### 📊 Visuals")
        for sec in page.get("Layout",[]):
            st.markdown(f"#### {sec.get('section','')}")
            for el in sec.get("elements",[]):
                x,y,typ=el.get("x"),el.get("y"),(el.get("type") or "").lower()
                if x not in df.columns or y not in df.columns: continue
                try:
                    fig=None
                    if typ=="bar": fig=px.bar(df,x=x,y=y)
                    elif typ=="line": fig=px.line(df,x=x,y=y)
                    elif typ=="pie": fig=px.pie(df,names=x,values=y)
                    elif typ=="table":
                        st.dataframe(df[[x,y]].head(20)); continue
                    if fig:
                        fig.update_layout(height=540,width=960,margin=dict(l=20,r=20,t=40,b=40),template="plotly_white")
                        st.plotly_chart(fig)
                except Exception as e:
                    st.warning(f"{typ} failed: {e}")
