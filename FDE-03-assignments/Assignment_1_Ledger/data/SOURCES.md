# Data sources

All inputs are public documents and open data published by West Berkshire Council and by
the UK government's Contracts Finder service. They are included unchanged, so every quote
and every payment in your pack can be traced back to the file it came from.

**Read-only.** Nothing in `data/` is ever edited, by you or by an agent. Changing a file
here is a red line, and the grader verifies against its own copy.

| File | What it is | Publisher | Role in Ledger |
|---|---|---|---|
| `contract-rules.pdf` | Contract Procedure Rules (Constitution, Part 8, September 2025), about 15 pages | West Berkshire Council | The criteria: thresholds, quote and tender rules, approvals, the anti-splitting rule |
| `spend/Over500_2026_P02_-_published.xlsx`, `P03`, `P04` | "Expenditure over £500", three monthly workbooks (May to July 2026), about 10,600 payments in total. Sheet `Data to publish`; the header row position varies | West Berkshire Council (transparency publication) | The full population of payments |
| `contracts.csv` | Contracts Finder export of awarded notices that mention "West Berkshire Council", open and closed, published from 2021 | Contracts Finder (UK government) | Basis of the off-contract, expired-notice and spend-versus-award tests. It is a raw notice export, not a contract register |
| `committee/audit-completed-work-2024-25-annual.pdf` | Internal audit completed work, 2024/25 annual appendix | Governance Committee papers | Past audit opinions |
| `committee/audit-completed-work-2025-26-q3.pdf` | Internal audit completed work, 2025/26 Q3 | Governance Committee papers | Past audit opinions, recent |
| `committee/internal-audit-plan-2025-28.pdf` | Internal Audit Plan 2025–28 | Governance Committee papers | Planned coverage and approach |
| `committee/risk-management-strategy-2024-27.pdf` | Risk Management Strategy 2024–2027 | Governance Committee papers | The council's own likelihood × impact scale |

Not included, and not public: the Strategic Risk Register, which the council treats as an
exempt report. The scoring method comes from the Risk Management Strategy instead.

## Licence and use

Local-authority transparency data and Contracts Finder data are published for reuse
(typically under the Open Government Licence v3.0); the committee papers and the
Constitution are public council documents. They are used here for teaching only.

Everything the system produces describes **risk indicators to investigate**. Nothing in
this assignment, or in what you build, asserts wrongdoing by the council, a service, an
officer or a supplier. The viewer pseudonymises supplier names before anything is
published (`viewer/collect.mjs`).
