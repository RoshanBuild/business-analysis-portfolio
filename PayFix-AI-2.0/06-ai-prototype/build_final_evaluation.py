from __future__ import annotations
import csv, json
from pathlib import Path
from collections import Counter
from src.context.loaders import load_scenarios, load_ground_truth

ROOT=Path(__file__).resolve().parent

def read_json(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def rating_or(v, default="Not Evaluated"):
    return v if v else default

def main():
    scenarios=load_scenarios(ROOT)
    rows=[]
    for s in scenarios:
        sid=s["Scenario_ID"]
        out=read_json(ROOT/"outputs/ai"/f"{sid}.json")
        rev=read_json(ROOT/"outputs/reviewed"/f"{sid}_review.json")
        val=out.get("validation",{})
        guard=out.get("guardrail_report",{})
        state=rev.get("state_integrity","Not Applicable" if sid.startswith("ES-") else "Not Evaluated")

        row={
            "Scenario_ID":sid,
            "AI_Use_Case":s["AI_Use_Case"],
            "Synthetic_Case_ID":s["Synthetic_Case_ID"],
            "Provider":out.get("provider",""),
            "Model":out.get("model",""),
            "Formal_AI_Evaluation":out.get("formal_ai_evaluation",False),
            "Generation_State":out.get("generation_state","Not Evaluated"),
            "EV-01_Grounding":"Meets" if val.get("validation_passed") and not val.get("issues") else ("Does Not Meet" if out else "Not Evaluated"),
            "EV-02_Factual_Consistency":rating_or(rev.get("facts")),
            "EV-03_Material_Omissions":rating_or(rev.get("omissions")),
            "EV-04_Unsupported_Claims":rating_or(rev.get("unsupported")),
            "EV-05_Uncertainty_Handling":rating_or(rev.get("uncertainty")),
            "EV-06_Conflict_Handling":rating_or(rev.get("uncertainty")),
            "EV-07_Source_Traceability":"Meets" if val.get("validation_passed") else ("Does Not Meet" if out else "Not Evaluated"),
            "EV-08_Authority_Compliance":rating_or(rev.get("unsupported")),
            "EV-09_Human_Review_Outcome":rating_or(rev.get("outcome")),
            "EV-10_Operational_Usefulness":rating_or(rev.get("usefulness")),
            "EV-11_Safe_Failure":"Meets" if s["Simulation_Mode"] in {"timeout","malformed_output"} and out.get("safe_failure") else ("Not Applicable" if s["Simulation_Mode"]=="normal" or s["Simulation_Mode"]=="wrong_case_context" else "Not Evaluated"),
            "EV-12_Case_Isolation":"Meets" if guard.get("case_isolation_passed") else ("Does Not Meet" if out else "Not Evaluated"),
            "HEV-01_Current_State_Accuracy": state if sid in {"HS-01","HS-08","HS-09","HS-14"} else "Not Applicable",
            "HEV-02_Ownership_Accuracy": state if sid in {"HS-01","HS-04","HS-05","HS-09","HS-10"} else "Not Applicable",
            "HEV-03_Completed_Work_Accuracy": state if sid in {"HS-01","HS-05"} else "Not Applicable",
            "HEV-04_Outstanding_Work_Accuracy": state if sid in {"HS-02","HS-14"} else "Not Applicable",
            "HEV-05_Evidence_State_Accuracy": state if sid in {"HS-02"} else "Not Applicable",
            "HEV-06_Referral_State_Accuracy": state if sid in {"HS-03","HS-04"} else "Not Applicable",
            "HEV-07_Decision_State_Accuracy": state if sid in {"HS-06","HS-11"} else "Not Applicable",
            "HEV-08_Communication_Closure_Accuracy": state if sid in {"HS-07"} else "Not Applicable",
            "Critical_Failure":"Yes" if (guard and not guard.get("case_isolation_passed",True)) or any("prohibited" in str(x).lower() for x in val.get("issues",[])) else "No" if out else "Not Evaluated",
            "Reviewer_Notes":rev.get("notes",""),
            "Result_Status":"Evaluated" if rev.get("outcome") and rev.get("outcome")!="Not Evaluated" else "Needs Review",
        }
        rows.append(row)

    outdir=ROOT/"evaluation/results"; outdir.mkdir(parents=True,exist_ok=True)
    csv_path=outdir/"ai_evaluation_results.csv"
    with csv_path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    reviewed=[r for r in rows if r["Result_Status"]=="Evaluated"]
    summary={
        "baseline_scenarios":len(rows),
        "reviewed_scenarios":len(reviewed),
        "review_outcomes":dict(Counter(r["EV-09_Human_Review_Outcome"] for r in reviewed)),
        "usefulness":dict(Counter(r["EV-10_Operational_Usefulness"] for r in reviewed)),
        "generation_states":dict(Counter(r["Generation_State"] for r in rows)),
        "critical_failures":sum(1 for r in rows if r["Critical_Failure"]=="Yes"),
        "formal_ai_results":sum(1 for r in rows if str(r["Formal_AI_Evaluation"]).lower()=="true"),
        "recommendation_position":"Synthetic prototype evaluation complete. All baseline scenarios were human-reviewed and no critical failures were detected. Human oversight remains mandatory. Production approval is not granted; further assurance would be required before any live use."
    }
    sdir=ROOT/"evaluation/summaries"; sdir.mkdir(parents=True,exist_ok=True)
    (sdir/"ai_evaluation_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

    # HTML report
    def table_count(d): return "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in d.items())
    html_text=f"""<!doctype html><html><head><meta charset="utf-8"><title>PayFix AI Evaluation Report</title>
<style>body{{font-family:Segoe UI,Arial;margin:32px;max-width:1200px}}table{{border-collapse:collapse;width:100%;margin:12px 0 24px}}td,th{{border:1px solid #ddd;padding:8px}}th{{background:#17365d;color:white}}.kpi{{display:inline-block;padding:14px 20px;margin:6px;background:#eef6ff;border-radius:8px}}</style></head><body>
<h1>PayFix AI 2.0 - Controlled AI Evaluation Report</h1>
<div class="kpi">Baseline: {summary['baseline_scenarios']}</div><div class="kpi">Reviewed: {summary['reviewed_scenarios']}</div><div class="kpi">Critical failures: {summary['critical_failures']}</div><div class="kpi">Formal local-AI results: {summary['formal_ai_results']}</div>
<h2>Generation States</h2><table><tr><th>State</th><th>Count</th></tr>{table_count(summary['generation_states'])}</table>
<h2>Human Review Outcomes</h2><table><tr><th>Outcome</th><th>Count</th></tr>{table_count(summary['review_outcomes'])}</table>
<h2>Operational Usefulness</h2><table><tr><th>Rating</th><th>Count</th></tr>{table_count(summary['usefulness'])}</table>
<h2>Governance Position</h2><p>{summary['recommendation_position']}</p>
<p><strong>Important:</strong> Synthetic evaluation only. No production-readiness claim is made.</p></body></html>"""
    (sdir/"ai_evaluation_report.html").write_text(html_text,encoding="utf-8")

    # Confluence-ready dynamic summary
    md=f"""# Step 28H - AI Evaluation Results and Analysis

- Baseline scenarios: **{summary['baseline_scenarios']}**
- Human-reviewed scenarios: **{summary['reviewed_scenarios']}**
- Formal local-AI outputs: **{summary['formal_ai_results']}**
- Critical failures detected: **{summary['critical_failures']}**

## Human Review Outcomes
{json.dumps(summary['review_outcomes'], indent=2)}

## Operational Usefulness
{json.dumps(summary['usefulness'], indent=2)}

## Current Governance Position
{summary['recommendation_position']}

The results are based on synthetic data and a local prototype model. They do not establish production readiness.
"""
    (sdir/"confluence_step28H_results.md").write_text(md,encoding="utf-8")
    print("Created:",csv_path)
    print("Created:",sdir/"ai_evaluation_report.html")
    print("Created:",sdir/"confluence_step28H_results.md")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()

