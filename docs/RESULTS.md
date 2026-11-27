# NAV feed audit results

Chainlink’s Ethereum USTB feed first posted **588 of 593 matched changes on the next issuer value-change date**. Four posted one calendar day after that date. The last posted value has no following change in the finalized issuer series, so its timing against this proxy is unknown. Eight of 601 issuer values were unseen on the active proxy through the pinned block. The issuer value-change date is a proxy for the valuation schedule. The data give neither the actual strike nor the publication time. [Inputs and clocks](METHOD.md#join-clocks-and-denominators) · [Source register](SOURCES.md#ustb)

![Timeline of Chainlink’s Ethereum delivery for 601 Superstate USTB value changes. 588 posted on the next issuer value-change date, four posted a day after, eight were unseen at the pin, and one has unknown timing.](ustb-gap.svg)

## Full history and coverage

The Ethereum pin is block **26,503,879**, November 27, 2026 at 03:33:11 UTC. Chainlink round counts extend through November 26 UTC. The last date available in Superstate’s official NAV field at the original capture was **November 24**, so label and daily measures stop there. Chainlink’s directory attributes its feed to the **Asset Manager API** and lists **Superstate** as auditor. Exact agreement measures delivery of a shared source.

| Check | Full history from Jun 27, 2024 | Review window from Sep 27, 2025 |
| --- | ---: | ---: |
| Active observations matching any issuer value exactly | 889 / 889 | 430 / 430 |
| Distinct issuer values observed by the pin | 593 / 601 | 289 / 289 |
| In-scope UTC dates with daily comparisons | 881 | 424 |
| Matched changed rounds | 593 | 289 |
| Posted on the next issuer value-change date | 588 | 287 |
| No following finalized issuer change for the matched round | 1 | 1 |
| Posted on the literal next NYSE session date | 582 | 284 |
| Exactly one NYSE session elapsed through posting date | 584 | 284 |
| Exactly two NYSE sessions elapsed | 8 | 5 |
| Zero NYSE sessions elapsed | 1 | 0 |

The digest covers 1,057 consecutive API date labels from January 3, 2024 through November 24, 2026. Later dates returned $11.291441 as a forward fill, including November 28 in a November 27 request. The narrower issuer cohort from September 29, 2025 contains 288 distinct values on 422 labels, all observed by the pin. The review round window starts on September 27 and includes the September 25 carry and the change from the September 26 label first posted September 29. That last change is included in review round timing and outside the review label-start cohort.

At the pin, contiguous lookup yielded 46 phase 1 and 874 phase 2 rounds. The crossover left 40 phase 1 and 849 phase 2 rounds active. All 920 stored rounds match an issuer value, including 31 inactive rounds excluded from the delivery figures. The eight unseen values were first labelled July 26, August 7, August 16, August 28, September 30, October 15 and December 4 in 2024, and August 13 in 2025. Each had a following issuer change and chain follow-up beyond that date. The cause of each omission and any delivery after the pin are unknown. [Proxy reconstruction](METHOD.md#study-pair-and-cutoff)

## Update timing and intervals

| Measure | Full history | Review round window |
| --- | ---: | ---: |
| Median hours since 00:00 UTC of the matched label, changed rounds | 37.33 h | 37.81 h |
| 90th percentile, changed rounds | 85.26 h | 85.70 h |
| Maximum, changed rounds | 110.18 h | 110.18 h |
| Median New York local time, changed rounds | 09:09:47 ET | 09:10:47 ET |
| Same-phase intervals with both endpoints inside the window | 887 | 429 |
| Median interval | 86,412 s | 86,412 s |
| Intervals over the published 95,400 s heartbeat | 283 | 132 |
| Longest observed interval | 95,484 s | 95,484 s |
| Median / 90th percentile absolute gap to previous UTC label at in-scope rounds | 0 / 1.19 bp | 0 / 1.01 bp |

These four changes posted one calendar day after the next issuer value-change date. Both Saturday posts occurred after one NYSE session had elapsed and both fail the literal next-session-date test.

| Issuer label | Next issuer change | Posting time in New York |
| --- | --- | --- |
| 2024-08-01 | Aug 2 | Sat Aug 3, 09:09:23 EDT |
| 2024-08-27 | Aug 28 | Thu Aug 29, 09:09:47 EDT |
| 2024-10-31 | Nov 1 | Sat Nov 2, 09:09:35 EDT |
| 2026-10-30 | Nov 2 | Tue Nov 3, 07:10:23 EST |

Six further NYSE-date exceptions posted on the next issuer **value-change** date. Superstate labels carry the prior value across Columbus Day (Oct 14, 2024, Oct 13, 2025 and Oct 12, 2026) and Veterans Day (Nov 11 in each year). SIFMA recommends full bond-market closures on those days. NYSE counts each as a session. Equal labels alone leave open whether the fund struck an unchanged NAV. Conversely, the Jan 8, 2025 value posted the next issuer value-change date, Jan 9 at 09:08:47 EST, when NYSE had a special closure and SIFMA recommended an early close. November 24, 2026’s value posted November 25 at 09:13:47 EST. It meets the NYSE test and is unclassified on the issuer proxy. [Business-day references](SOURCES.md#business-day-references)

The longest date-to-chain case was the Friday, February 13, 2026 label. It posted Tuesday, February 17 at 14:10:47 UTC (09:10:47 EST) after the Monday NYSE holiday. The review window contained 51 Monday posts out of 58 Friday-labelled changes. Its 122 weekend rounds all repeated the previous answer. The 121 in-window intervals ending on weekend rounds range from 95,400 to 95,472 seconds. The full-history interval maximum of 95,484 seconds occurred twice, ending March 15, 2025 at 15:40:11 UTC and October 13, 2025 at 20:42:23 UTC. The 84-second difference from the captured directory heartbeat gives no evidence of a particular trigger or service breach. New York conversions use daylight saving time, including 13:15:35 UTC → 09:15:35 EDT in October and 12:10:23 UTC → 07:10:23 EST in November. [Timing definitions](METHOD.md#join-clocks-and-denominators)

## Daily gaps

This comparison pairs the feed at **23:59:59 UTC** with the same-date issuer label from the later capture. Given the observed forward fills, that final labelled value may still have been unpublished at the sampling instant. These gaps measure retrospective differences to dated values. The data cannot establish stale prices against a contemporaneously available issuer NAV.

| Case | USD/share onchain | USD/share issuer label | Signed gap |
| --- | ---: | ---: | ---: |
| Jul 29, 2024, largest full-history UTC-close gap | 10.290755 | 10.296792 | −5.8630 bp |
| Aug 31–Sep 2, 2024, Labor Day weekend and holiday | 10.343571 | 10.349578 | −5.8041 bp |
| Oct 14, 2025, largest UTC-close gap in the review window | 10.852878 | 10.857540 | −4.2938 bp |
| Nov 11, 2025, Veterans Day | 10.884770 | 10.888154 | −3.1080 bp |
| Oct 3–4, 2026, weekend example | 11.231053 | 11.232233 | −1.0505 bp |

Each row is `10,000 × (onchain − issuer) / issuer`. On July 29, the feed held July 25’s $10.290755. July 26’s $10.295283 was one of the eight unseen values. The July 29 label exceeds the feed by $0.006037, comprising $0.004528 from July 25 to 26 and $0.001509 from July 26 to 29. This arithmetic establishes the role of the missing intermediate value in the comparison. Labor Day was the largest UTC-close holiday gap under both the federal and NYSE definitions.

On Veterans Day 2025, the 16:40:47 UTC update retained the November 7 NAV. The November 11 issuer label carried the November 10 NAV. That NAV first posted November 12 at 14:10:35 UTC (09:10:35 EST), on the next issuer value-change date. November 11 also had the review window’s largest absolute gap to the previous UTC label at a round. On October 3–4, 2026 the feed held Thursday’s value and the issuer series carried Friday’s. Friday’s NAV posted Monday, October 5 at 13:15:35 UTC (09:15:35 EDT), on the next issuer value-change date. The largest weekend UTC-close gap in the review window was −1.9839 bp, first observed November 29, 2025. [Weekend and holiday inputs](SOURCES.md#ustb)

## Month-end

Of 29 completed NYSE month-ends in scope, 28 had an observed value from a spell that began on the month-end label. **26 of those 28** posted on the literal next NYSE session date. Exactly one session elapsed before 27 of the 28, including the Thursday October 31, 2024 value that posted Saturday. The September 30, 2024 value was unseen through the pin. The October 30, 2026 value posted after two sessions. In the later window, the **September 30, 2026 $11.229908 NAV posted October 1 at 13:17:35 UTC** (09:17:35 EDT), 37.29 hours from 00:00 UTC of its label. [Month-end method](METHOD.md#join-clocks-and-denominators)

## Chronicle comparison

Chronicle’s Ethereum USTB consumer and Chainlink’s Ethereum proxy both matched **all seven** finalized Superstate values first labelled November 16–24, 2026. Both posted on the next issuer value-change date in **six of six classifiable cases**. November 24’s value appeared on both on November 25, with no finalized successor to classify the posting date. No sampled value was unseen through the common pin on either feed.

| Issuer label | Next issuer change | Chainlink first post (EST) | Chronicle first post (EST) | Chronicle minus Chainlink |
| --- | --- | --- | --- | ---: |
| Nov 16 | Nov 17 | 09:14:35 | 09:34:11 | +19m 36s |
| Nov 17 | Nov 18 | 09:16:59 | 09:06:47 | −10m 12s |
| Nov 18 | Nov 19 | 09:13:23 | 08:41:11 | −32m 12s |
| Nov 19 | Nov 20 | 09:17:35 | 08:20:23 | −57m 12s |
| Nov 20 | Nov 23 | 09:14:59 | 06:59:47 | −2h 15m 12s |
| Nov 23 | Nov 24 | 09:12:47 | 06:34:23 | −2h 38m 24s |
| Nov 24 | Unknown | Nov 25 09:13:47 | Nov 25 06:08:47 | −3h 05m |

Chronicle was earlier in six pairs and later in one. The table compares onchain posting times for exact matches, with both feeds observed through the same block. This sample provides no general ranking or publication-to-chain latency estimate. [Cross-check method](METHOD.md#chronicle-comparison) · [Chronicle receipts](../tests/evidence/chronicle-capture.json)

## Other products

| Product | Comparable evidence and limit |
| --- | --- |
| BUIDL | BNY documents class-specific NAV onchain, and launch materials state a $1 target. The reviewed offchain materials did not contain dated valuations for a matching share class. [Sources](SOURCES.md#buidl) |
| USTB | Public dated NAV/share and a matched Ethereum primary feed. The Chronicle sample covers a shorter shared window. Other wrappers, providers and networks are outside the measured scope. [Full history](#full-history-and-coverage) · [Chronicle comparison](#chronicle-comparison) |
| USYC | The API indexes its own onchain price reports. A comparison against its parent feed would reuse the same reports. [Sources](SOURCES.md#usyc) |
| OUSG | Administrator statements support a return check. The checked fund-wide accounts do not expose a corresponding per-token denominator. [Return cross-check](#ousg-return-cross-check) |
| USDY | Ondo USDY LLC reports publish accrued USD/token note principal. The old USDY oracle can be evaluated retrospectively at matched timestamps, subject to the range and clock limits below. [Note principal](#usdy-note-principal) |
| BENJI | Franklin files daily FOBXX market-based NAV per share. No matched BENJI Ethereum Chainlink feed was identified in the checked directory. [Filing availability](#benji-filing-availability) |

The initial dated issuer fund NAV screen admitted USTB and BENJI, **2 of 6**. Including USDY LLC’s distinct accrued principal benchmark gives **3 of 6** dated per-unit references. Offline issuer replay derives these selections from the evidence properties. Live mode reports complete fetched row counts and their date bounds. [Source eligibility](METHOD.md#other-product-references)

### BENJI filing availability

Franklin’s September and October 2026 Form N-MFP3 Item B.6 includes 21 and 22 daily close observations, respectively, all at **$1.0000** per share at reporting precision. The September filing was accepted October 6 at **15:46:56 EDT** and the October filing November 6 at **11:20:09 EST**. Both were accepted six calendar dates after report month-end. October’s acceptance was seven calendar dates after the last valuation label, October 30. These are SEC acceptance offsets, so an earlier public availability time for the valuations remains unknown. A generic-client probe of the September index and XML returned HTTP 403. The acceptance times were separately checked on the publicly rendered index pages. [Filing indices and XML](SOURCES.md#benji)

### OUSG return cross-check

The November document table yielded 14 one-day Ondo I LP account statements through November 25, with dates from November 6 to 25. No earlier November statement appeared in the table snapshot. The minimum, median and maximum absolute residual between derived accounting and chart returns were **0.00000720**, **0.00002232** and **0.01428620 bp**. Thirteen of 14 were within **0.000071 bp**. On November 24, the accounting return was 0.86268802 bp and the chart return 0.84840182 bp. That deviation and the absence of unit-level administrator values leave the chart’s exact lineage open.

For example, on November 23 the formula uses `10,000 × 105,379.91 / (342,831,549.04 + 716,651.64 − 999,978.97)`, giving **3.07635256 bp**. The chart’s November 23 and 24 midnight UTC buckets give `10,000 × (117.373629 / 117.337532 − 1)`, or **3.07633878 bp**. The downloadable evidence receipt lists each statement’s public URL, UTC fetch time and SHA-256. The replay computes every residual directly from the PDFs. [Paired return method](METHOD.md#other-product-references) · [Capture receipt](../tests/evidence/ousg-capture.json)

### USDY note principal

The table compares four May 2025 Ondo USDY LLC **Section C Reference Token** principal figures with the legacy Dynamic Rate Oracle’s `getPrice()` at each report date’s last Ethereum block at or before 23:59:59 UTC. The later retrospective `getPriceHistorical()` computation at study block 26,503,879 returns identical integers for all four dates. The oracle matches all four reports at six-decimal precision, with a largest absolute unrounded difference of **0.00340 bp** relative to the note principal. The report’s end-of-day timezone and publication time remain unknown. [Addresses, reports and contract source](SOURCES.md#usdy)

| Report date | Ethereum block | Report USD/token | Legacy oracle USD/token |
| --- | ---: | ---: | ---: |
| May 2, 2025 | 22,399,543 | 1.088693 | 1.08869325 |
| May 5, 2025 | 22,420,967 | 1.089066 | 1.08906575 |
| May 6, 2025 | 22,428,091 | 1.089190 | 1.08918995 |
| May 9, 2025 | 22,449,297 | 1.089563 | 1.08956263 |

The oracle integers use 18 decimals. To recover the signed difference use `10,000 × (oracle − note) / note`, then compare the oracle rounded to six decimals with the report. These are same-issuer pricing checks against accrued note principal.
