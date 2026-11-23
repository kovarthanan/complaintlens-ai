from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

TOKENS = {
    "US_SSN": "SSN", "CREDIT_CARD": "CARD", "US_BANK_NUMBER": "ACCOUNT",
    "ABA_ROUTING_NUMBER": "ROUTING", "PHONE_NUMBER": "PHONE",
    "EMAIL_ADDRESS": "EMAIL", "PERSON": "NAME",
}
ALLOW = ["Call", "Called", "Zelle", "Venmo", "PayPal", "Cash App", "Reach"]

_analyzer = AnalyzerEngine()
_analyzer.registry.add_recognizer(PatternRecognizer(
    supported_entity="US_SSN", name="ssn_any",
    patterns=[Pattern("ssn", r"\b\d{3}-\d{2}-\d{4}\b", 0.6)],
    context=["ssn", "social"]))
_analyzer.registry.add_recognizer(PatternRecognizer(
    supported_entity="ABA_ROUTING_NUMBER", name="routing_any",
    patterns=[Pattern("routing", r"\b\d{9}\b", 0.4)],
    context=["routing", "aba"]))

def _drop_overlaps(results):
    kept = []
    for r in sorted(results, key=lambda r: r.score, reverse=True):
        if all(r.end <= k.start or r.start >= k.end for k in kept):
            kept.append(r)
    return sorted(kept, key=lambda r: r.start)

SPANISH_HINTS = [" el ", " la ", " de ", " que ", " mi ", " y ", " ya ", " del ", " no "]

def _looks_spanish(text: str) -> bool:
    t = f" {text.lower()} "
    return sum(h in t for h in SPANISH_HINTS) >= 2

def redact(text: str) -> tuple[str, int]:
    entities = [e for e in TOKENS if not (e == "PERSON" and _looks_spanish(text))]
    found = _analyzer.analyze(text=text, entities=entities, language="en",
                          score_threshold=0.4, allow_list=ALLOW)    
    counters, seen, spans = {}, {}, []
    for r in _drop_overlaps(found):
        original = text[r.start:r.end]
        if original not in seen:
            label = TOKENS[r.entity_type]
            counters[label] = counters.get(label, 0) + 1
            seen[original] = f"[{label}_{counters[label]}]"
        spans.append((r.start, r.end, seen[original]))
    for start, end, token in reversed(spans):
        text = text[:start] + token + text[end:]
    return text, len(spans)

def redact_dataframe(df):
    out = df["consumer_narrative"].apply(redact)
    df["redacted_text"] = out.str[0]
    df["pii_count"] = out.str[1]
    return df.drop(columns=["consumer_narrative"])