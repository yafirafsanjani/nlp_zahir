import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app.api import analytics_routes
from app.main import app
from app.services.analytics_service import AnalyticsService


MASTER_COLUMNS = [
    "sub_conversation_id", "conversation_id", "source_file", "start_time",
    "penanganan_remote", "kategori_kendala_ml_predicted",
]


class TestAnalyticsServiceAndApi(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runs_dir = Path(self.temp_dir.name) / "runs"
        self.default_dir = Path(self.temp_dir.name) / "default"
        self._write_default([
            ["default_1", "default_conv", "default_chat.txt", "10/03/2026 09.00", "REMOTE", "DEFAULT_CATEGORY"],
            ["default_2", "default_conv", "default_chat.txt", "11/03/2026 09.00", "NON_REMOTE", "DEFAULT_CATEGORY"],
        ])
        self._write_session("session_one", [
            ["issue_1", "conv_1", "chat_1.txt", "01/01/2026 09.00", "REMOTE", "CATEGORY_A"],
            ["issue_2", "conv_1", "chat_1.txt", "02/01/2026 09.00", "NON_REMOTE", "CATEGORY_B"],
            ["issue_3", "conv_2", "chat_2.txt", "05/02/2026 09.00", "", "CATEGORY_A"],
            ["issue_4", "conv_3", "chat_3.txt", "not-a-date", "UNKNOWN", ""],
            ["issue_1", "conv_1", "chat_1.txt", "01/01/2026 09.00", "NON_REMOTE", "CATEGORY_B"],
        ])
        self._write_session("session_two", [
            ["isolated_1", "isolated_conv", "chat_9.txt", "03/03/2026 09.00", "REMOTE", "ISOLATED"],
        ], {"chat_9.txt": {"customer_name": "Customer Two"}})
        self.service = AnalyticsService(
            self.runs_dir,
            self.default_dir / "output" / "master_conversations_final.csv",
            self.default_dir / "raw" / "chat" / "chat_mapping.json",
        )
        self.original_service = analytics_routes.analytics_service
        analytics_routes.analytics_service = self.service
        self.client = TestClient(app)

    def tearDown(self):
        analytics_routes.analytics_service = self.original_service
        self.temp_dir.cleanup()

    def _write_session(self, session_id, rows, mapping=None, create_master=True, columns=None):
        session_dir = self.runs_dir / session_id
        (session_dir / "raw" / "chat").mkdir(parents=True, exist_ok=True)
        if mapping is None:
            mapping = {
                "chat_1.txt": {"customer_name": "Customer One"},
                "chat_2.txt": {"customer_name": "Customer Two"},
            }
        (session_dir / "raw" / "chat" / "chat_mapping.json").write_text(
            json.dumps(mapping), encoding="utf-8"
        )
        if create_master:
            output_dir = session_dir / "output"
            output_dir.mkdir(exist_ok=True)
            pd.DataFrame(rows, columns=columns or MASTER_COLUMNS).to_csv(
                output_dir / "master_conversations_final.csv", index=False
            )

    def _write_default(self, rows):
        mapping_path = self.default_dir / "raw" / "chat" / "chat_mapping.json"
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_path.write_text(
            json.dumps({"default_chat.txt": {"customer_name": "Default Customer"}}), encoding="utf-8"
        )
        output_dir = self.default_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows, columns=MASTER_COLUMNS).to_csv(
            output_dir / "master_conversations_final.csv", index=False
        )

    def test_overview_calculates_unique_issue_totals_and_remote_rate(self):
        data = self.service.overview("session_one")
        self.assertEqual(data["total_issues"], 4)
        self.assertEqual(data["total_conversations"], 3)
        self.assertEqual((data["remote_cases"], data["non_remote_cases"], data["unknown_remote_cases"]), (1, 1, 2))
        self.assertEqual(data["remote_rate"], 50.0)
        self.assertEqual(data["top_issue"], {"category": "CATEGORY_A", "count": 2})

    def test_issue_distribution_and_unknown_category(self):
        data = self.service.issues("session_one")
        categories = {item["category"]: item for item in data["categories"]}
        self.assertEqual(categories["CATEGORY_A"]["total_cases"], 2)
        self.assertEqual(categories["CATEGORY_A"]["percentage_of_total"], 50.0)
        self.assertEqual(categories["UNKNOWN_UNCLASSIFIED"]["total_cases"], 1)

    def test_remote_breakdown_includes_unknown(self):
        data = self.service.remote("session_one")
        self.assertEqual(data["total_unknown"], 2)
        categories = {item["category"]: item for item in data["remote_by_category"]}
        self.assertEqual(categories["CATEGORY_B"]["non_remote_cases"], 1)

    def test_customer_mapping_and_source_fallback(self):
        data = self.service.customers("session_one")
        customers = {item["customer"]: item for item in data["customers"]}
        self.assertEqual(customers["Customer One"]["total_issues"], 2)
        self.assertIn("Unknown (chat_3.txt)", customers)

    def test_daily_monthly_weekly_and_yearly_aggregation(self):
        daily = self.service.time_series("session_one", "daily")["data"]
        monthly = self.service.time_series("session_one", "monthly")["data"]
        weekly = self.service.time_series("session_one", "weekly")["data"]
        yearly = self.service.time_series("session_one", "yearly")["data"]
        self.assertEqual([row["period"] for row in daily], ["2026-01-01", "2026-01-02", "2026-02-05"])
        self.assertEqual([row["period"] for row in monthly], ["2026-01", "2026-02"])
        self.assertEqual([row["period"] for row in weekly], ["2025-12-29", "2026-02-02"])
        self.assertEqual(yearly, [{"period": "2026", "total_issues": 3, "remote_cases": 1, "non_remote_cases": 1, "unknown_remote_cases": 1, "top_issue": "CATEGORY_A"}])

    def test_invalid_dates_are_excluded_from_time_series(self):
        data = self.service.time_series("session_one", "monthly")
        self.assertEqual(sum(row["total_issues"] for row in data["data"]), 3)

    def test_empty_dataset_returns_serializable_empty_results(self):
        self._write_session("empty_session", [])
        data = self.service.overview("empty_session")
        self.assertEqual(data["total_issues"], 0)
        self.assertIsNone(data["top_issue"])
        self.assertEqual(data["category_distribution"], [])

    def test_session_isolation(self):
        self.assertEqual(self.service.overview("session_two")["total_issues"], 1)
        self.assertEqual(self.service.overview("session_two")["top_issue"]["category"], "ISOLATED")

    def test_default_endpoints_work_without_session_id(self):
        expected_totals = {
            "overview": 2,
            "issues": 2,
            "remote": 1,
            "customers": 1,
        }
        for endpoint, expected_total in expected_totals.items():
            response = self.client.get("/api/" + endpoint)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["dataset"], {"type": "default", "session_id": None})
            total_key = "total_issues" if endpoint in {"overview", "issues"} else (
                "total_remote" if endpoint == "remote" else "total_customers"
            )
            self.assertEqual(data[total_key], expected_total)

        time_series = self.client.get("/api/time-series", params={"period": "daily"})
        self.assertEqual(time_series.status_code, 200)
        self.assertEqual(time_series.json()["dataset"], {"type": "default", "session_id": None})
        self.assertEqual(len(time_series.json()["data"]), 2)

    def test_session_dataset_does_not_mix_with_default_dataset(self):
        session_data = self.client.get("/api/overview", params={"session_id": "session_two"}).json()
        default_data = self.client.get("/api/overview").json()
        self.assertEqual(session_data["dataset"], {"type": "session", "session_id": "session_two"})
        self.assertEqual(session_data["total_issues"], 1)
        self.assertEqual(session_data["top_issue"]["category"], "ISOLATED")
        self.assertEqual(default_data["total_issues"], 2)
        self.assertEqual(default_data["top_issue"]["category"], "DEFAULT_CATEGORY")

    def test_missing_master_csv_is_analysis_incomplete(self):
        self._write_session("not_analyzed", [], create_master=False)
        response = self.client.get("/api/overview", params={"session_id": "not_analyzed"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"]["code"], "SESSION_OUTPUT_NOT_FOUND")

    def test_invalid_session_id_returns_404(self):
        response = self.client.get("/api/overview", params={"session_id": "does_not_exist"})
        self.assertEqual(response.status_code, 404)

    def test_invalid_period_and_date_range_are_rejected(self):
        invalid_period = self.client.get("/api/time-series", params={"session_id": "session_one", "period": "hourly"})
        invalid_range = self.client.get("/api/issues", params={
            "session_id": "session_one", "start_date": "2026-02-01", "end_date": "2026-01-01",
        })
        self.assertEqual(invalid_period.status_code, 422)
        self.assertEqual(invalid_range.status_code, 400)

    def test_api_endpoints_and_json_have_no_nan(self):
        for endpoint in ["overview", "issues", "remote", "customers", "time-series?period=monthly"]:
            response = self.client.get("/api/" + endpoint, params={"session_id": "session_one"})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("NaN", response.text)
            self.assertNotIn("Infinity", response.text)

    def test_date_filter_is_inclusive(self):
        response = self.client.get("/api/issues", params={
            "session_id": "session_one", "start_date": "2026-01-02", "end_date": "2026-01-02",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_issues"], 1)

    def test_missing_required_column_is_rejected(self):
        bad_columns = [column for column in MASTER_COLUMNS if column != "penanganan_remote"]
        self._write_session("bad_data", [["x", "c", "chat_1.txt", "01/01/2026", "CATEGORY_A"]], columns=bad_columns)
        response = self.client.get("/api/overview", params={"session_id": "bad_data"})
        self.assertEqual(response.status_code, 500)

    def test_existing_health_endpoint_remains_functional(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
