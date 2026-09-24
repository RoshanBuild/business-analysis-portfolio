# PayFix AI 2.0 — Technical Business Analyst Portfolio

PayFix AI 2.0 is a UK-style **Technical Business Analyst portfolio project** for a future digital payment-dispute service.

The project demonstrates an end-to-end BA lifecycle from problem/context analysis and synthetic baseline analysis through process improvement, requirements, Agile delivery, digital/data systems analysis, Responsible AI, controlled prototype evaluation, testing/UAT design, security/privacy assurance, release readiness, live-service design, benefits measurement, and capability evidence.

> **Portfolio boundary:** this repository demonstrates analysis, design, traceability, governance and controlled prototype evidence. It is **not** presented as a deployed production financial service.

## Project at a glance

| Area | Evidence |
|---|---:|
| Synthetic dispute cases | 2,500 |
| Lifecycle events | 19,424 |
| Evidence records | 6,041 |
| Requirements | 228 |
| Product epics | 11 |
| User stories | 66 |
| Logical system components | 17 |
| Logical entities | 24 |
| Interfaces | 9 |
| Operations | 15 |
| AI evaluation scenarios | 26 |
| Formal UAT scenarios designed | 20 |
| Expected benefits | 10 |
| KPIs | 14 |
| BA capability areas mapped | 9 |

## Business problem and baseline

The synthetic baseline highlighted material process friction:

- Average resolution time: **128.4 hours**
- Finalised-case SLA breach rate: **49.7%**
- Average manual handoffs: **1.49 per case**
- Average rework: **0.66 per case**
- Average customer contacts: **2.20 per case**
- Escalation rate: **28.4%**
- Complaint indicator rate: **19.4%**

These values are from a **synthetic portfolio dataset**, not production performance.

## Delivery approach

The project uses a blended delivery model:

- **Agile** for the overall iterative lifecycle
- **Scrum** for planned product increments
- **Kanban** for discovery, defects, support and continuous-improvement work

Delivery is separated into four horizons:

- **H1 — Core Process Foundation:** human-controlled core dispute service
- **H2 — Selective Deterministic Automation:** rule-based/workflow automation where appropriate
- **H3 — Controlled AI Pilot:** Evidence Summarisation and Handoff Summarisation only
- **H4 — Conditional Future Expansion:** future scope requiring a new analysis/governance cycle

A core design rule is that **H1 must work without AI**.

## Requirements and backlog

The controlled requirements baseline contains **228 requirements**:

- 17 Business Requirements
- 19 User Requirements
- 52 Functional Requirements
- 50 Data Requirements
- 36 User Experience Requirements
- 18 Control Requirements
- 20 Non-Functional Requirements
- 16 AI Requirements

The Product Backlog contains **11 epics and 66 user stories**.

Requirements and delivery artefacts are intentionally many-to-many rather than forcing one Jira story per requirement.

See:

- [`03-requirements-backlog/PayFix_AI_2_Requirements_Baseline.pdf`](03-requirements-backlog/PayFix_AI_2_Requirements_Baseline.pdf)
- [`03-requirements-backlog/PayFix_AI_2_Product_Backlog.pdf`](03-requirements-backlog/PayFix_AI_2_Product_Backlog.pdf)

## Digital and data systems analysis

The logical technical design covers system context, logical architecture, data model, interfaces and API/data exchange, authority boundaries, resilience, and Responsible AI integration.

Key design evidence includes **17 logical components, 24 logical entities, 9 interfaces, 15 operations, and 10 authority categories**.

AI-generated content is **derived assistance**, not authoritative business state.

## Responsible AI

AI was not assumed to be the default solution.

The controlled H3 scope is limited to:

1. **Evidence Summarisation**
2. **Handoff Summarisation**

Key controls include minimum necessary context, grounding in supplied case/evidence information, mandatory human review, **Accept / Correct / Reject / Disregard**, no autonomous refund/fraud/dispute decisions, no direct AI write to authoritative state, and safe non-AI fallback.

## Controlled AI prototype

Controlled evaluation used synthetic scenarios:

- **26 scenarios**
- **23 usable / accepted outputs**
- **3 disregarded outputs**
- **0 critical failures**

Prototype evidence is not treated as production approval or as full-service UAT.

See [`06-ai-prototype/`](06-ai-prototype/).

## Testing and traceability

The testing framework includes business testing/UAT strategy, requirements-to-test traceability, **20 detailed UAT cases**, readiness assessment, defect and retest governance, and business sign-off design.

Full-service UAT has **not been executed** because the complete representative service has not been implemented.

Key artefacts:

- [`05-testing-assurance/PayFix_AI_2_UAT_Traceability_Final.xlsx`](05-testing-assurance/PayFix_AI_2_UAT_Traceability_Final.xlsx)
- [`05-testing-assurance/PayFix_AI_2_UAT_Execution_Readiness.xlsx`](05-testing-assurance/PayFix_AI_2_UAT_Execution_Readiness.xlsx)

## Security, privacy and release assurance

The project includes structured design for access control and authority, data minimisation, privacy principles, retention/deletion, security controls, AI privacy/security, release readiness, rollback/fallback, and go-live governance.

These are **design and assurance gates**, not certifications.

Key artefacts:

- [`05-testing-assurance/PayFix_AI_2_Security_Privacy_Compliance_Assurance.xlsx`](05-testing-assurance/PayFix_AI_2_Security_Privacy_Compliance_Assurance.xlsx)
- [`05-testing-assurance/PayFix_AI_2_Release_Implementation_Readiness.xlsx`](05-testing-assurance/PayFix_AI_2_Release_Implementation_Readiness.xlsx)

## Live service and benefits

The live-service model covers service ownership, monitoring, support escalation, incident/problem management, resilience/runbooks, and operational handover.

Benefits/performance work defines **10 expected benefits, 14 KPIs, future measurement methods, and post-implementation review**.

No production benefit is claimed as realised.

See:

- [`08-live-service-benefits/PayFix_AI_2_Live_Service_Support_Model.xlsx`](08-live-service-benefits/PayFix_AI_2_Live_Service_Support_Model.xlsx)
- [`08-live-service-benefits/PayFix_AI_2_Benefits_Performance_Measurement.xlsx`](08-live-service-benefits/PayFix_AI_2_Benefits_Performance_Measurement.xlsx)

## Business Analyst capability evidence

The portfolio is mapped across nine BA capability areas used throughout the project:

1. Adapting to delivery methodologies
2. Business modelling
3. Business process improvement
4. Context, problem and option analysis
5. Defining/managing business needs, user needs and requirements
6. Digital and data systems analysis
7. Stakeholder relationship management
8. Testing for business analysis
9. User experience analysis

See [`09-capability-evidence/PayFix_AI_2_UK_Government_BA_Capability_Evidence.xlsx`](09-capability-evidence/PayFix_AI_2_UK_Government_BA_Capability_Evidence.xlsx).

## Repository structure

```text
PayFix-AI-2.0/
├── README.md
├── .gitignore
├── 01-overview/
├── 02-discovery-process/
├── 03-requirements-backlog/
├── 04-technical-design/
├── 05-testing-assurance/
├── 06-ai-prototype/
├── 07-data/
├── 08-live-service-benefits/
├── 09-capability-evidence/
└── 10-project-closure/
```

## Evidence integrity

This repository deliberately does **not** claim real PayFix customer interviews or quotes, real organisational stakeholder workshops, production financial/customer data, completed full-service UAT, production security/privacy certification, a production deployment, live-service availability/incident performance, realised production benefits, or autonomous AI decision authority.

Synthetic data, design evidence, prototype evidence and future production evidence are kept clearly separate.

## Final project status

- **Portfolio lifecycle:** Complete
- **Production service:** Not live
- **Full-service UAT:** Not executed
- **Production deployment:** Not performed
- **Production approval:** Not granted
- **Benefits realisation:** Not yet measured

The project is closed as a completed **Technical Business Analyst portfolio project**.
