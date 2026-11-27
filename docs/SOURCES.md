# Source register

Accessed 2026-11-26 unless a source's reporting or filing date is given separately. A primary oracle-vendor source establishes what the vendor documents about its own feed. It does not establish independent fund NAV.

## BUIDL

- **Primary, transfer agent and fund announcement.** [Securitize product listing](https://securitize.io/blackrock/buidl) and [joint launch release, 2024-03-20](https://investors.securitize.io/news/news-details/2024/BlackRock-Launches-Its-First-Tokenized-Fund-BUIDL-on-the-Ethereum-Network-03-20-2024/default.aspx) distinguish the manager, BNY administrator and Securitize role and establish the USD 1 target and dividend mechanic. [Solana announcement, 2025-03-25](https://investors.securitize.io/news/news-details/2025/BlackRock-and-Securitize-Debut-New-BUIDL-Share-Class-on-Solana-Network-03-25-2025/default.aspx) identifies a separate share class.
- **Manager page lead.** The [BlackRock product URL](https://www.blackrock.com/us/individual/products/buidl/) returned HTTP 403 when fetched directly. The accessible [BlackRock submission to the SEC](https://www.sec.gov/files/ctf-memo-blackrock-05092025.pdf) identifies the product and does not provide a per-class NAV history.
- **Primary, issuer-filed.** [Form D, filed 2024-03-18](https://www.sec.gov/Archives/edgar/data/2013810/0002014390-24-000001-index.htm) and [Form D/A, signed 2025-07-17](https://www.sec.gov/Archives/edgar/data/2013810/000200468725000001/xslFormDX01/primary_doc.xml) identify BlackRock USD Institutional Digital Liquidity Fund Ltd. and its exempt offering.
- **Primary for the reporting company.** [Securitize Markets 2025 public financial statements](https://www.sec.gov/Archives/edgar/data/1668629/000166862926000003/securitizepublicaudit.pdf) describe the broker-dealer's holdings and $1/share redemption NAV. Treat the statement as a point disclosure from a fund holder and affiliate of the transfer agent.
- **Primary, fund administrator.** [BNY Data On-Chain guide, §§3.1–3.4](https://github.com/BNYMellon/bny-data-on-chain#3-sourcing-data-for-the-blackrock-usd-digital-liquidity-buidl-fund) gives share class keys, valuation date, reported NAV field and business-day cadence. Its offchain consumer example reads the same chain contract. No offchain historical download is identified there.

## USTB

- **Primary, fund page and API documentation.** The [Superstate fund page](https://superstate.com/assets/ustb) offers a historical data view/download and lists Invesco Advisers, Inc. as investment manager, Superstate Services LLC as transfer agent, and NAV Fund Services as NAV calculation agent. [Symbol metadata](https://api.superstate.com/v3/funds/USTB) binds USTB and CUSIP 86851T204 to the fund that issues tokenized and book-entry interests. [OpenAPI](https://api.superstate.com/api-docs/openapi.json) defines public history and filters and maps numeric fund ID 1 to USTB. The older [Superstate .co Swagger lead](https://api.superstate.co/swagger-ui/) also resolves to a Swagger page. Replay uses the verified .com endpoints.
- **Primary, machine-readable NAV history published by Superstate.** [Unfiltered NAV history](https://api.superstate.com/v1/funds/1/nav-daily) supports the reported 1,059-row discovery. [Month-end window](https://api.superstate.com/v1/funds/1/nav-daily?start_date=2026-09-29&end_date=2026-10-05) and [November window](https://api.superstate.com/v1/funds/1/nav-daily?start_date=2026-11-20&end_date=2026-11-26) provide the windows used in the replay.
- **Primary, current cross-check.** [Fund dashboard data](https://api.superstate.com/v2/funds/1/data) links the daily history's scale to `nav_per_share`. [Fund financials](https://api.superstate.com/v3/funds/USTB/financials) specifies USD as base currency and distinguishes official NAV date from indicative price time. [Current price API](https://api.superstate.com/v1/price/USTB) is a point price.

## USYC

- **Primary, token administrator and portal.** [Circle USYC product page](https://www.circle.com/usyc) identifies the Cayman fund and Circle International Bermuda's role. [Hashnote product structuring](https://usyc.docs.hashnote.com/overview/product-structuring) maps the token to fund shares. [Token Price documentation](https://usyc.docs.hashnote.com/overview/token-price) gives the NAV-to-supply price formula and explicitly identifies the [price reports endpoint](https://usyc.hashnote.com/api/price-reports) as an onchain series in JSON.
- **Primary, fund sponsor materials.** [Hashnote's STEP application](https://forum.arbitrum.foundation/t/hashnote-usyc-step-application/23587) describes administrator statements sent to investors. [Circle's 2025 annual report](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000116/a2025annualreport0331.pdf) gives summarized fund financials, without a daily USYC per-share history.

## OUSG

- **Primary, issuer website.** [Ondo OUSG page](https://ondo.finance/ousg) contains the embedded USD/token chart history and identifies the Ondo I LP product. Its portfolio section scopes the reported asset value to tokenized interests. [Issuer explanation of OUSG vs rOUSG](https://ondo.finance/blog/introducing-instant-24-7-365-subscriptions-and-redemptions-shifting-ousg-funds-into-blackrocks-b) distinguishes appreciating OUSG from rebasing rOUSG. [Yield documentation](https://docs.ondo.finance/qualified-access-products/ousg/yield) describes the manual business-day oracle update.
- **Primary, issuer and administrator.** [Trust & Transparency](https://docs.ondo.finance/qualified-access-products/ousg/trust-and-transparency) describes daily valuation and reconciliation with NAV Consulting and says the financial reports may lag the oracle by up to three days. An older archive link required sign-in. The [public November 2026 document table](https://app.ondo.finance/legal-documentation/us?month=2026-11) provides unaudited administrator-prepared PDFs by report date.
- **Primary, administrator PDFs hosted via Ondo's app.** November 23 [balance sheet](https://cdn.sanity.io/files/8k2tqa6n/production/7af65a83c8bd587422b52bbeaa0b0f6ab43ac26e.pdf) and [account statement](https://cdn.sanity.io/files/8k2tqa6n/production/bc2bd74231d48e1f89307293cc20364f622aed00.pdf). November 24 [balance sheet](https://cdn.sanity.io/files/8k2tqa6n/production/974f81e80c2ebae91cd8a8e32251b26f10bf8205.pdf), [account statement](https://cdn.sanity.io/files/8k2tqa6n/production/316ce1a9116ac54b223b734013878cf2f92b8c0c.pdf), and [trial balance](https://cdn.sanity.io/files/8k2tqa6n/production/56fa579d2ce9d79b5584613fb6e8e8ea5ca4161c.pdf). These are aggregate financials. The results record the November 23 account statement figures used in the return check.
- **Secondary discovery only.** [Philidor's Ondo dashboard](https://analytics.philidor.io/por/ondo) shows a sourced point estimate. [Pharos's OUSG write-up](https://pharos.watch/stablecoin/ousg-ondo-finance/) leads to the older Drive folder. Neither establishes a usable independent history. [CoinGecko OUSG](https://www.coingecko.com/en/coins/ousg) is secondary pricing.

## USDY

- **Primary, issuer website and docs.** [USDY product page](https://ondo.finance/usdy) contains embedded price chart history and describes a debt structure. [USDY Basics](https://docs.ondo.finance/general-access-products/usdy/basics) distinguishes accumulating USDY, rebasing rUSDY and current subscription terms. [USDY Price Oracle](https://docs.ondo.finance/general-access-products/usdy/usdy-price-oracle) specifies the November 1, 2026 change for Ethereum, BSC, Mantle and Tempo and the oracle formula.
- **Primary, issuer reports with verification agent text.** [USDY app's Tokenholder Protections section](https://app.ondo.finance/assets/usdy) distinguishes LLC and BVI report archives. The Ondo USDY LLC daily archive supplied the May 2025 reports listed below. Section C has end-of-day Token Principal on the Reference Token and Digital Tokens Outstanding rows. Ankura's verification statement in Section B covers the permitted assets. It does not attest to offchain price lineage. The reported sample is confined to the LLC daily archive.
- **Secondary discovery only.** [BSSC's USDY evaluation](https://specs.blockchainssc.org/tis/examples/evaluations-v2/TISv2-USDY.html) mentions issuer price history and multiplier data. The issuer HTML confirmed chart history. Neither that lead nor [CoinGecko market history](https://www.coingecko.com/en/coins/ondo-us-dollar-yield/historical_data) establishes independently valued NAV for USDY.

## BENJI

- **Primary, issuer.** [Franklin's FOBXX product page](https://www.franklintempleton.com/investments/options/money-market-funds/products/29386/SINGLCLASS/franklin-on-chain-u-s-government-money-fund), [Benji product explainer](https://digitalassets.franklintempleton.com/benji/) and [prospectus](https://www.sec.gov/Archives/edgar/data/1786958/000165558926000970/c485bpos.htm) identify the share/token mapping and distinguish market-based NAV from dealing NAV. The issuer factsheet's [monthly history table](https://www.franklintempleton.com/forms-literature/download/29386-FF) is yield history.
- **Primary, issuer-filed September history.** [EDGAR filing index](https://www.sec.gov/Archives/edgar/data/1786958/000207169126023634/0002071691-26-023634-index.htm) binds ticker FOBXX to series S000067043 and class C000215714 and gives the October 6 acceptance time. The [XML](https://www.sec.gov/Archives/edgar/data/1786958/000207169126023634/primary_doc.xml) provides machine-readable class rows. [Rendered Item B.6](https://www.sec.gov/Archives/edgar/data/1786958/000207169126023634/xslN-MFP3_X01/primary_doc.xml) defines business-day close, valuation basis and reporting precision.
- **Primary, issuer-filed October history.** [EDGAR filing index](https://www.sec.gov/Archives/edgar/data/1786958/000207169126025490/0002071691-26-025490-index.htm), [XML](https://www.sec.gov/Archives/edgar/data/1786958/000207169126025490/primary_doc.xml) and [rendered filing](https://www.sec.gov/Archives/edgar/data/1786958/000207169126025490/xslN-MFP3_X01/primary_doc.xml) establish the second month and November 6 acceptance.
- **Primary, SEC access policy.** [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) documents fair access and asks automated callers to declare their User-Agent.

## Research plan leads

- **Primary for providers.** [Chainlink SmartData feed registry](https://docs.chain.link/data-feeds/smartdata/addresses) documents USTB NAV/share and lists fund-manager API provenance. [RedStone's methodology](https://blog.redstone.finance/2026/04/23/nav-onchain-how-tokenized-fund-pricing-works-and-why-oracle-design-matters/) describes Securitize's BUIDL integration and single-source oracle design. [Chronicle Proof of Asset docs](https://docs.chroniclelabs.org/Products/proofOfAsset/) identify USTB share price reporting and BUIDL proof-of-asset integrations. These sources substantiate the plan's feed leads and do not supply independent issuer NAV histories. No feed was polled.
- **Primary for prior art.** [NavBridge README](https://github.com/vishnugovind10/navbridge/blob/b1239a110c65d36b0b46848fb3d9295afcf7d19e/README.md) and [MIT license](https://github.com/vishnugovind10/navbridge/blob/b1239a110c65d36b0b46848fb3d9295afcf7d19e/LICENSE) at the checked revision. It accepts mapped administrator CSV/JSON and ships simulated oracle data. The evidence here is a live-source feasibility check across six named products.

## Download and capture hashes

Run `python3 scripts/fetch_sources.py` to retrieve the five current non-SEC series responses and the three cited OUSG PDFs under ignored `data/sources/`. The receipt records the current UTC access date, SHA-256 and whether the saved bytes match the reference. A changed hash means the response bytes differ. A later page can still contain the same selected observations. The November 26 digests document the original series captures. The three OUSG PDF digests are from the November 27 retrieval.

| Source | Access date (UTC) | Reference response SHA-256 |
| --- | --- | --- |
| [USTB, 2026-09-29 to 2026-10-05](https://api.superstate.com/v1/funds/1/nav-daily?start_date=2026-09-29&end_date=2026-10-05) | 2026-11-26 | `a7029446ef8bdbe54c4964a2b4419eee2edcdb00d6718f0c078561858cdb51a3` |
| [USTB, 2026-11-20 to 2026-11-26](https://api.superstate.com/v1/funds/1/nav-daily?start_date=2026-11-20&end_date=2026-11-26) | 2026-11-26 | `c72e9d66cc8fdb1c0c7c1f2f529c67755fba66cc1939be941170a97aff178a5b` |
| [USYC, 2026-11-23 to 2026-11-25](https://usyc.hashnote.com/api/price-reports) | 2026-11-26 | `6c4a74d893878e1da5c6961e73748cdf8d21822362e48cc32bae74f7887f7add` |
| [OUSG, 2026-11-20 to 2026-11-26](https://ondo.finance/ousg) | 2026-11-26 | `0021874ff01f797790039c15681dcd434906b90abe8a0d9f7a8227027dec9c32` |
| [USDY, 2026-11-20 to 2026-11-26](https://ondo.finance/usdy) | 2026-11-26 | `6f2984c64bb82b0abc71f496c39ef3f7471786c705f5a60992da9cbc3ebfb317` |
| [BENJI, 2026-09-01 to 2026-09-30](https://www.sec.gov/Archives/edgar/data/1786958/000207169126023634/primary_doc.xml) | 2026-11-26 | `ab64fc4b57d95efbfcc476cff6b6111fc522ab96d1edbb27fb5cc00f0d5610ca` |
| [BENJI, 2026-10-01 to 2026-10-31](https://www.sec.gov/Archives/edgar/data/1786958/000207169126025490/primary_doc.xml) | 2026-11-26 | `04ee3848c6b56270a4efe60b1045e02bd62663216a70e69cccf7880e906b025e` |
| [ousg-2026-11-23-balance.pdf](https://cdn.sanity.io/files/8k2tqa6n/production/7af65a83c8bd587422b52bbeaa0b0f6ab43ac26e.pdf) | 2026-11-27 | `7ad1007a8ddbe7a0c5a4daa9f8dbc0c3f57f0b6bcb5406ece9fa7ba8a5809405` |
| [ousg-2026-11-23-account.pdf](https://cdn.sanity.io/files/8k2tqa6n/production/bc2bd74231d48e1f89307293cc20364f622aed00.pdf) | 2026-11-27 | `d9504b5b008c9455a7f4afd18dd964b5fc8fac30aa11b0565772a2b0a63cba69` |
| [ousg-2026-11-24-balance.pdf](https://cdn.sanity.io/files/8k2tqa6n/production/974f81e80c2ebae91cd8a8e32251b26f10bf8205.pdf) | 2026-11-27 | `a9732cd5f53f020d143540e7c1cb0f5bc9b75faf4be9aebf73e4bacbe99a7638` |

The SEC excerpts retained in the repository have separate hashes in the [evidence manifest](../tests/evidence/manifest.json). The historical non-SEC excerpt digests are recorded there as `historical_capture_sha256`. The removed composite text extract had SHA-256 `6cdf2a204915e93e1fc4e791e15004d60cd0437939e504bbed4e318320a57397`. It summarized the OUSG balance sheets and account statement, the USDY LLC reports below and the linked BUIDL launch and USYC API pages. The replay uses the recorded factual observations in the manifest. Third-party source bytes remain subject to their respective rights and terms of use.

### USDY LLC daily report archive

Open Tokenholder Protections and choose **Daily Attestation Reports – Ondo USDY LLC**. The May 2025 members below are under `2025/05 May/`. The study first checked these reports on November 26, 2026 UTC and independently hashed each recovered PDF on November 27, 2026 UTC. [Issuer report links](https://app.ondo.finance/assets/usdy) · [Issuer product page](https://ondo.finance/usdy)

| Archive member in `2025/05 May/` | PDF SHA-256 |
| --- | --- |
| `Ondo USDY LLC_ATCAttest_250502.pdf` | `1a43225da85de51396378f578bf7f4a9b1ee6d51dd8faa798fe00e7ca34c3cfb` |
| `Ondo USDY LLC_ATCAttest_250505.pdf` | `a3a4e9d9a467d65d47ea5678d13f354e2e4aade1f3b9af3320bf1f165ee5ee42` |
| `Ondo USDY LLC_ATCAttest_250506.pdf` | `5e33309517b4f36de773c9c7223128f03f8617e927b181fd55b66d751fbcee1a` |
| `Ondo USDY LLC_ATCAttest_250509.pdf` | `38c527c94493322fb9f510ce03383b03192a3b2ec9bf91e72cc814e5b58becdf` |

If you download the archive ZIP from the issuer, save it as `data/usdy-llc-daily.zip` and run the command below. It extracts only the four listed members into ignored `data/sources/` and records their hashes alongside the direct downloads. The full archive was approximately 277 MB when first checked. The four PDFs can also be downloaded individually through the issuer's archive.

```sh
python3 scripts/fetch_sources.py --usdy-archive data/usdy-llc-daily.zip
```
