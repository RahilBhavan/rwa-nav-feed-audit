# Round 1 implementation handoff

The pinned USTB comparison supersedes the first availability-only handoff. Start with [Results](docs/RESULTS.md), then read [Method](docs/METHOD.md) and [source receipts](docs/SOURCES.md#download-and-capture-hashes).

- Re-run the chart byte check and pinned history using the commands in [README](README.md). Recheck the switch blocks when verifying the difference between stored and active rounds.
- Recalculate largest daily and holiday gaps with the issuer label as denominator. Keep the 430-round window, the 288-value issuer cohort and the complete historical cohort distinct.
- Use the public SEC filing indices to confirm the acceptance timestamps. Live XML and index verification with genuine organizational identification is a maintainer follow-up. The generic probe returned HTTP 403.
- Review the exact [SVG](docs/ustb-gap.svg) and [text drafts](posts/DRAFTS.md) and their [preflight receipt](posts/post-review.json) independently before using the media or drafts externally. The render was inspected at 680 px and 342 px, the visible text stays within 20 words, and ink-to-paper contrast is 13.20:1. The figure has SHA-256 `b06cb56011bbf1c77e2ae39a69250790fef9677e0b55447744c0a6cdf2f23f86`.

The maintainer owns commits, push and any release. The original Round 1 rubric remains in its historical files.

Verification passed on Python 3.10 and 3.14 with 21 tests on each. A separate clean dRPC capture reproduced both pinned chain digests, the issuer-label digest, all reported USTB metrics and the exact chart. OUSG replay verified all 14 PDF digests and USDY replay verified all four reports and pinned oracle comparisons. All four draft bodies passed preflight.

[Public repository](https://github.com/RahilBhavan/rwa-nav-feed-audit)
