from pathlib import Path
import json, sys, urllib.request

ROOT=Path(__file__).resolve().parent
checks = {
    "Scenario CSV": ROOT/"data/scenarios/ai_evaluation_scenarios.csv",
    "Source CSV": ROOT/"data/sources/ai_evaluation_sources.csv",
    "Ground truth CSV": ROOT/"data/reference/ai_evaluation_ground_truth.csv",
    "Evidence prompt": ROOT/"prompts/evidence_summary/task_v1.txt",
    "Handoff prompt": ROOT/"prompts/handoff_summary/task_v1.txt",
}
bad=False
for name,p in checks.items():
    ok=p.exists(); print(f"{name}: {'OK' if ok else 'MISSING'}"); bad |= not ok
try:
    with urllib.request.urlopen("http://localhost:11434/api/tags",timeout=5) as r:
        data=json.loads(r.read().decode())
    names=[m.get("name","") for m in data.get("models",[])]
    print("Ollama service: OK")
    print("Installed models:", ", ".join(names) or "None")
    if not any(n.startswith("llama3.2:3b") or n=="llama3.2:latest" for n in names):
        print("Model llama3.2:3b: NOT FOUND")
        bad=True
    else: print("Model llama3.2:3b: OK")
except Exception as e:
    print("Ollama service: NOT AVAILABLE", e); bad=True
sys.exit(1 if bad else 0)
