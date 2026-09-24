from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

from src.context.loaders import load_scenarios, load_sources, get_scenario
from src.context.builders import build_bounded_context
from src.ai.schemas import EvidenceSummary, HandoffSummary
from src.ai.prompt_builder import build_messages
from src.ai.ollama_adapter import OllamaAdapter
from src.ai.demo_adapter import DemoAdapter
from src.validation.output_validation import validate_output
from src.evaluation.writer import write_json

def config(root):
    return json.loads((root/"config/prototype.json").read_text(encoding="utf-8"))

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--scenario", required=True)
    p.add_argument("--provider", choices=["ollama","demo"], default="ollama")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()

def main():
    a=args()
    root=Path(__file__).resolve().parent
    cfg=config(root)
    scenario=get_scenario(load_scenarios(root), a.scenario)
    context, guard=build_bounded_context(scenario, load_sources(root))
    schema = EvidenceSummary if scenario["AI_Use_Case"]=="Evidence Summarisation" else HandoffSummary
    messages=build_messages(root, scenario, context, schema.model_json_schema())
    ts=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    request={
        "scenario_id":scenario["Scenario_ID"],"case_id":scenario["Synthetic_Case_ID"],
        "provider":a.provider,"model":cfg["default_model"],"simulation_mode":scenario["Simulation_Mode"],
        "guardrail_report":guard,"context":context,"messages":messages
    }
    write_json(root/"outputs/logs"/f"{scenario['Scenario_ID']}_{ts}_request.json", request)

    print(f"Scenario: {scenario['Scenario_ID']} — {scenario['Scenario_Title']}")
    print(f"Case: {scenario['Synthetic_Case_ID']}")
    print(f"Authorised sources: {guard['included_source_count']}")
    print(f"Wrong-case sources excluded: {guard['excluded_wrong_case_count']}")

    if a.dry_run:
        print("DRY RUN COMPLETE — no model was called.")
        return

    mode=scenario["Simulation_Mode"]
    if mode=="timeout":
        result={"scenario_id":scenario["Scenario_ID"],"generation_state":"Failed","failure_type":"simulated_timeout",
                "safe_failure":True,"guardrail_report":guard,"ai_output":None}
        write_json(root/"outputs/ai"/f"{scenario['Scenario_ID']}.json", result)
        print("SIMULATED TIMEOUT handled safely.")
        return
    if mode=="malformed_output":
        result={"scenario_id":scenario["Scenario_ID"],"generation_state":"Unusable","failure_type":"simulated_malformed_output",
                "safe_failure":True,"guardrail_report":guard,"raw_output":"{not-valid-json"}
        write_json(root/"outputs/ai"/f"{scenario['Scenario_ID']}.json", result)
        print("SIMULATED MALFORMED OUTPUT handled safely.")
        return

    if a.provider=="demo":
        output=DemoAdapter().generate(scenario, context)
        meta={"model":"deterministic-demo","formal_ai_evaluation":False}
    else:
        adapter=OllamaAdapter(cfg["default_model"],cfg["ollama_base_url"],cfg["temperature"])
        output,meta=adapter.parse(messages,schema)

    validation=validate_output(output, context)
    result={
        "scenario_id":scenario["Scenario_ID"],
        "case_id":scenario["Synthetic_Case_ID"],
        "ai_use_case":scenario["AI_Use_Case"],
        "provider":a.provider,
        "model":meta.get("model"),
        "formal_ai_evaluation": a.provider=="ollama",
        "generation_state":"Generated" if validation["validation_passed"] else "Unusable",
        "validation":validation,
        "guardrail_report":guard,
        "model_metadata":meta,
        "ai_output":output.model_dump(),
    }
    write_json(root/"outputs/ai"/f"{scenario['Scenario_ID']}.json", result)
    print("Validation passed:", validation["validation_passed"])
    print("Saved:", root/"outputs/ai"/f"{scenario['Scenario_ID']}.json")

if __name__=="__main__":
    main()
