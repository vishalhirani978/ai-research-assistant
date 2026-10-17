import json
from llm import get_client, chat, chat_one, provider_order, PROVIDERS, FALLBACK_ERRORS
from search_tool import web_search
from datetime import date

client, model = get_client()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information on a topic. Returns a list of sources with title, url and content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                },
                "required": ["query"],
            },
        },
    }
]

SYSTEM_PROMPT = (
    "You are a careful research assistant. Use the web_search tool at least 2 times "
    "with different queries before answering. "
    "Rules: (1) Use ONLY facts that appear in the search results. Do not add numbers, "
    "product names, project names, or statuses from your own memory. "
    "(2) Every claim must name the source URL it came from. "
    "(3) If the search results do not cover something, write 'not found in sources'. "
    "(4) Write plain text with simple markdown. Never use special bracket citation markers; "
    "write each source as a plain URL in parentheses. "
    "(5) Prefer official sites, encyclopedias, reputable news, and .edu or documentation pages. "
    "Avoid Reddit, forums, Medium, Quora, and tag or index pages unless nothing better exists. "
    "(6) For time-sensitive topics, prefer the most recent sources and mention the date of the information."
)

SYSTEM_PROMPT = f"Today's date is {date.today():%B %d, %Y}. " + SYSTEM_PROMPT

def _run_agent_on(provider: str, topic: str, max_steps: int) -> tuple[str, dict[str, str]]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": topic},
    ]
    all_sources: dict[str, str] = {}
    model_name = PROVIDERS[provider]["model"]

    for step in range(max_steps):
        response = chat_one(provider, model=model_name, messages=messages, tools=TOOLS)
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content, all_sources

        messages.append(msg)

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            print(f"[step {step + 1}] ({provider}) searching: {args['query']}")
            results = web_search(args["query"])
            for r in results:
                if r.get("url"):
                    all_sources[r["url"]] = r.get("title", "")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(results),
                }
            )

    messages.append(
        {
            "role": "user",
            "content": "Stop searching now. Do NOT call any tools. Using only the search results above, write your final research notes with the source URL for each claim.",
        }
    )
    final = chat_one(provider, model=model_name, messages=messages)
    return final.choices[0].message.content, all_sources


def run_agent(topic: str, max_steps: int = 3) -> tuple[str, dict[str, str]]:
    """Returns (research_notes, {url: title}). The whole run stays on ONE provider;
    if it fails midway, the run restarts from scratch on the next provider."""
    last_error = None
    for name in provider_order():
        if not PROVIDERS[name]["api_key"]:
            continue
        try:
            return _run_agent_on(name, topic, max_steps)
        except FALLBACK_ERRORS as e:
            print(f"[{type(e).__name__}] {name} failed, restarting research on next provider...")
            last_error = e
    raise RuntimeError(f"All providers failed: {last_error}")


if __name__ == "__main__":
    topic = input("Research topic: ")
    notes, _ = run_agent(topic)
    print("\n" + notes)
