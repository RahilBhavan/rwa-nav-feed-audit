# Method

## Study pair and cutoff

Superstate fund ID `1`, CUSIP `86851T204`, has Ethereum share token `0x43415eB6ff9DB7E26A15b704e7A3eDCe97d31C4e`. Match its issuer-published USD NAV/share to Chainlink Ethereum proxy `0x289B5036cd942e619E1Ee48670F98d214E745AAC`. The proxy and both aggregators return the description **USTB NAV per Share** and six decimals. Each answer is an integer in millionths of a dollar per share. [Source register](SOURCES.md#ustb)

The pinned mainnet block is **26,503,879** (2026-11-27 03:33:11 UTC). The last complete UTC date at the pin is November 26. The label-dependent cutoff is the earlier of that date and the original financials response's `official.nav_date`, November 24. The capture register freezes the date, official NAV, UTC observation time and financials hash. Later live financials bytes are receipted and their currency checked. They cannot move either historical cutoff. The label digest covers consecutive labels through the pinned official date, including any finalized labels beyond the last complete UTC date. Those extra labels can identify the next issuer change but are excluded from the daily and coverage cohorts. Pinned chain follow-up continues beyond the label cutoff, so a value from the last finalized label can still be matched. For each phase, read the aggregator address via `phaseAggregators(uint16)` and its terminal round from `latestRoundData()` at the pin. Fetch every proxy `getRoundData(uint80)` ID from 1 through that terminal number. IDs encode `(phase << 64) | round`. Bounded Multicall3 groups keep RPC volume low. Check every returned ID, answer, timestamp and the terminal round against the aggregator. Missing, reverted or malformed rounds fail capture. [Chainlink historical data](https://docs.chain.link/data-feeds/historical-data) · [Multicall3 deployment](https://www.multicall3.com/deployments)

Stored rounds and consumer-visible rounds differ at a crossover. An archive-state binary search located the crossover. Historical reads of the adjacent blocks **20,464,406 / 20,464,407** verify the switch from phase 1 round 40 to phase 2 round 26 on 2024-08-05 at 19:18:47 UTC. Exclude phase 1 rounds 41–46 and phase 2 rounds 1–25 from the active stream. Phase 2 round 26 becomes active at the switch-block timestamp. Both sides of the switch quoted $10.305852. For every other active round, availability uses its `updatedAt`. The first cohort date has a partial day before the first round. The daily sampling point on that date is covered.

## Join, clocks and denominators

- **Exact fidelity.** Parse the source `net_asset_value_date` as a calendar label and `net_asset_value` as a decimal. Convert exactly to integer millionths, rejecting sub-micro-dollar precision, duplicate labels and gaps. Exact fidelity is the fraction of feed answers in the set of all issuer values up to the cutoff. Coverage reverses the join. Take distinct values on issuer labels inside the cohort and count those with an active observation by the pinned block. The label cohort can start later than its surrounding round window.
- **Repeated values and the issuer proxy.** The API returns carry-forward labels for dates without a newer published value, including future dates. For consecutive same-value labels, use the spell start as the candidate for the join. Retain all candidate starts through the earlier of the observation’s UTC date and the label cutoff. An ambiguous or future-only join can count toward exact fidelity with timing unclassified. The next issuer value-change date is the first following finalized label whose NAV differs. It is a proxy for the valuation schedule. Repeats alone cannot distinguish a fill from a valuation at the same NAV. The proxy supplies neither strike timestamps nor publication times.
- **Delivery dates and censoring.** Interpret the effective posting time in `America/New_York` using IANA timezone data, including the EDT/EST offset on each date. Compare the resulting date for literal equality with (1) the first scheduled NYSE session strictly after the issuer label and (2) the next finalized issuer value-change date, where available. Compute elapsed NYSE sessions separately after the label through the ET posting date, including early-close sessions. A Saturday can follow one elapsed session and fail the equality test. Calendar hours use the label’s 00:00:00 UTC as an arithmetic origin. They measure date-to-chain time without identifying any unconditional bound on oracle latency. [Business-day references](SOURCES.md#business-day-references)
- **Delivery chart.** For each in-range label spell, record the first active post assigned uniquely to that spell. Compare its ET date with the successor date when both are observed and the feed changed value. A value is unseen through the pin when it has no active match, has a documented successor and the chain window extends beyond that successor’s ET date. Other cases stay unknown, including absent successors, ambiguous matches and an initial feed observation without a known transition. The last matched change, from the November 24 label, posted on November 25, and its next issuer change remains right-censored. The replay preserves this null explicitly, including when live tail rows are later revised.
- **Basis points.** Signed gap is `10,000 × (feed − issuer) / issuer`, in the common USD/share unit. The daily gap pairs the latest active feed answer at **23:59:59 UTC** with Superstate’s **same date label**. This retrospective join can use a later-published value. The forward-fill observation makes contemporaneous availability an open question. The second measure compares each post-update answer on an in-scope UTC date with the **previous UTC date label** and computes percentiles on absolute gaps. They answer different questions. Negative values mean the feed trails the reference value. The denominator is always the issuer NAV used for that specific comparison.
- **Intervals.** Use consecutive `updatedAt` times within the same active phase and with both observations in the cohort. The directory gives 95,400 seconds as the heartbeat at capture. Compare it with observed intervals and retain the difference. The setting’s earlier history and each round’s trigger are unknown. The crossover gap is excluded from interval estimates. Percentiles use linear interpolation at rank `(n-1)p`.
- **Month-end.** Use the final NYSE session of each observed month. Report the first active post for the value spell starting on that label. The result distinguishes values held from an earlier label, unseen values and the two NYSE tests. November 2026 month-end is outside the study.

## Chronicle comparison

Use the Chronicle USTB Ethereum consumer, router and Chainlink-compatible adapter from Chronicle’s registry. Scan from the consumer’s deployment at block **22,926,094** through the common Ethereum pin **26,503,879**. Archive-state reads bracket deployment and verify the router target immediately before and after its activation at block **22,926,115** and again at the pin. The indexed router log history has one consumer switch through the pin. The activation log agrees with Ethereum RPC, and the pinned adapter reads the last consumer value at 18 decimals.

Walk the Blockscout v2 address index from the pinned upper bound through its final page or past the deployment boundary. Keep only `Poked(address,uint128,uint48)` events. Require a strictly descending block/log-index cursor and check its relationship to the page boundary. Requests are paced and retry rate limits, transient transport failures and timeouts with bounded backoff. The page safety limit fails the capture if reached before the boundary. A second provider scans contiguous, non-overlapping inclusive block ranges with address- and topic-filtered `eth_getLogs`. Compare the complete event sets by block hash, block number, log index, topics and data, plus transaction hash wherever the index supplies it. The RPC sweep supplies missing index transaction hashes. Then check each event against its successful receipt and the header’s hash and timestamp. Replay checks the pinned normalized event digest and the local coverage receipt. Raw pages stay local. [Chronicle contracts and receipts](SOURCES.md#chronicle-ustb)

Keep the complete event stream, including repeated writes. For delivery timing, limit both feeds to issuer spell starts after the router’s activation date in both UTC and New York, ending November 24, 2026. A date-only label on the activation day cannot resolve that partial day. The 2025 portion measures the Chronicle router consumer directly. The Chainlink-compatible adapter was deployed on April 10, 2026. Use only Chronicle values that match the six-decimal issuer integers exactly after scaling by `10^12`. Compare the first active changed post on each feed, using Chronicle’s block timestamp for visibility and keeping the payload’s `age` separately. A value already held at activation is left-censored. A final label with no successor is right-censored for the date test even when a post exists. A value can count as unseen only with no active observation by the pin and follow-up beyond its successor’s ET date. A same-day, earlier or later post is classified by its actual New York date. These dates describe when the labelled NAV series changed. Publication times remain unknown.

The side-by-side counts use the same denominator of issuer spell starts, retaining unseen and unknown as separate outcomes. Median posting times and earlier/later comparisons use the identical subset of exact matched pairs with finalized successors. The per-label output retains both post clocks and their elapsed difference when available, including pairs whose date classification is right-censored.

## Other product references

The original gate counts publicly retrievable dated issuer fund NAV per share for the same instrument. Eligibility uses the series unit, valuation basis and presence of multiple dates. The status notes explain why other public series fail that definition. USDY note principal is a broader per-unit reference with its own dated observations and a different valuation basis.

BENJI filing acceptance is the timestamp on the SEC index in `America/New_York`. Compute calendar-date differences from both the stated reporting-period end and the last valuation label. The filing precision is four decimals. Acceptance records the SEC’s own filing clock.

For OUSG, use all listed November statements through November 25. Extract unaudited **period-to-date** USD amounts from the changes in net asset value section. Divide net income by beginning balance plus additions minus redemptions. Compare against chart change from the statement date’s midnight UTC bucket to the following date’s midnight bucket. Each return is multiplied by 10,000. The result quantifies agreement without establishing a per-unit administrator level or the chart’s publication time.

For USDY, use the **Section C Reference Token** line of the four May 2025 Ondo USDY LLC reports. Use the accruing note denomination (USD per USDY token). Read `getPrice()` on the legacy oracle at the last pinned Ethereum block at or before 23:59:59 UTC on each report date. Check each block hash and prove the following block crosses midnight. Verify the result against `getPriceHistorical(timestamp)` at the later USTB study block. The report’s end-of-day clock has no verified timezone in this sample. Use the explicitly specified same-date UTC price bucket and round to the report’s precision.

## Replay and verification

```sh
python3 scripts/feed_history.py capture
python3 scripts/feed_history.py replay > data/ustb/results.json
python3 scripts/render_chart.py data/ustb/results.json docs/ustb-gap.svg --check
python3 scripts/chronicle_check.py capture
python3 scripts/chronicle_check.py replay > data/chronicle/results.json
python3 scripts/issuer_history.py
python3 scripts/issuer_history.py --live > data/issuer-history-live.json
python3 scripts/report_checks.py capture
python3 scripts/report_checks.py replay > data/ousg/results.json
```

Run `python3 scripts/feed_history.py activation` to add only the boundary reads to a valid existing chain capture with no boundary receipt. With an archive-capable keyless endpoint, `--rpc URL` changes the transport. On PublicNode the block header resolved, but pin-state requests were rejected by the archival access gate on retry. A direct 0xRPC attempt was interrupted by rate limiting and historical-state availability; the complete capture came from dRPC. The pinned block hash, phase-boundary hash, canonical round digest and normalized pre-cutoff issuer digest are verified on replay. Live page and API metadata can change independently of the selected observations.

Chronicle’s default completeness sweep uses 10,000-block ranges in batches of ten with public MEV Blocker. `--log-span` and `--log-batch` accommodate smaller provider limits and `--log-rpc` changes the independent log transport. `--rpc` controls archive-state reads. For individual inclusion checks, the default `--receipt-rpc` uses MEV Blocker with five events per batch (two calls each). Use `--receipt-batch 1` for dRPC’s free batch limit of three calls. Free dRPC also refused ranges above 100 blocks and throttled a full attempt using per-event calls. A range error, historical state error, unmatched log or exhausted retry fails capture. Rerun with the same pins and an endpoint that serves the required history.

The replay exposes headline denominators and all case inputs. The following examples use optional `jq`:

```sh
jq '{stored_round_fidelity, phases, issuer_labels, full: .full.summary, review_rounds: .review_window.summary, review_labels: .review_label_cohort}' data/ustb/results.json
jq '.full.daily[] | select(.day == "2024-07-29" or .day == "2024-09-02" or .day == "2025-11-11" or .day == "2026-10-03" or .day == "2026-10-04")' data/ustb/results.json
jq '.full.summary | {delivery_by_period, unseen_absent_from_all_stored_rounds}' data/ustb/results.json
jq '.full.delivery[] | select(.status != "next_change")' data/ustb/results.json
jq '.full.delivery[] | select(.status == "unseen") | {label,answer,absent_from_all_stored_rounds}' data/ustb/results.json
jq '{first,last,ranges,logs,max_logs_per_range,ordered_log_sha256}' data/chronicle/coverage.json
jq 'del(.rows)' data/chronicle/results.json
jq '.full.month_ends[] | select(.label == "2026-09-30")' data/ustb/results.json
```

The live issuer CLI reports complete response row counts and first/last labels for each fetch. A hash match is independent of fixed-window row agreement. The full USTB date range comes from feed replay. An unset `SEC_USER_AGENT` skips EDGAR while the other sources run. Report metadata distinguishes skipped requests, HTTP errors, parsing failures, revised rows and changed bytes. The command exits 1 for attempted verification failures, and the JSON marks verification incomplete when EDGAR is skipped. For the optional EDGAR run, set a genuine authorized organizational User-Agent with a nonpersonal contact locally and run `python3 scripts/issuer_history.py --live --verify-indices`. SEC reads are spaced at least 1.05 seconds apart. [SEC fair-access policy](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)

To recover the four USDY PDFs, use the issuer’s **Daily Attestation Reports – Ondo USDY LLC** archive in the [source register](SOURCES.md#usdy-llc-daily-report-archive). Pass the local archive to `python3 scripts/fetch_sources.py --usdy-archive PATH_TO_ZIP` and run `python3 scripts/report_checks.py usdy`. Then run `python3 scripts/report_checks.py usdy-oracle > data/sources/usdy-oracle-results.json` for the two pinned Ethereum reads per report date. Each PDF digest is verified before parsing. The same extraction works from individually downloaded files in `data/sources/`. To download the full archive from the published link, allow space for about 277 MB and run the download through the host workload scheduler where required.

```sh
# Save the ZIP from the issuer-linked archive to data/usdy-llc-daily.zip first.
python3 scripts/fetch_sources.py --usdy-archive data/usdy-llc-daily.zip
python3 scripts/report_checks.py usdy-oracle > data/sources/usdy-oracle-results.json
```

For raw extraction use `pdftotext -layout INPUT.pdf -` on any pinned PDF.

The [standalone SVG](ustb-gap.svg) shows one mark per value spell against its original issuer label date. The vertical jitter in the most populated row separates marks and encodes no additional measurement. The render byte check binds the chart to the verified replay. The description gives the sample size, dates, counts and clock limits.
