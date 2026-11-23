from typing import Literal
from pydantic import BaseModel, Field

Product = Literal["checking_savings", "credit_card", "mortgage",
                  "auto_loan", "personal_loan", "digital_banking", "money_transfer"]
Severity = Literal["low", "medium", "high", "critical"]
RegFlag = Literal["none", "reg_e_error_resolution", "reg_z_billing_dispute",
                  "udaap_risk", "fair_lending", "elder_financial_abuse"]

class ComplaintAnalysis(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    product: Product
    issue: str = Field(description="Short snake_case issue, e.g. unauthorized_transaction")
    severity: Severity = Field(description="critical = fraud, unauthorized txn, account frozen")
    regulatory_flag: RegFlag
    language: Literal["English", "Spanish", "Spanglish"]
    summary: str = Field(description="One English sentence")
    root_cause_hint: str
    suggested_response: str = Field(description="Polite, no refund promises, add fraud-safety line")