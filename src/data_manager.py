"""Validated, source-independent sensor records and lossless CSV storage.

One row represents one channel sample. Timestamps must include a UTC offset.
Only Python's standard library is required.
"""

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = "1"
FIELDS = (
    "schema_version", "motor_id", "session_id", "label", "channel", "unit",
    "timestamp", "sample_index", "sample_rate_hz", "value",
)
CHANNEL_UNITS = {
    "acceleration_x": "m/s^2",
    "acceleration_y": "m/s^2",
    "acceleration_z": "m/s^2",
    "current": "A",
    "acoustic": "FS",
    "temperature": "degC",
}
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DataValidationError(ValueError):
    """A record or CSV file does not satisfy the data contract."""


@dataclass(frozen=True)
class SensorRecord:
    motor_id: str
    session_id: str
    label: str
    channel: str
    unit: str
    timestamp: datetime
    sample_index: int
    sample_rate_hz: float
    value: float
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        for name in ("motor_id", "session_id", "label"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise DataValidationError(f"{name}: a non-empty string is required")
        if self.schema_version != SCHEMA_VERSION:
            raise DataValidationError("schema_version: unsupported version")
        if not isinstance(self.channel, str) or self.channel not in CHANNEL_UNITS:
            raise DataValidationError(f"channel: expected one of {tuple(CHANNEL_UNITS)}")
        if self.unit != CHANNEL_UNITS[self.channel]:
            raise DataValidationError(f"unit: {self.channel} requires {CHANNEL_UNITS[self.channel]}")
        if (not isinstance(self.timestamp, datetime)
                or self.timestamp.utcoffset() is None):
            raise DataValidationError("timestamp: timezone-aware datetime required")
        if type(self.sample_index) is not int or self.sample_index < 0:
            raise DataValidationError("sample_index: non-negative integer required")
        for name in ("sample_rate_hz", "value"):
            value = getattr(self, name)
            try:
                finite = type(value) in (int, float) and math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise DataValidationError(f"{name}: finite number required")
        if self.sample_rate_hz <= 0:
            raise DataValidationError("sample_rate_hz: must be positive")
        if self.channel == "acoustic" and not -1 <= self.value <= 1:
            raise DataValidationError("value: acoustic FS must be between -1 and 1")


def ensure_data_directories(root: Path | str = PROJECT_ROOT) -> dict[str, Path]:
    """Create and return raw/processed directories under an explicit project root."""
    paths = {kind: Path(root) / "data" / kind for kind in ("raw", "processed")}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _validate_batch(records: Iterable[SensorRecord]) -> list[SensorRecord]:
    result = list(records)
    if not result:
        raise DataValidationError("records: at least one sample is required")
    streams = {}
    sessions = {}
    for number, record in enumerate(result, start=1):
        if not isinstance(record, SensorRecord):
            raise DataValidationError(f"record {number}: SensorRecord required")
        record.__post_init__()
        session_key = (record.motor_id, record.session_id)
        if session_key in sessions and sessions[session_key] != record.label:
            raise DataValidationError(f"record {number}: session label changed")
        sessions[session_key] = record.label
        key = (*session_key, record.channel)
        previous = streams.get(key)
        if previous is not None:
            if record.sample_index <= previous.sample_index:
                raise DataValidationError(f"record {number}: duplicate or decreasing sample_index")
            if record.timestamp <= previous.timestamp:
                raise DataValidationError(f"record {number}: timestamp must increase within a channel")
            if record.sample_rate_hz != previous.sample_rate_hz:
                raise DataValidationError(f"record {number}: sample rate changed within a stream")
        streams[key] = record
    return result


def write_csv(path: Path | str, records: Iterable[SensorRecord]) -> Path:
    """Write a new CSV; validate first and never overwrite an existing file."""
    records = _validate_batch(records)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            row = {name: getattr(record, name) for name in FIELDS}
            row["timestamp"] = record.timestamp.isoformat()
            writer.writerow(row)
    return path


def read_csv(path: Path | str) -> list[SensorRecord]:
    """Read and validate a complete CSV, reporting physical line numbers."""
    records = []
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != list(FIELDS):
            raise DataValidationError(f"CSV header: expected {','.join(FIELDS)}")
        try:
            for row in reader:
                try:
                    if None in row or any(value is None for value in row.values()):
                        raise ValueError("wrong number of columns")
                    records.append(SensorRecord(
                        **{name: row[name] for name in (
                            "schema_version", "motor_id", "session_id", "label", "channel", "unit")},
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        sample_index=int(row["sample_index"]),
                        sample_rate_hz=float(row["sample_rate_hz"]),
                        value=float(row["value"]),
                    ))
                except (ValueError, TypeError) as error:
                    raise DataValidationError(f"CSV line {reader.line_num}: {error}") from error
        except csv.Error as error:
            raise DataValidationError(f"CSV line {reader.line_num}: {error}") from error
    return _validate_batch(records)
