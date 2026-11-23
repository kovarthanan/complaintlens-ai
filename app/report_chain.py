import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from app.config import MODEL_NAME

SYSTEM = """You write a weekly complaint MIS for a US retail bank's operations head.
Use ONLY the numbers in STATS. Never calculate, estimate or invent numbers.
Format:
WEEKLY COMPLAINT MIS | {period}
- Totals and severity split
- TOP 3 COMPLAINT DRIVERS, one line each
- CRITICAL and DEADLINE RISK counts
- REGULATORY EXPOSURE
- 3 ACTION ITEMS, each starting with the owning team
Under 200 words. Plain text.
- List EVERY regulatory flag in STATS, even if its count is 1.
- Each action item must name specific complaint IDs from CRITICAL COMPLAINTS where relevant.
- Mention elder_financial_abuse first if present; it is the highest-risk flag."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", "STATS:\n{stats}\n\nCRITICAL COMPLAINTS:\n{critical}"),
])
chain = prompt | ChatOpenAI(model=MODEL_NAME, temperature=0.2) | StrOutputParser()

def build_report(ok, summary: dict, period: str) -> str:
    crit = ok[ok["severity"] == "critical"]
    critical = "\n".join(f"- {r.complaint_id}: {r.summary}"
                         for r in crit.itertuples()) or "none"
    return chain.invoke({"period": period,
                         "stats": json.dumps(summary, indent=2),
                         "critical": critical})