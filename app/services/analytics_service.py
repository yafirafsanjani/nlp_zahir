"""Session-scoped, read-only analytics for the NLP master CSV."""

import json
from datetime import date
from pathlib import Path
from typing import Any, Optional

import pandas as pd


UNKNOWN_CATEGORY = "UNKNOWN_UNCLASSIFIED"
UNKNOWN_REMOTE = "UNKNOWN"
REQUIRED_COLUMNS = {
    "sub_conversation_id",
    "conversation_id",
    "source_file",
    "start_time",
    "penanganan_remote",
    "kategori_kendala_ml_predicted",
}


class AnalyticsError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AnalyticsService:
    """Loads the default master CSV or an explicitly requested session artifact."""

    def __init__(
        self,
        runs_dir: Optional[Path] = None,
        default_master_path: Optional[Path] = None,
        default_mapping_path: Optional[Path] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.runs_dir = (runs_dir or base_dir / "data" / "runs").resolve()
        self.default_master_path = (
            default_master_path or base_dir / "data" / "output" / "master_conversations_final.csv"
        ).resolve()
        self.default_mapping_path = (
            default_mapping_path or base_dir / "data" / "raw" / "chat" / "chat_mapping.json"
        ).resolve()

    def _session_dir(self, session_id: str) -> Path:
        if not session_id or not session_id.strip():
            raise AnalyticsError(400, "INVALID_SESSION_ID", "session_id harus disediakan.")
        candidate = (self.runs_dir / session_id).resolve()
        if candidate.parent != self.runs_dir or not candidate.is_dir():
            raise AnalyticsError(404, "SESSION_NOT_FOUND", "Session tidak ditemukan.")
        return candidate

    def _load_mapping(self, session_dir: Path) -> dict[str, Any]:
        return self._load_mapping_path(session_dir / "raw" / "chat" / "chat_mapping.json")

    @staticmethod
    def _load_mapping_path(mapping_path: Path) -> dict[str, Any]:
        if not mapping_path.is_file():
            return {}
        try:
            with mapping_path.open("r", encoding="utf-8") as file:
                mapping = json.load(file)
            return mapping if isinstance(mapping, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _remote_status(value: Any) -> str:
        if value is None or pd.isna(value):
            return UNKNOWN_REMOTE
        normalized = str(value).strip().upper()
        if normalized in {"REMOTE", "TRUE", "YES", "YA", "1", "T"}:
            return "REMOTE"
        if normalized in {"NON_REMOTE", "NON-REMOTE", "FALSE", "NO", "TIDAK", "0", "F"}:
            return "NON_REMOTE"
        return UNKNOWN_REMOTE

    @staticmethod
    def _category(value: Any) -> str:
        if value is None or pd.isna(value):
            return UNKNOWN_CATEGORY
        category = str(value).strip()
        if not category or category.lower() in {"nan", "none", "null", "unknown", "unclassified"}:
            return UNKNOWN_CATEGORY
        return category

    @staticmethod
    def _parse_timestamp(value: Any) -> pd.Timestamp:
        text = str(value).strip() if value is not None else ""
        for timestamp_format in (
            "%d/%m/%y %H.%M", "%d/%m/%Y %H.%M",
            "%d/%m/%y %H:%M", "%d/%m/%Y %H:%M",
        ):
            parsed = pd.to_datetime(text, format=timestamp_format, errors="coerce")
            if not pd.isna(parsed):
                return parsed
        return pd.NaT

    def load_data(
        self,
        session_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Optional[str]]]:
        if start_date and end_date and start_date > end_date:
            raise AnalyticsError(400, "INVALID_DATE_RANGE", "start_date tidak boleh setelah end_date.")

        if session_id:
            session_dir = self._session_dir(session_id)
            master_path = session_dir / "output" / "master_conversations_final.csv"
            mapping = self._load_mapping(session_dir)
            dataset = {"type": "session", "session_id": session_id}
            if not master_path.is_file():
                raise AnalyticsError(404, "SESSION_OUTPUT_NOT_FOUND", "Output analytics untuk session tidak tersedia.")
        else:
            master_path = self.default_master_path
            mapping = self._load_mapping_path(self.default_mapping_path)
            dataset = {"type": "default", "session_id": None}
            if not master_path.is_file():
                raise AnalyticsError(404, "DEFAULT_DATASET_NOT_FOUND", "Dataset analytics default tidak tersedia.")

        try:
            data = pd.read_csv(master_path, dtype=str, keep_default_na=False)
        except (OSError, pd.errors.EmptyDataError) as exc:
            raise AnalyticsError(500, "ANALYTICS_DATA_INVALID", "Master CSV tidak dapat dibaca.") from exc

        missing = REQUIRED_COLUMNS.difference(data.columns)
        if missing:
            raise AnalyticsError(
                500,
                "ANALYTICS_DATA_INVALID",
                "Master CSV tidak memiliki kolom analitik yang diperlukan.",
            )

        # A sub-conversation is the analytical issue; retain one record per ID.
        data = data.drop_duplicates(subset=["sub_conversation_id"], keep="first").copy()
        data["_remote_status"] = data["penanganan_remote"].map(self._remote_status)
        data["_category"] = data["kategori_kendala_ml_predicted"].map(self._category)
        data["_timestamp"] = data["start_time"].map(self._parse_timestamp)
        data["_customer"] = data["source_file"].map(lambda source: self._customer_name(source, mapping))

        if start_date:
            data = data[data["_timestamp"] >= pd.Timestamp(start_date)]
        if end_date:
            data = data[data["_timestamp"] < pd.Timestamp(end_date) + pd.Timedelta(days=1)]
        return data.reset_index(drop=True), mapping, dataset

    @staticmethod
    def _customer_name(source_file: Any, mapping: dict[str, Any]) -> str:
        source = str(source_file).strip() if source_file is not None else "unknown-source"
        mapped = mapping.get(source)
        if isinstance(mapped, dict):
            customer_name = mapped.get("customer_name")
            if customer_name and str(customer_name).strip():
                return str(customer_name).strip()
        # Preserve source boundaries without inventing a person or organization.
        return "Unknown (" + (source or "unknown-source") + ")"

    @staticmethod
    def _counts(frame: pd.DataFrame) -> dict[str, int]:
        return {
            "total": int(len(frame)),
            "remote": int((frame["_remote_status"] == "REMOTE").sum()),
            "non_remote": int((frame["_remote_status"] == "NON_REMOTE").sum()),
            "unknown": int((frame["_remote_status"] == UNKNOWN_REMOTE).sum()),
        }

    @staticmethod
    def _remote_rate(remote: int, non_remote: int) -> float:
        known = remote + non_remote
        return round((remote / known * 100) if known else 0.0, 2)

    @staticmethod
    def _top_issue(frame: pd.DataFrame) -> Optional[dict[str, Any]]:
        if frame.empty:
            return None
        counts = frame.groupby("_category").size().reset_index(name="count")
        top = counts.sort_values(["count", "_category"], ascending=[False, True]).iloc[0]
        return {"category": str(top["_category"]), "count": int(top["count"])}

    def _breakdown(self, frame: pd.DataFrame, key: str, include_percentage: bool = False) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        total = len(frame)
        for value, group in frame.groupby(key, sort=False, dropna=False):
            counts = self._counts(group)
            row = {
                "key": str(value),
                "total_cases": counts["total"],
                "remote_cases": counts["remote"],
                "non_remote_cases": counts["non_remote"],
                "unknown_remote_cases": counts["unknown"],
                "remote_rate": self._remote_rate(counts["remote"], counts["non_remote"]),
            }
            if include_percentage:
                row["percentage_of_total"] = round((counts["total"] / total * 100) if total else 0.0, 2)
            rows.append(row)
        return sorted(rows, key=lambda row: (-row["total_cases"], row["key"]))

    def overview(self, session_id: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> dict[str, Any]:
        data, _, dataset = self.load_data(session_id, start_date, end_date)
        counts = self._counts(data)
        distribution = [
            {"category": row["key"], "count": row["total_cases"], "percentage": row["percentage_of_total"]}
            for row in self._breakdown(data, "_category", include_percentage=True)
        ]
        valid_dates = data["_timestamp"].dropna()
        return {
            "session_id": session_id,
            "dataset": dataset,
            "total_issues": counts["total"],
            "total_conversations": int(data["conversation_id"].nunique()),
            "remote_cases": counts["remote"],
            "non_remote_cases": counts["non_remote"],
            "unknown_remote_cases": counts["unknown"],
            "remote_rate": self._remote_rate(counts["remote"], counts["non_remote"]),
            "top_issue": self._top_issue(data),
            "category_distribution": distribution,
            "analysis_period": {
                "start": valid_dates.min().isoformat() if not valid_dates.empty else None,
                "end": valid_dates.max().isoformat() if not valid_dates.empty else None,
            },
        }

    def issues(self, session_id: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> dict[str, Any]:
        data, _, dataset = self.load_data(session_id, start_date, end_date)
        return {
            "session_id": session_id,
            "dataset": dataset,
            "total_issues": int(len(data)),
            "categories": [
                {"category": row.pop("key"), **row}
                for row in self._breakdown(data, "_category", include_percentage=True)
            ],
        }

    def remote(self, session_id: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> dict[str, Any]:
        data, _, dataset = self.load_data(session_id, start_date, end_date)
        counts = self._counts(data)
        category_rows = self._breakdown(data, "_category")
        customer_rows = self._breakdown(data, "_customer")
        return {
            "session_id": session_id,
            "dataset": dataset,
            "total_remote": counts["remote"],
            "total_non_remote": counts["non_remote"],
            "total_unknown": counts["unknown"],
            "remote_rate": self._remote_rate(counts["remote"], counts["non_remote"]),
            "remote_by_category": [{"category": row.pop("key"), **row} for row in category_rows],
            "remote_by_customer": [{"customer": row.pop("key"), **row} for row in customer_rows],
        }

    def customers(self, session_id: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> dict[str, Any]:
        data, _, dataset = self.load_data(session_id, start_date, end_date)
        customers: list[dict[str, Any]] = []
        for customer, group in data.groupby("_customer", sort=False, dropna=False):
            counts = self._counts(group)
            top = self._top_issue(group)
            customers.append({
                "customer": str(customer),
                "total_issues": counts["total"],
                "total_remote": counts["remote"],
                "total_non_remote": counts["non_remote"],
                "total_unknown": counts["unknown"],
                "remote_rate": self._remote_rate(counts["remote"], counts["non_remote"]),
                "top_issue": top["category"] if top else UNKNOWN_CATEGORY,
            })
        return {
            "session_id": session_id,
            "dataset": dataset,
            "total_customers": len(customers),
            "customers": sorted(customers, key=lambda row: (-row["total_issues"], row["customer"])),
        }

    def time_series(
        self,
        session_id: Optional[str] = None,
        period: str = "monthly",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, Any]:
        if period not in {"daily", "weekly", "monthly", "yearly"}:
            raise AnalyticsError(400, "INVALID_PERIOD", "period harus daily, weekly, monthly, atau yearly.")
        data, _, dataset = self.load_data(session_id, start_date, end_date)
        dated = data.dropna(subset=["_timestamp"]).copy()
        if period == "daily":
            dated["_period"] = dated["_timestamp"].dt.strftime("%Y-%m-%d")
        elif period == "weekly":
            # Weeks start on Monday; label is the Monday date.
            dated["_period"] = (dated["_timestamp"] - pd.to_timedelta(dated["_timestamp"].dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
        elif period == "monthly":
            dated["_period"] = dated["_timestamp"].dt.strftime("%Y-%m")
        else:
            dated["_period"] = dated["_timestamp"].dt.strftime("%Y")

        records: list[dict[str, Any]] = []
        for label, group in dated.groupby("_period", sort=True):
            counts = self._counts(group)
            top = self._top_issue(group)
            records.append({
                "period": str(label),
                "total_issues": counts["total"],
                "remote_cases": counts["remote"],
                "non_remote_cases": counts["non_remote"],
                "unknown_remote_cases": counts["unknown"],
                "top_issue": top["category"] if top else UNKNOWN_CATEGORY,
            })
        return {"session_id": session_id, "dataset": dataset, "period": period, "data": records}

    def conversations(
        self,
        session_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        remote: Optional[str] = None,
        client_response: Optional[str] = None,
        match: Optional[str] = None,
    ) -> dict[str, Any]:
        data, mapping, dataset = self.load_data(session_id, start_date, end_date)
        frame = data.copy()

        if search:
            query = search.strip().lower()
            mask = (
                frame["sub_conversation_id"].str.lower().str.contains(query, na=False)
                | frame["conversation_id"].str.lower().str.contains(query, na=False)
                | frame["source_file"].str.lower().str.contains(query, na=False)
                | frame["_customer"].str.lower().str.contains(query, na=False)
                | frame["full_conversation"].str.lower().str.contains(query, na=False)
            )
            frame = frame[mask]

        if category:
            cat_filter = category.strip()
            frame = frame[
                (frame["_category"] == cat_filter)
                | (frame["kategori_kendala_ml_predicted"] == cat_filter)
                | (frame["kategori_kendala_ground_truth"] == cat_filter)
            ]

        if remote:
            rem_filter = remote.strip().upper()
            frame = frame[
                (frame["_remote_status"] == rem_filter)
                | (frame["penanganan_remote"].str.upper() == rem_filter)
            ]

        if client_response:
            resp_filter = client_response.strip().upper()
            frame = frame[frame["client_response"].str.upper() == resp_filter]

        if match:
            match_filter = match.strip().upper()
            frame = frame[frame["prediction_match"].str.upper() == match_filter]

        total = len(frame)
        page = max(1, page)
        page_size = max(1, min(200, page_size)) if page_size > 0 else 20
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_slice = frame.iloc[start_idx:end_idx]

        records = []
        for _, row in page_slice.iterrows():
            def _to_int(val: Any, default: int = 0) -> int:
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return default

            records.append({
                "sub_conversation_id": str(row.get("sub_conversation_id", "")),
                "conversation_id": str(row.get("conversation_id", "")),
                "source_file": str(row.get("source_file", "")),
                "customer": str(row.get("_customer", "Unknown")),
                "start_time": str(row.get("start_time", "")),
                "end_time": str(row.get("end_time", "")),
                "total_messages": _to_int(row.get("total_messages")),
                "client_messages_count": _to_int(row.get("client_messages_count")),
                "admin_messages_count": _to_int(row.get("admin_messages_count")),
                "has_media": str(row.get("has_media", "")).strip().lower() in ["true", "1"],
                "contains_credentials": str(row.get("contains_credentials", "")).strip().lower() in ["true", "1"],
                "client_response": str(row.get("client_response", "")),
                "penanganan_remote": str(row.get("penanganan_remote", "")),
                "kategori_kendala_ground_truth": str(row.get("kategori_kendala_ground_truth", "")),
                "kategori_kendala_ml_predicted": str(row.get("kategori_kendala_ml_predicted", "")),
                "prediction_confidence": str(row.get("prediction_confidence", "")),
                "prediction_match": str(row.get("prediction_match", "")),
                "full_conversation": str(row.get("full_conversation", "")),
            })

        return {
            "session_id": dataset["session_id"],
            "dataset": dataset,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": records,
        }

