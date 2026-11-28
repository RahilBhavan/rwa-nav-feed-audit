# Quality review, round 4

- Rubric version: 1
- Reviewer: claude-opus-5-5. The builder was GPT-6.2 Sol, so the reviewer comes from a different model family. Fresh pass; every check was rerun.
- Reviewed head: `4cd7c98ef18aa9ad44bcb25a89f7c7d61b581849`, clean tree, equal to `origin/main`. The research commit is `c1916c2`; `4cd7c98` changes only records.
- Reviewed at: 2026-11-28T19:05:55Z
- Scope: wrote only `QUALITY.json` and this file. Network reads were one block header and one `latestRoundData` at the pin through keyless RPC. I did not rerun the full Chainlink or Chronicle captures; I replayed the committed captures. Runs went through the workload gate.

**Overall 8/10 (rounds: 3, 5, 8, 8).** The big round-three gaps are closed: the Chronicle comparison now covers the consumer's full history with a second log sweep, the by-period split is reported, and absence from all 920 stored rounds is checked. Code sets the score. The new Chronicle comparison code has untested rules, and one single-line mutant silently changes a published number. Two evidence points also need agent work: how the README frames Chronicle's 2025 "unseen" values, and the near-matches counted as unseen in 2026.

| Dimension | R3 | R4 | One-line reason |
| --- | ---: | ---: | --- |
| Answer | 8 | 9 | H1 is the question and the first paragraph answers it (588 of 601, about 9:10 a.m., seven of eight unseen from 2024). The README's Chronicle line (337 vs 236; 1 vs 93 unseen) misleads without the 2025 caveat. |
| Evidence | 9 | 9 | Absence from all 920 rounds and the second log sweep close round three. New: 82 of Chronicle's 93 unseen labels fall in a period when its consumer carried no USTB NAV, and three 2026 "unseen" values were followed by values within 0.08 bp. |
| Reproducibility | 10 | 10 | 34/34 tests on 3.14 and 3.10; offline replays exit 0; Chronicle replay SHA-256 `2482b61c…` and SVG SHA-256 `29ad83e6…` match HANDOFF; the pinned block hash and `latestRoundData` answer 11,291,441 match live. |
| Usefulness | 8 | 9 | Full-history Chronicle comparison, by-period reliability and named prior art. The like-for-like comparison window is not the one the README leads with. |
| Completeness | 9 | 10 | Chronicle pair delivered over its full public history. The post-November-30 issuer recheck waits on time. |
| Documentation | 9 | 9 | jq, current-review links and HANDOFF title fixed. STATE and HANDOFF credit "Astra" without explanation and open with the round-four retry. |
| Post kit | 8 | 9 | Draft 1 gives the full outcome; chart labels fixed. The chart title is still "Chainlink USTB". |
| Code | 9 | 8 | Capture failure paths and after/before statuses are now tested. 7 of my 12 mutants survive; one changes the published "655 of 877" count with no failing test. |
| **Overall (lowest)** | **8** | **8** | |

## What the reviewer ran

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s tests` (3.14.8, 3.10) | 34/34 OK on both |
| `issuer_history.py`, `feed_history.py replay`, `render_chart.py … --check`, `chronicle_check.py replay`, `report_checks.py replay` | All exit 0. Chainlink 588 / 4 / 8 / 1; unseen absent from all stored rounds = 8; 920 rounds all matching. Chronicle 337 / 236 on date, 1 / 93 unseen, medians 33,047 s (09:10:47) and 41,549 s (11:32:29), 81 earlier, 165 later, median difference 8,586 s, 655 of 877 exact events. |
| Digests | Chronicle replay `2482b61ca285…` and SVG `29ad83e6124f…` match HANDOFF; events `ordered_log_sha256` `25b4e94eb3dd…` matches the committed receipt (358 ranges). |
| Live keyless reads at block 26,503,879 | Block hash `0x4763fd00…6249f` matches; proxy `latestRoundData` answer 11,291,441 = the November 24 NAV $11.291441. |
| Chronicle unseen check (my script over `data/chronicle/events.json`) | Before November 11, 2025: 216 writes, all two-decimal, ranging $6.16–$11.73; only 12 equal a recent label rounded to cents. 2026: eight unseen labels have an adjacent-day value (about ±1 bp); three were followed by near values: Oct 16 (+0.005 bp), Oct 30 (−0.076 bp), Nov 4 (+0.028 bp). |

## Mutation probe (12 single-line mutants, reverted)

Killed (5): after/before swapped, period split moved by a day, left-censoring disabled, NYSE session count from the label day, `changed` true for the first round.
Survived (7). Of these, one changes published output: dropping the 10¹² scale on issuer values changes `exact_matching_events` (RESULTS: 655 of 877). Six leave both replay outputs byte-identical (untested rules): unseen cutoff `<`→`<=`, spell start after a label gap, repeat-value ambiguity `>1`→`>2`, earlier-than-label ambiguity boundary, ties counted as earlier, and the complete-label guard on `next_changes`.

## Round-3 gaps

| Gap | Status |
| --- | --- |
| Answer: plain first line | Closed |
| Usefulness: 12-day Chronicle sample | Closed |
| Usefulness: by-period, prior art | Closed |
| Evidence: absence from all rounds; Chronicle completeness | Closed |
| Post kit: draft 1, chart labels and title | Partly (title unchanged) |
| Completeness: Chronicle pair | Closed |
| Code: Chronicle failure paths; after status | Closed (new survivors) |
| Documentation: stale labels, jq | Closed |
| Reproducibility: post-revision recapture | Open (time) |
| Evidence: publication-time polling | Open (Rahil, optional) |

## Remaining gaps

Agent: (1) test `exact_matching_events` and the six untested rules; (2) lead the README comparison with the like-for-like 2026 window and state that the 2025 consumer writes were not NAV values; (3) separate near values from skipped labels in the Chronicle unseen count; (4) make the chart title a claim; (5) update STATE/HANDOFF and explain or drop "Astra". Time: recapture after November 30. Rahil: chart and draft approval, posting, optional EDGAR identity and polling window. Details in `QUALITY.json`.

---

# Quality review, round 3

This is an independent review under rubric v1 of commit `75fe51c317caf3f9c73029339983f5a048b80213`, carried out on 2026-11-27 UTC. The reviewer wrote none of the reviewed code or documents. The commit history does not record which model built the project. The dashboard owner should confirm that the builder came from a different model family, as the rubric requires. Scores and gaps are also recorded in [`QUALITY.json`](../QUALITY.json).

**Overall: 8/10.** Answer, usefulness and the post kit share the cap. Previous rounds scored 3/10 and 5/10. Every round 2 defect is fixed. The headline is now true and is the strongest count the evidence supports. The forward-filled labels are cut at the official NAV date. The chart is honest. The drafts no longer invite a staleness reading. An independent recomputation from raw inputs reproduced every headline number exactly. Three things keep the project from a 9:

- The README does not answer the question in plain words.
- The Chronicle cross-check uses 12 days of a public history that runs to about 16 months.
- The results never say that 7 of the 8 skipped values fall in the first six months.

| Dimension | Score | Reason |
| --- | ---: | --- |
| Answer | 8 | The headline is correct, unhedged and not overclaimed. It does not pass the 10-second test, because the question is never stated and the H1 uses the coined term "next issuer value-change date". The plain answer, about 09:10 New York time on the next valuation morning, appears further down. |
| Evidence | 9 | Every number checked traces to replay output or a cited source. The five layers stay separate, and each limit sits next to its claim. Two gaps are minor. RESULTS can state that the 8 unseen values appear in none of the 920 stored rounds. Chronicle completeness rests on one third-party index. |
| Reproducibility | 10 | A fresh clone reproduced both pinned chain hashes, the normalized issuer digest and the exact chart bytes, even though the live financials bytes differed. The Chronicle, OUSG and live issuer replays also passed. Tests pass on Python 3.10 and 3.14. The only open item waits on time: a recapture after the issuer revises late-November labels. |
| Usefulness | 8 | The project measures delivery on real data, lists the skipped values and checks fidelity exactly. That goes beyond NavBridge's simulated data and the vendor's heartbeat setting. Three things are missing. The results do not show that reliability improved after 2024. The comparison with a second oracle is too small to rank the feeds, although enough history is public. The README never names the prior art. |
| Completeness | 9 | The reshaped brief is delivered: the availability gate, then the USTB study across weekends, holidays, month-end, heartbeat, deviation, a chart and review. The Chronicle pair covers only a short sample of its public history. |
| Documentation | 9 | The documents agree with the code and with each other on every number checked. Some labels are stale ("Round 2" link text, the HANDOFF title). Prior art is missing from the README. `jq` is used in METHOD but not listed. |
| Post kit | 8 | The chart passes its automated checks. Drafts 2 to 4 are accurate and each makes one claim. Draft 1 drops the 8 values that never posted, and its wording is hard to parse. The chart title "Chainlink USTB" states no point. The lone "Superstate" label at bottom left reads as an orphan word. |
| Code | 9 | The tests are behavioural and cover the round 2 gaps: Saturday posts, Columbus Day, the digest staying fixed under live revision, the 23:59:59 boundary and a tampered reference. Chronicle capture verification has no failure-path tests. The `after` status from `analyze()` is never asserted directly. |

## What the reviewer ran

All commands ran in a fresh clone at the reviewed head, in a scratch directory outside the repository. Captures ran through the host workload scheduler and used public, keyless endpoints only.

- **Tests.** `python3 -m unittest discover -s tests`: **25/25 pass** on Python 3.14.8 and 3.10.
- **USTB capture.** `python3 scripts/feed_history.py capture` from public dRPC at 05:05 UTC, then `replay`, then `render_chart.py … --check`. All three exited 0.
  - The chain hash `da192d93…` and the normalized label hash `f71f3296…` matched the pinned references.
  - The live financials bytes differed from the pinned snapshot but still reported `official.nav_date = 2026-11-24`.
  - The SVG SHA-256 is `4e7a2a20…5b97452`, matching the post receipt.
- **Independent recomputation.** A separate script read the raw `chain.json` and `issuer.json` without the project's metrics code. It rebuilt the active stream: phase 1 rounds 1–40, then phase 2 from round 26 at the switch-block time. It then classified every value spell from June 27, 2024 to November 24, 2026. Results:
  - 1,057 labels, 889 active rounds (40 in phase 1), and 889 of 889 matching an issuer value.
  - 601 spell starts: 588 posted on the next change date, 4 one day after, 8 unseen and 1 unknown.
  - 582 posted on the literal next NYSE session date. Sessions elapsed were {0: 1, 1: 584, 2: 8}.
  - The four late labels (2024-08-01, 2024-08-27, 2024-10-31, 2026-10-30) and the eight unseen dates were identical to RESULTS.
- **Secondary USTB figures.** The review-window column, timing table, intervals, daily-gap rows, the July 29 arithmetic, the month-end counts (29/28/26/27) and the September 30 example all match the replay.
- **Chronicle.** `python3 scripts/chronicle_check.py capture`, then `replay`: 25 events. All seven paired time differences match the RESULTS table, from +1,176 s to −11,100 s.
- **OUSG.** `python3 scripts/report_checks.py capture`, then `replay`: 14 pairs, and every PDF and chart byte check passed. The minimum, median and maximum residuals are 0.0000072, 0.0000223 and 0.0142862 bp, with 13 of 14 at or below 0.000071 bp. These match RESULTS.
- **Issuer history.** `python3 scripts/issuer_history.py` (offline) and `--live`: the gate is {USTB, BENJI} 2/6 and the benchmarks are {USTB, USDY, BENJI} 3/6. The live run skipped EDGAR because no authorized SEC identity was set, and it marked verification incomplete, as documented.
- **Not rerun.** The USDY oracle check needs the issuer's 277 MB archive. `report_checks.py` is unchanged since round 2, which reproduced it.
- **Chart.** The SVG was rendered at 342, 680 and 1360 px. Labels do not collide. Mark counts are 588, 4, 8 and 1.
- **Chronicle history check.** One keyless Blockscout v2 read at block 23,500,000 confirmed that the Chronicle consumer emitted `Poked` events in September 2025.
- **Privacy.** A scan of the tracked files found no machine paths, personal contacts or keys.

## Findings

### 1. The answer needs a plain-language first line (answer, agent)

The README's H1 reads "588 of 593 matched changes posted on the next issuer value-change date". It is exact, but a stranger has to decode "issuer value-change date" and work out the question. The evidence supports a plainer answer: Chainlink's Ethereum USTB feed posted each Superstate NAV on the next valuation morning, at a median of 09:09:47 ET, for 588 of 601 values. Four posted a day late, 8 never posted and 1 is too recent to classify. The coined term can become the definition beneath that answer. Using 601 as the denominator also puts the skipped values into the headline claim, instead of leaving them in the next sentence.

### 2. Reliability changed after 2024 (usefulness, agent)

Grouping the replay's delivery statuses by label year gives:

| Labels | On next change date | One day late | Unseen | Unknown | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Jun 27 – Dec 31, 2024 | 118 | 3 | 7 | 0 | 128 |
| Jan 1, 2025 – Nov 24, 2026 | 470 | 1 | 1 | 1 | 473 |

An integrator would care most about this split. The repository does not report it. Compute it in `ustb_metrics.analyze`, add a test and show it in RESULTS.

### 3. The Chronicle comparison can cover its full public history (usefulness and completeness, agent)

The capture's own router check shows the Chronicle consumer has been the router target since block 22,926,115 (July 2025), and Blockscout serves its `Poked` events from at least September 2025. The comparison stops at 7 values because `consumer_logs` walks at most four index pages. RESULTS correctly says the sample supports no ranking. Paging the full history, with paced requests and the existing per-log inclusion checks, would turn the anecdote into a two-oracle delivery comparison covering about 340 values. Few other public studies offer that.

### 4. Evidence refinements (evidence, agent)

- None of the 8 unseen values appears in any of the 920 stored rounds, including the 31 rounds on inactive aggregators. RESULTS can say so, with a replay field and a test, instead of stopping at "cause unknown".
- Chronicle event discovery depends on the Blockscout index. RPC checks confirm that each listed log was included in a block, but nothing confirms that no log was missed. Cross-check with chunked `eth_getLogs` calls or a second index.

### 5. Chart and drafts (post kit, agent; design approval is Rahil's)

- **Draft 1.** It reports 588 of 593 without the 8 values that never posted. Rewrite it as one claim over 601 values that names the skipped ones. Drafts 2 (the Friday NAV), 3 (Veterans Day) and 4 (September month-end) are accurate line by line against the replay.
- **Chart.** The title "Chainlink USTB" is a label, not a point. Use a claim of 20 words or fewer. Relabel the orphaned "Superstate" as "Superstate label date". Rename "Unseen" and "Unknown" so they read differently at a glance, for example "Never posted" and "Too recent". Rerun `render --check` and preflight, then update the hashes in `post-review.json` and HANDOFF.

### 6. Code (code, agent)

Add failure-path tests for Chronicle capture verification:

- a mismatched block hash or timestamp;
- a log missing from its receipt;
- index pages that overflow the page limit;
- a router switch from a nonzero address;
- an adapter end state that differs from the last event.

Add an `analyze()` case that asserts the `after` status and the one-day offset.

### 7. Documentation (documentation, agent)

Update the README and docs/README link text to "current quality review". Retitle HANDOFF for the round that implements these fixes. Add a prior-art sentence to the README, and list `jq` as an optional tool.

## What holds up

- **Exact fidelity.** All 920 stored and all 889 active answers equal an issuer value. The phase crossover is verified on chain at blocks 20,464,406 and 20,464,407.
- **Cutoff.** The cutoff is the earlier of the last complete UTC date and the official NAV date. The digest stays fixed across live revisions, which both a regression test and this round's fresh capture confirm. November 24's post is correctly left unclassified.
- **Two date tests.** The NYSE-date test and the issuer value-change test are reported separately, with exact definitions. The Saturday posts and bond-market holiday carries are named.
- **Daily-gap caveat.** The daily gaps are presented as retrospective, never as staleness against a NAV that was public at the time.
- **Other products.** The BENJI filing clocks, OUSG residuals and USDY oracle agreement keep their own definitions and limits.

## Items that do not lower the score

- **Time.** After 2026-11-30, rerun the clean-clone capture, replay and chart byte check once Superstate finalizes its late-November NAVs. Record the result in HANDOFF.
- **Rahil.** Four decisions remain:
  - design approval of the chart and draft texts;
  - whether and when to post;
  - optional live EDGAR verification with a genuine organizational `SEC_USER_AGENT`;
  - an optional single polling window to measure when Superstate publishes its NAV.

## Score history

| Round | Head | Overall |
| --- | --- | ---: |
| 1 | unrecorded (pre-release local revision) | 3 |
| 2 | `9752755` | 5 |
| 3 | `75fe51c` | 8 |

Orchestrator confirmation: GPT-6.2 Sol built the scientific slices. Each quality review ran as a fresh Claude Opus 5.5 task.
