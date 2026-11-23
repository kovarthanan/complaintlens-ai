import sys
from app.pipeline import run_pipeline

csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_30.csv"
limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

df, report = run_pipeline(csv_path, limit=limit)
print("Validation:", report)
print(df["status"].value_counts())

if "error" in df.columns:
    print("\nFirst error:\n", df["error"].dropna().iloc[0])

wanted = ["complaint_id", "severity", "product", "summary"]
print(df[[c for c in wanted if c in df.columns]].head(10))

df.to_csv("data/output_enriched.csv", index=False)
print("Saved to data/output_enriched.csv")