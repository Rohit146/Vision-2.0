import pandas as pd

def load_excel(file):
    return pd.read_excel(file, sheet_name=None)

def summarize_dataframe(df: pd.DataFrame):
    summary = []
    summary.append(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
    summary.append("Columns:")
    for col in df.columns:
        dtype = df[col].dtype
        sample = df[col].dropna().unique()[:3]
        summary.append(f" - {col} ({dtype}) → sample: {sample}")
    return "\n".join(summary)

def generate_data_profile(excel_dict):
    profiles = []
    for name, df in excel_dict.items():
        profiles.append(f"📄 Sheet: {name}")
        profiles.append(summarize_dataframe(df))
        profiles.append("-" * 40)
    return "\n".join(profiles)
