"""Replay the offchain NAV availability gate from recorded observations and SEC filings."""
import argparse
import hashlib
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen

EVIDENCE = Path(__file__).resolve().parents[1] / "tests" / "evidence"
NMFP = {"m": "http://www.sec.gov/edgar/nmfp3"}
LIMIT = 2_000_000
USER_AGENT = "rwa-nav-feed-audit/1.0"


def ustb_rows(raw):
    rows = []
    for row in json.loads(raw):
        check(row["fund_id"] == 1, "expected Superstate fund ID 1")
        day = datetime.strptime(row["net_asset_value_date"], "%m/%d/%Y").date().isoformat()
        rows.append((day, row["net_asset_value"]))
    return rows


def benji_rows(raw):
    form = ET.fromstring(raw)
    info = form.find("m:formData/m:generalInfo", NMFP)
    check(info is not None and info.findtext("m:seriesId", namespaces=NMFP) == "S000067043",
          "wrong Franklin series")
    report_label = info.findtext("m:reportDate", namespaces=NMFP)
    check(bool(report_label), "missing EDGAR report date")
    report_date = date.fromisoformat(report_label)
    share_class, = [
        item for item in form.findall("m:formData/m:classLevelInfo", NMFP)
        if item.findtext("m:classesId", namespaces=NMFP) == "C000215714"
    ]
    rows = []
    for row in share_class.findall("m:dailyNetAssetValuePerShareClass", NMFP):
        day = row.findtext("m:dailyNetAssetValuePerShareDateClass", namespaces=NMFP)
        value = row.findtext("m:dailyNetAssetValuePerShareClass", namespaces=NMFP)
        check(day and day[:7] == report_date.isoformat()[:7], "row outside the report month")
        check(value and re.fullmatch(r"[0-9]+\.[0-9]{4}", value), "invalid EDGAR NAV precision")
        rows.append((day, value))
    return rows


def ondo_chart(raw, product):
    # Decode the serialized chart props without executing page scripts.
    payloads = [
        json.loads(match, parse_float=Decimal)[1]
        for match in re.findall(rb"self\.__next_f\.push\((\[1,\"(?:[^\"\\]|\\.)*\"\])\)</script>", raw)
        if rb'\"assetData\"' in match or rb'\"history\"' in match
    ]
    payload = "\n".join(payloads)
    decoder = json.JSONDecoder(parse_float=Decimal)
    _, asset_marker, asset_payload = payload.partition('"assetData":{')
    check(bool(asset_marker), "missing Ondo assetData")
    asset, _ = decoder.raw_decode("{" + asset_payload)
    check(asset["symbol"] == product.lower(), "wrong Ondo product")
    _, history_marker, history_payload = payload.partition('"history":')
    check(bool(history_marker), "missing Ondo history")
    history, _ = decoder.raw_decode(history_payload)
    return [(row["timestamp"], row["asset"]["priceUsd"]) for row in history]


def usyc_rows(raw):
    report = json.loads(raw)
    check(report["entity"] == "usyc_price_report", "wrong USYC entity")
    return [
        (datetime.fromtimestamp(int(row["timestamp"]), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         row["price"])
        for row in report["data"]
    ]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def select_rows(rows, start, end):
    result = {}
    for observation, raw_value in rows:
        day = date.fromisoformat(observation[:10]).isoformat()
        if not start <= day <= end:
            continue
        value = Decimal(raw_value)
        check(value.is_finite() and value > 0, f"invalid price for {observation}")
        check(observation not in result, f"duplicate observation {observation}")
        result[observation] = format(value, "f")
    return [{"observation": day, "value": result[day]} for day in sorted(result)]


def read_source(url, user_agent):
    request = Request(url, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=12) as response:
        raw = response.read(LIMIT + 1)
    check(len(raw) <= LIMIT, "source exceeds the 2 MB request limit")
    return raw


def extract(raw, product):
    parsers = {"USTB": ustb_rows, "BENJI": benji_rows, "USYC": usyc_rows}
    return parsers[product](raw) if product in parsers else ondo_chart(raw, product)


def pinned_rows(source, product):
    if "fixture" in source:
        raw = (EVIDENCE / source["fixture"]).read_bytes()
        check(hashlib.sha256(raw).hexdigest() == source["sha256"], "fixture checksum mismatch")
        rows = extract(raw, product)
    else:
        rows = [(row["observation"], row["value"]) for row in source["observations"]]
    return select_rows(rows, source["start"], source["end"])


def compare_rows(pinned, live):
    expected = {row["observation"]: row["value"] for row in pinned}
    observed = {row["observation"]: row["value"] for row in live}
    missing = sorted(expected.keys() - observed.keys())
    added = sorted(observed.keys() - expected.keys())
    changed = [
        {"observation": label, "pinned": expected[label], "live": observed[label]}
        for label in sorted(expected.keys() & observed.keys())
        if expected[label] != observed[label]
    ]
    return {
        "status": "different" if missing or added or changed else "match",
        "pinned_count": len(pinned),
        "live_count": len(live),
        "missing": missing,
        "added": added,
        "changed": changed,
    }


def summarize(rows):
    labels = sorted({label for label, _ in rows})
    return dict(rows=len(rows), distinct_labels=len(labels),
                first=labels[0] if labels else None, last=labels[-1] if labels else None)


def edgar_index(raw, filing):
    text = raw.decode()
    for item in (filing["accession"], "N-MFP3", "S000067043", "C000215714", "FOBXX", filing["period"]):
        check(item in text, f"EDGAR filing index missing {item}")
    match = re.search(r'>Accepted</div>\s*<div[^>]*>([0-9 :\-]+)</div>', text)
    check(match and match[1] == filing["accepted_et"], "EDGAR acceptance differs from reference index")
    return match[1]


def filing_clock(filing, rows):
    accepted = datetime.fromisoformat(filing["accepted_et"]).replace(tzinfo=ZoneInfo("America/New_York"))
    period = date.fromisoformat(filing["period"])
    return dict(accepted_et=accepted.isoformat(), accepted_utc=accepted.astimezone(timezone.utc).isoformat(),
                days_after_report_end=(accepted.date()-period).days,
                days_after_last_valuation=(accepted.date()-date.fromisoformat(rows[-1]["observation"])).days,
                reported_distinct_values=len({Decimal(row["value"]) for row in rows}))


def replay(live=False, user_agent=None, verify_indices=False):
    manifest = json.loads((EVIDENCE / "manifest.json").read_bytes())
    manifest["mode"] = "live" if live else "offline"
    if live:
        manifest["pinned_accessed"] = manifest["accessed"]
        manifest["accessed"] = datetime.now(timezone.utc).date().isoformat()
    failures = []
    skipped = []
    sec_last_request = None

    def sec_read(url):
        nonlocal sec_last_request
        if sec_last_request is not None:
            time.sleep(max(0, 1.05 - (time.monotonic() - sec_last_request)))
        sec_last_request = time.monotonic()
        return read_source(url, user_agent)
    accepted = []
    benchmarks = []
    for product, record in manifest["products"].items():
        eligible = False
        for source in record.get("series", []):
            start, end = source["start"], source["end"]
            try:
                pinned = pinned_rows(source, product)
                check(len({row["observation"][:10] for row in pinned}) >= 2,
                      "need multiple pinned observation dates")
                source["rows"] = pinned
                eligible = eligible or (source["unit"] == "USD/share" and bool(source.get("valuation_basis")))
                if "filing" in source:
                    source["filing_clock"] = filing_clock(source["filing"], pinned)
                if not live:
                    continue
                if product == "BENJI" and not (user_agent and user_agent.strip()):
                    source.update(fetch_status="skipped", remedy=(
                        "Set SEC_USER_AGENT to genuine organization identification and an authorized "
                        "nonpersonal contact to opt in to live EDGAR verification."
                    ))
                    skipped.append(source["url"])
                    continue

                raw = sec_read(source["url"]) if product == "BENJI" else read_source(source["url"], USER_AGENT)
                digest = hashlib.sha256(raw).hexdigest()
                source.update(response_sha256=digest, bytes_match=digest == source["original_sha256"])
                rows = extract(raw, product)
                source["full_response"] = summarize(rows)
                if product == "USYC":
                    latest = sorted(rows, key=lambda row: row[0], reverse=True)[:3]
                    check(len(latest) == 3, "need three rolling USYC reports")
                    rolling_start, rolling_end = latest[-1][0][:10], latest[0][0][:10]
                    source["rows"] = select_rows(latest, rolling_start, rolling_end)
                    source["rolling_window"] = {"start": rolling_start, "end": rolling_end}
                else:
                    source["rows"] = select_rows(rows, start, end)
                    comparison = compare_rows(pinned, source["rows"])
                    source["comparison"] = comparison
                    if comparison["status"] != "match":
                        failures.append(source["url"])
                source["fetch_status"] = "ok"
                if product == "BENJI" and verify_indices:
                    try:
                        index = sec_read(source["filing"]["url"])
                        source["index"] = dict(response_sha256=hashlib.sha256(index).hexdigest(),
                                               accepted_et=edgar_index(index, source["filing"]))
                    except (OSError, HTTPException, ValueError) as exc:
                        source["index"] = dict(error=str(exc))
                        failures.append(source["filing"]["url"])
            except (OSError, HTTPException, ValueError, KeyError, ET.ParseError, ArithmeticError) as exc:
                if not live:
                    raise ValueError(f"{product} at {source['url']}: {exc}") from exc
                source["fetch_status"] = "error"
                source["error"] = {"type": type(exc).__name__, "message": str(exc)}
                if isinstance(exc, HTTPError):
                    source["error"]["http_status"] = exc.code
                    if product == "BENJI" and exc.code in {403, 429}:
                        source["error"]["remedy"] = (
                            "Read the SEC fair-access policy and verify request identification. "
                            "Use the pinned filing excerpt for offline replay."
                        )
                failures.append(source["url"])
        if eligible:
            accepted.append(product)
        note = record.get("note_reference", {})
        if product in accepted or (note.get("unit") == "USD/token principal"
                                   and len(note["observations"]) >= 2):
            benchmarks.append(product)
    minimum = manifest["minimum_products"]
    manifest["gate"] = {"accepted": accepted, "count": len(accepted), "passed": len(accepted) >= minimum}
    manifest["dated_per_unit_benchmarks"] = {"accepted": benchmarks, "count": len(benchmarks)}
    if live:
        manifest["live_verification"] = dict(passed=not failures and not skipped,
                                             failed_sources=failures, skipped_sources=skipped)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="compare live fixed windows to pinned observations and refresh rolling USYC")
    parser.add_argument("--verify-indices", action="store_true", help="also verify EDGAR filing indices during live reads")
    args = parser.parse_args()
    if args.verify_indices and not args.live:
        parser.error("--verify-indices requires --live")
    try:
        report = replay(live=args.live, user_agent=os.environ.get("SEC_USER_AGENT"),
                        verify_indices=args.verify_indices)
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(report, indent=2))
    return int(args.live and bool(report["live_verification"]["failed_sources"]))


if __name__ == "__main__":
    raise SystemExit(main())
