from agent import run_agent
from report import build_report

topic = input("Research topic: ")
notes, sources = run_agent(topic)
report = build_report(topic, notes, sources)

print("\n" + report.model_dump_json(indent=2))