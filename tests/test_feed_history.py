import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from decimal import Decimal
from pathlib import Path
from unittest.mock import call, patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import feed_history as feed
import chronicle_check as chronicle
import render_chart as chart
from report_checks import account_fields, compare_account, statement_links
from ustb_metrics import analyze, days


def round_row(phase, number, answer, timestamp, started=None):
    identifier = (phase << 64) | number
    return dict(id=identifier, answered_in_round=identifier, answer=answer,
                started_at=timestamp if started is None else started, updated_at=timestamp)


def time_utc(text):
    return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp())


class FeedTest(unittest.TestCase):
    def test_abi_rejects_wrong_round_and_bad_clock(self):
        rid = 2 << 64 | 9
        def encoded(rid, at):
            return "0x" + "".join(map(feed.word, (rid, 123, 10, at, rid)))
        self.assertEqual(feed.decode_round(encoded(rid, 11), rid, 12)["answer"], 123)
        for payload, expected in [(encoded(rid-1, 11), "invalid"), (encoded(rid, 13), "invalid"),
                                  ("0x1234", "ABI words")]:
            with self.subTest(payload=payload), self.assertRaisesRegex(ValueError, expected):
                feed.decode_round(payload, rid, 12)

    def test_switch_excludes_both_inactive_spans(self):
        one = round_row(1, 1, 100, 200)
        old_inactive = round_row(1, 2, 104, 240)
        new_inactive = round_row(2, 1, 101, 205)
        two = round_row(2, 2, 103, 214)
        tri = round_row(2, 3, 104, 247)
        bounds = [
            dict(block=feed.SWITCH_BLOCK-1, phase=1, latest=one, block_timestamp=215),
            dict(block=feed.SWITCH_BLOCK, phase=2, latest=two, block_timestamp=227),
        ]
        result = feed.active_rounds([one, old_inactive, new_inactive, two, tri], bounds)
        self.assertEqual([r["answer"] for r in result], [100, 103, 104])
        self.assertEqual(result[1]["updated_at"], 214)
        self.assertEqual(result[1]["visible_at"], 227)
        with self.assertRaisesRegex(ValueError, "differ"):
            feed.active_rounds([one, old_inactive, new_inactive, {**two, "answer": 102}, tri], bounds)

    def test_issuer_precision_duplicate_gap_and_future_cutoff(self):
        def payload(*items):
            return json.dumps([dict(fund_id=1, net_asset_value_date=day, net_asset_value=value)
                               for day, value in items]).encode()
        last = date(2026, 1, 3)
        label = ("01/03/2026", "10.00100100")
        self.assertEqual(feed.issuer_labels(payload(label, ("01/04/2026", "bad")), last, 6),
                         {last: 10001001})
        for args, reason in [
            ((label, label), "duplicate"),
            ((label, ("01/01/2026", "10")), "gap"),
            ((("01/03/2026", "10.0000003"),), "representable"),
        ]:
            with self.subTest(args=args), self.assertRaisesRegex(ValueError, reason):
                feed.issuer_labels(payload(*args), last, 6)

    def test_exact_value_and_holiday_joins_are_distinct(self):
        first, last = date(2025, 11, 7), date(2025, 11, 12)
        labels = dict(zip(days(first, last), (10884770, 10884770, 10884770, 10888154, 10888154, 10884770)))
        times = ["2025-11-10T14:10:23", "2025-11-11T16:40:47", "2025-11-12T14:10:35", "2025-11-12T16:40:00"]
        rounds = [round_row(2, i, answer, time_utc(at)) for i, (answer, at) in
                  enumerate(zip((10884770, 10884770, 10888154, 10884770), times), 1)]
        out = analyze(rounds, labels, first, last, 95400,
                      observed_through=time_utc("2025-11-13T06:00:00"))
        out_holiday = out["daily"][1]
        self.assertEqual(out_holiday["kind"], "Veterans Day")
        self.assertEqual(out_holiday["feed_label"], first)
        self.assertAlmostEqual(out_holiday["gap_bp"], Decimal("-3.107964858"), places=8)
        self.assertEqual(out["rounds"][1]["previous_utc_label_gap_bp"], out_holiday["gap_bp"])
        self.assertEqual(out["rounds"][2]["nyse_sessions"], 2)
        self.assertIsNone(out["rounds"][3]["label"])
        self.assertTrue(out["rounds"][3]["matched_value"])
        self.assertEqual(out["summary"]["ambiguous_rounds"], 1)

    def test_cli_fails_incomplete_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            run = subprocess.run([sys.executable, str(ROOT / "scripts/feed_history.py"),
                                  "replay", "--data", temp], text=True, capture_output=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn("receipts.json", run.stderr)

    def test_multicall_rejects_failed_subcall(self):
        rid = 2 << 64 | 44
        payload = "0x" + "".join(map(feed.word, (32, 1, 32, 0, 64, 0)))
        with patch.object(feed, "rpc_batch", return_value=[payload]), self.assertRaisesRegex(ValueError, str(rid)):
            feed.multicall_rounds("https://example.org", [rid])


    def test_literal_nyse_dates_month_end_and_columbus_day(self):
        first, last = date(2024, 10, 11), date(2024, 11, 4)
        changes = {first: 100, date(2024, 10, 15): 101, date(2024, 10, 31): 102,
                   date(2024, 11, 1): 103, date(2024, 11, 4): 104}
        value = 99
        labels = {first - timedelta(days=1): value}
        for day in days(first, last):
            value = changes.get(day, value)
            labels[day] = value
        rounds = [round_row(2, i, answer, time_utc(at)) for i, (answer, at) in enumerate([
            (99, "2024-10-11T13:00:00"), (100, "2024-10-15T13:00:00"),
            (101, "2024-10-16T13:00:00"), (102, "2024-11-03T02:00:00"),
        ], 1)]
        out = analyze(rounds, labels, first, last, 95_400,
                      observed_through=time_utc("2024-11-05T17:00:00"))
        holiday, weekend = out["rounds"][1], out["rounds"][3]
        self.assertEqual(holiday["nyse_sessions"], 2)
        self.assertFalse(holiday["posted_on_next_nyse_session_date"])
        self.assertTrue(holiday["posted_on_next_issuer_value_change_date"])
        self.assertEqual(weekend["visible_et"][:10], "2024-11-02")
        self.assertEqual(weekend["nyse_sessions"], 1)
        self.assertFalse(weekend["posted_on_next_nyse_session_date"])
        self.assertEqual(out["month_ends"][0]["label"], date(2024, 10, 31))
        self.assertEqual(out["summary"]["month_end_one_session_elapsed"], 1)
        self.assertEqual(out["summary"]["month_end_next_session_date"], 0)
        self.assertEqual(out["summary"]["uncovered_values"], [103, 104])
        self.assertEqual([r["status"] for r in out["delivery"][-2:]], ["unseen", "unknown"])

    def test_utc_close_boundary_and_finalized_lookahead(self):
        first, last, successor = list(days(date(2026, 1, 1), date(2026, 1, 3)))
        rows = [
            round_row(2, 1, 100, time_utc("2026-01-01T23:59:58")),
            round_row(2, 2, 101, time_utc("2026-01-01T23:59:59")),
            round_row(2, 3, 102, time_utc("2026-01-02T00:00:00")),
        ]
        labels = {first: 100, last: 101, successor: 102}
        observed = time_utc("2026-01-03T00:05:00")
        result = analyze(rows, labels, first, last, 95_400, observed_through=observed)
        self.assertEqual([r["feed"] for r in result["daily"]], [101, 102])
        self.assertEqual(result["delivery"][-1]["next_issuer_value_change_date"], successor)
        self.assertFalse(result["rounds"][-1]["matched_value"])
        result = analyze(rows, {first: 100, last: 101}, first, last, 95_400, observed_through=observed)
        self.assertIsNone(result["delivery"][-1]["next_issuer_value_change_date"])
        self.assertEqual(result["delivery"][-1]["status"], "unknown")

    def test_delivery_offsets_and_periods(self):
        first, early, late, last = list(days(date(2024, 12, 30), date(2025, 1, 2)))
        labels = dict(zip((first, early, late, last), (100, 101, 102, 103)))
        rounds = [round_row(2, i, answer, time_utc(at)) for i, (answer, at) in enumerate([
            (100, "2024-12-30T13:00:00"), (101, "2024-12-31T13:00:00"),
            (102, "2025-01-03T13:00:00"),
        ], 1)]
        out = analyze(rounds, labels, first, last, 95_400,
                      observed_through=time_utc("2025-01-05T17:00:00"))
        self.assertEqual([(r["status"], r["days_from_next_issuer_value_change"])
                          for r in out["delivery"]],
                         [("unknown", -1), ("before", -1), ("after", 1), ("unknown", None)])
        p2024, p2025 = out["summary"]["delivery_by_period"]
        self.assertEqual((p2024["first"], p2024["last"], p2024["total"]), (first, early, 2))
        self.assertEqual(p2024["counts"], dict(next_change=0, before=1, after=0, unseen=0, unknown=1))
        self.assertEqual((p2025["first"], p2025["last"], p2025["total"]), (late, last, 2))
        self.assertEqual(p2025["counts"], dict(next_change=0, before=0, after=1, unseen=0, unknown=1))

    def test_replay_pins_cutoff_across_live_revisions_and_rejects_tampered_reference(self):
        first, cached, missing, official, tail = list(days(date(2026, 11, 21), date(2026, 11, 25)))
        chain_at = time_utc("2026-11-27T03:33:11")
        one = round_row(1, 1, 10_000_000, time_utc("2026-11-21T12:00:00"))
        inactive = round_row(1, 2, 10_100_000, time_utc("2026-11-25T12:00:00"))
        two = round_row(2, 1, 10_000_000, time_utc("2026-11-24T12:00:00"))
        last = round_row(2, 2, 11_000_000, time_utc("2026-11-25T14:00:00"))
        chain = dict(chain_id=1, block=feed.BLOCK, block_hash=feed.BLOCK_HASH,
                     proxy=feed.PROXY, decimals=6, description=feed.FEED_NAME,
                     block_timestamp=chain_at, phases=[
                         dict(phase=i, description=feed.FEED_NAME, decimals=6, rounds=rows, aggregator="test")
                         for i, rows in [(1, [one, inactive]), (2, [two, last])]
                     ])
        bounds = [dict(block=feed.SWITCH_BLOCK+i-2, phase=i, latest=r, block_timestamp=r["updated_at"])
                  for i, r in [(1, one), (2, two)]]
        provenance = dict(porSource="Asset Manager API", porAuditor="Superstate", marketHours="NYSE")
        directory = dict(proxyAddress=feed.PROXY, name=feed.FEED_NAME, decimals=6, heartbeat=95_400,
                         contractAddress="test", docs=dict(provenance, blockchainName="Ethereum", baseAsset="USTB"))
        fund = dict(id=1, cusip="86851T204", symbol="USTB", deployments=[
            dict(chain_id=1, address="0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e")])

        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)
            receipts = {}

            def put(name, contents):
                feed.write_capture(destination, name, feed.SOURCES.get(name, feed.RPC),
                                   feed.json_bytes(contents), receipts)

            def issuer(end, tail_value):
                put("issuer.json", [dict(fund_id=1, net_asset_value_date=day.strftime("%m/%d/%Y"),
                                         net_asset_value=value)
                                    for day, value in [(first, "10"), (cached, "10.1"), (missing, "10.2"),
                                                        (official, "11"), (tail, tail_value)]])
                put("financials.json", dict(base_currency="USD",
                                           official=dict(nav_date=end, nav_per_share=tail_value)))
                (destination / "receipts.json").write_bytes(feed.json_bytes(receipts))

            put("chain.json", chain)
            put("activation.json", bounds)
            put("fund.json", fund)
            put("directory.json", [directory])
            issuer(official, "11")
            financials = receipts["financials.json"]
            ref = dict(chain_sha256=receipts["chain.json"]["sha256"],
                       activation_sha256=receipts["activation.json"]["sha256"],
                       labels_sha256=feed.sha(feed.json_bytes({str(first): 10_000_000, str(cached): 10_100_000,
                           str(missing): 10_200_000, str(official): 11_000_000})),
                       issuer_cutoff=dict(official=dict(nav_date=official.isoformat(), nav_per_share="11"),
                                          financials_sha256=financials["sha256"],
                                          observed_at_utc=financials["fetched_at_utc"]),
                       provenance=provenance, heartbeat=95_400)
            ref["receipts"] = dict(receipts)
            baseline = feed.replay(destination, ref)
            self.assertEqual(baseline["stored_round_fidelity"]["rounds"], 4)
            unseen = [r for r in baseline["full"]["delivery"] if r["status"] == "unseen"]
            self.assertEqual([(r["label"], r["absent_from_all_stored_rounds"]) for r in unseen],
                             [(cached, False), (missing, True)])
            self.assertEqual(baseline["full"]["summary"]["unseen_absent_from_all_stored_rounds"], 1)
            issuer(tail, "12.1")
            revised = feed.replay(destination, ref)
            self.assertEqual(revised["labels_sha256"], baseline["labels_sha256"])
            self.assertEqual(revised["full"], baseline["full"])
            self.assertEqual(revised["issuer_labels"], baseline["issuer_labels"])
            self.assertEqual([r["day"] for r in revised["full"]["daily"]],
                             [first, cached, missing, official])
            row = revised["full"]["rounds"][-1]
            self.assertEqual(row["label"], official)
            self.assertTrue(row["posted_on_next_nyse_session_date"])
            self.assertIsNone(row["next_issuer_value_change_date"])
            self.assertIsNone(row["posted_on_next_issuer_value_change_date"])

            for key, msg in [("chain_sha256", "pinned round fixture"),
                             ("labels_sha256", "historical issuer label/value")]:
                with self.subTest(key=key), patch.object(feed, "EVIDENCE", destination), \
                        patch.object(sys, "argv", ["feed_history.py", "replay", "--data", temp]), \
                        patch("sys.stderr") as stderr, self.assertRaises(SystemExit) as failure:
                    (destination / "ustb-capture.json").write_bytes(feed.json_bytes({**ref, key: "0"*64}))
                    feed.main()
                self.assertEqual(failure.exception.code, 1)
                self.assertIn(msg, stderr.write.call_args.args[0])


class ChronicleTest(unittest.TestCase):
    def test_join_uses_exact_changed_values_and_separates_censoring_from_absence(self):
        scale = 10**12
        activation = chronicle.ROUTER_START
        pin = time_utc("2026-11-27T03:33:11")
        evidence = dict(block=feed.BLOCK, block_hash=feed.BLOCK_HASH, decimals=18, timestamp=pin,
                        router_activation=dict(block=activation, timestamp=time_utc("2026-11-15T17:00:00")),
                        events=[
                            dict(block=activation+i, value=value, timestamp=time_utc(at))
                            for i, (value, at) in enumerate([
                                (100 * scale, "2026-11-15T16:00:00"),
                                (100 * scale, "2026-11-16T15:00:00"),
                                (101 * scale + 1, "2026-11-17T14:00:00"),
                                (101 * scale, "2026-11-17T15:00:00"),
                                (103 * scale, "2026-11-25T14:00:00"),
                            ])
                        ])
        issuer = [
            dict(label=label, answer=answer, first_post_et=post, status=status,
                 next_issuer_value_change_date=successor)
            for label, answer, post, status, successor in [
                ("2026-11-15", 99, None, "unseen", "2026-11-16"),
                ("2026-11-16", 100, None, "unseen", "2026-11-17"),
                ("2026-11-17", 101, "2026-11-17T09:05:00-05:00", "before", "2026-11-18"),
                ("2026-11-18", 102, None, "unseen", "2026-11-24"),
                ("2026-11-24", 103, "2026-11-25T09:10:00-05:00", "unknown", None),
            ]
        ]
        chainlink = dict(block=dict(block=feed.BLOCK, block_hash=feed.BLOCK_HASH, block_timestamp=pin),
                         issuer_labels=dict(last="2026-11-24"), full=dict(delivery=issuer))
        report = chronicle.compare(evidence, chainlink)
        baseline, exact, missed, tail = report["rows"]
        self.assertTrue(baseline["chronicle"]["left_censored"])
        self.assertIsNone(baseline["chronicle"]["first_post_et"])
        self.assertEqual(baseline["chronicle"]["status"], "unknown")
        self.assertEqual(exact["chronicle"]["first_post_et"].isoformat(), "2026-11-17T10:00:00-05:00")
        self.assertEqual(exact["chronicle_minus_chainlink_seconds"], 3_300)
        self.assertEqual(exact["chronicle"]["status"], "before")
        self.assertEqual(missed["chronicle"]["status"], "unseen")
        self.assertTrue(tail["chronicle"]["right_censored"])
        self.assertEqual(tail["chronicle"]["status"], "unknown")
        self.assertEqual(report["feeds"]["chainlink"]["paired_finalized_et_seconds"]["p50"], 32700)

    def test_pagination_traverses_past_five_full_pages_and_keeps_boundary(self):
        block = feed.BLOCK
        pages = []
        for page in range(6):
            entries = [dict(block_number=block - 50*page - i, index=3, topics=[chronicle.POKED])
                       for i in range(50)]
            cursor = {key: entries[-1][key] for key in ("block_number", "index")}
            pages.append(feed.json_bytes(dict(items=entries, next_page_params=cursor if page < 5 else None)))
        with patch.object(chronicle, "read_source", side_effect=pages) as read, \
                patch.object(chronicle, "write_capture"), patch.object(chronicle.time, "sleep"):
            rows = chronicle.consumer_logs(Path("."), {})
        self.assertEqual(read.call_count, 6)
        self.assertIn(f"block_number={block-49}&index=3", read.call_args_list[1].args[0])
        self.assertEqual([r["block_number"] for r in rows], list(range(block-299, block+1)))

    def test_pagination_rejects_stall_and_safety_limit(self):
        block = feed.BLOCK
        row = dict(block_number=block, index=3, topics=[chronicle.POKED])
        raw = feed.json_bytes(dict(items=[row], next_page_params=dict(block_number=block, index=3)))
        with patch.object(chronicle, "read_source", return_value=raw), \
                patch.object(chronicle, "write_capture"), patch.object(chronicle.time, "sleep"):
            with self.assertRaisesRegex(ValueError, "stalled"):
                chronicle.consumer_logs(Path("."), {})
            with self.assertRaisesRegex(ValueError, "page safety limit"):
                chronicle.consumer_logs(Path("."), {}, max_pages=1)

    def test_index_retries_rate_limit_and_timeout(self):
        throttled = HTTPError("https://example.com", 429, "Rate limited", {"Retry-After": "3"}, BytesIO())
        with patch.object(chronicle, "read_source", side_effect=[throttled, TimeoutError(), b"{}"]), \
                patch.object(chronicle.time, "sleep") as wait:
            self.assertEqual(chronicle.index_read("https://example.com"), b"{}")
        self.assertEqual(wait.call_args_list, [call(3), call(4)])

    def test_rpc_log_rejects_mismatched_block_or_missing_receipt_log(self):
        block, timestamp = feed.BLOCK, time_utc("2026-11-27T03:33:11")
        log = dict(block_number=block, block_hash=feed.BLOCK_HASH, transaction_hash="0x11",
                   block_timestamp="2026-11-27T03:33:11Z", index=7, data="0x01",
                   topics=[chronicle.POKED, "0x02", None, None])
        entry = dict(address=chronicle.CONSUMER, blockNumber=hex(block), blockHash=feed.BLOCK_HASH,
                     transactionHash="0x11", logIndex="0x7", data="0x01", topics=log["topics"][:2])
        receipt = dict(status="0x1", transactionHash="0x11", blockNumber=hex(block),
                       blockHash=feed.BLOCK_HASH, logs=[entry])
        header = dict(number=hex(block), hash=feed.BLOCK_HASH, timestamp=hex(timestamp))
        with patch.object(chronicle, "rpc_batch", return_value=[receipt, header]):
            self.assertEqual(chronicle.rpc_log(log, feed.RPC), timestamp)
        for r, h, message in [
            (receipt, dict(header, hash="0x00"), "receipt or block mismatch"),
            (receipt, dict(header, timestamp=hex(timestamp+1)), "receipt or block mismatch"),
            (dict(receipt, logs=[]), header, "missing from Ethereum receipt"),
        ]:
            with self.subTest(message=message), patch.object(chronicle, "rpc_batch", return_value=[r, h]), \
                    self.assertRaisesRegex(ValueError, message):
                chronicle.rpc_log(log, feed.RPC)

    def test_rpc_sweep_rejects_missing_indexed_log(self):
        indexed = dict(block_number=feed.BLOCK, index=1, block_hash=feed.BLOCK_HASH,
                       transaction_hash="0x1", topics=[chronicle.POKED, "0x02"], data="0x01")
        pin = dict(hash=feed.BLOCK_HASH, number=hex(feed.BLOCK))
        with patch.object(chronicle, "CONSUMER_DEPLOY", feed.BLOCK-20), \
                patch.object(chronicle, "rpc_batch", side_effect=[["0x1", pin], [[], [], []]]) as rpc, \
                self.assertRaisesRegex(ValueError, "1 index-only, 0 RPC-only"):
            chronicle.verify_log_ranges(Path("."), {}, [indexed], chronicle.LOG_RPC, 10, 10)
        params = [q[1][0] for q in rpc.call_args.args[1]]
        self.assertEqual([(int(x["fromBlock"], 16), int(x["toBlock"], 16)) for x in params],
                         [(feed.BLOCK-20, feed.BLOCK-11), (feed.BLOCK-10, feed.BLOCK-1),
                          (feed.BLOCK, feed.BLOCK)])

    def test_rpc_sweep_recovers_blank_index_tx_hash_and_rejects_disagreement(self):
        topics = [chronicle.POKED, "0x02"]
        indexed = dict(block_number=feed.BLOCK, index=1, block_hash=feed.BLOCK_HASH,
                       transaction_hash="", topics=topics, data="0x01")
        pin = dict(hash=feed.BLOCK_HASH, number=hex(feed.BLOCK))
        rpc_log = dict(blockNumber=hex(feed.BLOCK), logIndex="0x1", blockHash=feed.BLOCK_HASH,
                       address=chronicle.CONSUMER, removed=False, transactionHash="0x1234",
                       topics=topics, data="0x01")
        for tx, failure in [("", None), ("0x5678", "transaction differs")]:
            row = dict(indexed, transaction_hash=tx)
            with self.subTest(tx=tx), patch.object(chronicle, "CONSUMER_DEPLOY", feed.BLOCK), \
                    patch.object(chronicle, "rpc_batch", side_effect=[["0x1", pin], [[rpc_log]]]), \
                    patch.object(chronicle, "write_capture"):
                if failure:
                    with self.assertRaisesRegex(ValueError, failure):
                        chronicle.verify_log_ranges(Path("."), {}, [row], chronicle.LOG_RPC, 10, 10)
                else:
                    coverage = chronicle.verify_log_ranges(Path("."), {}, [row], chronicle.LOG_RPC, 10, 10)
                    self.assertEqual(coverage["index_missing_tx_hashes"], 1)
                    self.assertEqual(row["transaction_hash"], "0x1234")
        extra = dict(rpc_log, logIndex="0x2", transactionHash="0x6789")
        with patch.object(chronicle, "CONSUMER_DEPLOY", feed.BLOCK), \
                patch.object(chronicle, "rpc_batch", side_effect=[["0x1", pin], [[rpc_log, extra]]]), \
                self.assertRaisesRegex(ValueError, "0 index-only, 1 RPC-only"):
            chronicle.verify_log_ranges(Path("."), {}, [indexed], chronicle.LOG_RPC, 10, 10)

    def test_rejects_router_replacement_and_adapter_end_state_mismatch(self):
        row = dict(block_number=chronicle.ROUTER_START, topics=[chronicle.SWITCH],
                   data="0x" + feed.word(1) + feed.word(int(chronicle.CONSUMER, 16)), index=3)
        raw = feed.json_bytes(dict(items=[row], next_page_params=None))
        with patch.object(chronicle, "read_source", return_value=raw), \
                patch.object(chronicle, "write_capture"), patch.object(chronicle, "rpc_batch") as rpc:
            with self.assertRaisesRegex(ValueError, "unexpected Chronicle router history"):
                chronicle.router_activation(Path("."), {}, feed.RPC)
            rpc.assert_not_called()
        with self.assertRaisesRegex(ValueError, "adapter end state differs from last event"):
            chronicle.validate_end_state("0x" + feed.word(0) * 5,
                                         [dict(data="0x" + feed.word(1) + feed.word(0))])


class ChartTest(unittest.TestCase):
    def test_public_post_receipt_matches_chart_drafts_and_sources(self):
        receipt = json.loads((ROOT / "posts/post-review.json").read_bytes())
        card = receipt["standalone_chart"]
        svg = (ROOT / "posts" / card["file"]).read_bytes()
        ns = {"s": "http://www.w3.org/2000/svg"}
        tree = ET.fromstring(svg)
        visible = " ".join(t.text for t in tree.findall(".//s:text", ns))
        self.assertEqual(feed.sha(svg), card["sha256"])
        self.assertEqual(len(visible.split()), card["visible_words"])
        self.assertLessEqual(card["visible_words"], 20)
        self.assertEqual({g.get("id"): len(g) for g in tree.findall(".//s:g[@id]", ns)}, card["mark_counts"])
        self.assertEqual(tree.find("s:desc", ns).text, card["alt_text"])

        copy = (ROOT / "posts" / receipt["copy_file"]).read_bytes()
        self.assertEqual(feed.sha(copy), receipt["copy_file_sha256"])
        drafts = re.findall(r"^## (.+)\n\n(.+)\n\n\[[^\]]+\]\((https://[^)]+)\)", copy.decode(), re.M)
        headings = re.findall(r"^#{1,6} (.+)$", (ROOT / "docs/RESULTS.md").read_text(), re.M)
        anchors = {re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-") for h in headings}
        self.assertEqual(len(drafts), len(receipt["drafts"]))
        for (title, body, link), draft in zip(drafts, receipt["drafts"]):
            self.assertEqual((title, feed.sha(body.encode()), link),
                             (draft["title"], draft["copy_sha256"], draft["evidence"]))
            self.assertIn(link.rsplit("#", 1)[-1], anchors)

    def test_cli_matches_chart_coordinates_and_fails_a_stale_chart(self):
        rows = [
            {"label": "2024-06-27", "status": "next_change"},
            {"label": "2024-08-01", "status": "after",
             "next_issuer_value_change_date": "2024-08-02", "first_post_et": "2024-08-03T09:09:23-04:00"},
            {"label": "2026-11-24", "status": "unknown"},
        ]
        report = {"full": {"delivery": rows, "summary": {
            "first": "2024-06-27", "last": "2026-11-24",
            "delivery_statuses": {"next_change": 1, "after": 1, "unknown": 1},
        }}}
        with tempfile.TemporaryDirectory() as temp:
            infile, outfile = (Path(temp) / f for f in ("report.json", "gap.svg"))
            infile.write_text(json.dumps(report))
            cmd = [sys.executable, str(ROOT / "scripts/render_chart.py"), str(infile), str(outfile)]
            subprocess.run(cmd, check=True)
            ns = {"s": "http://www.w3.org/2000/svg"}
            svg = ET.parse(outfile)
            dots = svg.findall(".//s:g[@id]/s:circle", ns)
            self.assertEqual(len(dots), len(rows))
            self.assertEqual(float(dots[0].get("cx")), chart.LEFT)
            self.assertEqual(float(dots[-1].get("cx")), chart.RIGHT)
            self.assertIn("2026-11-24", svg.find("s:desc", ns).text)
            words = " ".join(t.text for t in svg.findall(".//s:text", ns)).split()
            self.assertLessEqual(len(words), 20)
            subprocess.run(cmd + ["--check"], check=True)
            outfile.write_text("<svg/>")
            result = subprocess.run(cmd + ["--check"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("chart differs", result.stderr)
        rows[1]["first_post_et"] = "2024-08-04T08:00:00-04:00"
        with self.assertRaisesRegex(ValueError, "displayed categories"):
            chart.render(report)


class AccountTest(unittest.TestCase):
    def test_account_extracts_signed_flows_and_rejects_wrong_date(self):
        content = """Ondo I LP
Account Statement (Unaudited)
Reporting Currency : USD
Start Of Period : 11/23/2026
End Of Period : 11/23/2026
Statement of Changes in Net Asset Value
Beginning Balance   100.00   99.00
Additions -   22.00
Net Income (Loss) (1.10)   99.00
Redemptions (5.00)   -
Ending Balance: 93.90   99.00
"""
        fields = account_fields(content, "2026-11-23")
        self.assertEqual(fields["Additions"], Decimal("0"))
        out = compare_account("2026-11-23", fields,
                              {"2026-11-23T00:00:00Z": Decimal("100"),
                               "2026-11-24T00:00:00Z": Decimal("99")})
        self.assertEqual(out["denominator_usd"], Decimal("95.00"))
        self.assertEqual(out["chart_bp"], Decimal("-100"))
        with self.assertRaisesRegex(ValueError, "identity or date mismatch"):
            account_fields(content, "2026-11-24")
        with self.assertRaisesRegex(ValueError, "no November"):
            statement_links(b"<html/>")
