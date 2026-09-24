from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
from src.context.loaders import load_scenarios

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--provider",choices=["ollama","demo"],default="ollama")
    a=p.parse_args()
    root=Path(__file__).resolve().parent
    scenarios=load_scenarios(root)
    failures=[]
    for i,s in enumerate(scenarios,1):
        sid=s["Scenario_ID"]
        print(f"\n[{i}/{len(scenarios)}] {sid}")
        r=subprocess.run([sys.executable,"run_scenario.py","--scenario",sid,"--provider",a.provider],cwd=root)
        if r.returncode!=0:
            failures.append(sid)
    print("\nCOMPLETE")
    print("Failed scenario processes:", failures if failures else "None")
    if a.provider=="demo":
        print("NOTE: demo outputs are pipeline demonstrations only, not formal AI quality evidence.")

if __name__=="__main__":
    main()
