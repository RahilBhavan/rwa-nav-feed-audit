# NAV feed audit: Public issuer NAV history qualified for two of six products

This independent study checked whether six tokenized Treasury products have enough public issuer NAV history to support comparisons with onchain feeds. The issuer fund NAV screen found two qualifying products on November 26, 2026, below the three-product threshold. The repository replays the recorded observations and publishes instructions for retrieving source material.

## Results

| Measure | Finding |
| --- | --- |
| Issuer fund NAV history | 2 of 6 products qualified. The replay includes 14 USTB date labels in two 2026 windows and 43 BENJI/FOBXX business-day valuations from September and October 2026, all in USD per share. [Results](docs/RESULTS.md#sample-accepted-rows) |
| Broader per-unit benchmarks | 3 of 6 products had dated benchmarks when the screen included USDY LLC's May 2025 accrued note principal in USD per token. [Results](docs/RESULTS.md) |

## How it works

`scripts/issuer_history.py` reads the research observations, verifies and extracts the BENJI filing excerpts, and counts the documented classifications. It can also compare current issuer responses with the recorded windows. `scripts/fetch_sources.py` saves non-SEC source files and records their hashes locally.

## Run it

Use Python 3.10 or newer from the repository root. The offline replay and all 10 tests require only the standard library.

```sh
python3 scripts/issuer_history.py
python3 -m unittest discover -s tests -v
```

Download the available non-SEC inputs and record their hashes under ignored `data/sources/`.

```sh
python3 scripts/fetch_sources.py
```

For an optional live comparison that includes EDGAR, set `SEC_USER_AGENT` locally to your own genuine identification and contact details. The CLI uses that value for the EDGAR requests only. The command makes seven bounded public requests and returns a failure status on source errors or fixed-window differences. EDGAR returned HTTP 403 for both filings with a contactless identifier in the original review. [EDGAR access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)

```sh
python3 scripts/issuer_history.py --live --user-agent "${SEC_USER_AGENT:?Set your genuine EDGAR identification and contact locally}"
```

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

- The published result measures benchmark availability. Historical chain updates, feed lag, deviation and heartbeat remain open.
- Source dates and filing acceptance times leave the original publication times unresolved. Franklin's series has four decimal places of reporting precision.
- Live responses can change. The offline replay uses the recorded observations and filing excerpts.
- This is independent research and has no affiliation with the named companies.

## License

The project code is licensed under the [MIT License](LICENSE). Third-party filings and data retain their own terms.

Part of [Rahil Bhavan's projects](https://github.com/RahilBhavan).
