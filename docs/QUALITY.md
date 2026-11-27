# Quality review, round 2

Independent review under rubric v1 of commit `9752755de1d97de83ca42f0b1965e5be9aadd19f`, carried out 2026-11-27 UTC. The reviewer did not write any of the reviewed code or documents. Scores and gaps are also recorded in [`QUALITY.json`](../QUALITY.json).

**Overall: 5/10, capped by the post kit.** Round 1 scored 3/10. The USTB delivery study is now built, pinned and reproducible, and the core counts hold up exactly. Two clock problems keep it short of a 9. First, the headline sentence states a stricter claim than the metric behind it supports. Second, the last two issuer labels in scope are API forward fills, not published NAVs. The chart and three of the four drafts inherit both problems.

| Dimension | Score | Reason |
| --- | ---: | --- |
| Answer | 6 | The headline is clear but false as worded. 582 of 593 changes, not 584, arrived on the next NYSE session date. Using the issuer's own valuation calendar gives a stronger answer, 589 of 593, which the study does not report. |
| Evidence | 6 | Every reported number reproduces, and the layers and limits are well kept. Forward-filled labels are treated as observations. The −5.86 bp extreme is not linked to the skipped July 26, 2024 value. The 'published after' caveat understates the evidence. |
| Reproducibility | 7 | A clean clone reproduced every USTB metric and the exact chart bytes from a fresh dRPC capture, and the OUSG and USDY checks also reproduced. The pinned label digest includes the two forward-filled labels, so a capture after Superstate publishes the November 25 NAV will fail replay. |
| Usefulness | 7 | The measured delivery schedule, the eight skipped values and the forward-fill behaviour go beyond NavBridge's simulated data and the vendor's heartbeat parameter. It covers one oracle on one chain. |
| Completeness | 8 | The reshaped brief is delivered: weekends, holidays, month-ends, heartbeat, a chart, a multi-day OUSG check, the USDY oracle and BENJI filing clocks. Nothing is half-built. |
| Documentation | 8 | The documents are thorough, agree with the code and read without chat history. The remaining errors are small: the headline wording, the access date, the weekend interval count and a missed tie. |
| Post kit | 5 | The chart title needs a footnote, and the chart plots two forward-fill points as data. Its bands are built in by construction, and a label overlaps a data point. Draft 1 reuses the 584 count. Drafts 2 and 3 invite a staleness reading the evidence does not support. |
| Code | 7 | The code is clean and the tests are behavioural with failure paths. The logic where this review found defects (posting-date semantics, trailing fills, month-end, digest tamper) is untested. |

## What the reviewer ran

All commands ran in a fresh clone at the reviewed head, in a scratch directory outside the repository. Heavy captures ran through the host workload scheduler.

- `python3 -m unittest discover -s tests`: **21/21 pass** on Python 3.14.8 and on Python 3.10.
- `python3 scripts/issuer_history.py` exits 0. The gate is `{USTB, BENJI}` 2/6 and the benchmarks are `{USTB, USDY, BENJI}` 3/6.
- `python3 scripts/feed_history.py capture` read from public dRPC, then `replay`, then `render_chart.py … --check`. All exited 0. The replay JSON is identical to the builder's except for receipt timestamps. Results:
  - 920 stored rounds: 46 in phase 1 (40 active) and 874 in phase 2 (849 active). All 920 match an issuer value, and 31 are archival only.
  - 889 of 889 active observations match an issuer value exactly. 593 of 601 distinct values are covered.
  - Session counts are {0: 1, 1: 584, 2: 8}. The median is 37.33 h, the 90th percentile 85.26 h and the maximum 110.18 h.
  - 283 intervals exceed 95,400 s, and the longest is 95,484 s.
  - The month-end count is 29/28/27. Daily extremes match RESULTS: −5.8630 bp on 2024-07-29, −5.8041 bp on 2024-09-02, −4.2938 bp on 2025-10-14 and −3.1080 bp on 2025-11-11.
  - In the window, 430/430 observations match, coverage is 289/289, the issuer cohort is 288/288, sessions are {1: 284, 2: 5}, 51 of 58 Friday changes posted Monday and there were 122 weekend rounds.
- `python3 scripts/report_checks.py capture`, then `replay`: 14 pairs, all PDF digests and the chart bytes match. The minimum, median and maximum residuals are 0.0000072, 0.0000223 and 0.0142862 bp, with 13 of 14 within 0.000071 bp. November 23 gives 3.07635256 vs 3.07633878 bp.
- `python3 scripts/report_checks.py usdy-oracle`, run with the four digest-verified May 2025 PDFs: block hashes and the midnight crossing verified, and the evidence digest matches. The oracle agrees with the retrospective range and matches the report to six decimals on all four dates. The largest gap is 0.0034 bp.
- `python3 scripts/issuer_history.py --live` with no SEC identity: exit 0. Both USTB windows and the OUSG and USDY windows match, USYC refreshed, and both EDGAR reads were skipped with the remedy text. Verification is marked incomplete. The reviewer had no authorized SEC identification, so live EDGAR was not attempted.
- Two direct public reads of the Superstate API (an NAV window to 2026-11-28 and the financials endpoint) at 04:27 UTC, plus a 1360 px render of the committed SVG.

## Findings

### 1. "On the next NYSE session date" is not what 584 measures

The metric counts NYSE sessions after the label, through the ET posting date. Two changes posted on a Saturday after one session:

| Label | Posted (ET) | Sessions | On next session date? |
| --- | --- | ---: | --- |
| 2024-08-01 (Thu) | Sat 2024-08-03 09:09:23 | 1 | No, a day late |
| 2024-10-31 (Thu, month-end) | Sat 2024-11-02 09:09:35 | 1 | No, a day late |

Literally, **582 of 593** changes arrived on the next NYSE session date. RESULTS' table row ("observed after one NYSE session") is correct. The README title, README paragraph 1, RESULTS paragraph 1 and draft 1 are not. The month-end sentence has the same issue: on the posting-date definition, 26 of 28 observed month-end values arrived on the next session date.

### 2. The issuer's own calendar gives the stronger answer

Six of the nine NYSE exceptions fall the day after a bond-market holiday when Superstate's own labels carry the prior NAV. These are Columbus Day 2024-10-14, 2025-10-13 and 2026-10-12, and Veterans Day 2024-11-11, 2025-11-11 and 2026-11-11. The fund did not value on those days, so a change posted two NYSE sessions later was still on the next valuation date. The zero-session case (posted 2025-01-09, an NYSE closure) was a Superstate valuation date.

The reviewer took valuation dates to be the starts of value spells in the issuer series, up to the official NAV date. On that calendar, **589 of 593** changes posted on the next valuation date. The four one-day-late cases are 2024-08-01, 2024-08-27, 2024-10-31 and 2026-10-30, and **8** issuer values never appeared. That is the strongest headline the evidence supports, and it needs no external holiday calendar. The NYSE figure can stay as a secondary row.

### 3. The last labels in scope are forward fills

The pinned capture (2026-11-27 04:00 UTC) gives 11/25, 11/26 and 11/27 the 11/24 NAV, 11.291441, and `official.nav_date` is 2026-11-24. A request ending 2026-11-28, made at 04:27 UTC, also returned a **future-dated** 11/28 label with the same value. The API fills dates without a published NAV.

November 25 was an ordinary valuation day, so its fill will be replaced. As a result:

- the daily series ends in two 0 bp rows, which are the two dots on the zero line in the chart;
- the label counts (1,059 / 883 / 426) include two non-observations;
- the pinned label digest, and so every future capture-and-replay, depends on values Superstate will revise.

It also sharpens the reading of the daily gap metric. At 23:59:59 UTC on date D, the API most likely showed a fill of the previous NAV, which is what the feed held. The plotted gap is therefore a retrospective accrual gap, not staleness against a value a consumer could have read. The −1 bp weekday band and the −3 bp Friday band follow the bill yield. The −5.86 bp extreme is Friday accrual plus the skipped July 26, 2024 value.

### 4. Chart and drafts

- **Chart.** The title "USTB trailed Superstate's NAV" names the fund, not the feed, and holds only with the footnote above. It shows two fill artefacts at 0 bp. The "−5.86 · 2024-07-29" label overlaps a data point at 1360 px. The automated checks pass: 19 visible words, the byte check holds and the SHA-256 is `b06cb560…`. The fix is a delivery-schedule chart (589 next valuation date, 4 one day late, 8 never appeared) with a title that holds without a footnote.
- **Drafts.** Draft 1 carries the 584 wording. Draft 3 (Veterans Day) is accurate line by line, but Superstate did not value on November 11, and the feed posted the November 10 NAV on the next valuation date. A reader will see oracle lag. Draft 2 compares against a Friday label that may not have been public until Monday. Draft 4 (September month-end) is sound. All four pass preflight. Editorial and design approval remain pending, and design approval is Rahil's.

### What holds up

- **Exact fidelity.** 920 of 920 stored and 889 of 889 active answers equal an issuer value.
- **Phase join.** The crossover at blocks 20,464,406/407 is verified on-chain, and inactive spans are excluded and tested.
- **Coverage.** 593 of 601. The eight skipped values are listed with dates.
- **Heartbeat.** The heartbeat is treated as a directory setting, and the 84-second overshoot is not overclaimed.
- **Provenance.** The caveat that the feed's source is the asset manager's API sits beside the claim.
- **Other products.** The BENJI filing clocks, OUSG residuals and USDY oracle agreement reproduce exactly.
- **Privacy.** Public files contain no machine paths, contacts or keys.

## Gaps and owners

| # | Dimension | Owner | Fix |
| --- | --- | --- | --- |
| 1 | Answer | agent | Add next-NYSE-date and next-valuation-date fields. Lead with 589/593, and keep 582/593 and 584/593 with exact definitions. |
| 2 | Evidence | agent | Cap label metrics at `official.nav_date`, drop or flag provisional daily rows, recompute the digest and counts, move the live window end to 11/24 and document the forward-fill behaviour. |
| 3 | Reproducibility | agent | Same cutoff, plus a regression test that a revised trailing fill leaves the digest unchanged. |
| 4 | Reproducibility | time | After 2026-11-30, run a fresh clean-clone capture, replay and render check, and record the result in HANDOFF. |
| 5 | Post kit | agent | Replace the chart with the delivery-schedule chart, remove the fill points, fix the label collision, and update the SHA in post-review.json and HANDOFF. |
| 6 | Post kit | agent | Rewrite drafts 1–3 around next-valuation-date delivery and rerun preflight. |
| 7 | Code | agent | Add tests: Saturday post, Columbus Day carry, trailing fills, weekend month-end, the 23:59:59 boundary and a tampered reference digest. |
| 8 | Documentation | agent | Fix the access date, the 121 weekend intervals, the 2025-03-15 interval tie, the month-end wording and the README's QUALITY link text. |
| 9 | Usefulness | agent | Optional: add one more USTB feed (Chronicle, RedStone or another chain) for a cross-oracle comparison. |
| 10 | Evidence | rahil | Optional: approve one bounded polling window on the public financials endpoint to bracket Superstate's publication time. |

Gaps 1–3 and 5–7 are needed for a 9 or better on Answer, Evidence, Reproducibility, Post kit and Code. Gaps 4 and 10, live EDGAR identification, design approval and posting are pending items and do not lower the score.

## History

| Round | Head | Overall | Cap |
| --- | --- | ---: | --- |
| 1 | pre-release local revision | 3 | Completeness, because the feed comparison was missing |
| 2 | `9752755` | 5 | Post kit, from the clock and forward-fill issues |

The round 1 narrative is preserved in this file's history at commit `9752755`.
