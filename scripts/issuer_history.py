"""Replay the offchain NAV availability gate from recorded observations and SEC filings."""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path
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
    check(info.findtext("m:seriesId", namespaces=NMFP) == "S000067043", "wrong Franklin series")
    report_date = date.fromisoformat(info.findtext("m:reportDate", namespaces=NMFP))
    share_class, = [
        item for item in form.findall("m:formData/m:classLevelInfo", NMFP)
        if item.findtext("m:classesId", namespaces=NMFP) == "C000215714"
    ]
    rows = []
    for row in share_class.findall("m:dailyNetAssetValuePerShareClass", NMFP):
        day = row.findtext("m:dailyNetAssetValuePerShareDateClass", namespaces=NMFP)
        check(day[:7] == report_date.isoformat()[:7], "row outside the report month")
        rows.append((day, row.findtext("m:dailyNetAssetValuePerShareClass", namespaces=NMFP)))
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
    asset, _ = decoder.raw_decode("{" + payload.split('"assetData":{', 1)[1])
    check(asset["symbol"] == product.lower(), "wrong Ondo product")
    history, _ = decoder.raw_decode(payload.split('"history":', 1)[1])
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


def replay(live=False, user_agent=None):
    manifest = json.loads((EVIDENCE / "manifest.json").read_bytes())
    manifest["mode"] = "live" if live else "offline"
    if live:
        check(bool(user_agent and user_agent.strip()), "live comparison requires genuine EDGAR request identification")
        manifest["pinned_accessed"] = manifest["accessed"]
        manifest["accessed"] = datetime.now(timezone.utc).date().isoformat()
    failures = []
    accepted = []
    benchmarks = []
    for product, record in manifest["products"].items():
        for source in record.get("series", []):
            start, end = source["start"], source["end"]
            try:
                pinned = pinned_rows(source, product)
                check(len({row["observation"][:10] for row in pinned}) >= 2,
                      "need multiple pinned observation dates")
                if not live:
                    source["rows"] = pinned
                    continue

                source_user_agent = user_agent if product == "BENJI" else USER_AGENT
                rows = extract(read_source(source["url"], source_user_agent), product)
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
            except (OSError, HTTPException, ValueError, KeyError, IndexError, AttributeError,
                    TypeError, ET.ParseError, ArithmeticError) as exc:
                if not live:
                    raise ValueError(f"{product} at {source['url']}: {exc}") from exc
                source["fetch_status"] = "error"
                source["error"] = {"type": type(exc).__name__, "message": str(exc)}
                failures.append(source["url"])
        if record["status"] == "usable":
            check(bool(record.get("series")), f"{product} is missing its usable series")
            accepted.append(product)
        if record["status"] in {"usable", "note_reference_history"}:
            benchmarks.append(product)
    minimum = manifest["minimum_products"]
    manifest["gate"] = {"accepted": accepted, "count": len(accepted), "passed": len(accepted) >= minimum}
    manifest["dated_per_unit_benchmarks"] = {"accepted": benchmarks, "count": len(benchmarks)}
    if live:
        manifest["live_verification"] = {"passed": not failures, "failed_sources": failures}
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="compare live fixed windows to pinned observations and refresh rolling USYC")
    parser.add_argument("--user-agent", help="your genuine request identification for live reads, including EDGAR contact")
    args = parser.parse_args()
    if args.live and not (args.user_agent and args.user_agent.strip()):
        parser.error("--live requires --user-agent with your genuine EDGAR request identification and contact")
    options = {"user_agent": args.user_agent} if args.user_agent else {}
    try:
        report = replay(live=args.live, **options)
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(report, indent=2))
    return int(args.live and not report["live_verification"]["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
