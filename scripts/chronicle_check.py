"""Compare a pinned Chronicle Ethereum consumer sample with the Chainlink replay."""
import argparse
import json
from datetime import date, datetime
from http.client import HTTPException
from pathlib import Path
from urllib.parse import urlencode

from feed_history import (BLOCK, BLOCK_HASH, EVIDENCE, ROOT, RPC, USER_AGENT,
                          address, call, check, json_bytes, read_source, replay, rpc_batch, sha, utc,
                          words, write_capture)
from fetch_sources import save
from ustb_metrics import ET

START = 26_417_731  # Includes a starting observation preceding the label cohort.
FIRST_LABEL = date(2026, 11, 16)
CONSUMER = "0x15fe07bc9019a0dec7de49c29e816261a047d252"
ROUTER = "0xdf8decbdb89c95297ee6ef816bd8a7b66973f254"
ADAPTER = "0x5d2edcad212e2f480cd8e97d839b7d539249b6e5"
ROUTER_START = 22_926_115
POKED = "0x9f8b8154174dc4a9ed8bbe5a985ecf6d8b2db481a1c64a02c8d94ae7929e0ba6"
SWITCH = "0xfc802c9c0959bd0fa05d6d93d4b62c7c5df5b0d1b5dc34c51ed73cde3e5b7b94"


def consumer_logs(destination, receipts):
    base = f"https://eth.blockscout.com/api/v2/addresses/{CONSUMER}/logs"
    cursor = dict(block_number=BLOCK + 1, index=0)
    logs = []
    for page in range(1, 5):
        url = base + "?" + urlencode(cursor)
        raw = read_source(url, USER_AGENT)
        write_capture(destination, f"consumer-page-{page}.json", url, raw, receipts)
        indexed = json.loads(raw)
        entries = indexed["items"]
        logs.extend(entry for entry in entries if START <= entry["block_number"] <= BLOCK
                    and entry["topics"][0] == POKED)
        cursor = indexed["next_page_params"]
        if cursor is None or (entries and entries[-1]["block_number"] < START):
            break
    else:
        raise ValueError("consumer index exceeds bounded page limit")
    order = [(log["block_number"], log["index"]) for log in logs]
    check(bool(logs) and order == sorted(set(order), reverse=True), "empty, unordered or duplicate logs")
    return list(reversed(logs))


def rpc_log(log, rpc):
    tx_hash, number = log["transaction_hash"], log["block_number"]
    receipt, header = rpc_batch(rpc, [
        ("eth_getTransactionReceipt", [tx_hash]),
        ("eth_getBlockByNumber", [hex(number), False]),
    ])
    check(receipt["status"] == "0x1" and receipt["transactionHash"] == tx_hash
          and int(header["number"], 16) == int(receipt["blockNumber"], 16) == number
          and header["hash"] == receipt["blockHash"] == log["block_hash"]
          and utc(int(header["timestamp"], 16)) == datetime.fromisoformat(
              log["block_timestamp"].replace("Z", "+00:00")), "log receipt or block mismatch")
    check(any(r["address"] == CONSUMER and r["data"] == log["data"]
              and r["topics"] == [t for t in log["topics"] if t]
              and int(r["logIndex"], 16) == log["index"] for r in receipt["logs"]),
          "log missing from Ethereum receipt")
    return int(header["timestamp"], 16)


def contract_call(contract, selector, block):
    return "eth_call", [{"to": contract, "data": "0x" + selector}, hex(block)]


def capture(destination, rpc):
    destination.mkdir(parents=True, exist_ok=True)
    receipts = {}
    logs = consumer_logs(destination, receipts)
    router_url = f"https://eth.blockscout.com/api/v2/addresses/{ROUTER}/logs"
    router_raw = read_source(router_url, USER_AGENT)
    write_capture(destination, "router-logs.json", router_url, router_raw, receipts)
    router_page = json.loads(router_raw)
    check(router_page["next_page_params"] is None, "router index needs pagination")
    indexed_switch, = [
        entry
        for entry in router_page["items"]
        if entry["topics"][0] == SWITCH and entry["block_number"] <= BLOCK
    ]
    old, new = words(indexed_switch["data"], 2)
    check(old == 0 and new == int(CONSUMER, 16) and indexed_switch["block_number"] == ROUTER_START,
          "unexpected Chronicle router history")
    (onchain_switch,), = rpc_batch(rpc, [
        ("eth_getLogs", [dict(address=ROUTER, topics=[SWITCH],
                             fromBlock=hex(ROUTER_START), toBlock=hex(ROUTER_START))]),
    ])
    check(onchain_switch["data"] == indexed_switch["data"]
          and int(onchain_switch["logIndex"], 16) == indexed_switch["index"]
          and onchain_switch["blockHash"] == indexed_switch["block_hash"], "router event mismatch")
    network, pin, router = rpc_batch(rpc, [
        ("eth_chainId", []), ("eth_getBlockByNumber", [hex(BLOCK), False]),
        contract_call(ADAPTER, "f887ea40", BLOCK),  # router()
    ])
    left, right, decimals = rpc_batch(rpc, [
        contract_call(ROUTER, "b72a40c1", START),   # uscribe()
        contract_call(ROUTER, "b72a40c1", BLOCK),
        call(ADAPTER, "decimals"),
    ])
    latest, = rpc_batch(rpc, [call(ADAPTER, "latestRoundData")])
    check(network == "0x1" and pin["hash"] == BLOCK_HASH and int(pin["number"], 16) == BLOCK
          and address(router) == ROUTER and address(left) == address(right) == CONSUMER
          and words(decimals, 1) == [18], "Chronicle contract, scale or block mismatch")
    check(words(latest, 5)[1] == words(logs[-1]["data"], 2)[0], "adapter end state differs from last event")
    events = []
    for log in logs:
        val, age = words(log["data"], 2)
        timestamp = rpc_log(log, rpc)
        check(0 < val < 2**128 and 0 < age <= timestamp, "invalid Chronicle Poked value or age")
        events.append(dict(block=log["block_number"], block_hash=log["block_hash"],
                           tx=log["transaction_hash"], index=log["index"],
                           value=val, payload_age=age, timestamp=timestamp))

    evidence = dict(start=START, block=BLOCK, block_hash=BLOCK_HASH, timestamp=int(pin["timestamp"], 16),
                    consumer=CONSUMER, router=ROUTER, adapter=ADAPTER, decimals=18,
                    router_activation=dict(block=ROUTER_START, block_hash=onchain_switch["blockHash"],
                                           tx=onchain_switch["transactionHash"]), events=events)
    write_capture(destination, "events.json", rpc, json_bytes(evidence), receipts)
    save(destination / "receipts.json", json_bytes(receipts))


def compare(evidence, chainlink):
    check(evidence["block_hash"] == chainlink["block"]["block_hash"] == BLOCK_HASH,
          "comparison block mismatch")
    previous = None
    first_change = {}
    for event in evidence["events"]:
        answer, remainder = divmod(event["value"], 10**12)
        if not remainder and previous is not None and event["value"] != previous:
            first_change.setdefault(answer, event["timestamp"])
        previous = event["value"]
    rows = []
    seen = set()
    for row in chainlink["full"]["delivery"]:
        label = date.fromisoformat(row["label"])
        if label < FIRST_LABEL:
            continue
        check(row["answer"] not in seen, "ambiguous repeated issuer value in Chronicle sample")
        seen.add(row["answer"])
        left_censored = evidence["events"][0]["value"] == row["answer"] * 10**12
        match = None if left_censored else first_change.get(row["answer"])
        check(match is None or utc(match).date() >= label, "Chronicle match predates the issuer label")
        chronicle_et = utc(match).astimezone(ET) if match is not None else None
        successor = row["next_issuer_value_change_date"]
        chainlink_et = datetime.fromisoformat(row["first_post_et"]) if row["first_post_et"] else None
        rows.append(dict(
            label=row["label"], answer=row["answer"], next_issuer_value_change_date=successor,
            chainlink_et=chainlink_et.isoformat() if chainlink_et else None,
            chronicle_et=chronicle_et.isoformat() if chronicle_et else None,
            chronicle_possibly_left_censored=left_censored,
            chronicle_minus_chainlink_seconds=int((chronicle_et - chainlink_et).total_seconds())
            if chronicle_et and chainlink_et else None,
            chronicle_on_next_change=str(chronicle_et.date()) == successor if chronicle_et and successor else None,
            chainlink_on_next_change=str(chainlink_et.date()) == successor if chainlink_et and successor else None,
        ))
    check(bool(rows), "missing overlapping finalized issuer labels")
    return dict(events=len(evidence["events"]), rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["capture", "replay"])
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "chronicle")
    parser.add_argument("--chainlink-data", type=Path, default=ROOT / "data" / "ustb")
    parser.add_argument("--rpc", default=RPC)
    args = parser.parse_args()
    try:
        if args.mode == "capture":
            capture(args.data, args.rpc)
            return
        ref = json.loads((EVIDENCE / "chronicle-capture.json").read_bytes())
        raw = (args.data / "events.json").read_bytes()
        check(sha(raw) == ref["receipts"]["events.json"]["sha256"], "pinned Chronicle evidence checksum mismatch")
        ustb = json.loads((EVIDENCE / "ustb-capture.json").read_bytes())
        report = json.loads(json_bytes(replay(args.chainlink_data, ustb)))
        print(json_bytes(compare(json.loads(raw), report)).decode(), end="")
    except (OSError, HTTPException, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Chronicle check: {exc}\n")


if __name__ == "__main__":
    main()
