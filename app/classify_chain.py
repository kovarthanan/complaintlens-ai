import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.config import MODEL_NAME, MAX_CONCURRENCY, MAX_RETRIES
from app.schemas import ComplaintAnalysis

SYSTEM = """You are a complaint analyst at a US retail bank.
Rules:
- severity=critical for fraud, unauthorized transactions, frozen accounts or elder abuse.
- regulatory_flag:
  reg_e_error_resolution = unauthorized or wrong electronic transfer (ACH, debit card, Zelle, wire)
  reg_z_billing_dispute = credit card billing error or unauthorized credit card charge
  udaap_risk = misleading ads, hidden or undisclosed fees, promised bonus not paid
  elder_financial_abuse = an older customer being exploited
  fair_lending = credit denied with no reason or possible discrimination
- Use the customer-selected product as a strong hint for product.
- Tokens like [ACCOUNT_1] are redacted values. Never guess them.
- summary: one English sentence, even if the complaint is in Spanish.
- suggested_response: polite, never blame the customer, never promise refunds, dates or amounts.
- issue describes the problem in snake_case (e.g. escrow_increase); never repeat the regulatory_flag value.
- reg_z_billing_dispute applies ONLY to credit card products. Any unauthorized credit card charge is reg_z_billing_dispute.
- Never tell the customer to monitor their account or avoid fees.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", "Customer-selected product: {product}\nComplaint:\n{text}"),
])

llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

chain = (prompt | llm.with_structured_output(ComplaintAnalysis)) \
        .with_retry(stop_after_attempt=MAX_RETRIES + 1)

def classify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    inputs = [{"text": t, "product": p}
          for t, p in zip(df["redacted_text"], df["product_raw"])]
    results = chain.batch(inputs, config={"max_concurrency": MAX_CONCURRENCY},
                          return_exceptions=True)
    rows = []
    for cid, r in zip(df["complaint_id"], results):
        if isinstance(r, Exception):
            rows.append({
                "complaint_id": cid,
                "status": "needs_review",
                "error": f"{type(r).__name__}: {str(r)[:300]}",
            })
        else:
            rows.append({"complaint_id": cid, "status": "ok", **r.model_dump()})
    return df.merge(pd.DataFrame(rows), on="complaint_id", how="left")