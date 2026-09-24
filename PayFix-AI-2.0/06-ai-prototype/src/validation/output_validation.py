from __future__ import annotations

PROHIBITED_PHRASES = [
    "fraud confirmed",
    "fraud is confirmed",
    "refund approved",
    "refund has been approved",
    "case is closed",
    "ownership transferred",
    "must approve the refund",
]

def _refs(output):
    ids = set()
    if hasattr(output, "evidence_considered"):
        ids.update(x.source_id for x in output.evidence_considered)
    if hasattr(output, "key_evidence_facts"):
        for fact in output.key_evidence_facts:
            ids.update(fact.source_ids)
    if hasattr(output, "source_references"):
        ids.update(x.source_id for x in output.source_references)
    return ids

def validate_output(output, context):
    issues = []
    if output.case_id != context["case_id"]:
        issues.append(f"Case ID mismatch: {output.case_id} vs {context['case_id']}")
    allowed = {x["source_id"] for x in context["source_items"]}
    referenced = _refs(output)
    unknown = sorted(referenced - allowed)
    if unknown:
        issues.append("Unknown/out-of-context source references: " + ", ".join(unknown))
    text = output.model_dump_json().lower()
    hits = [p for p in PROHIBITED_PHRASES if p in text]
    if hits:
        issues.append("Potential prohibited authoritative wording: " + ", ".join(hits))
    return {
        "validation_passed": not issues,
        "issues": issues,
        "allowed_source_ids": sorted(allowed),
        "referenced_source_ids": sorted(referenced),
    }
