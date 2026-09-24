from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel, Field

class SourceReference(BaseModel):
    source_id: str
    source_type: str
    short_description: str

class GroundedFact(BaseModel):
    fact: str
    source_ids: List[str] = Field(min_length=1)

class EvidenceSummary(BaseModel):
    ai_use_case: Literal["Evidence Summarisation"]
    case_id: str
    status: Literal["AI-assisted draft — human review required"]
    evidence_considered: List[SourceReference]
    key_evidence_facts: List[GroundedFact]
    missing_information: List[str]
    conflicting_information: List[str]
    uncertainty_limitations: List[str]
    draft_summary: str
    prohibited_decision_statement: Literal[
        "This summary does not constitute a fraud determination, dispute decision, refund approval or final finding."
    ]

class HandoffSummary(BaseModel):
    ai_use_case: Literal["Handoff Summarisation"]
    case_id: str
    status: Literal["AI-assisted draft — human review required"]
    current_case_state: str
    current_queue_owner: str
    completed_work: List[str]
    outstanding_work: List[str]
    customer_action: List[str]
    evidence_position: List[str]
    specialist_position: List[str]
    decision_approval: List[str]
    complaint_escalation: List[str]
    waiting_dependencies: List[str]
    conflicts_uncertainty: List[str]
    source_references: List[SourceReference]
    draft_handoff_summary: str
    prohibited_decision_statement: Literal[
        "This summary does not transfer ownership, make a fraud determination, approve a refund, finalise a dispute decision or close a case."
    ]

class GuardrailTestOutput(BaseModel):
    guardrail_id: str
    status: Literal["AI-assisted draft — human review required"]
    prohibited_action_taken: bool
    safe_response: str
    notes: List[str]
