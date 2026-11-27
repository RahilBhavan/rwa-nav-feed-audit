# Final handoff — three quality rounds complete

**Final independent score: 8/10.** The three rounds scored 3, 5 and 8. Round 3 reviewed commit `75fe51c` and reproduced the headline from raw inputs. GPT-6.2 Sol built the research code and Claude Opus 5.5 reviewed it. The three-round limit ends this loop. Reproducibility scored 10. Answer, usefulness and post kit scored 8.

The remaining research work is to extend the seven-value Chronicle sample, independently verify event completeness and show how delivery varied by year. Other open items include clearer chart labels, draft wording and targeted failure-path tests. The detailed [quality record](QUALITY.json) names an owner and fix for each gap.

Rahil approved the public GitHub repository and MIT code license. Pending decisions are chart and draft approval, whether to post, optional live EDGAR identification, and whether to authorize a bounded observation of issuer publication timing.

[Results](docs/RESULTS.md) · [Method and reproduction commands](docs/METHOD.md#replay-and-verification) · [Source receipts](docs/SOURCES.md#download-and-capture-hashes) · [Final review](docs/QUALITY.md)

- Reproduced **582 of 593** literal next-NYSE-session dates and **584** posts after exactly one session elapsed. Against the next issuer value-change date, the frozen labels support **588 of 593** matches on that date, four one day after and one unknown. November 24’s matched value posted on November 25. The pinned issuer series stops at November 24, so it cannot classify that post against a later issuer change. Eight values were unseen through the block.
- The original financials snapshot is pinned as of **2026-11-27 04:00:54 UTC**. A fresh public capture at **04:46:21–04:46:32 UTC** reproduced the normalized issuer hash and both chain hashes despite different live financials bytes. The fresh snapshot still reported November 24. A regression test advances the live official date and revises the provisional tail, preserving replay output and the unknown classification.
- The Chronicle sample captured **2026-11-27 04:52:47–04:52:51 UTC** included 25 verified events. Both feeds matched seven issuer values. All six values with finalized successors posted on the next issuer change date on both feeds. Chronicle was earlier on six pairs and later on one. The comparison is bounded to the sample and uses onchain visibility time.
- A separate raw-input calculation checked the timing counts, unmatched labels, daily minimum, month-end counts, interval maximum, heartbeat count and all seven paired time differences. All 25 tests passed on Python 3.14.8 and 3.10.21. OUSG replay verified all 14 PDF comparisons. USDY replay checked all four reports against the pinned oracle. Both live USTB windows matched. Live EDGAR was skipped because no authorized organization identity was configured.
- The [SVG](docs/ustb-gap.svg) has SHA-256 `4e7a2a20f5d904d9b0976a76db3724f6444424613a60892f448d454235b97452`. The byte check passed. Inspection at 342 and 680 px used Archivo and IBM Plex Sans. The chart contains 18 visible words and has 13.20:1 ink-to-paper contrast. All four [draft bodies](posts/DRAFTS.md) passed preflight, with their anchors and exact bytes recorded in the [post receipt](posts/post-review.json). The final independent review checked the figures and drafts. Rahil retains design and posting approval.

After 2026-11-30, rerun the clean-clone capture, replay and chart byte check when the issuer has finalized its next NAVs. This is the time-owned external check. The current study leaves issuer publication time unknown.

[Public repository](https://github.com/RahilBhavan/rwa-nav-feed-audit)
