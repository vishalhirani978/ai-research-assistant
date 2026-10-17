from openai import OpenAI
from llm import PROVIDERS, PROVIDER, FALLBACK_ERRORS

CHAR_FIXES = str.maketrans({
    "\u2011": "-",   # non-breaking hyphen
    "\u2010": "-",   # hyphen
    "\u00a0": " ",   # non-breaking space
    "\u202f": " ",   # narrow non-breaking space
})


def clean(text: str) -> str:
    return text.translate(CHAR_FIXES)


def stream_report(topic: str, notes: str, sources: dict[str, str]):
    """Yields the report text chunk by chunk. Falls back to the other provider on errors."""
    source_list = "\n".join(f"- {title} | {url}" for url, title in sources.items())
    messages = [
        {
            "role": "system",
            "content": (
                "Write a clear markdown research report from the notes. "
                "Use ONLY facts from the notes. After each claim, put the plain source URL "
                "in parentheses, like (https://example.com). "
                "Never use 【 】 brackets or footnote markers. "
                "End with a 'Sources' list using only the allowed URLs."
            ),
        },
        {
            "role": "user",
            "content": f"Topic: {topic}\n\nNotes:\n{notes}\n\nAllowed sources:\n{source_list}",
        },
    ]

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
            stream = c.chat.completions.create(
                model=cfg["model"], messages=messages, stream=True
            )
        except FALLBACK_ERRORS as e:
            print(f"[{type(e).__name__}] {name} failed, trying next provider...")
            last_error = e
            continue

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield clean(chunk.choices[0].delta.content)
        return

    raise RuntimeError(f"All providers failed: {last_error}")