from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Mapping

import pandas as pd

from fin68.exceptions import DataDecodingError, HttpError

from ..http_core import HttpSession
from ..progress import finish_progress, start_progress, update_progress

Namespace = str
Operation = str


def _strict_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


class InvestorCoreImpl:
    """
    Pure-Python investor bridge.  It forwards validated requests coming from the
    public client to the corresponding private API endpoints and materialises
    the JSON payloads as ``pandas.DataFrame`` objects.
    """

    _NAMESPACE_OPS: Mapping[Namespace, set[Operation]] = {
        "stock": {"flow", "breakdown", "foreign_room"},
        "market": {"flow", "breakdown"},
        "sector": {"flow", "breakdown", "foreign_room"},
    }

    _ID_FIELD: Mapping[Namespace, str] = {
        "stock": "symbol",
        "market": "symbol",
        "sector": "icb",
    }

    def __init__(self, session: HttpSession) -> None:
        self.session = session

    def fetch_df(self, namespace: Namespace, op: Operation, params: dict[str, Any]) -> pd.DataFrame:
        namespace = namespace.lower()
        if namespace not in self._NAMESPACE_OPS:
            raise ValueError(f"Unsupported investor namespace: {namespace!r}")

        op = op.lower()
        allowed_ops = self._NAMESPACE_OPS[namespace]
        if op not in allowed_ops:
            raise ValueError(
                f"Operation {op!r} is not available for namespace {namespace!r}. "
                f"Allowed operations: {sorted(allowed_ops)}."
            )

        endpoint = f"/market-data/investor/{namespace}/{op}"
        payload = self._prepare_payload(params)
   
        ids = payload.get("ids")
        if isinstance(ids, list) and len(ids) > 1:
            records: list[dict[str, Any]] = []
            start_progress(len(ids), f"{namespace}:{op}")
            try:
                for index, item_id in enumerate(ids, start=1):
                    single_payload = dict(payload)
                    single_payload["ids"] = [item_id]
                    raw = self._request(endpoint, single_payload)
                    records.extend(self._normalise_records(raw, namespace))
                    update_progress(index)
                    
            finally:
                finish_progress()
        else:
            raw = self._request(endpoint, payload)
            records = self._normalise_records(raw, namespace)
        
        frame = self._to_dataframe(records, namespace)
 
        interval = payload.get("interval", "1D")
        if isinstance(interval, str) and interval.upper() != "1D":
            frame = self._resample_frame(frame, namespace, interval.upper())
          
        return frame

    def _prepare_payload(self, params: dict[str, Any]) -> dict[str, Any]:
        payload = {key: value for key, value in params.items() if value is not None}

        ids = payload.get("ids")
        if ids is not None:
            if isinstance(ids, (list, tuple)):
                normalized_ids = [str(value).strip() for value in ids if str(value).strip()]
            else:
                normalized_ids = [str(ids).strip()]
            payload["ids"] = normalized_ids

        group = payload.get("group")
        if group is not None:
            group_str = str(group).strip().lower()
            if group_str:
                payload["group"] = group_str

        interval = payload.get("interval")
        if interval is not None:
            interval_str = str(interval).strip().upper()
            if interval_str:
                payload["interval"] = interval_str

        for key in ("start", "end"):
            value = payload.get(key)
            if isinstance(value, datetime):
                payload[key] = value.date().isoformat()
            elif isinstance(value, date):
                payload[key] = value.isoformat()
            elif value is not None:
                payload[key] = str(value).strip()

        return payload

    def _request(self, endpoint: str, payload: dict[str, Any]) -> Any:
        try:
            response = self.session.post(endpoint, json_body=payload)
        except HttpError as exc:
            if exc.status_code not in {404, 405}:
                raise
            query = self._to_query_params(payload)
            response = self.session.get(endpoint, params=query)
        return response.json()

    def _to_query_params(self, payload: dict[str, Any]) -> dict[str, Any]:
        query: dict[str, Any] = {}
        for key, value in payload.items():
            if key == "ids":
                if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                    value = ",".join(str(v).strip() for v in value if str(v).strip())
            query[key] = value
        return query

    def _resample_frame(self, frame: pd.DataFrame, namespace: Namespace, interval: str) -> pd.DataFrame:
        if frame.empty:
            return frame

        date_column = next((name for name in ("date", "Date") if name in frame.columns), None)
        if not date_column:
            return frame

        working = frame.dropna(subset=[date_column])
        if working.empty:
            return frame

        working = working.copy()
        working[date_column] = pd.to_datetime(working[date_column], errors="coerce")
        working = working.dropna(subset=[date_column])
        if working.empty:
            return frame

        preferred_field = self._ID_FIELD.get(namespace)
        candidate_fields: tuple[str, ...] = tuple(
            field for field in (preferred_field, "symbol", "icb", "code", "ticker") if field
        )
        id_field: str | None = next((field for field in candidate_fields if field in working.columns), None)

        if id_field is not None:
            working[id_field] = working[id_field].apply(_strict_str)
            working = working[working[id_field] != ""]

        numeric_cols = [
            column
            for column in working.select_dtypes(include="number").columns.tolist()
            if column != id_field
        ]
        if not numeric_cols:
            return frame

        group_iter: Iterable[tuple[Any, pd.DataFrame]]
        if id_field:
            group_iter = working.groupby(id_field, group_keys=False)
        else:
            group_iter = [(None, working)]

        aggregated_frames: list[pd.DataFrame] = []
        for group_key, group_df in group_iter:
            resampled = (
                group_df.set_index(date_column)[numeric_cols]
                .resample(interval)
                .sum(min_count=1)
            )
            if resampled.empty:
                continue

            resampled.index.name = date_column
            resampled = resampled.reset_index()

            if id_field and group_key is not None:
                resampled[id_field] = _strict_str(group_key)

            preserved_cols = [
                col
                for col in group_df.columns
                if col not in numeric_cols and col not in (date_column, id_field)
            ]
            for column in preserved_cols:
                resampled[column] = group_df[column].iloc[0]

            aggregated_frames.append(resampled)

        if not aggregated_frames:
            return frame

        combined = pd.concat(aggregated_frames, ignore_index=True)

        sort_columns: list[str] = []
        if id_field and id_field in combined.columns:
            sort_columns.append(id_field)
        if date_column in combined.columns:
            sort_columns.append(date_column)

        if sort_columns:
            combined = combined.sort_values(sort_columns).reset_index(drop=True)

        return combined

    def _normalise_records(self, payload: Any, namespace: Namespace) -> list[dict[str, Any]]:
        if payload is None:
            return []

        if isinstance(payload, list):
            return [self._ensure_mapping(item, namespace) for item in payload]

        if isinstance(payload, Mapping):
            for key in ("data", "results", "items", "records"):
                if key in payload:
                    return self._normalise_records(payload[key], namespace)

            if all(isinstance(value, list) for value in payload.values()):
                extracted: list[dict[str, Any]] = []
                for identifier, entries in payload.items():
                    for item in entries:
                        extracted.append(self._ensure_mapping(item, namespace, identifier))
                return extracted

        raise DataDecodingError("Unexpected payload format for investor endpoint.")

    def _ensure_mapping(
        self,
        entry: Any,
        namespace: Namespace,
        identifier: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(entry, Mapping):
            raise DataDecodingError("Investor payload entries must be JSON objects.")

        data = dict(entry)
        if identifier is not None:
            field = self._ID_FIELD.get(namespace, "id")
            if field not in data:
                data[field] = identifier
        return data

    def _to_dataframe(self, rows: list[dict[str, Any]], namespace: Namespace) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()

        frame = pd.DataFrame.from_records(rows)
        for column in ("date", "Date", "trade_date", "timestamp"):
            if column in frame.columns:
                if column == "timestamp" and pd.api.types.is_numeric_dtype(frame[column]):
                    frame[column] = pd.to_datetime(frame[column], unit="s", errors="coerce")
                else:
                    frame[column] = pd.to_datetime(frame[column], errors="coerce")

        sort_columns: list[str] = []
        id_field = self._ID_FIELD.get(namespace)
        if id_field and id_field in frame.columns:
            sort_columns.append(id_field)
        if "date" in frame.columns:
            sort_columns.append("date")
        elif "Date" in frame.columns:
            sort_columns.append("Date")

        if sort_columns:
            frame = frame.sort_values(sort_columns).reset_index(drop=True)

        return frame
