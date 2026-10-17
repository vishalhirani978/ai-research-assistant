from agent import run_agent
from stream_report import stream_report

topic = input("Research topic: ")
notes, sources = run_agent(topic)

print("\n--- REPORT ---\n")
for piece in stream_report(topic, notes, sources):
    print(piece, end="", flush=True)
print()