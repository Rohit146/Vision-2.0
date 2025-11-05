# AI BI Mockup Builder (Power BI / MicroStrategy)

- Upload Excel → Generate **compact JSON spec** → Edit → **Auto dashboard** (KPIs, slicers, charts) → Export spec & data.
- Built for low token use (no long narratives).

## Run
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
streamlit run app.py
