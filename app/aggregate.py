import pandas as pd

RESPONSE_DAYS = 15  # assumed response target; make configurable

def aggregate(df: pd.DataFrame, as_of: str | None = None):
    ok = df[df["status"] == "ok"].copy()
    today = pd.Timestamp(as_of) if as_of else pd.Timestamp.today().normalize()
    ok["days_open"] = (today - pd.to_datetime(ok["date_received"])).dt.days
    ok["days_to_response_deadline"] = RESPONSE_DAYS - ok["days_open"]

    def pct(col):
        return (ok[col].value_counts(normalize=True) * 100).round(1).to_dict()

    summary = {
        "total": len(ok),
        "needs_review": int((df["status"] == "needs_review").sum()),
        "severity_pct": pct("severity"),
        "sentiment_pct": pct("sentiment"),
        "by_product": ok["product"].value_counts().to_dict(),
        "top_issues": ok["issue"].value_counts().head(5).to_dict(),
        "regulatory": ok.loc[ok["regulatory_flag"] != "none",
                             "regulatory_flag"].value_counts().to_dict(),
        "critical": int((ok["severity"] == "critical").sum()),
        "deadline_risk": int((ok["days_to_response_deadline"] <= 3).sum()),
    }
    return ok, summary