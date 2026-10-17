import os
from dotenv import load_dotenv
from openai import (
    OpenAI,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)

load_dotenv()

PROVIDERS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": "gemini-3.8-flash",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": "openai/gpt-oss-120b",
    },
}

PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

FALLBACK_ERRORS = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)


def get_client():
    cfg = PROVIDERS[PROVIDER]
    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    return client, cfg["model"]


def chat(client, **kwargs):
    """Calls the chosen provider; on rate limit, timeout or server error, tries the other one."""
    order = [PROVIDER] + [p for p in PROVIDERS if p != PROVIDER]
    last_error = None
    for name in order:
        cfg = PROVIDERS[name]
        if not cfg["api_key"]:
            continue
        c = OpenAI(
            base_url=cfg["base_url"],
            api_key=cfg["api_key"],
            timeout=30,
            max_retries=0,
        )
        try:
            return c.chat.completions.create(**{**kwargs, "model": cfg["model"]})
        except FALLBACK_ERRORS as e:
            print(f"[{type(e).__name__}] {name} failed, trying next provider...")
            last_error = e
    raise RuntimeError(f"All providers failed: {last_error}")

    

def provider_order():
    return [PROVIDER] + [p for p in PROVIDERS if p != PROVIDER]


def chat_one(name, **kwargs):
    """Calls ONE specific provider, with no fallback. Errors go up to the caller."""
    cfg = PROVIDERS[name]
    c = OpenAI(
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        timeout=30,
        max_retries=0,
    )
    return c.chat.completions.create(**{**kwargs, "model": cfg["model"]})