# Independent NAV feed audit for tokenized funds

How far do onchain NAV or price feeds lag or deviate from issuer-published NAV for BUIDL, USTB, USYC, OUSG, USDY and BENJI? Compare supported pairs across normal business days, weekends and month-end using issuer NAV history and onchain feed updates.

The initial study tests whether dated issuer fund NAV history is publicly retrievable for at least three products. If fewer qualify, document the narrower finding and close the initial study. The follow-up scope is USTB delivery timing, where the availability study found a usable issuer series.

## Research method

1. Record the instrument, valuation unit, source, and available clocks for every series. Distinguish issuer statements, offering terms, arithmetic, onchain facts, and interpretation.
2. For supported feed pairs, pin the dates, blocks, and inputs. Measure deviation, heartbeat and lag where the source clocks allow it. Include weekends and month-end and produce a chart.
3. Use public, keyless reads. Document source URLs, access dates, identities and digests. Store downloaded inputs in ignored local storage.
4. Independently review the results and reproduce the calculations.

See [Method](docs/METHOD.md), [Results](docs/RESULTS.md), [Sources](docs/SOURCES.md), and [Decisions](docs/DECISIONS.md).
