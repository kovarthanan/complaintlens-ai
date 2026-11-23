# ComplaintLens

**AI complaint triage for US retail banking.** ComplaintLens redacts PII, classifies consumer complaints with schema-validated LLM output, flags regulatory risk (Reg E, Reg Z, UDAAP, elder financial abuse, fair lending), tracks response deadlines and writes a weekly complaint MIS report.

It is built as an **API-first service** that a bank's existing complaint platform (for example ServiceNow, Pega or Salesforce) could call, rather than a replacement for one.

> Independent portfolio project. Demo data is synthetic (fictional "Northbridge Bank") or drawn from the public [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/). No real customer data is included in this repository.

---

## The problem

Large banks receive thousands of complaints a week across the CFPB portal, email, apps and call centres. Manual triage means:

- **Urgent cases get buried**: a fraud complaint waits behind "app won't load".
- **Deadlines slip**: regulator-routed complaints have response timelines.
- **No clear numbers**: leadership can't see which product or process is causing the most pain.
- **AI is risky by default**: complaints contain SSNs and account numbers that must not reach an external LLM.

## How it works

```
CSV / API source
      │
      ▼
validate.py        clean input: required columns, empty rows, duplicates, bad dates
      │
      ▼
redact.py          PII → tokens ([SSN_1], [ACCOUNT_1]) on the server; raw text dropped
      │
      ▼
classify_chain.py  LangChain + Pydantic structured output, batched, with retry
      │            (invalid output → "needs_review", batch never fails)
      ▼
aggregate.py       pandas: counts, percentages, days open, deadline risk
      │
      ▼
report_chain.py    LLM writes the weekly MIS using ONLY the computed numbers
```

**Core rule: the LLM judges, pandas counts.** Every number in the report comes from code, never from the model.

## Output per complaint

| Field | Values |
|---|---|
| `sentiment` | positive, neutral, negative |
| `product` | checking_savings, credit_card, mortgage, auto_loan, personal_loan, digital_banking, money_transfer |
| `issue` | short snake_case description |
| `severity` | low, medium, high, critical |
| `regulatory_flag` | none, reg_e_error_resolution, reg_z_billing_dispute, udaap_risk, fair_lending, elder_financial_abuse |
| `language` | English, Spanish, Spanglish |
| `summary` | one English sentence (also for Spanish input) |
| `root_cause_hint`, `suggested_response` | free text, compliance-safe wording |

## Tech stack

| Area | Tools |
|---|---|
| LLM orchestration | LangChain (LCEL), `with_structured_output`, `.batch()`, `.with_retry()` |
| Validation | Pydantic |
| PII redaction | Microsoft Presidio + spaCy, custom SSN and routing-number recognisers |
| Data | pandas |
| API | FastAPI + Uvicorn |
| Config | python-dotenv |

## Project structure

```
complaintlens/
├── app/
│   ├── config.py          settings and secrets from .env
│   ├── schemas.py         Pydantic contract for LLM output
│   ├── validate.py        input cleaning
│   ├── redact.py          PII redaction
│   ├── classify_chain.py  per-complaint LLM classification
│   ├── aggregate.py       metrics and deadline maths
│   ├── report_chain.py    weekly MIS report
│   ├── pipeline.py        runs the steps in order
│   └── api.py             FastAPI endpoints
├── data/                  sample input (real data is git-ignored)
├── run.py                 command-line entry point
├── .env.example
└── requirements.txt
```

## Getting started

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg

cp .env.example .env    # then add your OpenAI API key
```

**Command line** (test on a few rows first to control cost):

```bash
python run.py data/sample_30.csv 5
```

**API:**

```bash
python -m uvicorn app.api:app --reload
```

Open `http://localhost:8000/docs` and call `POST /complaints/analyze` with a CSV file.

## Design decisions

- **Redact before the LLM.** The order of steps is a security decision, not just a coding choice.
- **Schema as contract.** One Pydantic model is shared by the LLM, the API and the analytics.
- **Fail soft.** One bad row is marked `needs_review` with its error reason instead of failing 10,000 rows.
- **Prompt versioning.** `PROMPT_VERSION` is tracked so every classification can be traced.
- **Fixed-clock testing.** Deadline logic accepts an `as_of` date, so results are repeatable.

## What testing found (and fixed)

- A Spanish complaint about an 82-year-old customer was first rated **low**: the English NER model had redacted most of the sentence as "names". After skipping name detection on Spanish text, it was correctly rated **critical / elder_financial_abuse**. Lesson: redaction quality directly affects classification quality.
- Presidio's built-in recogniser rejected a well-known sample SSN, letting it through; a custom pattern recogniser now catches it.
- Regulatory flags improved after the prompt defined each flag explicitly (prompt v1 → v3).

## Known limitations

- Names in Spanish text are not detected (production fix: add a Spanish spaCy model).
- Street addresses are not yet redacted.
- Classification accuracy has been checked manually on a small sample, not measured at scale.

## Roadmap

- [ ] Report endpoint (`/complaints/report`) combining aggregation and MIS
- [ ] SQLite storage with an audit log (model, prompt version, input hash)
- [ ] Automated ingestion (scheduled pull from the CFPB API or a ServiceNow export)
- [ ] pytest suite for redaction and deadline logic
- [ ] Accuracy evaluation against CFPB's own product and issue labels
- [ ] Streamlit / Angular dashboard