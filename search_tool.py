import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web and return a clean list of sources. Never crashes."""
    try:
        response = tavily.search(
            query=query,
            max_results=max_results,
            exclude_domains=["reddit.com", "medium.com", "quora.com", "pinterest.com"],
        )
    except Exception as e:
        print(f"[search error] {e}")
        return [
            {
                "title": "Search failed",
                "url": "",
                "content": f"Search failed: {e}. Try a different query using normal words, without site: operators.",
            }
        ]
    return [
        {"title": r["title"], "url": r["url"], "content": r["content"]}
        for r in response["results"]
    ]