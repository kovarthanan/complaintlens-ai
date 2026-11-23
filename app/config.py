import os
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required setting: {name} (add it to .env)")
    return value

OPENAI_API_KEY = _require("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "5"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
PROMPT_VERSION = "v1"