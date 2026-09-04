# Risk Register — Sentinel Ground Radar Modernization

> FICTIONAL SAMPLE DOCUMENT. Created for an AI demonstration. The people,
> company, program, and risks are invented.

**Program:** SOW-003, Sentinel Ground Radar Modernization
**Register version:** 1.4
**Last reviewed:** 11 August 2026
**Review cadence:** Monthly, at the program review

Scoring: Probability and Impact each rated 1 (low) to 5 (high). Exposure is the
product. Risks scoring 12 or above are High and require an active mitigation
plan with a named owner.

## R-01 — SPX-4 supply chain constraint
**Probability:** 3 **Impact:** 4 **Exposure:** 12 (High)
**Owner:** Sofia Berenson
The SPX-4 processing stack has a single qualified supplier with a quoted
sixteen-week lead time. Fourteen production units are needed by Q1 2027.
*Mitigation:* Place the production order by 1 December 2026, four weeks earlier
than the schedule requires. Qualify a second source in parallel; assessment due
30 November 2026.

## R-02 — Reference scenario set delivery delay
**Probability:** 5 **Impact:** 4 **Exposure:** 20 (High) — the highest exposure on the program
**Owner:** Dana Whitfield
The reference scenario data set is ACME-furnished and was due 31 July 2026. As
of 11 August it has not been delivered; ACME now projects 29 August. Accuracy
feasibility analysis cannot begin without it, and PDR content depends on that
analysis.
*Mitigation:* Begin analysis with synthetic clutter profiles so the tooling is
proven before real data arrives. Issue formal GFE delay notice on 30 August if
undelivered. Raised from Medium at the August review.

## R-03 — 98.5% accuracy target may be unachievable
**Probability:** 3 **Impact:** 5 **Exposure:** 15 (High)
**Owner:** Marcus Oyelaran
If the reference scenario set includes heavy-clutter littoral cases, the
contracted 98.5% track-detection accuracy may require an additional filtering
stage that is not in the current cost basis. Estimated cost of that stage is
$400,000 to $600,000.
*Mitigation:* Complete the feasibility assessment within two weeks of receiving
the scenario set. If infeasible, negotiate either a scenario-weighted accuracy
target or a CCN for the filtering stage. Do not proceed to CDR with an
unresolved accuracy requirement.

## R-05 — Mk III controller integration untested at pilot
**Probability:** 3 **Impact:** 4 **Exposure:** 12 (High)
**Owner:** Marcus Oyelaran
Site 07, the pilot, runs a Mk II antenna controller. Eleven of the remaining
in-scope sites run Mk III. Integration issues specific to Mk III would not
surface until Site 01 deployment in Q3 2027, late enough to be expensive.
*Mitigation:* Add a Mk III emulator to the integration lab. CCN submitted at
$185,000; decision expected 5 September 2026. Held at Medium pending that
decision.

## R-06 — Field team badging lead time
**Probability:** 2 **Impact:** 3 **Exposure:** 6 (Medium)
**Owner:** Sofia Berenson
Site badging takes six to eight weeks. Ten field engineers deploy from June
2027; three already hold current credentials.
*Mitigation:* Open badging paperwork by 1 April 2027. Track as a schedule
predecessor in the IMS.

## R-07 — Operator workflow regression
**Probability:** 2 **Impact:** 4 **Exposure:** 8 (Medium)
**Owner:** Sofia Berenson
The console port must preserve all current operator workflows. Undocumented
workflows discovered late would force rework after CDR.
*Mitigation:* Run operator shadowing sessions at three sites before PDR.
Document observed workflows and baseline them as requirements.

## R-04 — SPX-4 development unit delivery (CLOSED)
**Closed:** 11 August 2026
Units were due 15 July and arrived 22 July. The one-week slip consumed float
without touching the critical path. Integration lab stood up 29 July.
