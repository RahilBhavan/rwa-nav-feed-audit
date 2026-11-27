"""Capture and replay the USTB Ethereum Chainlink proxy history."""
import argparse
import hashlib
import json
import re
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from http.client import HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from fetch_sources import save
from issuer_history import EVIDENCE, LIMIT, USER_AGENT, check, read_source, ustb_rows
from ustb_metrics import analyze

ROOT = Path(__file__).resolve().parents[1]
BLOCK = 26_503_879
BLOCK_HASH = "0x4763fd004596f13e42369a95222159fa52ccd36db8925d324d86631625e6249f"
PROXY = "0x289b5036cd942e619e1ee48670f98d214e745aac"
RPC = "https://eth.drpc.org"
MULTICALL = "0xca11bde05977b3631167028862be2a173976ca11"
FEED_NAME = "USTB NAV per Share"
WINDOW = date(2025, 9, 27)
SWITCH_BLOCK = 20_464_407
SOURCES = {
    "issuer.json": "https://api.superstate.com/v1/funds/1/nav-daily",
    "directory.json": "https://reference-data-directory.vercel.app/feeds-mainnet.json",
    "fund.json": "https://api.superstate.com/v3/funds/USTB",
    "financials.json": "https://api.superstate.com/v3/funds/USTB/financials",
}
SELECTORS = {
    "aggregator": "245a7bfc",
    "phaseAggregators": "c1597304",
    "phaseId": "58303b10",
    "latestRoundData": "feaf968c",
    "getRoundData": "9a6fc8f5",
    "decimals": "313ce567",
    "description": "7284e416",
}
DAY = timedelta(days=1)


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, default=str) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


def rpc_batch(url, calls):
    request = [
        dict(jsonrpc="2.0", id=i, method=method, params=params)
        for i, (method, params) in enumerate(calls)
    ]
    result = None
    for attempt in range(3):
        try:
            http = Request(url, data=json.dumps(request).encode(), headers={
                "Content-Type": "application/json", "User-Agent": USER_AGENT,
            })
            with urlopen(http, timeout=25) as response:
                raw = response.read(LIMIT + 1)
            check(len(raw) <= LIMIT, "RPC response exceeds the 2 MB limit")
            result = json.loads(raw)
            break
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
            time.sleep(2 ** attempt)
        except (TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    check(isinstance(result, list) and len(result) == len(calls), f"invalid RPC batch: {result!s:.400}")
    by_id = {r["id"]: r for r in result}
    check(set(by_id) == set(range(len(calls))), "missing or duplicate RPC response ID")
    for i, (method, params) in enumerate(calls):
        check("result" in by_id[i], f"RPC {method} {str(params)[:180]}: {by_id[i].get('error')}")
    return [by_id[i]["result"] for i in range(len(calls))]


def call(address, method, argument=None, block=BLOCK):
    arg = "" if argument is None else f"{argument:064x}"
    return "eth_call", [{"to": address, "data": "0x" + SELECTORS[method] + arg}, hex(block)]


def words(value, count):
    check(bool(re.fullmatch(r"0x[0-9a-fA-F]+", value)) and len(value) == 2 + 64 * count,
          f"expected {count} ABI words")
    return [int(value[i:i+64], 16) for i in range(2, len(value), 64)]


def address(value):
    number, = words(value, 1)
    check(0 < number < 2**160, "invalid aggregator address")
    return f"0x{number:040x}"


def description(value):
    raw = bytes.fromhex(value.removeprefix("0x"))
    check(len(raw) >= 64 and int.from_bytes(raw[:32], "big") == 32, "invalid ABI string")
    length = int.from_bytes(raw[32:64], "big")
    check(64 + length <= len(raw), "truncated ABI string")
    return raw[64:64+length].decode()


def decode_round(value, expected_id, cutoff):
    round_id, answer, started, updated, answered = words(value, 5)
    check(round_id == answered == expected_id and 0 < answer < 2**255
          and 0 < started <= updated <= cutoff, f"invalid or missing round {expected_id}")
    return dict(id=round_id, answer=answer, started_at=started, updated_at=updated, answered_in_round=answered)


def word(number):
    return f"{number:064x}"


def multicall_rounds(url, ids):
    # Multicall3 tryAggregate(bool,(address,bytes)[]) at the same pinned block.
    # The leading offsets are measured from the start of the array's tuple offsets.
    items = []
    offsets = []
    offset = 32 * len(ids)
    for rid in ids:
        calldata = call(PROXY, "getRoundData", rid)[1][0]["data"][2:]
        item = word(int(PROXY, 16)) + word(64) + word(len(calldata) // 2) + calldata.ljust(128, "0")
        offsets.append(word(offset))
        items.append(item)
        offset += len(item) // 2
    data = "0xbce38bd7" + word(0) + word(64) + word(len(ids)) + "".join(offsets + items)
    payload, = rpc_batch(url, [("eth_call", [{"to": MULTICALL, "data": data}, hex(BLOCK)])])
    raw = bytes.fromhex(payload.removeprefix("0x"))

    def number(index):
        check(index >= 0 and index + 32 <= len(raw), "truncated multicall ABI response")
        return int.from_bytes(raw[index:index+32], "big")

    check(number(0) == 32 and number(32) == len(ids), "multicall response count mismatch")
    values = []
    for i, rid in enumerate(ids):
        start = 64 + number(64 + 32 * i)
        check(number(start) == 1, f"multicall could not read round {rid}")
        data_start = start + number(start + 32)
        size = number(data_start)
        check(size == 160 and data_start + 32 + size <= len(raw), "invalid multicall round payload")
        values.append("0x" + raw[data_start+32:data_start+32+size].hex())
    return values


def capture_chain(url, batch_size):
    chain, block = rpc_batch(url, [
        ("eth_chainId", []), ("eth_getBlockByNumber", [hex(BLOCK), False]),
    ])
    decimals, title, phase_word = rpc_batch(
        url, [call(PROXY, method) for method in ("decimals", "description", "phaseId")])
    aggregator, proxy_latest = rpc_batch(
        url, [call(PROXY, method) for method in ("aggregator", "latestRoundData")])
    check(chain == "0x1" and block and int(block["number"], 16) == BLOCK
          and block["hash"] == BLOCK_HASH, "pinned Ethereum block identity mismatch")
    cutoff = int(block["timestamp"], 16)
    phase_count, = words(phase_word, 1)
    check(phase_count == 2, "unexpected phase count at pinned block")
    phases = []
    latest_id = words(proxy_latest, 5)[0]
    for phase in range(1, phase_count + 1):
        endpoint, = rpc_batch(url, [call(PROXY, "phaseAggregators", phase)])
        endpoint = address(endpoint)
        phase_decimals, phase_title, latest = rpc_batch(url, [
            call(endpoint, method) for method in ("decimals", "description", "latestRoundData")
        ])
        terminal = decode_round(latest, words(latest, 5)[0], cutoff)
        check(0 < terminal["id"] <= 10_000, "unexpected aggregator round bound")
        ids = [(phase << 64) | number for number in range(1, terminal["id"] + 1)]
        rounds = []
        for offset in range(0, len(ids), batch_size):
            group = ids[offset:offset+batch_size]
            results = multicall_rounds(url, group)
            rounds.extend(decode_round(value, rid, cutoff) for value, rid in zip(results, group))
            time.sleep(0.25)
        check({**rounds[-1], "id": terminal["id"], "answered_in_round": terminal["id"]} == terminal,
              "aggregator terminal round differs from proxy")
        phases.append(dict(phase=phase, aggregator=endpoint, decimals=words(phase_decimals, 1)[0],
                           description=description(phase_title), rounds=rounds))
    check(phases[-1]["aggregator"] == address(aggregator) and
          phases[-1]["rounds"][-1] == decode_round(proxy_latest, latest_id, cutoff),
          "current aggregator or latest round differs from proxy")
    return dict(chain_id=1, block=BLOCK, block_hash=BLOCK_HASH, block_timestamp=cutoff,
                proxy=PROXY, decimals=words(decimals, 1)[0], description=description(title), phases=phases)


def capture_activation(url):
    boundaries = []
    for number, phase in ((SWITCH_BLOCK - 1, 1), (SWITCH_BLOCK, 2)):
        block, phase_word, latest = rpc_batch(url, [
            ("eth_getBlockByNumber", [hex(number), False]),
            call(PROXY, "phaseId", block=number),
            call(PROXY, "latestRoundData", block=number),
        ])
        cutoff = int(block["timestamp"], 16)
        round_id = words(latest, 5)[0]
        check(int(block["number"], 16) == number and words(phase_word, 1)[0] == round_id >> 64 == phase,
              "proxy switch boundary differs from reference")
        boundaries.append(dict(block=number, block_hash=block["hash"], block_timestamp=cutoff,
                               phase=phase, latest=decode_round(latest, round_id, cutoff)))
    return boundaries


def write_capture(destination, filename, url, raw, receipts):
    save(destination / filename, raw)
    receipts[filename] = dict(url=url, fetched_at_utc=datetime.now(timezone.utc).isoformat(),
                              sha256=sha(raw))


def activation_only(destination, rpc):
    receipts = json.loads((destination / "receipts.json").read_bytes())
    write_capture(destination, "activation.json", rpc, json_bytes(capture_activation(rpc)), receipts)
    save(destination / "receipts.json", json_bytes(receipts))


def capture(destination, rpc, batch_size):
    destination.mkdir(parents=True, exist_ok=True)
    receipts = {}
    with TemporaryDirectory(prefix=".capture-", dir=destination) as folder:
        staging = Path(folder)
        for filename, url in SOURCES.items():
            write_capture(staging, filename, url, read_source(url, USER_AGENT), receipts)
        write_capture(staging, "chain.json", rpc, json_bytes(capture_chain(rpc, batch_size)), receipts)
        write_capture(staging, "activation.json", rpc, json_bytes(capture_activation(rpc)), receipts)
        for filename in receipts:
            (staging / filename).replace(destination / filename)
        save(destination / "receipts.json", json_bytes(receipts))


def validate_chain(chain):
    check(chain["chain_id"] == 1 and chain["block"] == BLOCK and chain["block_hash"] == BLOCK_HASH
          and chain["proxy"] == PROXY and chain["decimals"] == 6 and chain["description"] == FEED_NAME,
          "chain fixture identity mismatch")
    check([p["phase"] for p in chain["phases"]] == [1, 2], "missing or unordered proxy phase")
    rounds = []
    for phase in chain["phases"]:
        check(phase["description"] == FEED_NAME and phase["decimals"] == 6, "phase denomination mismatch")
        check(bool(phase["rounds"]), "empty proxy phase")
        previous = 0
        for number, row in enumerate(phase["rounds"], 1):
            expected_id = (phase["phase"] << 64) | number
            check(row["id"] == row["answered_in_round"] == expected_id, "noncontiguous proxy round IDs")
            check(0 < row["answer"] < 2**255 and 0 < row["started_at"] <= row["updated_at"]
                  <= chain["block_timestamp"], f"bad answer or clock in round {expected_id}")
            check(previous < row["updated_at"], "round clocks are nonmonotonic within a phase")
            previous = row["updated_at"]
            rounds.append(row)
    return rounds


def active_rounds(rounds, boundaries):
    before, after = boundaries
    check((before["block"], after["block"]) == (SWITCH_BLOCK - 1, SWITCH_BLOCK)
          and (before["phase"], after["phase"]) == (1, 2), "bad phase crossover boundary")
    before_id, after_id = before["latest"]["id"], after["latest"]["id"]
    by_id = {r["id"]: r for r in rounds}
    check(before["latest"] == by_id[before_id] and after["latest"] == by_id[after_id],
          "switch-block proxy rounds differ from pinned history")
    before_timestamp, switch = before["block_timestamp"], after["block_timestamp"]
    check(by_id[before_id]["updated_at"] <= before_timestamp < switch
          and by_id[after_id]["updated_at"] <= switch, "nonchronological phase switch")
    check(all(r["updated_at"] > before_timestamp for r in rounds if before_id < r["id"] < 2 << 64)
          and all(r["updated_at"] > switch for r in rounds if r["id"] > after_id),
          "phase switch omits a newer round")
    return [
        {**r, "visible_at": switch if r["id"] == after_id else r["updated_at"]}
        for r in rounds if r["id"] <= before_id or r["id"] >= after_id
    ]


def issuer_labels(raw, last, decimals):
    labels = {}
    for day, value in ustb_rows(raw):
        day = date.fromisoformat(day)
        if day > last:
            continue
        scaled = Decimal(value).scaleb(decimals)
        check(scaled.is_finite() and scaled > 0 and scaled == scaled.to_integral_value(),
              f"NAV for {day} is not positive or exactly representable")
        check(day not in labels, f"duplicate issuer label {day}")
        labels[day] = int(scaled)
    check(bool(labels), "missing pinned issuer NAVs")
    ordered = sorted(labels)
    check(all(right-left == DAY for left, right in zip(ordered, ordered[1:])),
          "gap in pinned issuer date labels")
    check(ordered[-1] == last, "issuer date labels stop before the pinned cutoff")
    return labels


def replay(destination, reference):
    receipts = json.loads((destination / "receipts.json").read_bytes())
    check(set(receipts) == {*SOURCES, "chain.json", "activation.json"}, "incomplete feed capture receipts")
    raw = {}
    for filename, receipt in receipts.items():
        raw[filename] = (destination / filename).read_bytes()
        check(sha(raw[filename]) == receipt["sha256"], f"local checksum mismatch: {filename}")
        if filename in SOURCES:
            check(receipt["url"] == SOURCES[filename], f"unexpected source URL: {filename}")
    chain = json.loads(raw["chain.json"])
    stored_rounds = validate_chain(chain)
    boundaries = json.loads(raw["activation.json"])
    rounds = active_rounds(stored_rounds, boundaries)
    fund = json.loads(raw["fund.json"])
    check(fund["id"] == 1 and fund["cusip"] == "86851T204" and fund["symbol"] == "USTB"
          and any(d.get("chain_id") == 1 and
                  d["address"].lower() == "0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e"
                  for d in fund["deployments"]), "issuer fund/share deployment identity mismatch")
    financials = json.loads(raw["financials.json"])
    check(financials["base_currency"] == "USD", "unexpected issuer denomination")
    entries = json.loads(raw["directory.json"])
    matches = [item for item in entries if item.get("proxyAddress", "").lower() == PROXY]
    franklin_terms = re.compile(r"(?i)\b(benji|franklin|fobxx)\b")
    franklin_entries = [item.get("name") for item in entries if franklin_terms.search(" ".join(
        str(item.get(k, "")) for k in ("name", "assetName", "path", "docs")))]
    check(len(matches) == 1, "expected one Chainlink directory entry")
    directory = matches[0]
    check(directory["name"] == FEED_NAME and directory["decimals"] == chain["decimals"]
          and directory["docs"]["blockchainName"] == "Ethereum" and directory["docs"]["baseAsset"] == "USTB",
          "directory identity differs from pinned USTB feed")
    provenance = {field: directory["docs"][field] for field in ("porSource", "porAuditor", "marketHours")}
    heartbeat = directory["heartbeat"]
    check(isinstance(heartbeat, int) and heartbeat > 0, "invalid directory heartbeat")
    # Live financials can move forward while a historical replay stays pinned.
    # Retain finalized labels beyond the last complete UTC day for lookahead only.
    cutoff = reference["issuer_cutoff"]
    origin = reference["receipts"]["financials.json"]
    check(cutoff["financials_sha256"] == origin["sha256"]
          and cutoff["observed_at_utc"] == origin["fetched_at_utc"], "pinned official NAV receipt mismatch")
    official = cutoff["official"]
    official_date = date.fromisoformat(official["nav_date"])
    last = min(utc(chain["block_timestamp"]).date() - DAY, official_date)
    labels = issuer_labels(raw["issuer.json"], official_date, chain["decimals"])
    check(Decimal(official["nav_per_share"]).scaleb(chain["decimals"]) == labels[official_date],
          "pinned official NAV differs from the issuer label at the cutoff")
    label_digest = sha(json_bytes({str(day): answer for day, answer in labels.items()}))
    check(sha(raw["chain.json"]) == reference["chain_sha256"], "pinned round fixture checksum mismatch")
    check(sha(raw["activation.json"]) == reference["activation_sha256"], "pinned phase switch checksum mismatch")
    check(label_digest == reference["labels_sha256"], "historical issuer label/value checksum mismatch")
    check(heartbeat == reference["heartbeat"] and provenance == reference["provenance"],
          "feed directory heartbeat or provenance differs from reference capture")
    first = utc(rounds[0]["updated_at"]).date()
    check(min(labels) <= first, "issuer history starts after proxy rounds")
    phases = [
        dict(phase=p["phase"], aggregator=p["aggregator"], description=p["description"],
             decimals=p["decimals"], rounds=len(p["rounds"]),
             started_utc=utc(p["rounds"][0]["updated_at"]).isoformat(),
             ended_utc=utc(p["rounds"][-1]["updated_at"]).isoformat(),
             active_rounds=sum(r["id"] >> 64 == p["phase"] for r in rounds))
        for p in chain["phases"]
    ]
    label_values = {value for day, value in labels.items() if day <= last}
    active_ids = {row["id"] for row in rounds}
    return dict(
        block={k: chain[k] for k in ("block", "block_hash", "block_timestamp", "proxy")},
        phases=phases, phase_switch=boundaries, heartbeat=heartbeat, provenance=provenance,
        activation_sha256=sha(raw["activation.json"]),
        stored_round_fidelity=dict(rounds=len(stored_rounds),
            matching=sum(row["answer"] in label_values for row in stored_rounds),
            archival_only=sum(row["id"] not in active_ids for row in stored_rounds)),
        stored_rounds=[{**r, "active": r["id"] in active_ids,
                        "matches_an_issuer_label": r["answer"] in label_values}
                       for r in stored_rounds],
        directory_current_aggregator=directory["contractAddress"],
        directory_benji_name_candidates=franklin_entries,
        receipts=receipts, chain_sha256=sha(raw["chain.json"]), labels_sha256=label_digest,
        issuer_labels=dict(total_to_cutoff=sum(day <= last for day in labels), first=min(labels), last=last,
                           finalized_through=official_date, cutoff=cutoff),
        full=analyze(rounds, labels, first, last, heartbeat, observed_through=chain["block_timestamp"]),
        review_window=analyze(rounds, labels, WINDOW, last, heartbeat, observed_through=chain["block_timestamp"]),
        review_label_cohort=analyze(rounds, labels, date(2025, 9, 29), last, heartbeat,
                                    observed_through=chain["block_timestamp"])["summary"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["capture", "activation", "replay"])
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "ustb")
    parser.add_argument("--rpc", default=RPC)
    parser.add_argument("--batch-size", default=32, type=int)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 64:
        parser.error("--batch-size must be between 1 and 64")
    try:
        if args.mode == "capture":
            capture(args.data, args.rpc, args.batch_size)
        elif args.mode == "activation":
            activation_only(args.data, args.rpc)
        else:
            reference = json.loads((EVIDENCE / "ustb-capture.json").read_bytes())
            print(json_bytes(replay(args.data, reference)).decode(), end="")
    except (OSError, HTTPException, ValueError, KeyError, InvalidOperation) as exc:
        parser.exit(1, f"feed history: {exc}\n")


if __name__ == "__main__":
    main()
