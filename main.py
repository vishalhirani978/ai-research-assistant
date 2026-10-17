from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent import run_agent
from report import build_report, ResearchReport
from stream_report import stream_report

app = FastAPI(title="AI Research Assistant")


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=200)


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/research", response_model=ResearchReport)
def research(req: ResearchRequest):
    """Returns the structured JSON report."""
    try:
        notes, sources = run_agent(req.topic)
        return build_report(req.topic, notes, sources)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/research/stream")
def research_stream(topic: str):
    """Streams the markdown report live."""
    notes, sources = run_agent(topic)
    return StreamingResponse(
        stream_report(topic, notes, sources), media_type="text/plain"
    )