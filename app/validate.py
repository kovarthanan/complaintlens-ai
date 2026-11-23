import pandas as pd

COLUMN_MAP = {
    "Complaint ID": "complaint_id",
    "Date received": "date_received",
    "Submitted via": "submitted_via",
    "Product": "product_raw",
    "Sub-product": "sub_product",
    "Issue": "cfpb_issue",
    "State": "state",
    "Consumer complaint narrative": "consumer_narrative",
}
REQUIRED = ["complaint_id", "date_received", "consumer_narrative"]

def load_and_validate(path: str) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(path, dtype=str)
    df = df.rename(columns=COLUMN_MAP)

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    df = df[[c for c in COLUMN_MAP.values() if c in df.columns]]
    total = len(df)

    df["consumer_narrative"] = df["consumer_narrative"].str.strip()
    df = df[df["consumer_narrative"].fillna("") != ""]
    df = df.drop_duplicates(subset="complaint_id")
    df["date_received"] = pd.to_datetime(df["date_received"], errors="coerce")
    df = df.dropna(subset=["date_received"])

    report = {"total_rows": total, "valid_rows": len(df), "dropped": total - len(df)}
    return df.reset_index(drop=True), report