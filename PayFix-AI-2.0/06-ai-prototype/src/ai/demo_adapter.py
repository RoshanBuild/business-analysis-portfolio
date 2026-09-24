from __future__ import annotations
# Deterministic offline fallback for pipeline demonstrations only.
# Do NOT use these outputs as formal AI quality results.

from src.ai.schemas import EvidenceSummary, HandoffSummary, SourceReference, GroundedFact

class DemoAdapter:
    def generate(self, scenario: dict, context: dict):
        refs = [
            SourceReference(
                source_id=s["source_id"],
                source_type=s["source_type"],
                short_description=s["source_content"][:100],
            )
            for s in context["source_items"]
        ]
        if scenario["AI_Use_Case"] == "Evidence Summarisation":
            facts = [
                GroundedFact(fact=s["source_content"], source_ids=[s["source_id"]])
                for s in context["source_items"]
            ]
            return EvidenceSummary(
                ai_use_case="Evidence Summarisation",
                case_id=context["case_id"],
                status="AI-assisted draft — human review required",
                evidence_considered=refs,
                key_evidence_facts=facts,
                missing_information=[],
                conflicting_information=[],
                uncertainty_limitations=["Deterministic demo output; not formal AI evaluation evidence."],
                draft_summary=" ".join(s["source_content"] for s in context["source_items"]),
                prohibited_decision_statement="This summary does not constitute a fraud determination, dispute decision, refund approval or final finding.",
            )
        return HandoffSummary(
            ai_use_case="Handoff Summarisation",
            case_id=context["case_id"],
            status="AI-assisted draft — human review required",
            current_case_state="See authoritative source records.",
            current_queue_owner="See authoritative source records.",
            completed_work=[s["source_content"] for s in context["source_items"] if s["source_state"] in {"completed","finalised","delivered","recorded"}],
            outstanding_work=[s["source_content"] for s in context["source_items"] if s["source_state"] in {"outstanding","pending","open","in_progress","unknown","not_recorded","not_started","not_ready"}],
            customer_action=[],
            evidence_position=[],
            specialist_position=[],
            decision_approval=[],
            complaint_escalation=[],
            waiting_dependencies=[],
            conflicts_uncertainty=["Deterministic demo output; not formal AI evaluation evidence."],
            source_references=refs,
            draft_handoff_summary=" ".join(s["source_content"] for s in context["source_items"]),
            prohibited_decision_statement="This summary does not transfer ownership, make a fraud determination, approve a refund, finalise a dispute decision or close a case.",
        )
