import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.pipeline import run_pipeline

app = FastAPI(title="ComplaintLens API", version="1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/complaints/analyze")
def analyze(file: UploadFile = File(...), limit: int | None = None):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")
    try:
        df, report = run_pipeline(file.file, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    results = json.loads(df.to_json(orient="records", date_format="iso"))
    return {"validation": report, "count": len(results), "results": results}