import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import feed_history as feed
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
        out = analyze(rounds, labels, first, last, 95400)
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


class ChartTest(unittest.TestCase):
    def test_cli_matches_chart_coordinates_and_fails_a_stale_chart(self):
        daily = [{"day": str(d), "gap_bp": str(-3 if d == date(2024, 7, 29) else -1)}
                 for d in days(date(2024, 6, 27), date(2026, 11, 26))]
        report = {"full": {"daily": daily, "summary": {"max_behind_daily_close": daily[32]}}}
        with tempfile.TemporaryDirectory() as temp:
            infile, outfile = (Path(temp) / f for f in ("report.json", "gap.svg"))
            infile.write_text(json.dumps(report))
            cmd = [sys.executable, str(ROOT / "scripts/render_chart.py"), str(infile), str(outfile)]
            subprocess.run(cmd, check=True)
            ns = {"s": "http://www.w3.org/2000/svg"}
            svg = ET.parse(outfile)
            dots = svg.findall(".//s:g[@id='daily-gaps']/s:circle", ns)
            self.assertEqual(len(dots), len(daily))
            self.assertEqual(float(dots[0].get("cx")), chart.LEFT)
            self.assertEqual(float(dots[-1].get("cx")), chart.RIGHT)
            self.assertEqual(float(dots[32].get("cy")), (chart.TOP+chart.BOTTOM)/2)
            focus = svg.find(".//s:circle[@id='deepest-gap']", ns)
            self.assertEqual((focus.get("cx"), focus.get("cy")), (dots[32].get("cx"), dots[32].get("cy")))
            self.assertIn("2024-07-29", svg.find("s:desc", ns).text)
            words = " ".join(t.text for t in svg.findall(".//s:text", ns)).split()
            self.assertLessEqual(len(words), 20)
            subprocess.run(cmd + ["--check"], check=True)
            outfile.write_text("<svg/>")
            check = subprocess.run(cmd + ["--check"], capture_output=True, text=True)
            self.assertEqual(check.returncode, 1)
            self.assertIn("chart differs", check.stderr)
        report["full"]["daily"][0]["gap_bp"] = "NaN"
        with self.assertRaisesRegex(ValueError, "outside"):
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
