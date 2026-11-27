# Method

## Study pair and cutoff

Superstate fund ID `1`, CUSIP `86851T204`, has Ethereum share token `0x43415eB6ff9DB7E26A15b704e7A3eDCe97d31C4e`. Match its issuer-published USD NAV/share to Chainlink Ethereum proxy `0x289B5036cd942e619E1Ee48670F98d214E745AAC`. The proxy and both aggregators return the description **USTB NAV per Share** and six decimals. Each answer is an integer in millionths of a dollar per share. [Source register](SOURCES.md#ustb)

The pinned mainnet block is **26,503,879** (2026-11-27 03:33:11 UTC). The last full UTC date in scope is November 26. For each phase, read the aggregator address via `phaseAggregators(uint16)` and its terminal round from `latestRoundData()` at the pin. Fetch every proxy `getRoundData(uint80)` ID from 1 through that terminal number. IDs encode `(phase << 64) | round`. Bounded Multicall3 groups keep RPC volume low. Check every returned ID, answer, timestamp and the terminal round against the aggregator. Missing, reverted or malformed rounds fail capture. [Chainlink historical data](https://docs.chain.link/data-feeds/historical-data) · [Multicall3 deployment](https://www.multicall3.com/deployments)

Stored rounds and consumer-visible rounds differ at a crossover. An archive-state binary search located the crossover. Historical reads of the adjacent blocks **20,464,406 / 20,464,407** verify the switch from phase 1 round 40 to phase 2 round 26 on 2024-08-05 at 19:18:47 UTC. Exclude phase 1 rounds 41–46 and phase 2 rounds 1–25 from the active stream. Phase 2 round 26 becomes active at the switch-block timestamp. Both sides of the switch quoted $10.305852. For every other active round, availability uses its `updatedAt`. The first cohort date has a partial day before the first round. The daily sampling point on that date is covered.

## Join, clocks and denominators

- **Exact fidelity.** Parse the source `net_asset_value_date` as a calendar label and `net_asset_value` as a decimal. Convert exactly to integer millionths, rejecting sub-micro-dollar precision, duplicate labels and gaps. Exact fidelity is the fraction of feed answers in the set of all issuer values up to the cutoff. Coverage reverses the join. Take distinct values on issuer labels inside the cohort and count those with an active observation by the pinned block. The label cohort can start later than its surrounding round window.
- **Repeated values.** Preserve every dated issuer row. For a run of consecutive labels with the same value, use its first label as the candidate date and retain all candidate spell starts on or before the update’s UTC date. An ambiguous or future-only match can count toward value fidelity and is excluded from elapsed-time statistics. Identical consecutive feed answers count in freshness and interval checks. Only value-changing rounds count in the delivery timing distribution. Holiday and weekend duplicates are repeated labels. The API does not identify the number of valuation strikes.
- **Delivery clocks.** Calendar hours equal effective onchain time minus 00:00:00 UTC on the matched issuer date. NYSE session steps count scheduled exchange sessions after that date through the effective update date in `America/New_York`, including early-close trading days. A post before the session opens counts on that session date. The number of weekday steps also appears separately. The NYSE calendar is an explicit comparison rule drawn from the directory’s market-hours field, and a federal holiday can be an NYSE session. The issuer label has no validated timezone, NAV strike time or publication time. The midnight origin is a convention for date-to-chain elapsed time. It can bound oracle-only latency only if publication followed that origin and preceded the onchain round. The data do not establish either the exact publication time or an unconditional latency bound. [NYSE and federal calendars](SOURCES.md#business-day-references)
- **Basis points.** Signed gap is `10,000 × (feed − issuer) / issuer`, in the common USD/share unit. The primary daily measure pairs the latest active feed answer at **23:59:59 UTC** with Superstate’s **same date label**. It is a retrospective comparison of the posted answer with a dated value. The second measure compares each post-update answer with the **previous UTC date label** and computes percentiles on absolute gaps. They answer different questions. Negative values mean the feed trails the reference value. The denominator is always the issuer NAV used for that specific comparison.
- **Intervals.** Use consecutive `updatedAt` times within the same active phase and with both observations in the cohort. The directory gives 95,400 seconds as the heartbeat at capture. Compare it with observed intervals and retain the difference. The setting’s earlier history and each round’s trigger are unknown. The crossover gap is excluded from interval estimates. Percentiles use linear interpolation at rank `(n-1)p`.
- **Month-end.** Use the final NYSE session of each observed month. Report the first active post for the value spell starting on that label. Values held from an earlier label or skipped through the cutoff are visible in the result. November 2026 month-end is outside the study.

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
python3 scripts/issuer_history.py
python3 scripts/issuer_history.py --live > data/issuer-history-live.json
python3 scripts/report_checks.py capture
python3 scripts/report_checks.py replay > data/ousg/results.json
```

Run `python3 scripts/feed_history.py activation` to add only the boundary reads to a valid existing chain capture with no boundary receipt. With an archive-capable keyless endpoint, `--rpc URL` changes the transport. On PublicNode the block header resolved, but pin-state requests were rejected by the archival access gate on retry. A direct 0xRPC attempt was interrupted by rate limiting and historical-state availability; the complete capture came from dRPC. The pinned block hash, phase-boundary hash, canonical round digest and normalized pre-cutoff issuer digest are verified on replay. Live page and API metadata can change independently of the selected observations.

The replay exposes headline denominators and all case inputs. For example, with `jq` installed:

```sh
jq '{stored_round_fidelity, phases, issuer_labels, full: .full.summary, rounds_430: .review_window.summary, labels_288: .review_label_cohort}' data/ustb/results.json
jq '.full.daily[] | select(.day == "2024-07-29" or .day == "2024-09-02" or .day == "2025-11-11" or .day == "2026-10-03" or .day == "2026-10-04")' data/ustb/results.json
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

The [standalone SVG](ustb-gap.svg) is generated directly from the full daily gap series. It shows one point per UTC date with a linear zero-to-minus-six-bp axis and highlights the observed minimum. A byte comparison ties the SVG to the replay. Its alt description provides the denominator, date range, minimum and clock limit.
