# Roadmap: NAV feed timeliness audit

Draft, 2026-11-28. Planning only; no repo edits. Effort: S up to 3 days, M 1–2 weeks, L 3+ weeks.

**Current state.** USTB on Ethereum. Chainlink posted 588 of 601 issuer NAV values on the next NAV-change date, usually around 9:10 a.m. ET. In the 340-label shared window the Chronicle consumer posted 236 on date. Independent review round 4 scored 8/10, the lowest code score of the RWA set. Its open gaps: 7 of 12 single-line mutants survive, including one that changes a published number (the 10^12 scale). The Chronicle "unseen" counts mix a 2025 period when the consumer carried no exact NAV with genuine skips, and the chart title states no point.

**The bar.** Chainlink SmartData reports carry `navPerShare`, `navDate`, `aum` and a `ripcord` status ([schema docs](https://docs.chain.link/data-streams/reference/report-schema-overview), accessed 2026-11-28). They are used by Amundi/Spiko, Fidelity International, WisdomTree and others ([Chainlink Q1 2026 review](https://chain.link/blog/quarterly-review-q1-2026)). Deloitte examined Chainlink's data feeds against AICPA attestation standards in April 2026 (secondary source). Feed operators publish schemas, not **measured delivery against the issuer's own NAV history**. That is the gap this repo fills.

## Single change that most raises the ceiling

First fix the code so the numbers are trustworthy. Then generalize to a **NAV-feed freshness table** for every onchain NAV feed with a public issuer series: on-date rate, lag distribution, missed values and ripcord events, re-measured on a stated cadence. An SLA-style table across feeds and providers is the kind of thing a fund operations or risk team cites.

## Ranked features

| # | Feature | Impact | Effort | Needs |
|---|---|---|---|---|
| 1 | Kill the surviving mutants; split the Chronicle "unseen" categories; fix the chart title | 4 | S | No |
| 2 | Feed-agnostic measurement core (any feed and issuer series pair) | 4 | M | No |
| 3 | Coverage: BENJI/FOBXX, USDY and other pairs already screened, plus SmartData feeds with public NAV | 5 | M | Issuer histories: some need scraping (check terms); flag any paid source |
| 4 | Ripcord and `navDate` staleness monitor | 4 | S–M | Rahil approves any scheduled run |
| 5 | Freshness table and CSV, method-versioned | 4 | S–M | Rahil approves publishing |
| 6 | Issuer confirmation of strike and publication times | 3 | S | Rahil sends any message |

1. **Fix first.** *Proof:* rerunning the 12 mutants leaves 0 survivors, or each survivor is documented as equivalent. Chronicle's count is split into "no exact NAV carried (2025)", "skipped label" and "near-duplicate value", and each 2026 case is listed.
2. **Core.** *Proof:* the USTB results reproduce exactly through the new core, and a synthetic feed with planted delays returns the planted lags.
3. **Coverage.** *Proof:* each added pair states its issuer series source, its coverage dates and the label rule. Pairs without a public series are listed as excluded, as BUIDL and USYC already are.
4. **Ripcord monitor.** *Proof:* historical replay lists every ripcord change and every `navDate` older than one business day, with block references.
5. **Table.** Every cell equals the CSV, with no third-party requests.
6. **Issuer times.** Replace "value-change date approximates valuation" with confirmed times where issuers answer, and keep the approximation otherwise.

## Non-goals

No ranking of oracle providers as "better" beyond the measured pairs. No claim about price accuracy beyond matching issuer-published values.
