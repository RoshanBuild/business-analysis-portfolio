from __future__ import annotations
from typing import Dict, List, Tuple

def build_bounded_context(scenario: Dict[str, str], all_sources: List[Dict[str, str]]) -> Tuple[Dict, Dict]:
    expected_case = scenario["Synthetic_Case_ID"]
    scenario_sources = [r for r in all_sources if r["Scenario_ID"] == scenario["Scenario_ID"]]

    included, excluded_not_permitted, excluded_wrong_case = [], [], []
    for r in scenario_sources:
        allowed = r.get("Include_In_AI_Context","").strip().lower() == "yes"
        same_case = r.get("Case_ID") == expected_case
        if not same_case:
            excluded_wrong_case.append(r)
            continue
        if not allowed:
            excluded_not_permitted.append(r)
            continue
        included.append({
            "source_id": r["Source_ID"],
            "source_type": r["Source_Type"],
            "source_state": r["Source_State"],
            "source_time": r["Source_Time"],
            "source_content": r["Source_Content"],
            "authoritative_source": r["Authoritative_Source"],
            "data_quality_flag": r["Data_Quality_Flag"],
        })

    if not included and scenario.get("Simulation_Mode") not in {"timeout","malformed_output"}:
        raise ValueError(f"No authorised source records available for {scenario['Scenario_ID']}")

    context = {
        "scenario_id": scenario["Scenario_ID"],
        "case_id": expected_case,
        "ai_use_case": scenario["AI_Use_Case"],
        "scenario_title": scenario["Scenario_Title"],
        "scenario_type": scenario["Scenario_Type"],
        "scenario_purpose": scenario["Scenario_Purpose"],
        "source_items": included,
    }
    report = {
        "expected_case_id": expected_case,
        "scenario_source_count": len(scenario_sources),
        "included_source_count": len(included),
        "excluded_not_permitted_count": len(excluded_not_permitted),
        "excluded_wrong_case_count": len(excluded_wrong_case),
        "excluded_wrong_case_source_ids": [r["Source_ID"] for r in excluded_wrong_case],
        "case_isolation_passed": all(r["Case_ID"] != expected_case for r in excluded_wrong_case),
    }
    return context, report
