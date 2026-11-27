"""Reproduce comparisons from Ondo's public chart and dated PDF reports."""
import argparse
import json
import re
import subprocess
import time
from http.client import HTTPException
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from pathlib import Path
from statistics import median

from feed_history import BLOCK, BLOCK_HASH, RPC, json_bytes, rpc_batch, word, words
from fetch_sources import save
from issuer_history import EVIDENCE, USER_AGENT, check, ondo_chart, read_source

ROOT = Path(__file__).resolve().parents[1]
TABLE = "https://app.ondo.finance/legal-documentation/us?month=2026-11"
CHART = "https://ondo.finance/ousg"
USDY_LEGACY = "0xa0219aa5b31e65bc920b5b6dfb8edf0988121de0"
PDF_URL = r"https://cdn\.sanity\.io/files/8k2tqa6n/production/[a-f0-9]+\.pdf"


def statement_links(raw):
    # The server embeds the same report objects as the visible document table.
    rows = re.findall(
        rf'"reportDate":"(2026-11-\d{{2}})"[^{{}}]+?"accountStatementUrl":"({PDF_URL})"',
        raw.decode().replace("\\", ""),
    )
    links = {}
    for day, url in rows:
        if "2026-11-02" <= day <= "2026-11-25":
            check(links.setdefault(day, url) == url, f"conflicting statement links for {day}")
    check(bool(links), "no November 2026 account statements found")
    return dict(sorted(links.items()))


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                          capture_output=True, text=True).stdout


def account_fields(content, day):
    label = date.fromisoformat(day).strftime("%m/%d/%Y")
    for pattern in (r"Ondo I LP", r"Account Statement \(Unaudited\)", r"Reporting Currency\s*:\s*USD",
                    rf"Start Of Period\s*:\s*{label}", rf"End Of Period\s*:\s*{label}"):
        check(re.search(pattern, content), f"statement identity or date mismatch for {day}")
    parts = content.split("Statement of Changes in Net Asset Value", 1)
    check(len(parts) == 2, f"missing account statement section for {day}")
    fields = {}
    for name in ["Beginning Balance", "Additions", "Net Income (Loss)", "Redemptions", "Ending Balance"]:
        match = re.search(rf"^\s*{re.escape(name)}:? +(-|\(?[\d,]+\.\d{{2}}\)?) +", parts[1], re.M)
        check(match, f"missing {name} for {day}")
        raw = match[1].replace(",", "").replace("(", "-").replace(")", "")
        fields[name] = Decimal("0" if raw == "-" else raw)
    return fields


def compare_account(day, fields, chart):
    next_day = date.fromisoformat(day) + timedelta(days=1)
    start, end = (chart[f"{d}T00:00:00Z"] for d in (day, next_day))
    denominator = fields["Beginning Balance"] + fields["Additions"] + fields["Redemptions"]
    income = fields["Net Income (Loss)"]
    check(denominator > 0 and start > 0 and end > 0, f"invalid return denominator or price for {day}")
    reconciliation = denominator + income - fields["Ending Balance"]
    check(abs(reconciliation) <= Decimal("0.01"), f"statement NAV flows do not reconcile for {day}")
    account_bp = income / denominator * 10_000
    chart_bp = (end / start - 1) * 10_000
    return dict(day=day, chart_next_day=str(next_day), statement_usd=fields, denominator_usd=denominator,
                chart_start=start, chart_end=end, account_bp=account_bp, chart_bp=chart_bp,
                reconciliation_usd=reconciliation, absolute_residual_bp=abs(account_bp - chart_bp))


def capture(destination):
    destination.mkdir(parents=True, exist_ok=True)
    receipts = {}

    def fetch(filename, url):
        raw = read_source(url, USER_AGENT)
        save(destination / filename, raw)
        receipts[filename] = dict(url=url, sha256=sha256(raw).hexdigest(),
                                  fetched_at_utc=datetime.now(timezone.utc).isoformat())
        return raw

    index = fetch("index.html", TABLE)
    fetch("chart.html", CHART)
    for day, url in statement_links(index).items():
        fetch(f"ousg-{day}.pdf", url)
        time.sleep(0.25)
    save(destination / "receipts.json", (json.dumps(receipts, indent=2) + "\n").encode())


def replay(destination):
    pin = json.loads((EVIDENCE / "ousg-capture.json").read_bytes())
    reference = pin["receipts"]
    bytes_match = {}
    receipts = json.loads((destination / "receipts.json").read_bytes())
    check(set(receipts) == set(reference), "unexpected OUSG capture files")
    for filename, receipt in receipts.items():
        raw = (destination / filename).read_bytes()
        digest = sha256(raw).hexdigest()
        check(digest == receipt["sha256"], f"local checksum mismatch for {filename}")
        check(receipt["url"] == reference[filename]["url"], f"unexpected URL for {filename}")
        bytes_match[filename] = digest == reference[filename]["sha256"]
        if filename.endswith(".pdf"):
            check(bytes_match[filename], f"reference PDF checksum mismatch for {filename}")
    chart = dict(ondo_chart((destination / "chart.html").read_bytes(), "OUSG"))
    rows = []
    for day in statement_links((destination / "index.html").read_bytes()):
        fields = account_fields(pdf_text(destination / f"ousg-{day}.pdf"), day)
        rows.append(compare_account(day, fields, chart))
    comparable = [(f"{r['day']}", str(r["chart_start"]), str(r["chart_end"])) for r in rows]
    digest = sha256(json.dumps(comparable, separators=(",", ":")).encode()).hexdigest()
    check(digest == pin["chart_pairs_sha256"], "normalized OUSG chart values changed")
    residuals = [r["absolute_residual_bp"] for r in rows]
    return dict(pairs=len(rows), chart_pairs_sha256=digest, bytes_match=bytes_match, rows=rows,
                min_residual_bp=min(residuals), median_residual_bp=median(residuals),
                max_residual_bp=max(residuals),
                within_0_000071_bp=sum(v <= Decimal("0.000071") for v in residuals))


def usdy(destination):
    manifest = json.loads((EVIDENCE / "manifest.json").read_bytes())
    results = []
    for source in manifest["usdy_archive"]["members"]:
        path = destination / source["download"]
        check(sha256(path.read_bytes()).hexdigest() == source["sha256"], f"checksum mismatch: {path.name}")
        text = pdf_text(path)
        day = date.fromisoformat(path.stem.removeprefix("usdy-"))
        report_day = f"{day.month}/{day.day}/{day.year}"
        check("Daily Report Prepared by Ondo USDY LLC" in text and
              re.search(rf"(?m)^Date \(end of day\)[ \t]+{report_day}[ \t]*$", text),
              f"USDY report identity or date mismatch: {path.name}")
        section = re.search(r"(?ms)^C\. Token Balance Outstanding\s+(.+?)^Digital Tokens:", text)
        check(section, f"missing Section C: {path.name}")
        match = re.search(r"(?m)^Reference Token[ \t]+-[ \t]+([0-9]+\.[0-9]{6})[ \t]*$", section[1])
        check(match, f"missing Section C Reference Token principal: {path.name}")
        results.append(dict(file=path.name, report_date=str(day), usd_per_token=match[1]))
    return results


def usdy_oracle(destination, rpc):
    notes = usdy(destination)
    chain_id, block = rpc_batch(rpc, [
        ("eth_chainId", []), ("eth_getBlockByNumber", [hex(BLOCK), False]),
    ])
    check(chain_id == "0x1" and block["hash"] == BLOCK_HASH, "USDY oracle read at wrong block")
    manifest = json.loads((EVIDENCE / "manifest.json").read_bytes())
    archives = {r["download"]: r for r in manifest["usdy_archive"]["members"]}
    rows = []
    for entry in notes:
        source = archives[entry["file"]]
        day_start = datetime.fromisoformat(entry["report_date"]).replace(tzinfo=timezone.utc)
        timestamp = int(day_start.timestamp()) + 86_399
        output, = rpc_batch(rpc, [("eth_call", [
            {"to": USDY_LEGACY, "data": "0xa712c9c7" + word(timestamp)}, hex(BLOCK)
        ])])
        retrospective, = words(output, 1)
        end_block = source["ethereum_end_of_date_block"]
        contemporaneous, following, price_response = rpc_batch(rpc, [
            ("eth_getBlockByNumber", [hex(end_block), False]),
            ("eth_getBlockByNumber", [hex(end_block + 1), False]),
            ("eth_call", [{"to": USDY_LEGACY, "data": "0x98d5fdca"}, hex(end_block)]),
        ])
        check(contemporaneous["hash"] == source["ethereum_end_of_date_hash"] and
              int(contemporaneous["timestamp"], 16) <= timestamp < int(following["timestamp"], 16),
              "USDY report-day block identity or clock mismatch")
        raw, = words(price_response, 1)
        note = Decimal(entry["usd_per_token"])
        price = Decimal(raw).scaleb(-18)
        check(note > 0 and price > 0, "USDY rate and principal must be positive")
        rows.append(dict(**entry, oracle_asof_utc=datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                         report_day_block=end_block, report_day_block_hash=contemporaneous["hash"],
                         oracle_usd_per_token=price, oracle_integer=raw,
                         agrees_with_retrospective_range=raw == retrospective,
                         gap_bp=(price-note)*10_000/note,
                         matches_report_precision=price.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP) == note))
    evidence = dict(chain_id=1, block=BLOCK, block_hash=BLOCK_HASH, oracle=USDY_LEGACY, rows=rows)
    digest = sha256(json_bytes(evidence)).hexdigest()
    check(digest == manifest["usdy_archive"]["oracle_capture"]["evidence_sha256"],
          "USDY pinned comparison checksum mismatch")
    return dict(source_url=rpc, fetched_at_utc=datetime.now(timezone.utc).isoformat(),
                evidence_sha256=digest, **evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["capture", "replay", "usdy", "usdy-oracle"])
    parser.add_argument("--data", type=Path)
    parser.add_argument("--rpc", default=RPC, help="keyless archive Ethereum RPC for usdy-oracle")
    args = parser.parse_args()
    try:
        if args.mode == "usdy":
            print(json.dumps(usdy(args.data or ROOT / "data" / "sources"), indent=2))
        elif args.mode == "usdy-oracle":
            print(json_bytes(usdy_oracle(args.data or ROOT / "data" / "sources", args.rpc)).decode(), end="")
        else:
            destination = args.data or ROOT / "data" / "ousg"
            if args.mode == "capture":
                capture(destination)
            else:
                print(json.dumps(replay(destination), indent=2, default=str))
    except (OSError, ValueError, KeyError, HTTPException, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"report checks: {exc}\n")


if __name__ == "__main__":
    main()
