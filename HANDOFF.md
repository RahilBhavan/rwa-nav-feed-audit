# Reopened quality loop implementation handoff

The implementation starts from `0e3936364167fe0e504a2c49eb004371e4e71f87`. The [current independent quality review](docs/QUALITY.md) scores the previous research revision `75fe51c` at 8/10. The [round-three gap register](QUALITY.json) records that review. This handoff records producer verification for the reopened slice. Independent review of the changed artifact and Rahil’s design approval are pending.

[Results](docs/RESULTS.md) · [Method](docs/METHOD.md#replay-and-verification) · [Source register](docs/SOURCES.md) · [Public repository](https://github.com/RahilBhavan/rwa-nav-feed-audit)

## Evidence to review

- **Chainlink answer and denominators.** 588 of 601 values posted on the next date the issuer’s labelled NAV changed. Four posted one day later, eight were unseen and one posted without a finalized successor date in the issuer series. The 2024 labels split 118 on date, three a day after and seven unseen. The later labels split 470 on date, one a day after, one unseen and one unknown. All eight unseen amounts are absent from all 920 stored rounds. Replay covers both aggregator phases, with 31 inactive rounds included in the absence check.
- **Chronicle capture and comparability.** Capture starts at consumer deployment block 22,926,094. Archive state and the router log pin activation at block 22,926,115. The range ends at Ethereum block 26,503,879 with hash `0x4763fd004596f13e42369a95222159fa52ccd36db8925d324d86631625e6249f` on November 27, 2026 at 03:33:11 UTC. The comparison starts on July 16, 2025, after the partial activation day. Both feeds use the frozen November 24 issuer cutoff. The compatible adapter was deployed later, on April 10, 2026. The earlier observations are router-consumer history.
- **Completeness.** The independent MEV Blocker sweep matched the 877 Blockscout v2 events in 358 contiguous ranges with at most six events per range. The normalized ordered log SHA-256 is `25b4e94eb3dd236486b718b22bd63f7c03293737b9fc74d2828786318da5d9dc`. The state, index and inclusion roles and capture digests are in the [Chronicle receipt](tests/evidence/chronicle-capture.json).
- **Shared outcomes.** Out of 340 issuer values, Chainlink was on date for 337 and Chronicle for 236. One Chainlink and 93 Chronicle values were unseen. A further value was right-censored for both feeds and appeared onchain. Among 246 exact pairs with finalized successors, median times were 09:10:47 and 11:32:29 New York time respectively. Chronicle was earlier for 81 and later for 165. Publication time is unknown. The first exact Chronicle match dates to November 11, 2025. The earlier stream contains nonmatching writes and the results do not assign a cause.
- **Capture failure paths.** Tests cover six full index pages, cursor stalls, a finite page safety cap, HTTP 429 and timeout retries, mismatched blocks and timestamps, missing receipt events, missing sweep events, blank and conflicting index hashes, unexpected router state and adapter end-state mismatch. Delivery tests cover before and after offsets, period counts, all-stored-round absence and distinct handling of unseen and censored cases.
- **Exact chart and drafts.** The [SVG](docs/ustb-gap.svg) has SHA-256 `29ad83e6124f13add910fa7867975405abbbdf80dc74862f63570305cd66703d`. It contains 20 visible words and 588/4/8/1 marks. The producer inspected the librsvg renders using Archivo and IBM Plex Sans at 342, 360, 390, 680 and 1,360 px. Ink contrast is 13.20:1 on paper and 12.82:1 on the accent. The smallest label is nominally 14.08 px at 342 px, and the 588 dots form a dense band at phone width. All four exact [draft bodies](posts/DRAFTS.md) passed X Growth preflight and local anchor checks. The draft file SHA-256 is `1b8c1f0d76bb618bf0c1c38ceb706a14c91d92fbd34e59565bae9503ff3ecbc6`. The [post receipt](posts/post-review.json) has the per-body hashes, render hashes, copy and visual limits.

## Producer verification

- The full suite passed all 34 tests on Python 3.14.8 and 3.10.21 through the host workload scheduler. The completed Chronicle capture used the same scheduler. `git diff --check` passed.
- The completed keyless Chronicle capture ran on November 27 from 17:04:27 to 17:08:02 UTC. All 877 receipt and block-header checks passed. The normalized event capture SHA-256 is `6a9f68e7ea77c0273fc2890ffa7f2fe5b544428a9dababd0634c5ce09763c226`. Chronicle replay produced identical bytes on Python 3.14 and 3.10, SHA-256 `2482b61ca2851515830a7d408a20ff9b3f757560c9944fa6d6531a675c8de30a`.
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
