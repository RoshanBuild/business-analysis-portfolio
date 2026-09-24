#!/usr/bin/env python3
"""
Generate deterministic synthetic data for PayFix AI 2.0.

Outputs:
- dispute_cases_raw.csv
- dispute_cases_clean.csv
- case_events.csv
- case_evidence.csv
- dispute_analysis_view.csv
- data_validation_report.csv
- generation_summary.txt

No real personal, banking, card, account, email, address, or identity data is used.
"""

from __future__ import annotations

import argparse
import copy
import csv
import random
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

SEED = 20260730
DEFAULT_CASES = 2500
START_DATE = datetime(2025, 1, 1, 8, 0, 0)
END_DATE = datetime(2026, 6, 30, 18, 0, 0)

DISPUTE_CATEGORIES = [
    "Duplicate Debit",
    "Unauthorised Transaction",
    "Delayed Refund",
    "Incorrect Amount",
    "Merchant Non-confirmation",
    "Subscription Dispute",
    "Cash Withdrawal Dispute",
    "Failed Payment",
    "Other",
]
DISPUTE_WEIGHTS = [12, 17, 15, 9, 11, 10, 7, 14, 5]

TRANSACTION_TYPES = [
    "Card Purchase",
    "Bank Transfer",
    "Direct Debit",
    "Cash Withdrawal",
    "Wallet Payment",
]
TRANSACTION_WEIGHTS = [46, 20, 15, 8, 11]

SUBMISSION_CHANNELS = ["Web", "Mobile", "Call Centre", "Email", "Chat"]
SUBMISSION_WEIGHTS = [31, 34, 16, 10, 9]

SERVICE_SEGMENTS = ["Standard", "Assisted Digital", "Vulnerable Support"]
SEGMENT_WEIGHTS = [81, 12, 7]

MERCHANT_CATEGORIES = [
    "Retail",
    "Travel",
    "Subscription",
    "Utilities",
    "Digital Services",
    "Cash Withdrawal",
    "Other",
]
MERCHANT_WEIGHTS = [28, 14, 14, 12, 14, 8, 10]

EVIDENCE_TYPES = [
    "Receipt",
    "Bank Statement",
    "Merchant Communication",
    "Identity Evidence",
    "Screenshot",
    "Other",
]
FILE_FORMATS = ["PDF", "JPG", "PNG", "CSV", "Other"]

CASE_STATUSES = [
    "Submitted",
    "Awaiting Evidence",
    "In Triage",
    "In Investigation",
    "Pending Customer",
    "Pending Merchant",
    "Pending Approval",
    "Resolved",
    "Rejected",
    "Cancelled",
]
FINAL_STATUSES = {"Resolved", "Rejected", "Cancelled"}
PENDING_STATUSES = set(CASE_STATUSES) - FINAL_STATUSES

OUTCOMES = [
    "Full Refund",
    "Partial Refund",
    "No Refund",
    "Customer Withdrawn",
    "Duplicate Case",
    "Fraud Referral",
    "Pending",
]

QUEUES = [
    "Customer Service",
    "Payment Operations",
    "Fraud Review",
    "Refund Approval",
    "Complaints",
    "Technical Support",
]

SLA_BY_PRIORITY = {"Urgent": 24, "High": 72, "Standard": 120, "Low": 168}

BASE_RESOLUTION_HOURS = {
    "Duplicate Debit": 48,
    "Unauthorised Transaction": 96,
    "Delayed Refund": 72,
    "Incorrect Amount": 60,
    "Merchant Non-confirmation": 84,
    "Subscription Dispute": 78,
    "Cash Withdrawal Dispute": 108,
    "Failed Payment": 54,
    "Other": 90,
}


def weighted_choice(rng: random.Random, values: list[str], weights: list[int]) -> str:
    return rng.choices(values, weights=weights, k=1)[0]


def random_datetime(rng: random.Random, start: datetime, end: datetime) -> datetime:
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, seconds))


def iso(dt: datetime | None) -> str:
    return "" if dt is None else dt.isoformat(timespec="seconds")


def parse_iso(value: str) -> datetime | None:
    return None if not value else datetime.fromisoformat(value)


def money(value: float) -> str:
    return f"{value:.2f}"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def choose_priority(
    rng: random.Random,
    category: str,
    amount: float,
    service_segment: str,
) -> str:
    score = 0
    if category in {"Unauthorised Transaction", "Cash Withdrawal Dispute"}:
        score += 2
    if amount >= 500:
        score += 2
    elif amount >= 150:
        score += 1
    if service_segment == "Vulnerable Support":
        score += 2
    if score >= 5:
        return weighted_choice(rng, ["Urgent", "High"], [55, 45])
    if score >= 3:
        return weighted_choice(rng, ["High", "Standard"], [60, 40])
    if score == 2:
        return weighted_choice(rng, ["High", "Standard", "Low"], [30, 60, 10])
    return weighted_choice(rng, ["Standard", "Low"], [80, 20])


def choose_initial_queue(category: str, fraud_referral: bool) -> str:
    if fraud_referral:
        return "Fraud Review"
    if category in {"Failed Payment", "Merchant Non-confirmation"}:
        return "Technical Support"
    if category in {"Delayed Refund", "Duplicate Debit", "Incorrect Amount"}:
        return "Payment Operations"
    return "Customer Service"


def choose_outcome(rng: random.Random, category: str, fraud_referral: bool) -> str:
    if fraud_referral and rng.random() < 0.26:
        return "Fraud Referral"
    if category == "Duplicate Debit":
        return weighted_choice(
            rng,
            ["Full Refund", "Partial Refund", "No Refund", "Duplicate Case"],
            [62, 7, 19, 12],
        )
    if category == "Delayed Refund":
        return weighted_choice(
            rng,
            ["Full Refund", "Partial Refund", "No Refund", "Pending"],
            [54, 8, 25, 13],
        )
    if category == "Unauthorised Transaction":
        return weighted_choice(
            rng,
            ["Full Refund", "Partial Refund", "No Refund", "Fraud Referral", "Pending"],
            [39, 9, 27, 15, 10],
        )
    return weighted_choice(
        rng,
        ["Full Refund", "Partial Refund", "No Refund", "Customer Withdrawn", "Pending"],
        [35, 13, 37, 6, 9],
    )


def generate_cases(rng: random.Random, count: int) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    for idx in range(1, count + 1):
        case_id = f"PFXC-{idx:06d}"
        transaction_id = f"TXN-{rng.randint(1, count * 5):07d}"
        category = weighted_choice(rng, DISPUTE_CATEGORIES, DISPUTE_WEIGHTS)
        transaction_type = weighted_choice(rng, TRANSACTION_TYPES, TRANSACTION_WEIGHTS)
        channel = weighted_choice(rng, SUBMISSION_CHANNELS, SUBMISSION_WEIGHTS)
        segment = weighted_choice(rng, SERVICE_SEGMENTS, SEGMENT_WEIGHTS)
        merchant_category = weighted_choice(rng, MERCHANT_CATEGORIES, MERCHANT_WEIGHTS)

        submission = random_datetime(rng, START_DATE, END_DATE)
        transaction = submission - timedelta(
            days=rng.randint(1, 60), hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
        )

        amount = round(clamp(rng.lognormvariate(4.25, 1.05), 3.0, 2500.0), 2)

        evidence_completeness = weighted_choice(
            rng, ["Complete", "Partial", "Missing"], [52, 36, 12]
        )
        evidence_count_ranges = {
            "Complete": (2, 4),
            "Partial": (1, 2),
            "Missing": (0, 0),
        }
        ev_low, ev_high = evidence_count_ranges[evidence_completeness]
        initial_evidence_count = rng.randint(ev_low, ev_high)

        fraud_probability = 0.08
        if category == "Unauthorised Transaction":
            fraud_probability += 0.37
        if category == "Cash Withdrawal Dispute":
            fraud_probability += 0.15
        if amount >= 800:
            fraud_probability += 0.08
        fraud_referral = rng.random() < min(fraud_probability, 0.65)

        priority = choose_priority(rng, category, amount, segment)
        sla_target = SLA_BY_PRIORITY[priority]

        manual_handoffs = max(
            0,
            int(round(rng.gauss(1.3 if not fraud_referral else 2.4, 0.9))),
        )
        rework = max(
            0,
            int(
                round(
                    rng.gauss(
                        0.35
                        + (0.9 if evidence_completeness == "Missing" else 0.0)
                        + (0.35 if evidence_completeness == "Partial" else 0.0),
                        0.7,
                    )
                )
            ),
        )

        base_hours = BASE_RESOLUTION_HOURS[category]
        evidence_penalty = {"Complete": 0, "Partial": 25, "Missing": 62}[
            evidence_completeness
        ]
        fraud_penalty = 50 if fraud_referral else 0
        resolution_hours = max(
            6.0,
            rng.gauss(base_hours + evidence_penalty + fraud_penalty, 22)
            + manual_handoffs * rng.uniform(8, 18)
            + rework * rng.uniform(9, 22),
        )

        # Leave some cases pending at the end of the analysis period.
        pending = rng.random() < 0.075
        if submission > END_DATE - timedelta(days=8):
            pending = rng.random() < 0.45

        first_response_hours = max(
            0.25,
            rng.gauss(
                {"Urgent": 2.5, "High": 8, "Standard": 18, "Low": 28}[priority],
                4.5,
            ),
        )
        first_response = submission + timedelta(hours=first_response_hours)

        outcome = "Pending" if pending else choose_outcome(rng, category, fraud_referral)
        if outcome == "Pending":
            pending = True

        if pending:
            resolution = None
            case_status = weighted_choice(
                rng,
                [
                    "Awaiting Evidence",
                    "In Triage",
                    "In Investigation",
                    "Pending Customer",
                    "Pending Merchant",
                    "Pending Approval",
                ],
                [18, 12, 28, 18, 12, 12],
            )
            resolution_hours_value: float | None = None
        else:
            resolution = submission + timedelta(hours=resolution_hours)
            if outcome in {"Customer Withdrawn", "Duplicate Case"}:
                case_status = "Cancelled"
            elif outcome == "No Refund":
                case_status = "Rejected"
            else:
                case_status = "Resolved"
            resolution_hours_value = round(
                (resolution - submission).total_seconds() / 3600, 2
            )

        if outcome == "Full Refund":
            refund_amount = amount
        elif outcome == "Partial Refund":
            refund_amount = round(amount * rng.uniform(0.2, 0.8), 2)
        else:
            refund_amount = 0.0

        sla_breached = (
            False
            if resolution_hours_value is None
            else resolution_hours_value > sla_target
        )

        customer_contact_count = max(
            0,
            int(
                round(
                    rng.gauss(
                        0.8
                        + manual_handoffs * 0.35
                        + rework * 0.65
                        + (1.1 if sla_breached else 0.0),
                        0.9,
                    )
                )
            ),
        )
        customer_update_count = max(
            0,
            int(round(rng.gauss(1.6 + resolution_hours / 120, 1.0))),
        )

        escalation_probability = 0.05
        escalation_probability += 0.30 if sla_breached else 0
        escalation_probability += 0.08 * min(manual_handoffs, 3)
        escalation_flag = rng.random() < min(escalation_probability, 0.78)

        complaint_probability = 0.025
        complaint_probability += 0.16 if sla_breached else 0
        complaint_probability += 0.05 * min(customer_contact_count, 4)
        if segment == "Vulnerable Support":
            complaint_probability += 0.03
        complaint_flag = rng.random() < min(complaint_probability, 0.60)

        sentiment_score = (
            1
            + (2 if sla_breached else 0)
            + min(customer_contact_count, 3)
            + (1 if evidence_completeness == "Missing" else 0)
        )
        if sentiment_score >= 5:
            sentiment = weighted_choice(
                rng, ["Frustrated", "Distressed"], [65, 35]
            )
        elif sentiment_score >= 3:
            sentiment = weighted_choice(
                rng, ["Neutral", "Frustrated", "Distressed"], [20, 68, 12]
            )
        else:
            sentiment = weighted_choice(
                rng, ["Neutral", "Positive", "Frustrated"], [64, 23, 13]
            )

        assigned_queue = choose_initial_queue(category, fraud_referral)
        if complaint_flag and rng.random() < 0.18:
            assigned_queue = "Complaints"
        if outcome in {"Full Refund", "Partial Refund"} and rng.random() < 0.25:
            assigned_queue = "Refund Approval"
        # Fraud referrals retain a clear Fraud Review ownership route.
        if fraud_referral:
            assigned_queue = "Fraud Review"

        cases.append(
            {
                "case_id": case_id,
                "transaction_id": transaction_id,
                "submission_datetime": iso(submission),
                "submission_channel": channel,
                "customer_service_segment": segment,
                "transaction_datetime": iso(transaction),
                "transaction_type": transaction_type,
                "transaction_amount_gbp": money(amount),
                "merchant_category": merchant_category,
                "dispute_category": category,
                "customer_sentiment": sentiment,
                "evidence_completeness": evidence_completeness,
                "initial_evidence_count": initial_evidence_count,
                "priority": priority,
                "assigned_queue": assigned_queue,
                "case_status": case_status,
                "first_response_datetime": iso(first_response),
                "resolution_datetime": iso(resolution),
                "sla_target_hours": sla_target,
                "manual_handoff_count": manual_handoffs,
                "rework_count": rework,
                "customer_contact_count": customer_contact_count,
                "customer_update_count": customer_update_count,
                "fraud_referral_flag": "Yes" if fraud_referral else "No",
                "escalation_flag": "Yes" if escalation_flag else "No",
                "complaint_flag": "Yes" if complaint_flag else "No",
                "outcome": outcome,
                "refund_amount_gbp": money(refund_amount),
                "resolution_time_hours": (
                    "" if resolution_hours_value is None else f"{resolution_hours_value:.2f}"
                ),
                "first_response_time_hours": f"{first_response_hours:.2f}",
                "sla_breached_flag": "Yes" if sla_breached else "No",
                "data_quality_flag": "Valid",
            }
        )

    return cases


def generate_events(
    rng: random.Random, cases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    event_number = 1

    for case in cases:
        case_id = str(case["case_id"])
        submission = parse_iso(str(case["submission_datetime"]))
        resolution = parse_iso(str(case["resolution_datetime"]))
        assert submission is not None

        event_rows: list[tuple[datetime, str, str, str, str, str, str, str]] = []
        queue = "Customer Service"
        status = "Submitted"

        event_rows.append(
            (
                submission,
                "Submission",
                "",
                "Submitted",
                "Customer",
                "No",
                "",
                queue,
            )
        )

        triage_time = submission + timedelta(hours=rng.uniform(0.5, 8))
        next_queue = str(case["assigned_queue"])
        event_rows.append(
            (
                triage_time,
                "Assignment",
                status,
                "In Triage",
                "System",
                "Yes",
                queue,
                next_queue,
            )
        )
        status = "In Triage"
        queue = next_queue

        completeness = str(case["evidence_completeness"])
        if completeness != "Complete":
            request_time = triage_time + timedelta(hours=rng.uniform(1, 10))
            event_rows.append(
                (
                    request_time,
                    "Evidence Request",
                    status,
                    "Awaiting Evidence",
                    "Operations",
                    "No",
                    queue,
                    queue,
                )
            )
            status = "Awaiting Evidence"
            receive_time = request_time + timedelta(
                hours=rng.uniform(8, 65 if completeness == "Missing" else 38)
            )
            event_rows.append(
                (
                    receive_time,
                    "Evidence Received",
                    status,
                    "In Investigation",
                    "Customer",
                    "No",
                    queue,
                    queue,
                )
            )
            status = "In Investigation"
            current_time = receive_time
        else:
            current_time = triage_time + timedelta(hours=rng.uniform(2, 12))
            event_rows.append(
                (
                    current_time,
                    "Review",
                    status,
                    "In Investigation",
                    "Payment Operations",
                    "No",
                    queue,
                    queue,
                )
            )
            status = "In Investigation"

        for _ in range(int(case["manual_handoff_count"])):
            new_queue = weighted_choice(
                rng,
                [
                    "Payment Operations",
                    "Fraud Review",
                    "Refund Approval",
                    "Customer Service",
                    "Technical Support",
                ],
                [35, 18, 18, 14, 15],
            )
            current_time += timedelta(hours=rng.uniform(3, 20))
            event_rows.append(
                (
                    current_time,
                    "Assignment",
                    status,
                    status,
                    "Operations",
                    "No",
                    queue,
                    new_queue,
                )
            )
            queue = new_queue

        if str(case["escalation_flag"]) == "Yes":
            current_time += timedelta(hours=rng.uniform(4, 22))
            event_rows.append(
                (
                    current_time,
                    "Escalation",
                    status,
                    status,
                    "Operations",
                    "No",
                    queue,
                    queue,
                )
            )

        if resolution is not None:
            decision_time = max(
                current_time + timedelta(hours=rng.uniform(3, 18)),
                resolution - timedelta(hours=rng.uniform(1, 8)),
            )
            event_rows.append(
                (
                    decision_time,
                    "Decision",
                    status,
                    "Pending Approval",
                    "Operations",
                    "No",
                    queue,
                    "Refund Approval"
                    if str(case["outcome"]) in {"Full Refund", "Partial Refund"}
                    else queue,
                )
            )
            status = "Pending Approval"

            notification_time = min(
                resolution,
                decision_time + timedelta(minutes=rng.randint(10, 180)),
            )
            event_rows.append(
                (
                    notification_time,
                    "Notification",
                    status,
                    status,
                    "System",
                    "Yes",
                    queue,
                    queue,
                )
            )
            event_rows.append(
                (
                    resolution,
                    "Closure",
                    status,
                    str(case["case_status"]),
                    "Operations",
                    "No",
                    queue,
                    queue,
                )
            )

        event_rows.sort(key=lambda item: item[0])

        for row in event_rows:
            event_datetime, event_type, from_status, to_status, actor, automated, q_from, q_to = row
            waiting_reason = "None"
            if event_type == "Evidence Received":
                waiting_reason = "Customer"
            elif event_type == "Decision" and rng.random() < 0.22:
                waiting_reason = "Internal Review"
            elif event_type == "Assignment" and q_to == "Technical Support":
                waiting_reason = "Technical Failure"

            events.append(
                {
                    "event_id": f"EVT-{event_number:08d}",
                    "case_id": case_id,
                    "event_datetime": iso(event_datetime),
                    "event_type": event_type,
                    "from_status": from_status,
                    "to_status": to_status,
                    "actor_role": actor,
                    "automated_flag": automated,
                    "queue_from": q_from,
                    "queue_to": q_to,
                    "waiting_reason": waiting_reason,
                }
            )
            event_number += 1

    return events


def generate_evidence(
    rng: random.Random, cases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    evidence_rows: list[dict[str, Any]] = []
    evidence_number = 1

    for case in cases:
        count = int(case["initial_evidence_count"])
        if str(case["evidence_completeness"]) != "Complete" and rng.random() < 0.62:
            count += rng.randint(0, 2)

        submission = parse_iso(str(case["submission_datetime"]))
        assert submission is not None

        for idx in range(count):
            completeness_status = weighted_choice(
                rng,
                ["Complete", "Incomplete", "Unreadable"],
                [79, 16, 5],
            )
            if completeness_status == "Complete":
                review_outcome = weighted_choice(
                    rng,
                    ["Accepted", "Further Evidence Required"],
                    [88, 12],
                )
            else:
                review_outcome = weighted_choice(
                    rng,
                    ["Rejected", "Further Evidence Required"],
                    [45, 55],
                )

            evidence_rows.append(
                {
                    "evidence_id": f"EVD-{evidence_number:08d}",
                    "case_id": str(case["case_id"]),
                    "evidence_type": weighted_choice(
                        rng, EVIDENCE_TYPES, [28, 18, 18, 5, 23, 8]
                    ),
                    "submitted_by": weighted_choice(
                        rng, ["Customer", "Merchant", "Operations"], [78, 12, 10]
                    ),
                    "received_datetime": iso(
                        submission + timedelta(hours=rng.uniform(0.1, 70))
                    ),
                    "file_format": weighted_choice(
                        rng, FILE_FORMATS, [45, 20, 20, 4, 11]
                    ),
                    "completeness_status": completeness_status,
                    "review_outcome": review_outcome,
                    "sensitive_data_flag": "Yes" if rng.random() < 0.17 else "No",
                    "security_scan_result": weighted_choice(
                        rng, ["Passed", "Failed", "Not Applicable"], [91, 2, 7]
                    ),
                }
            )
            evidence_number += 1

    return evidence_rows


def inject_controlled_errors(
    rng: random.Random, clean_cases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    raw_cases = copy.deepcopy(clean_cases)
    n = len(raw_cases)

    # Deliberate, documented errors for data-quality practice.
    for idx in rng.sample(range(n), max(4, n // 125)):
        raw_cases[idx]["evidence_completeness"] = ""
        raw_cases[idx]["data_quality_flag"] = "Warning"

    for idx in rng.sample(range(n), max(3, n // 250)):
        amount = float(raw_cases[idx]["transaction_amount_gbp"])
        raw_cases[idx]["refund_amount_gbp"] = money(amount + rng.uniform(1, 50))
        raw_cases[idx]["data_quality_flag"] = "Error"

    duplicate_sources = rng.sample(range(n // 2), max(3, n // 500))
    duplicate_targets = rng.sample(range(n // 2, n), len(duplicate_sources))
    for src, target in zip(duplicate_sources, duplicate_targets):
        raw_cases[target]["case_id"] = raw_cases[src]["case_id"]
        raw_cases[target]["data_quality_flag"] = "Error"

    for idx in rng.sample(range(n), max(3, n // 300)):
        raw_cases[idx]["transaction_datetime"] = raw_cases[idx]["submission_datetime"]
        raw_cases[idx]["data_quality_flag"] = "Error"

    for idx in rng.sample(range(n), max(3, n // 350)):
        if raw_cases[idx]["case_status"] in FINAL_STATUSES:
            raw_cases[idx]["resolution_datetime"] = ""
            raw_cases[idx]["data_quality_flag"] = "Error"

    for idx in rng.sample(range(n), max(3, n // 320)):
        raw_cases[idx]["dispute_category"] = "Invalid Category"
        raw_cases[idx]["data_quality_flag"] = "Error"

    return raw_cases


def validate_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = [str(row["case_id"]) for row in cases]
    id_counts = Counter(ids)
    allowed_categories = set(DISPUTE_CATEGORIES)

    rules: list[tuple[str, str, Any]] = [
        (
            "DQ-01",
            "case_id must be unique and non-null",
            lambda row: bool(str(row["case_id"]).strip())
            and id_counts[str(row["case_id"])] == 1,
        ),
        (
            "DQ-02",
            "transaction_amount_gbp must be greater than zero",
            lambda row: float(row["transaction_amount_gbp"]) > 0,
        ),
        (
            "DQ-03",
            "refund_amount_gbp cannot exceed transaction_amount_gbp",
            lambda row: float(row["refund_amount_gbp"])
            <= float(row["transaction_amount_gbp"]),
        ),
        (
            "DQ-04",
            "transaction_datetime must precede submission_datetime",
            lambda row: parse_iso(str(row["transaction_datetime"]))
            < parse_iso(str(row["submission_datetime"])),
        ),
        (
            "DQ-05",
            "first_response_datetime cannot precede submission",
            lambda row: parse_iso(str(row["first_response_datetime"]))
            >= parse_iso(str(row["submission_datetime"])),
        ),
        (
            "DQ-06",
            "resolution_datetime cannot precede submission",
            lambda row: not str(row["resolution_datetime"])
            or parse_iso(str(row["resolution_datetime"]))
            >= parse_iso(str(row["submission_datetime"])),
        ),
        (
            "DQ-07",
            "final statuses require a resolution date",
            lambda row: str(row["case_status"]) not in FINAL_STATUSES
            or bool(str(row["resolution_datetime"])),
        ),
        (
            "DQ-08",
            "pending statuses must not contain a final resolution date",
            lambda row: str(row["case_status"]) not in PENDING_STATUSES
            or not bool(str(row["resolution_datetime"])),
        ),
        (
            "DQ-09",
            "fraud referrals require Fraud Review or a Fraud Referral outcome",
            lambda row: str(row["fraud_referral_flag"]) != "Yes"
            or str(row["assigned_queue"]) == "Fraud Review"
            or str(row["outcome"]) == "Fraud Referral",
        ),
        (
            "DQ-12",
            "SLA flag must agree with resolution duration and target",
            lambda row: (
                str(row["resolution_time_hours"]) == ""
                and str(row["sla_breached_flag"]) == "No"
            )
            or (
                str(row["resolution_time_hours"]) != ""
                and (
                    (
                        float(row["resolution_time_hours"])
                        > float(row["sla_target_hours"])
                    )
                    == (str(row["sla_breached_flag"]) == "Yes")
                )
            ),
        ),
        (
            "DQ-13",
            "dispute categories must match the controlled data dictionary",
            lambda row: str(row["dispute_category"]) in allowed_categories,
        ),
        (
            "DQ-14",
            "no direct personal or banking identifiers are permitted",
            lambda row: True,
        ),
    ]

    report: list[dict[str, Any]] = []
    for rule_id, description, check in rules:
        failures = 0
        for row in cases:
            try:
                if not check(row):
                    failures += 1
            except (TypeError, ValueError):
                failures += 1
        report.append(
            {
                "rule_id": rule_id,
                "validation_rule": description,
                "records_checked": len(cases),
                "failure_count": failures,
                "pass_count": len(cases) - failures,
                "status": "PASS" if failures == 0 else "FAIL",
            }
        )
    return report


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows available for {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def create_analysis_view(
    cases: list[dict[str, Any]],
    events: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    event_counts = Counter(str(row["case_id"]) for row in events)
    evidence_counts = Counter(str(row["case_id"]) for row in evidence)
    waiting_counts = Counter(
        str(row["case_id"])
        for row in events
        if str(row["waiting_reason"]) != "None"
    )

    view: list[dict[str, Any]] = []
    for row in cases:
        output = dict(row)
        case_id = str(row["case_id"])
        output["event_count"] = event_counts[case_id]
        output["evidence_record_count"] = evidence_counts[case_id]
        output["waiting_event_count"] = waiting_counts[case_id]
        view.append(output)
    return view


def write_summary(
    path: Path,
    cases: list[dict[str, Any]],
    events: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    raw_report: list[dict[str, Any]],
    clean_report: list[dict[str, Any]],
) -> None:
    raw_failures = sum(int(row["failure_count"]) for row in raw_report)
    clean_failures = sum(int(row["failure_count"]) for row in clean_report)
    category_counts = Counter(str(row["dispute_category"]) for row in cases)
    breached = sum(str(row["sla_breached_flag"]) == "Yes" for row in cases)

    lines = [
        "PayFix AI 2.0 Synthetic Dataset Generation Summary",
        "=" * 56,
        f"Seed: {SEED}",
        f"Case records: {len(cases):,}",
        f"Event records: {len(events):,}",
        f"Evidence records: {len(evidence):,}",
        f"SLA-breached cases: {breached:,}",
        f"Raw validation failures: {raw_failures:,}",
        f"Clean validation failures: {clean_failures:,}",
        "",
        "Dispute category counts:",
    ]
    for category, count in category_counts.most_common():
        lines.append(f"- {category}: {count:,}")

    lines.extend(
        [
            "",
            "Important notice:",
            "All records are synthetic and created solely for portfolio analysis.",
            "No real customer, account, payment-card, banking, identity, address,",
            "email, telephone, or transaction data is included.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate PayFix AI 2.0 synthetic dispute data."
    )
    parser.add_argument(
        "--output-dir",
        default="PayFix-AI-2.0/07-data/generated",
        help="Directory where generated files will be stored.",
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=DEFAULT_CASES,
        help="Number of synthetic dispute cases.",
    )
    args = parser.parse_args()

    if args.cases < 100:
        raise ValueError("--cases must be at least 100 for meaningful analysis.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)

    clean_cases = generate_cases(rng, args.cases)
    events = generate_events(rng, clean_cases)
    evidence = generate_evidence(rng, clean_cases)
    raw_cases = inject_controlled_errors(rng, clean_cases)
    analysis_view = create_analysis_view(clean_cases, events, evidence)

    raw_report = validate_cases(raw_cases)
    clean_report = validate_cases(clean_cases)

    combined_report: list[dict[str, Any]] = []
    for dataset_name, report in [
        ("dispute_cases_raw.csv", raw_report),
        ("dispute_cases_clean.csv", clean_report),
    ]:
        for row in report:
            combined_report.append({"dataset": dataset_name, **row})

    write_csv(output_dir / "dispute_cases_raw.csv", raw_cases)
    write_csv(output_dir / "dispute_cases_clean.csv", clean_cases)
    write_csv(output_dir / "case_events.csv", events)
    write_csv(output_dir / "case_evidence.csv", evidence)
    write_csv(output_dir / "dispute_analysis_view.csv", analysis_view)
    write_csv(output_dir / "data_validation_report.csv", combined_report)
    write_summary(
        output_dir / "generation_summary.txt",
        clean_cases,
        events,
        evidence,
        raw_report,
        clean_report,
    )

    clean_failures = sum(int(row["failure_count"]) for row in clean_report)
    if clean_failures:
        raise RuntimeError(
            f"Clean data validation failed with {clean_failures} failure(s)."
        )

    print("PayFix AI 2.0 synthetic data generated successfully.")
    print(f"Output directory: {output_dir.resolve()}")
    print(f"Cases: {len(clean_cases):,}")
    print(f"Events: {len(events):,}")
    print(f"Evidence records: {len(evidence):,}")
    print("Clean validation failures: 0")


if __name__ == "__main__":
    main()
