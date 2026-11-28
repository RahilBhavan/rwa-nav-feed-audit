"""Capture the complete pinned Chronicle Ethereum USTB consumer history and compare delivery."""
import argparse
import json
import time
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from feed_history import (BLOCK, BLOCK_HASH, EVIDENCE, ROOT, RPC, USER_AGENT,
                          address, call, check, json_bytes, read_source, replay, retry_delay,
                          rpc_batch, sha, utc, words, write_capture)
from fetch_sources import save
from ustb_metrics import DAY, ET, delivery_counts, delivery_status, describe

CONSUMER_DEPLOY = 22_926_094
CONSUMER = "0x15fe07bc9019a0dec7de49c29e816261a047d252"
ROUTER = "0xdf8decbdb89c95297ee6ef816bd8a7b66973f254"
ADAPTER = "0x5d2edcad212e2f480cd8e97d839b7d539249b6e5"
ROUTER_START = 22_926_115
POKED = "0x9f8b8154174dc4a9ed8bbe5a985ecf6d8b2db481a1c64a02c8d94ae7929e0ba6"
SWITCH = "0xfc802c9c0959bd0fa05d6d93d4b62c7c5df5b0d1b5dc34c51ed73cde3e5b7b94"
INDEX = "https://eth.blockscout.com/api/v2/addresses"
LOG_RPC = "https://rpc.mevblocker.io"
# Exact match stays the primary rule. A separate near-value category records an
# unseen value followed by a write this close to it on or before its successor date.
NEAR_VALUE_BP = Decimal("0.1")


def index_read(url):
    for attempt in range(5):
        backoff = 2 ** (attempt + 1)
        try:
            return read_source(url, USER_AGENT)
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 4:
                raise
            with exc:
                backoff = retry_delay(exc, backoff)
        except (TimeoutError, ConnectionError, HTTPException, URLError):
            if attempt == 4:
                raise
        time.sleep(backoff)


def indexed_logs(destination, receipts, contract, start, name, *, max_pages=500):
    base = f"{INDEX}/{contract}/logs"
    cursor = (BLOCK + 1, 0)
    logs = []
    for page in range(1, max_pages + 1):
        url = base + "?" + urlencode(dict(block_number=cursor[0], index=cursor[1]))
        if page > 1:
            time.sleep(1)
        raw = index_read(url)
        write_capture(destination, f"{name}-page-{page}.json", url, raw, receipts)
        payload = json.loads(raw)
        entries = payload["items"]
        order = [(log["block_number"], log["index"]) for log in entries]
        check(order == sorted(set(order), reverse=True) and all(key < cursor for key in order),
              "Blockscout pagination stalled, unordered or duplicate page")
        next_cursor = payload["next_page_params"]
        if next_cursor is not None:
            next_key = (next_cursor["block_number"], next_cursor["index"])
            check(bool(order) and next_key == order[-1],
                  "Blockscout pagination stalled or skipped page boundary")
        logs.extend(log for log in entries if start <= log["block_number"] <= BLOCK)
        if next_cursor is None or (order and order[-1][0] < start):
            return list(reversed(logs))
        cursor = next_key
    raise ValueError("Blockscout pagination exceeds page safety limit")


def consumer_logs(destination, receipts, **options):
    logs = [log for log in indexed_logs(destination, receipts, CONSUMER, CONSUMER_DEPLOY,
                                       "consumer", **options) if log["topics"][:1] == [POKED]]
    check(bool(logs), "no Chronicle Poked events indexed")
    return logs


def log_identity(block, block_hash, tx, index, topics, data):
    return block, index, block_hash.lower(), tuple(t.lower() for t in topics), data.lower(), (tx or "").lower()


def index_identity(log):
    return log_identity(log["block_number"], log["block_hash"], log["transaction_hash"],
                        log["index"], [t for t in log["topics"] if t], log["data"])


def rpc_identity(log):
    return log_identity(int(log["blockNumber"], 16), log["blockHash"], log["transactionHash"],
                        int(log["logIndex"], 16), log["topics"], log["data"])


def verify_log_ranges(destination, receipts, logs, rpc, span, batch_size):
    network, pin = rpc_batch(rpc, [("eth_chainId", []), ("eth_getBlockByNumber", [hex(BLOCK), False])])
    check(network == "0x1" and pin["hash"] == BLOCK_HASH and int(pin["number"], 16) == BLOCK,
          "independent log RPC chain or pin mismatch")
    ranges = [(first, min(first + span - 1, BLOCK))
              for first in range(CONSUMER_DEPLOY, BLOCK + 1, span)]
    indexed = {key[:-1]: key[-1] for key in map(index_identity, logs)}
    found = {}
    counts = []
    for offset in range(0, len(ranges), batch_size):
        group = ranges[offset:offset + batch_size]
        results = rpc_batch(rpc, [
            ("eth_getLogs", [dict(address=CONSUMER, topics=[POKED],
                                 fromBlock=hex(first), toBlock=hex(last))])
            for first, last in group
        ])
        for (first, last), result in zip(group, results):
            check(isinstance(result, list), "independent log RPC returned an invalid range")
            counts.append(len(result))
            for log in result:
                *key_parts, tx = rpc_identity(log)
                key = tuple(key_parts)
                check(log.get("removed") is False and log["address"].lower() == CONSUMER
                      and len(key[3]) == 2 and key[3][0] == POKED and first <= key[0] <= last
                      and tx and key not in found, "invalid or duplicate independent Chronicle log")
                found[key] = tx
    index_only, rpc_only = indexed.keys() - found.keys(), found.keys() - indexed.keys()
    check(not index_only and not rpc_only,
          f"Chronicle log completeness mismatch: {len(index_only)} index-only, {len(rpc_only)} RPC-only")
    check(all(not tx or tx == found[key] for key, tx in indexed.items()),
          "Chronicle log transaction differs between Blockscout and RPC")
    for log in logs:
        # Blockscout omits the transaction hash on many older logs. The second
        # read recovers it by exact block hash, log index, topics and data.
        log["transaction_hash"] = found[index_identity(log)[:-1]]
    coverage = dict(first=CONSUMER_DEPLOY, last=BLOCK, block_hash=BLOCK_HASH, span=span,
                    ranges=len(ranges), max_logs_per_range=max(counts), logs=len(found),
                    index_missing_tx_hashes=sum(not tx for tx in indexed.values()),
                    ordered_log_sha256=sha(json_bytes([(*key, found[key]) for key in sorted(found)])))
    write_capture(destination, "coverage.json", rpc, json_bytes(coverage), receipts)
    return coverage


def rpc_log(log, rpc, *, observations=None):
    tx_hash, number = log["transaction_hash"], log["block_number"]
    if observations is None:
        observations = rpc_batch(rpc, [
            ("eth_getTransactionReceipt", [tx_hash]),
            ("eth_getBlockByNumber", [hex(number), False]),
        ])
    receipt, header = observations
    check(receipt and header and receipt["status"] == "0x1" and receipt["transactionHash"] == tx_hash
          and int(header["number"], 16) == int(receipt["blockNumber"], 16) == number
          and header["hash"] == receipt["blockHash"] == log["block_hash"]
          and utc(int(header["timestamp"], 16)) == datetime.fromisoformat(
              log["block_timestamp"].replace("Z", "+00:00")), "log receipt or block mismatch")
    check(any(r["address"].lower() == CONSUMER and rpc_identity(r) == index_identity(log)
              for r in receipt["logs"]), "log missing from Ethereum receipt")
    return int(header["timestamp"], 16)


def contract_call(contract, selector, block):
    return "eth_call", [{"to": contract, "data": "0x" + selector}, hex(block)]


def router_activation(destination, receipts, rpc):
    logs = indexed_logs(destination, receipts, ROUTER, 0, "router")
    switches = [entry for entry in logs if entry["topics"][:1] == [SWITCH]]
    check(len(switches) == 1, "unexpected Chronicle router history")
    switch = switches[0]
    old, new = words(switch["data"], 2)
    check(old == 0 and new == int(CONSUMER, 16) and switch["block_number"] == ROUTER_START,
          "unexpected Chronicle router history")
    chain_logs, header = rpc_batch(rpc, [
        ("eth_getLogs", [dict(address=ROUTER, topics=[SWITCH],
                             fromBlock=hex(ROUTER_START), toBlock=hex(ROUTER_START))]),
        ("eth_getBlockByNumber", [hex(ROUTER_START), False]),
    ])
    check(len(chain_logs) == 1 and chain_logs[0]["address"].lower() == ROUTER
          and rpc_identity(chain_logs[0])[:-1] == index_identity(switch)[:-1]
          and (not switch["transaction_hash"] or chain_logs[0]["transactionHash"] == switch["transaction_hash"])
          and header["hash"] == switch["block_hash"] and int(header["number"], 16) == ROUTER_START
          and utc(int(header["timestamp"], 16)) == datetime.fromisoformat(switch["block_timestamp"].replace("Z", "+00:00")),
          "router event mismatch")
    return dict(block=ROUTER_START, block_hash=header["hash"], tx=chain_logs[0]["transactionHash"],
                timestamp=int(header["timestamp"], 16))


def validate_end_state(latest, logs):
    check(words(latest, 5)[1] == words(logs[-1]["data"], 2)[0],
          "adapter end state differs from last event")


def capture(destination, rpc, log_rpc, span, batch_size, receipt_rpc, receipt_batch_size):
    destination.mkdir(parents=True, exist_ok=True)
    receipts = {}
    logs = consumer_logs(destination, receipts)
    activation = router_activation(destination, receipts, rpc)
    network, pin, router = rpc_batch(rpc, [
        ("eth_chainId", []), ("eth_getBlockByNumber", [hex(BLOCK), False]),
        contract_call(ADAPTER, "f887ea40", BLOCK),  # router()
    ])
    prior_target, left, right = rpc_batch(rpc, [
        contract_call(ROUTER, "b72a40c1", ROUTER_START - 1),  # uscribe()
        contract_call(ROUTER, "b72a40c1", ROUTER_START),
        contract_call(ROUTER, "b72a40c1", BLOCK),
    ])
    decimals, latest = rpc_batch(rpc, [call(ADAPTER, "decimals"), call(ADAPTER, "latestRoundData")])
    prior_code, creation_code = rpc_batch(rpc, [
        ("eth_getCode", [CONSUMER, hex(CONSUMER_DEPLOY - 1)]),
        ("eth_getCode", [CONSUMER, hex(CONSUMER_DEPLOY)]),
    ])
    check(network == "0x1" and pin["hash"] == BLOCK_HASH and int(pin["number"], 16) == BLOCK
          and address(router) == ROUTER and words(prior_target, 1) == [0]
          and address(left) == address(right) == CONSUMER and words(decimals, 1) == [18],
          "Chronicle contract, scale or block mismatch")
    check(prior_code == "0x" and creation_code.startswith("0x") and len(creation_code) > 2,
          "Chronicle deployment boundary mismatch")
    validate_end_state(latest, logs)
    deployment, = rpc_batch(rpc, [("eth_getBlockByNumber", [hex(CONSUMER_DEPLOY), False])])
    check(int(deployment["number"], 16) == CONSUMER_DEPLOY, "Chronicle deployment block mismatch")
    state = dict(deployment=dict(block=CONSUMER_DEPLOY, block_hash=deployment["hash"],
                                timestamp=int(deployment["timestamp"], 16),
                                bytecode_sha256=sha(bytes.fromhex(creation_code[2:]))),
                 router_activation=activation, block=BLOCK, block_hash=BLOCK_HASH,
                 timestamp=int(pin["timestamp"], 16), decimals=18, adapter_value=words(latest, 5)[1])
    write_capture(destination, "archive-state.json", rpc, json_bytes(state), receipts)
    coverage = verify_log_ranges(destination, receipts, logs, log_rpc, span, batch_size)
    events = []
    for start in range(0, len(logs), receipt_batch_size):
        group = logs[start:start + receipt_batch_size]
        calls = []
        for log in group:
            calls.extend([
                ("eth_getTransactionReceipt", [log["transaction_hash"]]),
                ("eth_getBlockByNumber", [hex(log["block_number"]), False]),
            ])
        observations = rpc_batch(receipt_rpc, calls)
        for i, log in enumerate(group):
            val, age = words(log["data"], 2)
            timestamp = rpc_log(log, receipt_rpc, observations=observations[2*i:2*i+2])
            check(0 < val < 2**128 and 0 < age < 2**48 and age <= timestamp,
                  "invalid Chronicle Poked value or age")
            events.append(dict(block=log["block_number"], block_hash=log["block_hash"],
                               tx=log["transaction_hash"], index=log["index"],
                               value=val, payload_age=age, timestamp=timestamp))
        if start + receipt_batch_size < len(logs):
            time.sleep(0.25)

    evidence = dict(start=CONSUMER_DEPLOY, block=BLOCK, block_hash=BLOCK_HASH,
                    timestamp=int(pin["timestamp"], 16), consumer=CONSUMER, router=ROUTER,
                    adapter=ADAPTER, decimals=18, router_activation=activation,
                    ordered_log_sha256=coverage["ordered_log_sha256"], events=events)
    write_capture(destination, "events.json", receipt_rpc, json_bytes(evidence), receipts)
    save(destination / "receipts.json", json_bytes(receipts))


def near_value(events, raw, label, successor):
    """First write within NEAR_VALUE_BP of an unseen issuer value, from its label date to its successor date."""
    if successor is None:
        return None
    for event in events:
        posted = utc(event["timestamp"]).astimezone(ET)
        difference = (event["value"] - raw) * 10_000 / Decimal(raw)
        if label <= posted.date() <= successor and abs(difference) <= NEAR_VALUE_BP:
            return dict(first_post_et=posted, value=event["value"], difference_bp=f"{difference:.3f}")
    return None


def compare(evidence, chainlink):
    check(evidence["block"] == chainlink["block"]["block"] == BLOCK
          and evidence["block_hash"] == chainlink["block"]["block_hash"] == BLOCK_HASH
          and evidence["timestamp"] == chainlink["block"]["block_timestamp"],
          "comparison block mismatch")
    activation = evidence["router_activation"]
    entered = utc(activation["timestamp"])
    # Exclude activation day in either clock. A date-only label on that day
    # cannot establish whether the relevant value was available before activation.
    first = max(entered.date(), entered.astimezone(ET).date()) + DAY
    through_et = utc(evidence["timestamp"]).astimezone(ET).date()
    scale = 10**(evidence["decimals"] - 6)
    first_change = {}
    observed = set()
    previous = None
    baseline = None
    for event in evidence["events"]:
        value = event["value"]
        if event["block"] <= activation["block"]:
            baseline = value
        else:
            observed.add(value)
            if value != previous:
                first_change.setdefault(value, utc(event["timestamp"]).astimezone(ET))
        previous = value
    # Keep only the final value held at activation, plus subsequent observations.
    if baseline is not None:
        observed.add(baseline)

    rows = []
    post_activation = [e for e in evidence["events"] if e["block"] > activation["block"]]
    delivery = chainlink["full"]["delivery"]
    occurrence_counts = Counter(row["answer"] for row in delivery)
    for row in delivery:
        label = date.fromisoformat(row["label"])
        if label < first:
            continue
        raw = row["answer"] * scale
        successor = (date.fromisoformat(row["next_issuer_value_change_date"])
                     if row["next_issuer_value_change_date"] else None)
        left_censored = raw == baseline
        post = None if left_censored else first_change.get(raw)
        link_post = datetime.fromisoformat(row["first_post_et"]) if row["first_post_et"] else None
        # A repeated or earlier-only exact value cannot establish this spell's first post.
        ambiguous = (post and utc(post.timestamp()).date() < label) or occurrence_counts[row["answer"]] > 1
        if ambiguous:
            post = None
        status = delivery_status(post, successor, through_et, observed_value=raw in observed,
                                 changed=post is not None)
        near = near_value(post_activation, raw, label, successor) if status == "unseen" else None
        paired = post is not None and link_post is not None
        rows.append(dict(
            label=label, answer=row["answer"], next_issuer_value_change_date=successor,
            chainlink=dict(first_post_et=link_post, status=row["status"],
                           right_censored=successor is None or (link_post is None and successor >= through_et)),
            chronicle=dict(first_post_et=post, status=status, left_censored=left_censored,
                           right_censored=successor is None or (post is None and successor >= through_et),
                           ambiguous=bool(ambiguous), near_value=near),
            chronicle_minus_chainlink_seconds=int(post.timestamp()-link_post.timestamp()) if paired else None,
        ))
    check(bool(rows), "missing shared issuer labels")
    paired = [r for r in rows if r["chronicle_minus_chainlink_seconds"] is not None]
    finalized = [r for r in paired if r["next_issuer_value_change_date"] is not None]
    differences = [r["chronicle_minus_chainlink_seconds"] for r in finalized]
    feeds = {}
    for feed in ("chainlink", "chronicle"):
        # The clock summary uses identical paired labels with successors on both feeds.
        times = [r[feed]["first_post_et"] for r in finalized]
        feeds[feed] = dict(counts=delivery_counts(r[feed] for r in rows),
                           paired_finalized_et_seconds=describe(
                               t.hour * 3600 + t.minute * 60 + t.second for t in times))
    periods = []
    for year in sorted({r["label"].year for r in rows}):
        group = [r for r in rows if r["label"].year == year]
        periods.append(dict(year=year, labels=len(group),
                            chronicle_unseen_with_near_value=sum(r["chronicle"]["near_value"] is not None for r in group),
                            **{feed: delivery_counts(r[feed] for r in group) for feed in feeds}))
    events = evidence["events"]
    issuer_values = {row["answer"] * scale for row in delivery}
    exact_events = [event for event in events if event["value"] in issuer_values]
    return dict(events=len(events), exact_matching_events=len(exact_events),
                first_event=events[0], first_exact_event=next(iter(exact_events), None),
                first=first, last=chainlink["issuer_labels"]["last"], labels=len(rows), feeds=feeds,
                by_period=periods, near_value_bp=NEAR_VALUE_BP,
                chronicle_unseen_near_values=[
                    dict(label=r["label"], issuer_answer=r["answer"],
                         **r["chronicle"]["near_value"]) for r in rows if r["chronicle"]["near_value"]],
                by_period_unseen_without_near_value={
                    p["year"]: p["chronicle"]["unseen"] - p["chronicle_unseen_with_near_value"] for p in periods},
                paired_finalized_seconds=describe(differences), paired_without_successor=len(paired)-len(finalized),
                baseline_at_activation=baseline, pre_activation_events=sum(
                    e["block"] < activation["block"] for e in evidence["events"]),
                chronicle_earlier=sum(d < 0 for d in differences),
                chronicle_later=sum(d > 0 for d in differences), ties=differences.count(0),
                rows=rows)


def replay_events(destination, reference):
    receipts = json.loads((destination / "receipts.json").read_bytes())
    raw = (destination / "events.json").read_bytes()
    check(sha(raw) == receipts["events.json"]["sha256"] == reference["receipts"]["events.json"]["sha256"],
          "pinned Chronicle evidence checksum mismatch")
    evidence = json.loads(raw)
    archive = (destination / "archive-state.json").read_bytes()
    check(sha(archive) == receipts["archive-state.json"]["sha256"] ==
          reference["receipts"]["archive-state.json"]["sha256"], "pinned Chronicle state checksum mismatch")
    coverage_raw = (destination / "coverage.json").read_bytes()
    check(sha(coverage_raw) == receipts["coverage.json"]["sha256"],
          "local Chronicle coverage checksum mismatch")
    coverage = json.loads(coverage_raw)
    check((coverage["first"], coverage["last"], coverage["block_hash"],
           coverage["logs"], coverage["ordered_log_sha256"]) ==
          (evidence["start"], evidence["block"], evidence["block_hash"],
           len(evidence["events"]), evidence["ordered_log_sha256"]),
          "Chronicle coverage and event stream disagree")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["capture", "replay"])
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "chronicle")
    parser.add_argument("--chainlink-data", type=Path, default=ROOT / "data" / "ustb")
    parser.add_argument("--rpc", default=RPC)
    parser.add_argument("--log-rpc", default=LOG_RPC)
    parser.add_argument("--log-span", type=int, default=10_000)
    parser.add_argument("--log-batch", type=int, default=10)
    parser.add_argument("--receipt-rpc", default=LOG_RPC)
    parser.add_argument("--receipt-batch", type=int, default=5, help="events per batch, at two calls each")
    args = parser.parse_args()
    try:
        if args.mode == "capture":
            check(1 <= args.log_span <= 100_000 and 1 <= args.log_batch <= 100,
                  "invalid log span or batch size")
            check(1 <= args.receipt_batch <= 50, "invalid receipt batch size")
            capture(args.data, args.rpc, args.log_rpc, args.log_span, args.log_batch,
                    args.receipt_rpc, args.receipt_batch)
            return
        ref = json.loads((EVIDENCE / "chronicle-capture.json").read_bytes())
        evidence = replay_events(args.data, ref)
        ustb = json.loads((EVIDENCE / "ustb-capture.json").read_bytes())
        report = json.loads(json_bytes(replay(args.chainlink_data, ustb)))
        print(json_bytes(compare(evidence, report)).decode(), end="")
    except (OSError, HTTPException, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Chronicle check: {exc}\n")


if __name__ == "__main__":
    main()
