import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.data_manager import DataValidationError, SensorRecord, write_csv
from src.sensor_interface import CsvSensorSource, SensorSource


class SensorInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "recording.csv"
        first = SensorRecord(
            motor_id="motor-01", session_id="session-01", label="unlabeled",
            channel="current", unit="A", timestamp=datetime(2026, 10, 31, tzinfo=timezone.utc),
            sample_index=0, sample_rate_hz=1000, value=0.25,
        )
        # A slower channel and a second current sample exercise mixed-channel order.
        self.records = [
            first, replace(first, channel="temperature", unit="degC",
                           sample_rate_hz=1, value=25),
            replace(first, sample_index=1, value=0.3,
                    timestamp=first.timestamp + timedelta(milliseconds=1)),
        ]

    def test_csv_preserves_values_identity_and_file_order(self):
        write_csv(self.path, self.records)
        source = CsvSensorSource(str(self.path))
        self.assertIsInstance(source, SensorSource)
        self.assertEqual(list(source.read_records()), self.records)
        self.assertEqual(list(source), self.records)

    def test_independent_reads_do_not_share_cursor(self):
        write_csv(self.path, self.records)
        source = CsvSensorSource(self.path)
        first, second = source.read_records(), source.read_records()
        self.assertEqual(next(first), self.records[0])
        self.assertEqual(list(second), self.records)
        self.assertEqual(list(first), self.records[1:])
        self.assertEqual(list(source), self.records)

    def test_missing_file_errors_on_read_not_construction(self):
        source = CsvSensorSource(self.path)
        with self.assertRaises(FileNotFoundError):
            source.read_records()

    def test_invalid_later_row_rejected_before_any_records_returned(self):
        write_csv(self.path, self.records)
        content = self.path.read_text(encoding="utf-8").replace(",0.3", ",nan")
        self.path.write_text(content, encoding="utf-8")
        with self.assertRaisesRegex(DataValidationError, "CSV line 4"):
            CsvSensorSource(self.path).read_records()

    def test_read_reloads_file_and_does_not_modify_it(self):
        write_csv(self.path, self.records)
        source = CsvSensorSource(self.path)
        before = self.path.read_bytes()
        list(source)
        self.assertEqual(self.path.read_bytes(), before)
        self.path.write_text("invalid header\n", encoding="utf-8")
        with self.assertRaises(DataValidationError):
            list(source)

    def test_empty_file_does_not_silently_end_stream(self):
        self.path.write_text("", encoding="utf-8")
        with self.assertRaises(DataValidationError):
            list(CsvSensorSource(self.path))

    def test_consumer_accepts_an_alternative_source(self):
        records = self.records

        class InMemorySource(SensorSource):
            def read_records(self):
                return iter(records)

        def collect(source: SensorSource):
            return [(record.channel, record.value) for record in source]

        write_csv(self.path, records)
        self.assertEqual(collect(CsvSensorSource(self.path)), collect(InMemorySource()))

    def test_base_contract_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            SensorSource()


if __name__ == "__main__":
    unittest.main()
