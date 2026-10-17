# AI Research Assistant

Give it any topic. An AI agent searches the web, reads the results, and writes a **cited research report**, available as validated JSON or as a live-streamed markdown report, through a FastAPI API.

Built as a portfolio project using **free APIs only** (no paid keys).

## Features

- **Agent with tool use**: the LLM decides what to search (function calling) and runs up to 3 search steps via Tavily.
- **Cited reports**: every claim comes with a source URL, and only URLs that were really returned by search are allowed.
- **Structured output**: the JSON report is validated with Pydantic and retried if validation fails.
- **Streaming**: the markdown report is streamed token by token.
- **Provider fallback**: Gemini is the default, Groq is the automatic backup on rate limit, timeout, connection error or server error.
- **Date-aware and source-aware prompt**: the agent knows today's date and avoids Reddit, forums and Medium.
- **REST API** built with FastAPI, with interactive docs.

## How it works

```
topic -> agent (LLM + web_search tool) -> research notes + sources
      -> report builder -> JSON report (Pydantic)   [POST /research]
      -> stream writer  -> markdown report (stream) [GET /research/stream]
```

1. `agent.py`: runs the search loop. The whole run stays on one provider; if that provider fails midway, the run restarts on the other one.
2. `report.py`: turns the notes into a validated `ResearchReport`.
3. `stream_report.py`: streams a readable markdown report.
4. `llm.py`: provider settings and fallback logic.
5. `search_tool.py`: Tavily search wrapper that never crashes the app.
6. `main.py`: FastAPI app.

## Tech stack

Python, `uv`, FastAPI, Uvicorn, Pydantic, OpenAI-compatible SDK (used for Gemini and Groq), Tavily.

## Setup

1. Clone the repo and install dependencies:

```bash
git clone https://github.com/vishalhirani978/ai-research-assistant.git
cd ai-research-assistant
uv sync
```

2. Copy `.env.example` to `.env` and fill in your keys:

```
GEMINI_API_KEY=
GROQ_API_KEY=
TAVILY_API_KEY=
LLM_PROVIDER=gemini
```

Where to get the free keys:

- Gemini: Google AI Studio (aistudio.google.com)
- Groq: console.groq.com
- Tavily: tavily.com

Never commit your `.env` file.

## Run

```bash
uv run python run_report.py        # asks for a topic, prints a JSON report
uv run python run_stream.py        # asks for a topic, streams a markdown report
uv run uvicorn main:app --reload   # starts the API
```

Interactive API docs: http://127.0.0.1:8000/docs

To use Groq first (PowerShell):

```powershell
$env:LLM_PROVIDER="groq"
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/research` | Returns a structured JSON report |
| GET | `/research/stream?topic=...` | Streams a markdown report (`text/plain`) |

The topic must be 2 to 200 characters.

**Example: JSON report**

```bash
curl -X POST http://127.0.0.1:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "Machine Learning vs Deep Learning"}'
```

Response (shortened):

```json
{
  "topic": "Machine Learning vs Deep Learning",
  "summary": "...",
  "key_findings": [
    {
      "finding": "DL employs deep neural networks that automatically discover hierarchical features directly from raw data",
      "source_urls": ["https://ischool.syracuse.edu/deep-learning-vs-machine-learning"]
    }
  ],
  "sources": [
    {
      "title": "Syracuse iSchool: Deep Learning vs Machine Learning",
      "url": "https://ischool.syracuse.edu/deep-learning-vs-machine-learning"
    }
  ],
  "limitations": "..."
}
```

**Example: streaming report**

```bash
curl -N --get "http://127.0.0.1:8000/research/stream" --data-urlencode "topic=Machine Learning vs Deep Learning"
```

If both providers are unavailable, `POST /research` returns HTTP 503.

## Known limitations

- **Free-tier limits**: Gemini and Groq free tiers have per-minute and daily limits, so a request can fail when both are exhausted. Wait a minute and retry.
- **Claims can be wrong**: the model sometimes adds details that are not on the cited page. Spot-check important claims against the sources.
- **Ambiguous topics** (for example a name shared by several people) can mix results. Use clear, specific topics.
- **Streaming starts late**: the agent finishes searching first, then the report streams.
- **Mid-stream failures** are not recovered; fallback only happens if the stream cannot start.

## Possible improvements

Web frontend, tests, Dockerfile, caching repeated topics, a per-claim verification pass, domain allow/deny lists for sources.