# Meeting Notes — Sentinel Modernization Kickoff

> FICTIONAL SAMPLE DOCUMENT. Created for an AI demonstration. The people,
> company, and program are invented.

**Date:** 14 July 2026, 09:00–11:15 ET
**Location:** ACME Reston campus, Building 4, Room 220 (hybrid)
**Program:** Sentinel Ground Radar Modernization (SOW-003)

**Attendees**
- Dana Whitfield — Program Manager, Leidos
- Marcus Oyelaran — Chief Engineer, Leidos
- Sofia Berenson — Integration Lead, Leidos
- Priya Raghunathan — Technical Lead, ACME
- Tom Beckwith — Contracting Officer, ACME
- Ray Kowalczyk — Site Operations Manager, ACME (remote)

## 1. Program overview

Dana walked the integrated master schedule. Period of performance runs 1 July
2026 through 31 December 2027, with SRR on 15 August. The critical path runs
through the SPX-4 development units — everything in the integration lab is
blocked until those arrive.

Priya confirmed ACME is tracking the two development units for delivery by
15 July, one day after this meeting. Marcus flagged that if they slip past
15 August, SRR content will be theoretical rather than demonstrated.

## 2. Pilot site selection

Ray raised a concern about Site 07 as the pilot. Site 07 has the lowest
operational tempo, which is why it was chosen, but it is also the only site
running the older Mk II antenna controller. Testing there may not surface
integration issues that appear at the Mk III sites.

**Decision:** Site 07 remains the pilot for schedule reasons. Marcus will add a
Mk III controller emulator to the integration lab scope so Mk III behaviour is
exercised before Site 01 deployment. This may require a CCN — Dana to assess.

## 3. Track detection accuracy

Extended discussion on the 98.5% track-detection accuracy requirement. Marcus
noted the reference scenario set has not yet been delivered, and the achievable
accuracy depends heavily on the clutter profiles it contains. Priya committed to
delivering the scenario set by 31 July.

Marcus stated that if the scenario set includes the heavy-clutter littoral
cases, 98.5% may not be achievable without an additional filtering stage not
currently in the cost basis.

**Action:** Marcus to provide a technical assessment within two weeks of
receiving the scenario set.

## 4. Security and site access

Ray reported that site badging takes six to eight weeks for new personnel.
Field teams do not deploy until June 2027, but badging must start by April 2027.
Sofia noted three engineers already hold current credentials from a prior
program.

## 5. Communications cadence

- Weekly technical sync — Tuesdays 10:00 ET, Marcus and Priya
- Monthly program review — first Thursday, Dana and Tom
- Quarterly executive review — Dana, Tom, and both organizations' leadership
- Risk register reviewed at every monthly program review

## Action items

| # | Action | Owner | Due |
|---|--------|-------|-----|
| A-01 | Deliver two SPX-4 development units to integration lab | Priya | 15 Jul 2026 |
| A-02 | Deliver reference scenario data set | Priya | 31 Jul 2026 |
| A-03 | Technical assessment of 98.5% accuracy feasibility | Marcus | 2 weeks after A-02 |
| A-04 | Assess CCN need for Mk III emulator in lab scope | Dana | 28 Jul 2026 |
| A-05 | Confirm as-built documentation availability for all 12 in-scope sites | Ray | 8 Aug 2026 |
| A-06 | Publish integrated master schedule baseline | Dana | 22 Jul 2026 |
