# Decisions

## 2026-11-26 — Sequence the work around the availability of issuer NAV

1. Test all six named funds for public, dated, issuer-published per-share or per-token observations. Record units, provenance and whether publication time is available. Keep price proxies and repeated readings of a single latest value out of the count.
2. If fewer than three qualify, document the coverage finding and close the empirical work. Otherwise map comparable feeds, pin blocks and extract update histories for supported pairs.
3. Measure heartbeat, deviation and lag where identifiable, including weekend and month-end coverage. Preserve the distinction between a valuation date and a publication timestamp. Produce one chart.
4. Prepare reproducibility instructions, source register and draft posts for the supported outcome. Obtain an independent review and allow one repair round. Close with HANDOFF.md.


## 2026-11-26 — Stop the feed comparison

The study reran six tests and the offline and live extractors. The two JSON outputs differed only in the mode label. USTB and BENJI supply 57 pinned per-share observations. OUSG supplies dated displayed prices but the checked accounting reports give fund-wide dollars without a matching unit count. Counting the chart as an independent benchmark would assume the very provenance the audit needs to establish. The two qualifying products fall below the three-product threshold. Close on benchmark availability and send the finished finding and drafts to independent review.

## 2026-11-26 — Independent review and scope decision

Independent review flagged that our initial plan said “per-token” without specifying what that value represents. The brief explicitly sets the gate on issuer NAV history. USDY LLC publishes a dated per-token debt principal, a valid reference for an audit of note pricing. Including it changes the broader benchmark count to three. Retain both counts and stop rather than using different economic quantities to clear the fund-NAV gate. The brief's first process rule calls for a narrower finding and a stop here.

Other dead ends included USYC's indexed oracle history, BUIDL's stable-value target and the missing matching unit denominator in OUSG fund accounts. OUSG accounts still corroborate a daily price change. The review checked the original November 23 PDF and independently recalculated both returns.

One repair round addressed benchmark scope, provisional USTB dates, source roles, OUSG return arithmetic, live comparison and draft wording. Nine tests passed. The repaired public replay preserved five successful requests and reported HTTP 403 on the two Franklin filings. The earlier live run had matched both.

## 2026-11-26 — Reopen for a USTB delivery study and public release

Round one scored 3/10 on the reopened scope. Its strongest lead pairs Ethereum Chainlink USTB NAV per Share with Superstate's dated NAV. Build a pinned comparison covering weekends, holidays and month-end. The feed names the manager API as its source. Measure delivery of that value and qualify any timing claim by the clocks available. Treat the reviewer's preliminary numbers as leads pending reproduction. BENJI and USDY retain their distinct benchmark definitions.

## Prepublication evidence packaging

The replay records the study's selected date/value observations in a common schema and retains the public SEC filing excerpts. Non-SEC source bytes are retrieved separately. The source register traces each historical capture and distinguishes its digest from later download receipts.

## 2026-11-27 — Public release

Rahil selected the MIT License for the project code. Third-party filings and data retain their own terms. The public history begins with the sanitized release tree. Earlier review hashes identify local research revisions.

## 2026-11-27 — Reconstruct the active proxy and preserve both comparison clocks

The reviewer’s 430-round lead was a trailing window within phase 2. The pinned proxy maps two aggregators, which continued to store rounds while inactive. Adjacent block state established the switch at block 20,464,407, allowing the study to measure the active proxy across 889 observations. Keep the 920 stored-round count for fidelity and retain the trailing result for comparison. Use the same-date label at UTC close for the daily series, and the previous date label at round time for the separate update-level measure.

The November Ondo document table supported 14 OUSG return pairs, including an outlier on November 24. Keep the per-unit level and exact chart provenance unresolved. BENJI uses separate filing and valuation clocks. USDY compares issuer note principal with the legacy oracle at each report-day block and cross-checks the later historical ranges. Independent Round 2 review follows implementation.

## 2026-11-27 — Distinguish the posting date from sessions elapsed

Round 2 scored 5/10 after independently reproducing the capture. Two Saturday observations exposed a difference between counting elapsed NYSE sessions and landing on the next session date. Use explicit posting-date equality and examine the issuer's observed NAV changes. Label that clock by what the API shows. Freeze the official reference date so subsequent updates to provisional labels cannot change the reported study.

Use the captured November 24 official NAV date for the historical labels and the Ethereum pin for follow-up. The value from the last issuer label reached both feeds, with no finalized next change to compare against. Keep it visible as unknown. Use a short common November window for the second-feed comparison, where Chronicle's public consumer logs and Ethereum receipts support an exact-value join.

## 2026-11-27 — Close the three-round quality loop

Round 3 scored 8/10 on the published research commit 75fe51c. Scores rose from 3 to 5 to 8. The authorized round limit was reached. The final review and handoff commit changes documentation and records only. The dashboard compares exact commit hashes, so the scored research revision precedes this closeout.
