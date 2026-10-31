import csv
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.data_manager import (
    CHANNEL_UNITS, FIELDS, DataValidationError, SensorRecord,
    ensure_data_directories, read_csv, write_csv,
)


class DataManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "recording.csv"
        self.record = SensorRecord(
            motor_id="motor-01", session_id="session-01", label="unlabeled",
            channel="current", unit="A", timestamp=datetime(2026, 10, 31, tzinfo=timezone.utc),
            sample_index=0, sample_rate_hz=1000, value=0.25,
        )

    def test_round_trip_multiple_channels_and_csv_escaping(self):
        records = [replace(self.record, channel=channel, unit=unit,
                           motor_id='Motor, "özel"', value=0.25)
                   for channel, unit in CHANNEL_UNITS.items()]
        records.append(replace(self.record, motor_id='Motor, "özel"', sample_index=1,
                               timestamp=self.record.timestamp + timedelta(milliseconds=1)))
        write_csv(self.path, iter(records))
        self.assertEqual(read_csv(self.path), records)

    def test_invalid_fields(self):
        for changes in (
            {"motor_id": " "}, {"session_id": ""}, {"label": ""},
            {"channel": "unknown"}, {"unit": "mA"},
            {"timestamp": datetime(2026, 10, 31)}, {"sample_index": -1},
            {"sample_index": True}, {"sample_rate_hz": 0},
            {"sample_rate_hz": float("inf")}, {"value": float("nan")},
            {"value": True}, {"schema_version": "2"},
            {"channel": "acoustic", "unit": "FS", "value": 2},
        ):
            with self.subTest(changes=changes), self.assertRaises(DataValidationError):
                replace(self.record, **changes)

    def test_no_overwrite(self):
        self.path.write_text("original", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            write_csv(self.path, [self.record])
        self.assertEqual(self.path.read_text(encoding="utf-8"), "original")

    def test_invalid_batch_creates_no_file(self):
        for records in ([], [self.record, self.record], [object()],
                        [self.record, replace(self.record, sample_index=1)],
                        [self.record, replace(self.record, label="healthy")]):
            with self.subTest(records=records), self.assertRaises(DataValidationError):
                write_csv(self.path, records)
            self.assertFalse(self.path.exists())

    def test_rate_change_rejected_but_index_gaps_preserved(self):
        later = replace(self.record, sample_index=2,
                        timestamp=self.record.timestamp + timedelta(milliseconds=2))
        with self.assertRaises(DataValidationError):
            write_csv(self.path, [self.record, replace(later, sample_rate_hz=500)])
        write_csv(self.path, [self.record, later])
        self.assertEqual(read_csv(self.path)[1].sample_index, 2)

    def test_missing_extra_and_duplicate_headers(self):
        for fields in (FIELDS[:-1], (*FIELDS, "extra"), (*FIELDS[:-1], "unit")):
            with self.subTest(fields=fields):
                self.path.write_text(",".join(fields) + "\n", encoding="utf-8")
                with self.assertRaisesRegex(DataValidationError, "header"):
                    read_csv(self.path)

    def test_bad_csv_value_reports_line(self):
        write_csv(self.path, [self.record])
        content = self.path.read_text(encoding="utf-8").replace(",0.25", ",nan")
        self.path.write_text(content, encoding="utf-8")
        with self.assertRaisesRegex(DataValidationError, "CSV line 2.*finite"):
            read_csv(self.path)

    def test_truncated_row(self):
        self.path.write_text(",".join(FIELDS) + "\n1,motor\n", encoding="utf-8")
        with self.assertRaisesRegex(DataValidationError, "CSV line 2"):
            read_csv(self.path)

    def test_duplicate_samples_in_external_csv(self):
        write_csv(self.path, [self.record])
        with self.path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        with self.path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerows([*rows, rows[1]])
        with self.assertRaisesRegex(DataValidationError, "duplicate"):
            read_csv(self.path)

    def test_empty_csv_and_header_only(self):
        for content in ("", ",".join(FIELDS) + "\n"):
            self.path.write_text(content, encoding="utf-8")
            with self.assertRaises(DataValidationError):
                read_csv(self.path)

    def test_data_directories(self):
        for _ in range(2):
            paths = ensure_data_directories(self.root)
            self.assertTrue(paths["raw"].is_dir())
            self.assertTrue(paths["processed"].is_dir())


if __name__ == "__main__":
    unittest.main()
