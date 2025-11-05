import pandas as pd

def load_excel(file):
    return pd.read_excel(file, sheet_name=None)

def summarize_dataframe(df: pd.DataFrame):
    return {
        "rows": df.shape[0],
        "cols": df.shape[1],
        "numeric": df.select_dtypes(include=["number"]).columns.tolist(),
        "categorical": df.select_dtypes(exclude=["number"]).columns.tolist()
    }

def generate_data_profile(excel_dict):
    profiles = {}
    for name, df in excel_dict.items():
        profiles[name] = summarize_dataframe(df)
    return profiles
