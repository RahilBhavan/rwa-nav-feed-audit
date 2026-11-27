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
