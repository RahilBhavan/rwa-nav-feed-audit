# Issuer-history results

**The strict issuer fund NAV gate failed at 2/6 on 2026-11-26.** USTB and BENJI/FOBXX have retrievable, dated issuer NAV per share. The broader dated per-unit benchmark count is **3/6** when USDY LLC’s accrued note principal per token is included. The benchmarks measure different instruments and retain their own valuation definitions. Feed lag and deviation remain unmeasured.

| Product | Status | Evidence and decision |
| --- | --- | --- |
| BUIDL | No qualifying offchain history found | Securitize's launch release specifies a target of $1 per token and monthly distribution of daily accrued dividends. Its broker-dealer financial statements quote $1 per share. Form D/D-A concerns the offering. The BNY fund accounting guide documents separate class-level valuation dates and NAV fields on Ethereum, including Ethereum A and I. RedStone and Chronicle are feed providers. None of the checked sources supplies a dated offchain per-class series. [Sources](SOURCES.md#buidl) |
| USTB | Usable dated NAV/share | Superstate's API returned 1,059 distinct date labels from 2024-01-03 through 2026-11-26 in one full response. The replay pins 14 rows across two windows. At capture the financials endpoint gave official NAV 11.291441 USD/share dated November 24, alongside a different indicative price on November 26. The daily history repeats 11.29144100 on November 24–26. November 25 and 26 are provisional carry-forward labels. Weekend and holiday labels establish coverage of the published series. [Sources](SOURCES.md#ustb) |
| USYC | Circular oracle history | Circle International Bermuda administers the token representing the Hashnote fund share. The historical endpoint returned 45 reports at access. For example round 561 reported 1.144875672876728641 USD per USYC at 2026-11-25 13:33:35 UTC. Hashnote says the API indexes normalized onchain reports. Circle's filing and product materials did not supply an independent per-share series. [Sources](SOURCES.md#usyc) |
| OUSG | Accounting return check available, chart provenance unresolved | Ondo's public OUSG page contained 1,396 dated USD/token chart entries at capture. Ondo's app hosts public administrator statements with fund-wide NAV and daily accounting figures. Those figures support a daily change check. The examined packets lack a per-unit NAV or an offchain unit count covering the same fund interests. A tokenized-only denominator would mix populations with fund-wide NAV. [Return cross-check](#ousg-return-cross-check) · [Sources](SOURCES.md#ousg) |
| USDY | Usable note-principal history, outside the NAV gate | The site published 1,165 dated USD/token chart entries on access and documents the continuous oracle method from November 1, 2026 on specified chains. Separately, public Ondo USDY LLC reports show end-of-day reference token principal, including $1.088693 on 2025-05-02, $1.089066 on May 5 and $1.089190 on May 6. Those values are accrued debt principal per token. Reserve values and collateralization measure backing. The reports establish an issuer-published note reference for that entity and period. They do not prove an independent source for the chart's prices or a fund NAV. [Sources](SOURCES.md#usdy) |
| BENJI | Usable filed market-based NAV/share, flat at reported precision | Franklin files FOBXX class C000215714 in Form N-MFP3. The September and October 2026 reports contain exactly 43 business-day rows (21 and 22 respectively), all $1.0000 per share. These are observations of market-based NAV rounded to four decimals. They cannot establish intraday or sub-precision movement. The two reports were accepted October 6 and November 6 respectively. Original valuation publication times remain unknown. [Sources](SOURCES.md#benji) |

## Sample accepted rows

Use `python3 scripts/issuer_history.py` for the 57 pinned issuer fund NAV rows. The count combines 14 USTB date labels, including repeated values carried on different dates, and 43 BENJI business-day observations.

| Observation date | USTB official history, USD/share | BENJI filed market-based NAV, USD/share |
| --- | ---: | ---: |
| 2026-09-29 | 11.22883000 | 1.0000 |
| 2026-09-30 | 11.22990800 | 1.0000 |
| 2026-10-01 | 11.23105300 | 1.0000 |
| 2026-10-02 | 11.23223300 | 1.0000 |
| 2026-10-03 | 11.23223300 | — |
| 2026-10-04 | 11.23223300 | — |
| 2026-10-05 | 11.23554700 | 1.0000 |

The em dash means there is no row in this BENJI filing for that date. The selected USTB and BENJI windows show different weekend date coverage. Source clocks, pricing definitions, share classes, and rounding would have to match a feed before any measured difference could be attributed to it.

## OUSG return cross-check

For the November 23, 2026 statement date (D), the unaudited Ondo I LP account statement shows period net income of $105,379.91 on a beginning balance of $342,831,549.04, with $716,651.64 of additions and $999,978.97 of redemptions. The implied accounting return uses the beginning balance after both flows as its denominator. The corresponding chart comparison uses the November 23 and 24 midnight UTC buckets (D to D+1). [Account statement and chart sources](SOURCES.md#ousg) · [Recorded chart observations](../tests/evidence/manifest.json)

| Series | Calculation in basis points | Result |
| --- | --- | ---: |
| November 23 implied accounting return | 10,000 × 105,379.91 / (342,831,549.04 + 716,651.64 − 999,978.97) | 3.0764 bp |
| OUSG chart, November 23 → 24 UTC | 10,000 × (117.373629 / 117.337532 − 1) | 3.0763 bp |

Accounting returns can check daily chart changes. This pair leaves the chart’s per-unit level, data path and publication timing unresolved. The near match cannot identify which source supplies the chart.
