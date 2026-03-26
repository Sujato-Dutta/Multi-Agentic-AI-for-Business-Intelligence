"""Data ingestion agent — loads CSV, REST API (JSON/XML/CSV), or demo datasets."""

import io
import json
import logging
from typing import Any

import pandas as pd
import requests as http_requests

from utils.demo_data import get_demo_dataset

logger = logging.getLogger(__name__)


class DataIngestionAgent:
    """Ingests data from CSV uploads, REST APIs, or built-in demo datasets."""

    def run(self, *, source: str, file_bytes: bytes | None = None,
            rest_url: str | None = None, rest_headers: str | None = None,
            rest_params: str | None = None, demo_name: str | None = None) -> dict[str, Any]:
        logger.info("DataIngestionAgent: source=%s", source)

        if source == "csv" and file_bytes:
            df = self._load_csv(file_bytes)
        elif source == "rest" and rest_url:
            df = self._load_rest(rest_url, rest_headers, rest_params)
        elif source == "demo" and demo_name:
            df = get_demo_dataset(demo_name)
        else:
            raise ValueError(f"Invalid source '{source}' or missing required fields")

        # Basic cleaning
        df = self._clean_dataframe(df)

        metadata = {
            "source": source,
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": {c: str(d) for c, d in df.dtypes.items()},
        }
        logger.info("Ingested %d rows, %d columns", metadata["rows"], len(metadata["columns"]))
        return {"dataframe": df, "metadata": metadata}

    def _load_csv(self, file_bytes: bytes) -> pd.DataFrame:
        """Load CSV or Excel file from raw bytes."""
        buf = io.BytesIO(file_bytes)
        try:
            return pd.read_csv(buf)
        except Exception:
            buf.seek(0)
            try:
                return pd.read_excel(buf)
            except Exception:
                buf.seek(0)
                # Try tab-separated
                return pd.read_csv(buf, sep="\t")

    def _load_rest(self, url: str, headers_json: str | None, params_json: str | None) -> pd.DataFrame:
        """Load data from REST API — supports JSON, XML, and CSV responses."""
        headers = json.loads(headers_json) if headers_json else {}
        params = json.loads(params_json) if params_json else {}

        resp = http_requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").lower()

        # 1. JSON response
        if "json" in content_type or self._looks_like_json(resp.text):
            return self._parse_json_response(resp.text)

        # 2. XML response
        if "xml" in content_type or resp.text.strip().startswith("<?xml") or resp.text.strip().startswith("<"):
            return self._parse_xml_response(resp.text)

        # 3. CSV / TSV response
        if "csv" in content_type or "text/plain" in content_type or "tab-separated" in content_type:
            return self._parse_csv_response(resp.text)

        # 4. Fallback — try JSON first, then CSV
        try:
            return self._parse_json_response(resp.text)
        except Exception:
            try:
                return self._parse_csv_response(resp.text)
            except Exception:
                raise ValueError(
                    f"Cannot parse REST response. Content-Type: '{content_type}'. "
                    f"Supported formats: JSON, XML, CSV/TSV. "
                    f"First 200 chars: {resp.text[:200]}"
                )

    def _parse_json_response(self, text: str) -> pd.DataFrame:
        """Parse JSON response — handles arrays, nested objects, and paginated responses."""
        data = json.loads(text)

        # Direct array of records
        if isinstance(data, list):
            return self._flatten_to_df(data)

        # Dict with known wrapper keys
        if isinstance(data, dict):
            # Check common wrapper keys
            for key in ("data", "results", "items", "records", "rows",
                        "entries", "response", "values", "hits", "documents"):
                if key in data and isinstance(data[key], list):
                    return self._flatten_to_df(data[key])

            # Nested dict: e.g. {"hits": {"hits": [...]}}
            for key, val in data.items():
                if isinstance(val, dict):
                    for subkey in ("data", "results", "items", "hits"):
                        if subkey in val and isinstance(val[subkey], list):
                            return self._flatten_to_df(val[subkey])

            # Single record
            return pd.DataFrame([data])

        raise ValueError("JSON response is not a recognized structure")

    def _parse_xml_response(self, text: str) -> pd.DataFrame:
        """Parse XML response into DataFrame."""
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(text)
            records = []

            # Try to find repeating child elements
            children = list(root)
            if not children:
                raise ValueError("XML has no child elements")

            # All children with the same tag = rows
            tag_counts: dict[str, int] = {}
            for child in children:
                tag_counts[child.tag] = tag_counts.get(child.tag, 0) + 1

            # Most frequent tag is likely the row element
            row_tag = max(tag_counts, key=tag_counts.get)  # type: ignore

            for elem in root.findall(row_tag):
                record: dict[str, str] = {}
                # Attributes
                record.update(elem.attrib)
                # Child text elements
                for child in elem:
                    record[child.tag] = child.text or ""
                if record:
                    records.append(record)

            if not records:
                raise ValueError("No records found in XML")

            return pd.DataFrame(records)
        except Exception as e:
            raise ValueError(f"Failed to parse XML: {e}")

    def _parse_csv_response(self, text: str) -> pd.DataFrame:
        """Parse CSV/TSV text response."""
        buf = io.StringIO(text)
        try:
            df = pd.read_csv(buf)
            if len(df.columns) <= 1:
                buf.seek(0)
                df = pd.read_csv(buf, sep="\t")
            return df
        except Exception:
            buf.seek(0)
            return pd.read_csv(buf, sep="\t")

    def _flatten_to_df(self, records: list) -> pd.DataFrame:
        """Convert list of records to DataFrame, flattening nested dicts one level."""
        flattened = []
        for record in records:
            if isinstance(record, dict):
                flat: dict[str, Any] = {}
                for key, val in record.items():
                    if isinstance(val, dict):
                        for subkey, subval in val.items():
                            flat[f"{key}_{subkey}"] = subval
                    elif isinstance(val, list):
                        flat[key] = str(val)  # Store as string
                    else:
                        flat[key] = val
                flattened.append(flat)
            else:
                flattened.append({"value": record})
        return pd.DataFrame(flattened)

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic cleaning: strip whitespace from headers, coerce numeric columns."""
        # Strip whitespace from column names
        df.columns = [str(c).strip() for c in df.columns]

        # Drop fully empty rows/columns
        df = df.dropna(how="all", axis=0)
        df = df.dropna(how="all", axis=1)

        # Try to coerce object columns to numeric where possible
        for col in df.select_dtypes(include=["object"]).columns:
            try:
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().mean() > 0.7:  # >70% parseable
                    df[col] = converted
            except Exception:
                pass

        return df

    def _looks_like_json(self, text: str) -> bool:
        """Quick heuristic check if text looks like JSON."""
        stripped = text.strip()
        return stripped.startswith("{") or stripped.startswith("[")
