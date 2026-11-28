# Reopened quality loop implementation handoff

Round four scored the research commit `4cd7c98` at 8/10 ([review](docs/QUALITY.md), [gap register](QUALITY.json)). This handoff records the producer's verification of the repair commit that follows it. A round-five independent review of that commit and Rahil's design approval are pending.

[Results](docs/RESULTS.md) · [Method](docs/METHOD.md#replay-and-verification) · [Source register](docs/SOURCES.md) · [Public repository](https://github.com/RahilBhavan/rwa-nav-feed-audit)

## Evidence to review

- **Chainlink answer and denominators.** 588 of 601 values posted on the next date the issuer’s labelled NAV changed. Four posted one day later, eight were unseen and one posted without a finalized successor date in the issuer series. The 2024 labels split 118 on date, three a day after and seven unseen. The later labels split 470 on date, one a day after, one unseen and one unknown. All eight unseen amounts are absent from all 920 stored rounds. Replay covers both aggregator phases, with 31 inactive rounds included in the absence check.
- **Chronicle capture and comparability.** Capture starts at consumer deployment block 22,926,094. Archive state and the router log pin activation at block 22,926,115. The range ends at Ethereum block 26,503,879 with hash `0x4763fd004596f13e42369a95222159fa52ccd36db8925d324d86631625e6249f` on November 27, 2026 at 03:33:11 UTC. The comparison starts on July 16, 2025, after the partial activation day. Both feeds use the frozen November 24 issuer cutoff. The compatible adapter was deployed later, on April 10, 2026. The earlier observations are router-consumer history.
- **Completeness.** The independent MEV Blocker sweep matched the 877 Blockscout v2 events in 358 contiguous ranges with at most six events per range. The normalized ordered log SHA-256 is `25b4e94eb3dd236486b718b22bd63f7c03293737b9fc74d2828786318da5d9dc`. The state, index and inclusion roles and capture digests are in the [Chronicle receipt](tests/evidence/chronicle-capture.json).
- **Shared outcomes.** Out of 340 issuer values, Chainlink was on date for 337 and Chronicle for 236. One Chainlink and 93 Chronicle values were unseen. A further value was right-censored for both feeds and appeared onchain. Among 246 exact pairs with finalized successors, median times were 09:10:47 and 11:32:29 New York time respectively. Chronicle was earlier for 81 and later for 165. Publication time is unknown. In 2026 alone (224 labels) Chainlink was on date for 222 and Chronicle for 205, with 0 and 11 unseen; three of Chronicle's 11 have a write within 0.1 bp of the NAV on the successor date. Eighty-two of the 93 unseen are 2025 labels. The first exact Chronicle match dates to November 11, 2025. The earlier stream contains nonmatching writes and the results do not assign a cause.
- **Capture failure paths.** Tests cover six full index pages, cursor stalls, a finite page safety cap, HTTP 429 and timeout retries, mismatched blocks and timestamps, missing receipt events, missing sweep events, blank and conflicting index hashes, unexpected router state and adapter end-state mismatch. Delivery tests cover before and after offsets, period counts, all-stored-round absence and distinct handling of unseen and censored cases.
- **Exact chart and drafts.** The [SVG](docs/ustb-gap.svg) has SHA-256 `a4a9248add98bf9c7fd161a862563365910fa669a879d73b2b849009740d26e7` and the title "588 of 601 USTB NAVs reached Chainlink the next NAV day". It contains 20 visible words and 588/4/8/1 marks. The producer inspected the librsvg renders with the pinned Archivo and IBM Plex Sans files at 342 and 680 px and hashed all five widths (342, 360, 390, 680 and 1,360 px) in the post receipt. Ink contrast is 13.20:1 on paper and 12.82:1 on the accent. The smallest label is nominally 14.08 px at 342 px, and the 588 dots form a dense band at phone width. All four exact [draft bodies](posts/DRAFTS.md) passed X Growth preflight and local anchor checks. The draft file is unchanged, SHA-256 `1b8c1f0d76bb618bf0c1c38ceb706a14c91d92fbd34e59565bae9503ff3ecbc6`. The [post receipt](posts/post-review.json) has the per-body hashes, render hashes, copy and visual limits.

## Producer verification

- The full suite passed all 39 tests on Python 3.14.8 and 3.10 through the host workload scheduler. Five tests are new: exact published counts (877 events, 655 exact, first exact block 23,775,027, 337/236 on date, 1/93 unseen, 81/165 earlier/later, near values), ties and ambiguity rules, the unseen cutoff and near-value window, the strict unseen boundary and the label-gap spell rules. Ten single-line mutants of `ustb_metrics.py` and `chronicle_check.py` were applied one at a time and each failed at least one test, including the seven that survived in round four. The completed Chronicle capture used the same scheduler. `git diff --check` passed.
- The completed keyless Chronicle capture ran on November 27 from 17:04:27 to 17:08:02 UTC. All 877 receipt and block-header checks passed. The normalized event capture SHA-256 is `6a9f68e7ea77c0273fc2890ffa7f2fe5b544428a9dababd0634c5ce09763c226`. Chronicle replay, now with the near-value fields, has SHA-256 `86c024ff6793ce6c1d9e5494b841ea2fde817c124e401cbcc534d03db85a32b8` (the round-four replay was `2482b61c…`; the old and new outputs differ only in the added fields).
- A separate standard-library calculation read the captured issuer labels, both stored phases, the crossover and the verified Chronicle events directly. It rebuilt the issuer value spells, checked all 920 stored answers for the eight unseen amounts and reproduced all shared delivery counts, paired medians and earlier/later counts. This is a producer cross-check. The independent data-source check is the full second log sweep.
- Chainlink replay used the existing pinned capture and reproduced the current chart bytes. The offline issuer screen and OUSG replays also passed. The immutable round-three review records the previous independent live Chainlink capture. The post-revision issuer durability check remains tied to later finalized values.

## Reproduce

Run pulls and suites through the host workload scheduler where required. Capture writes source files under ignored `data/`.

```sh
python3 -m unittest discover -s tests -v
python3.10 -m unittest discover -s tests -v
python3 scripts/feed_history.py capture
python3 scripts/feed_history.py replay > data/ustb/results.json
python3 scripts/chronicle_check.py capture
python3 scripts/chronicle_check.py replay > data/chronicle/results.json
python3 scripts/render_chart.py data/ustb/results.json docs/ustb-gap.svg --check
python3 scripts/issuer_history.py
git diff --check
```

For the keyless provider limits and optional transports, see [replay and verification](docs/METHOD.md#replay-and-verification). Chart bytes, visible word count, mark counts, alt text, exact draft bodies and evidence anchors are checked by the suite. To inspect a phone render, use `rsvg-convert -w 390 -o card.png docs/ustb-gap.svg` with Archivo and IBM Plex Sans available to Fontconfig.

The time-owned follow-up remains a clean-clone recapture, replay and SVG byte check after November 30 once Superstate finalizes later NAVs. Rahil retains review and posting approval, optional authentic EDGAR identification and any separate issuer publication observation.

## Independent review status

Round four (8/10 on `4cd7c98`) is recorded in [QUALITY.json](QUALITY.json). The repair commit that follows it closes the agent-owned gaps. The verifying agent reran all 39 tests on two Python versions, the chart check and both feed replays. Round five is next. Open items that are not agent-owned: the post-November-30 clean-clone recapture (time), Rahil's chart and posting decisions, optional EDGAR identification and the optional polling window.
