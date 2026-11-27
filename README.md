# USTB NAV feed audit: 584 of 593 changed answers arrived on the next NYSE session date

![Daily USTB feed gap at UTC close reached 5.86 basis points below the same-date issuer label.](docs/ustb-gap.svg)

Chainlink’s Ethereum USTB feed usually posted a changed Superstate NAV on the next NYSE session date. Across June 27, 2024 to November 26, 2026, **584 of 593 value changes** arrived on that schedule. Every active proxy observation matched a published Superstate NAV exactly, while **8 of 601** distinct issuer values in the overlap never appeared on the active proxy.

## Results

The largest daily gap was **5.86 basis points below** the issuer’s same-date label at 23:59:59 UTC on July 29, 2024. Chainlink identifies its source as the Asset Manager API and names Superstate as the auditor in its directory. The comparison measures delivery from a dated label. The issuer’s publication timestamp is unknown.

[Results and chart](docs/RESULTS.md) · [Method](docs/METHOD.md) · [Sources and digests](docs/SOURCES.md) · [Draft posts](posts/DRAFTS.md)

## How it works

The primary pair is the USTB NAV per Share proxy on Ethereum and Superstate’s USD NAV/share history. The comparison verifies both historical proxy phases and uses the state at block **26,503,879** as its cutoff. The original six-product screen also found dated Franklin BENJI/FOBXX filed market-based NAV and USDY LLC accrued note principal per token. OUSG accounting supports a return comparison. BUIDL and USYC lacked a suitable public offchain series in the sources checked.

## Run it

All 21 tests passed. Requires Python 3.10+ and IANA timezone data. PDF extraction requires Poppler’s `pdftotext`. All fetches are public reads. Run the capture commands through the host workload scheduler where one is required. Data and receipts are written under ignored `data/`.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/issuer_history.py
python3 scripts/feed_history.py capture
python3 scripts/feed_history.py replay > data/ustb/results.json
python3 scripts/render_chart.py data/ustb/results.json docs/ustb-gap.svg --check
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
- [Quality review](docs/QUALITY.md) preserves the historical assessment and follow-up scope.

## Sources

Superstate, Circle/Hashnote and Ondo publish the series checked in November 2026. The SEC hosts Franklin's September and October 2026 filings. The source register gives the access dates, response hashes and instructions for the May 2025 USDY LLC reports. [Source register](docs/SOURCES.md)

## Scope and limits

The comparison is retrospective. The issuer date supplies no publication clock. The final block bounds the observed history. This independent project has no affiliation with the providers.

## License

Project code is [MIT-licensed](LICENSE). Third-party sources retain their own terms. The repository includes research results, selected factual observations and source receipts. Full downloaded inputs stay local.

Part of [Rahil Bhavan's projects](https://github.com/RahilBhavan).
