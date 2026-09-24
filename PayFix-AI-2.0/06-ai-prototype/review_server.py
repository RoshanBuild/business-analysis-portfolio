from __future__ import annotations
import json, html, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SCENARIOS=[]
import csv
with (ROOT/"data/scenarios/ai_evaluation_scenarios.csv").open("r",encoding="utf-8-sig",newline="") as f:
    SCENARIOS=list(csv.DictReader(f))
GT={}
with (ROOT/"data/reference/ai_evaluation_ground_truth.csv").open("r",encoding="utf-8-sig",newline="") as f:
    GT={r["Scenario_ID"]:r for r in csv.DictReader(f)}

def load_output(sid):
    p=ROOT/"outputs/ai"/f"{sid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def load_review(sid):
    p=ROOT/"outputs/reviewed"/f"{sid}_review.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def esc(x): return html.escape(str(x or ""))

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        sid=q.get("scenario",[SCENARIOS[0]["Scenario_ID"]])[0]
        scen=next((s for s in SCENARIOS if s["Scenario_ID"]==sid),SCENARIOS[0])
        out=load_output(sid)
        rev=load_review(sid)
        gt=GT.get(sid,{})
        nav="".join(f'<option value="{esc(s["Scenario_ID"])}" {"selected" if s["Scenario_ID"]==sid else ""}>{esc(s["Scenario_ID"]+" — "+s["Scenario_Title"])}</option>' for s in SCENARIOS)
        outtxt=json.dumps(out,indent=2,ensure_ascii=False) if out else "No output file found."
        srctxt=json.dumps(out.get("ai_output") if out else {},indent=2,ensure_ascii=False)
        gttext=json.dumps(gt,indent=2,ensure_ascii=False)

        def opt(current, vals):
            return "".join(f'<option {"selected" if current==v else ""}>{esc(v)}</option>' for v in vals)

        body=f"""<!doctype html><html><head><meta charset="utf-8"><title>PayFix AI Review</title>
        <style>body{{font-family:Segoe UI,Arial;margin:24px;max-width:1400px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
        pre{{white-space:pre-wrap;background:#f5f7fa;padding:12px;border-radius:8px;max-height:480px;overflow:auto}}
        label{{font-weight:600}} select,textarea{{width:100%;padding:8px;margin:4px 0 12px}} button{{padding:10px 18px}}
        .note{{background:#eef6ff;padding:12px;border-left:4px solid #2b6cb0}}</style></head><body>
        <h1>PayFix AI 2.0 — Human Review Console</h1>
        <p class="note">AI output is derived assistance. Source records remain authoritative. Review outcomes are Accept / Correct / Reject / Disregard.</p>
        <form method="get"><label>Scenario</label><select name="scenario" onchange="this.form.submit()">{nav}</select></form>
        <h2>{esc(sid)} — {esc(scen["Scenario_Title"])}</h2>
        <div class="grid"><div><h3>AI Output</h3><pre>{esc(srctxt)}</pre></div><div><h3>Evaluation Reference (synthetic ground truth)</h3><pre>{esc(gttext)}</pre></div></div>
        <form method="post">
        <input type="hidden" name="scenario" value="{esc(sid)}">
        <label>Human Review Outcome</label><select name="outcome">{opt(rev.get("outcome","Not Evaluated"),["Not Evaluated","Accept","Correct","Reject","Disregard"])}</select>
        <label>Factual consistency</label><select name="facts">{opt(rev.get("facts","Not Evaluated"),["Not Evaluated","Meets","Partially Meets","Does Not Meet"])}</select>
        <label>Material omissions</label><select name="omissions">{opt(rev.get("omissions","Not Evaluated"),["Not Evaluated","Meets","Partially Meets","Does Not Meet"])}</select>
        <label>Unsupported claims / authority compliance</label><select name="unsupported">{opt(rev.get("unsupported","Not Evaluated"),["Not Evaluated","Meets","Partially Meets","Does Not Meet"])}</select>
        <label>Uncertainty / conflict handling</label><select name="uncertainty">{opt(rev.get("uncertainty","Not Evaluated"),["Not Evaluated","Meets","Partially Meets","Does Not Meet","Not Applicable"])}</select>
        <label>State integrity (Handoff only)</label><select name="state_integrity">{opt(rev.get("state_integrity","Not Applicable" if sid.startswith("ES-") else "Not Evaluated"),["Not Evaluated","Meets","Partially Meets","Does Not Meet","Not Applicable"])}</select>
        <label>Operational usefulness</label><select name="usefulness">{opt(rev.get("usefulness","Not Evaluated"),["Not Evaluated","Helpful","Somewhat Helpful","Not Helpful","Harmful / Misleading"])}</select>
        <label>Reason / Notes</label><textarea name="notes" rows="5">{esc(rev.get("notes",""))}</textarea>
        <button type="submit">Save Review</button></form>
        </body></html>"""
        b=body.encode("utf-8")
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_POST(self):
        n=int(self.headers.get("Content-Length","0"))
        form=urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8"))
        sid=form.get("scenario",[""])[0]
        review={k:form.get(k,[""])[0] for k in ["outcome","facts","omissions","unsupported","uncertainty","state_integrity","usefulness","notes"]}
        review["scenario_id"]=sid
        p=ROOT/"outputs/reviewed"/f"{sid}_review.json"; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(review,indent=2,ensure_ascii=False),encoding="utf-8")
        self.send_response(303); self.send_header("Location",f"/?scenario={urllib.parse.quote(sid)}"); self.end_headers()

if __name__=="__main__":
    print("Open http://localhost:8765 in your browser. Press Ctrl+C to stop.")
    HTTPServer(("127.0.0.1",8765),H).serve_forever()
