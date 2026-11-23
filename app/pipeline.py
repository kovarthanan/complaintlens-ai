from app.validate import load_and_validate
from app.redact import redact_dataframe
from app.classify_chain import classify_dataframe

def run_pipeline(csv_path: str, limit: int | None = None):
    df, report = load_and_validate(csv_path)   # step 1: clean input
    if limit:
        df = df.head(limit)
    df = redact_dataframe(df)                  # step 2: adds redacted_text
    df = classify_dataframe(df)                # step 3: reads redacted_text
    return df, report