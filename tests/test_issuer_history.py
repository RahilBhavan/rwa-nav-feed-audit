import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime as RealDatetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import issuer_history as audit


def mock_response(product, source):
    """Build a synthetic wire-format stub from the research observations."""
    rows = source["rows"]
    if product == "BENJI":
        return (audit.EVIDENCE / source["fixture"]).read_bytes()
    if product == "USTB":
        return json.dumps([
            {
                "fund_id": 1,
                "net_asset_value_date": date.fromisoformat(row["observation"]).strftime("%m/%d/%Y"),
                "net_asset_value": row["value"],
            }
            for row in rows
        ]).encode()
    if product == "USYC":
        return json.dumps({
            "entity": "usyc_price_report",
            "data": [
                {
                    "timestamp": int(RealDatetime.fromisoformat(
                        row["observation"].replace("Z", "+00:00")
                    ).timestamp()),
                    "price": row["value"],
                }
                for row in rows
            ],
        }).encode()
    history = [
        '{"timestamp":' + json.dumps(row["observation"]) + ',"asset":{"priceUsd":' + row["value"] + "}}"
        for row in rows
    ]
    payload = '{"assetData":{"symbol":"' + product.lower() + '"},"history":[' + ",\n".join(history) + "]}"
    return ("<script>self.__next_f.push(" + json.dumps([1, payload], separators=(",", ":"))
            + ")</script>").encode()


class IssuerHistoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(audit, "urlopen", side_effect=AssertionError("offline replay called network")):
            cls.report = audit.replay()
        cls.products = cls.report["products"]

    def test_all_six_products_and_gate(self):
        self.assertEqual(
            {p: item["status"] for p, item in self.products.items()},
            {
                "BUIDL": "no_offchain_series_found",
                "USTB": "usable",
                "USYC": "circular_oracle_history",
                "OUSG": "display_history_unverified_lineage",
                "USDY": "note_reference_history",
                "BENJI": "usable",
            },
        )
        self.assertEqual(self.report["minimum_products"], 3)
        extracted_verified = {
            p for p, item in self.products.items() if any(
                s["unit"] == "USD/share" and "valuation_basis" in s
                and len({r["observation"] for r in s["rows"]}) >= 2
                for s in item.get("series", []))
        }
        self.assertEqual(extracted_verified, {"USTB", "BENJI"})
        self.assertEqual(extracted_verified, set(self.report["gate"]["accepted"]))
        self.assertEqual(self.report["gate"], {"accepted": ["USTB", "BENJI"], "count": 2, "passed": False})
        self.assertEqual(self.report["dated_per_unit_benchmarks"],
                         {"accepted": ["USTB", "USDY", "BENJI"], "count": 3})

    def test_ustb_keeps_month_end_weekends_and_precision(self):
        fall, november = self.products["USTB"]["series"]
        self.assertEqual([len(fall["rows"]), len(november["rows"])], [7, 5])
        values = {row["observation"]: row["value"] for row in fall["rows"]}
        self.assertEqual(values["2026-09-30"], "11.22990800")
        self.assertEqual(values["2026-10-02"], "11.23223300")
        self.assertEqual(values["2026-10-02"], values["2026-10-03"])
        self.assertEqual(values["2026-10-02"], values["2026-10-04"])
        self.assertNotEqual(values["2026-10-02"], values["2026-10-05"])
        self.assertEqual(november["rows"][-1]["observation"], "2026-11-24")
        self.assertEqual(november["rows"][-1]["value"], "11.29144100")
        with self.assertRaisesRegex(ValueError, "expected Superstate fund ID 1"):
            audit.ustb_rows(b'[{"fund_id":2}]')

    def test_benji_class_business_dates_and_reported_precision(self):
        september, october = self.products["BENJI"]["series"]
        self.assertEqual([len(september["rows"]), len(october["rows"])], [21, 22])
        rows = september["rows"] + october["rows"]
        self.assertEqual({row["value"] for row in rows}, {"1.0000"})
        self.assertEqual(september["rows"][-1]["observation"], "2026-09-30")
        self.assertEqual(october["rows"][-1]["observation"], "2026-10-30")
        self.assertNotIn("2026-09-07", {row["observation"] for row in rows})
        raw = (audit.EVIDENCE / september["fixture"]).read_bytes()
        with self.assertRaises(ValueError):
            audit.benji_rows(raw.replace(b"C000215714", b"C000000000"))

    def test_excluded_histories_keep_source_clock_and_decimal(self):
        expected = {
            "USYC": ("2026-11-25T13:33:35Z", "1.144875672876728641"),
            "OUSG": ("2026-11-26T00:00:00Z", "117.395732"),
            "USDY": ("2026-11-26T00:00:00Z", "1.154470247702"),
        }
        for product, (day, value) in expected.items():
            with self.subTest(product=product):
                series, = self.products[product]["series"]
                self.assertEqual(series["rows"][-1], {"observation": day, "value": value})

    def test_duplicate_dates_rejected_inside_window(self):
        with self.assertRaisesRegex(ValueError, "duplicate observation"):
            audit.select_rows([("2026-09-29", "1")] * 2, "2026-09-29", "2026-09-30")

    def test_source_digest_enforced(self):
        source = self.products["BENJI"]["series"][0]
        with self.assertRaisesRegex(ValueError, "checksum"):
            audit.pinned_rows(dict(source, sha256="bad"), "BENJI")


class LiveComparisonTest(unittest.TestCase):
    def setUp(self):
        snapshot = audit.replay()
        self.products = snapshot["products"]
        self.responses = {
            source["url"]: mock_response(product, source)
            for product, record in self.products.items() for source in record.get("series", [])
        }

    def source(self, product, index=0):
        return self.products[product]["series"][index]["url"]

    def run_live(self, user_agent="Synthetic test caller"):
        def open_response(request, timeout):
            expected = user_agent if request.host == "www.sec.gov" else audit.USER_AGENT
            self.assertEqual(request.get_header("User-agent"), expected)
            self.assertEqual(timeout, 12)
            raw = self.responses[request.full_url]
            if isinstance(raw, Exception):
                raise raw
            return io.BytesIO(raw)

        stdout = io.StringIO()
        with (patch.object(audit, "urlopen", side_effect=open_response) as fetch,
              patch("sys.argv", ["issuer_history.py", "--live"]),
              patch.dict("os.environ", {"SEC_USER_AGENT": user_agent}),
              patch.object(audit.time, "sleep"),
              redirect_stdout(stdout)):
            exit_status = audit.main()
        self.assertEqual(fetch.call_count, len(self.responses))
        return exit_status, json.loads(stdout.getvalue())

    def test_cli_skips_edgar_without_opt_in(self):
        for source in self.products["BENJI"]["series"]:
            del self.responses[source["url"]]
        status, result = self.run_live(user_agent="")
        self.assertEqual(status, 0)
        self.assertFalse(result["live_verification"]["passed"])
        self.assertEqual(len(result["live_verification"]["skipped_sources"]), 2)
        source = result["products"]["BENJI"]["series"][0]
        self.assertEqual(source["fetch_status"], "skipped")
        self.assertIn("SEC_USER_AGENT", source["remedy"])
        self.assertEqual(len(source["rows"]), 21)

    def test_source_size_cap(self):
        with patch.object(audit, "urlopen", return_value=io.BytesIO(b"abcd")), patch.object(audit, "LIMIT", 3):
            with self.assertRaisesRegex(ValueError, "2 MB request limit"):
                audit.read_source("https://example.org", audit.USER_AGENT)

    def test_edgar_index_identifiers_and_time(self):
        source = self.products["BENJI"]["series"][0]
        filing = source["filing"]
        raw = (
            f'{filing["accession"]} N-MFP3 S000067043 C000215714 FOBXX {filing["period"]}'
            f'<div>Accepted</div> <div class="info">{filing["accepted_et"]}</div>'
        ).encode()
        self.assertEqual(audit.edgar_index(raw, filing), filing["accepted_et"])
        self.assertEqual(source["filing_clock"]["days_after_report_end"], 6)
        october = self.products["BENJI"]["series"][1]
        self.assertEqual(october["filing_clock"]["days_after_last_valuation"], 7)
        with self.assertRaisesRegex(ValueError, "acceptance differs"):
            audit.edgar_index(raw.replace(b"15:46:56", b"15:46:55"), filing)

    def test_live_index_replay_checks_identity_and_hashes_bytes(self):
        for source in self.products["BENJI"]["series"]:
            filing = source["filing"]
            self.responses[filing["url"]] = (
                f'{filing["accession"]} N-MFP3 S000067043 C000215714 FOBXX {filing["period"]}'
                f'<div>Accepted</div><div>{filing["accepted_et"]}</div>'
            ).encode()
        with (patch.object(audit, "read_source", side_effect=lambda url, _: self.responses[url]),
              patch.object(audit.time, "sleep") as sleep,
              patch.object(audit.time, "monotonic", return_value=0)):
            result = audit.replay(live=True, user_agent="Synthetic test caller", verify_indices=True)
        self.assertTrue(result["live_verification"]["passed"])
        self.assertEqual(sleep.call_count, 3)
        self.assertTrue(all(c.args[0] >= 1 for c in sleep.call_args_list))
        for source in result["products"]["BENJI"]["series"]:
            digest = audit.hashlib.sha256(self.responses[source["filing"]["url"]]).hexdigest()
            self.assertEqual(source["index"]["response_sha256"], digest)

    def test_match_and_rolling_refresh(self):
        url = self.source("USYC")
        reports = json.loads(self.responses[url])
        latest = max(reports["data"], key=lambda row: int(row["timestamp"]))
        new_timestamp = int(latest["timestamp"]) + 12 * 86400
        reports["data"].append(dict(latest, timestamp=str(new_timestamp)))
        self.responses[url] = json.dumps(reports).encode()

        class FutureDatetime(RealDatetime):
            @classmethod
            def now(cls, tz=None):
                if tz != timezone.utc:
                    raise AssertionError("live access date must use UTC")
                return cls(2027, 1, 1, tzinfo=tz)

        identity = "Test caller supplied User-Agent"
        with patch.object(audit, "datetime", FutureDatetime):
            status, report = self.run_live(user_agent=identity)
        self.assertEqual(status, 0)
        self.assertEqual(report["accessed"], "2027-01-01")
        self.assertEqual(report["pinned_accessed"], "2026-11-26")
        self.assertFalse(report["gate"]["passed"])
        self.assertTrue(report["live_verification"]["passed"])
        rolling, = report["products"]["USYC"]["series"]
        self.assertEqual(rolling["start"], "2026-11-23")
        self.assertEqual(rolling["end"], "2026-11-25")
        self.assertEqual(rolling["rolling_window"]["end"], "2026-12-07")
        self.assertEqual(len(rolling["rows"]), 3)
        self.assertEqual(rolling["fetch_status"], "ok")
        self.assertEqual(rolling["full_response"]["rows"], 4)
        self.assertNotIn("comparison", rolling)
        september, = report["products"]["BENJI"]["series"][:1]
        self.assertEqual(september["comparison"]["status"], "match")
        self.assertEqual(september["comparison"]["pinned_count"], 21)
        self.assertFalse(september["bytes_match"])  # The stub is a filing excerpt.
        self.assertEqual(september["full_response"]["distinct_labels"], 21)

    def test_preserves_results_across_source_errors(self):
        sec = self.source("BENJI")
        self.responses[sec] = HTTPError(sec, 403, "Forbidden", None, None)
        ustb = self.source("USTB")
        self.responses[ustb] = TimeoutError("socket timed out")
        self.responses[self.source("OUSG")] = self.responses[self.source("USDY")]
        usyc = self.source("USYC")
        self.responses[usyc] = self.responses[usyc].replace(b"usyc_price_report", b"wrong_entity")

        status, report = self.run_live()
        self.assertEqual(status, 1)
        self.assertFalse(report["live_verification"]["passed"])
        self.assertEqual(set(report["live_verification"]["failed_sources"]),
                         {sec, ustb, self.source("OUSG"), usyc})
        products = report["products"]
        for product, message in (
            ("USTB", "socket timed out"), ("USYC", "wrong USYC entity"),
            ("OUSG", "wrong Ondo product"), ("BENJI", "HTTP Error 403"),
        ):
            with self.subTest(product=product):
                source = products[product]["series"][0]
                self.assertEqual(source["fetch_status"], "error")
                self.assertIn(message, source["error"]["message"])
        self.assertEqual(products["BENJI"]["series"][0]["error"]["http_status"], 403)
        self.assertIn("fair-access", products["BENJI"]["series"][0]["error"]["remedy"])
        self.assertEqual(products["BENJI"]["series"][1]["comparison"]["status"], "match")
        self.assertEqual(products["USDY"]["series"][0]["comparison"]["status"], "match")

    def test_detects_missing_added_and_revised_observations(self):
        ustb = self.source("USTB")
        revision = sorted(json.loads(self.responses[ustb]), key=lambda row: row["net_asset_value_date"])
        revision.pop(0)
        revision[0]["net_asset_value"] = "11.23000000"
        self.responses[ustb] = json.dumps(revision).encode()
        ousg = self.source("OUSG")
        raw = self.responses[ousg]
        history_start = raw.index(b"{", raw.index(b"history"))
        first_row = raw[history_start:raw.index(rb",\n", history_start)]
        added_row = first_row.replace(b"00:00:00Z", b"12:00:00Z")
        self.responses[ousg] = raw.replace(first_row, first_row + rb",\n" + added_row, 1)
        self.responses[self.source("USTB", 1)] = b"[]"

        status, report = self.run_live()
        self.assertEqual(status, 1)
        first, second = report["products"]["USTB"]["series"]
        self.assertEqual(first["fetch_status"], "ok")
        self.assertEqual(first["comparison"]["status"], "different")
        self.assertEqual(first["comparison"]["missing"], ["2026-09-29"])
        self.assertEqual(first["comparison"]["changed"], [
            {"observation": "2026-09-30", "pinned": "11.22990800", "live": "11.23000000"},
        ])
        self.assertEqual(second["comparison"]["live_count"], 0)
        self.assertEqual(len(second["comparison"]["missing"]), 5)
        self.assertEqual(report["products"]["OUSG"]["series"][0]["comparison"]["added"],
                         ["2026-11-20T12:00:00Z"])


if __name__ == "__main__":
    unittest.main()
