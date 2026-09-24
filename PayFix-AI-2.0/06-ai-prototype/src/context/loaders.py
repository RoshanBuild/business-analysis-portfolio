from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Dict, List

def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def load_scenarios(root: Path):
    return read_csv(root / "data" / "scenarios" / "ai_evaluation_scenarios.csv")

def load_sources(root: Path):
    return read_csv(root / "data" / "sources" / "ai_evaluation_sources.csv")

def load_ground_truth(root: Path):
    rows = read_csv(root / "data" / "reference" / "ai_evaluation_ground_truth.csv")
    return {r["Scenario_ID"]: r for r in rows}

def get_scenario(rows, scenario_id: str):
    matches = [r for r in rows if r["Scenario_ID"] == scenario_id]
    if len(matches) != 1:
        raise ValueError(f"Scenario lookup expected 1 row for {scenario_id}; found {len(matches)}")
    return matches[0]
