import json
from pydantic import BaseModel, Field, ValidationError
from llm import get_client, chat

client, model = get_client()


class Source(BaseModel):
    title: str
    url: str


class KeyFinding(BaseModel):
    finding: str = Field(description="One clear factual finding")
    source_urls: list[str] = Field(description="URLs that support this finding")


class ResearchReport(BaseModel):
    topic: str
    summary: str = Field(description="3-5 sentence overview")
    key_findings: list[KeyFinding]
    sources: list[Source]
    limitations: str = Field(description="What is uncertain or missing")


def build_report(
    topic: str, notes: str, sources: dict[str, str], retries: int = 2
) -> ResearchReport:
    schema = json.dumps(ResearchReport.model_json_schema())
    source_list = "\n".join(f"- {title} | {url}" for url, title in sources.items())

    messages = [
        {
            "role": "system",
            "content": (
                "Convert the research notes into a JSON report. Reply with ONLY valid "
                "JSON matching this JSON schema, with no markdown fences:\n"
                f"{schema}\n"
                "Use only URLs from the allowed source list."
            ),
        },
        {
            "role": "user",
            "content": f"Topic: {topic}\n\nNotes:\n{notes}\n\nAllowed sources:\n{source_list}",
        },
    ]

    for _ in range(retries + 1):
        response = chat(client, 
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return ResearchReport.model_validate_json(raw)
        except ValidationError as e:
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": f"That JSON did not match the schema: {e}. Reply again with only the corrected JSON.",
                }
            )

    raise RuntimeError("Could not produce a valid report")
