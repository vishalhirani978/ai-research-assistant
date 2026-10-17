from search_tool import web_search

results = web_search("tell me about recent advances in LLM")
for r in results:
    print(f"Title: {r['title']}")
    print(f"Url:{r['url']}")
    print(f" {r['content'][:150]}...\n")