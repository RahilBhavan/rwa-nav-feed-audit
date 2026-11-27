# USTB NAV feed audit: 588 of 593 matched changes posted on the next issuer value-change date

![Chainlink’s Ethereum USTB delivery timeline. 588 changes posted on the next issuer value-change date, four a day after, eight unseen by the pin and one with unknown timing.](docs/ustb-gap.svg)

Across June 27, 2024 to November 24, 2026 issuer labels, Chainlink’s Ethereum USTB feed posted **588 of 593 matched changes on the next issuer value-change date**. Four posted a day after it, and the final match has no following finalized issuer change in the capture. All 889 active observations matched an issuer NAV through the pinned block. Eight of 601 distinct issuer values were unseen on the active proxy by that block.

## Results

**582 of 593** changed answers posted on the literal next NYSE session date. Exactly one session elapsed for 584, including two Saturday posts. Issuer value-change dates approximate the valuation schedule. The issuer’s actual strike and publication times are unknown. Chainlink identifies its source as the Asset Manager API and names Superstate as the auditor in its directory.

[Results and chart](docs/RESULTS.md) · [Method](docs/METHOD.md) · [Sources and digests](docs/SOURCES.md) · [Draft posts](posts/DRAFTS.md)

## How it works

The primary pair is the USTB NAV per Share proxy on Ethereum and Superstate’s USD NAV/share history. The comparison verifies both historical proxy phases and uses the state at block **26,503,879** as its cutoff. The shorter [Chronicle comparison](docs/RESULTS.md#chronicle-comparison) matches all seven sampled values on both feeds. The original six-product screen also found dated Franklin BENJI/FOBXX filed market-based NAV and USDY LLC accrued note principal per token. OUSG accounting supports a return comparison. BUIDL and USYC lacked a suitable public offchain series in the sources checked.

## Run it

Requires Python 3.10+ and IANA timezone data. PDF extraction requires Poppler’s `pdftotext`. All fetches are public reads. Run the capture commands through the host workload scheduler where one is required. Data and receipts are written under ignored `data/`.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/issuer_history.py
python3 scripts/feed_history.py capture
python3 scripts/feed_history.py replay > data/ustb/results.json
python3 scripts/render_chart.py data/ustb/results.json docs/ustb-gap.svg --check
python3 scripts/chronicle_check.py capture
python3 scripts/chronicle_check.py replay > data/chronicle/results.json
python3 scripts/issuer_history.py --live > data/issuer-history-live.json
python3 scripts/report_checks.py capture
python3 scripts/report_checks.py replay > data/ousg/results.json
```

The feed replay verifies both chain captures and the normalized pre-cutoff issuer history before it reports round-level joins, daily gaps and month ends. The raw full-response hash can change as the source adds later dates. If an archival endpoint is unavailable, pass a public, archive-capable URL with `--rpc` and rerun the capture at the same blocks. See [input verification and commands](docs/METHOD.md#replay-and-verification) for the USDY reports and EDGAR options.

Live issuer replay skips EDGAR by default. Set `SEC_USER_AGENT` locally to genuine organization identification and an authorized nonpersonal contact to include EDGAR. Add `--verify-indices` to check submission identities and acceptance times. A one-time generic-client test returned HTTP 403 for the September index and XML. The offline command uses the pinned filing excerpts and records both acceptance times from the public filing indices.

## Repository layout

- `scripts/` contains the replay and retrieval commands.
- `tests/` contains the test suite, research observations, and SEC filing excerpts.
- `docs/` contains the findings, methods and provenance.
- `posts/` contains draft summaries with evidence links.

## Documentation

Public repository: [RahilBhavan/rwa-nav-feed-audit](https://github.com/RahilBhavan/rwa-nav-feed-audit).

- [Results](docs/RESULTS.md) records why each product did or did not qualify.
- [Method](docs/METHOD.md) defines the screen, clocks and extraction steps.
- [Sources](docs/SOURCES.md) lists provenance, retrieval routes and capture hashes.
- [Decisions](docs/DECISIONS.md) records the scope decisions.
- [Quality review](docs/QUALITY.md) records the final three-round assessment and remaining gaps.

## Sources

Superstate, Circle/Hashnote and Ondo publish the series checked in November 2026. The SEC hosts Franklin's September and October 2026 filings. The source register gives the access dates, response hashes and instructions for the May 2025 USDY LLC reports. [Source register](docs/SOURCES.md)

## Scope and limits

The comparison is retrospective. The issuer date supplies no publication clock. The final block bounds onchain follow-up and the captured official NAV date bounds issuer labels. The Chronicle comparison covers a shorter shared window. This independent project has no affiliation with the providers.

## License

Project code is [MIT-licensed](LICENSE). Third-party sources retain their own terms. The repository includes research results, selected factual observations and source receipts. Full downloaded inputs stay local.

Part of [Rahil Bhavan's projects](https://github.com/RahilBhavan).
