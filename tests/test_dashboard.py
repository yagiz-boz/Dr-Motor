import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

from src.dashboard_data import read_upload, recording_profile
from src.data_manager import DataValidationError, SensorRecord, write_csv
from src.motor_profile import ContractError

ROOT = Path(__file__).resolve().parents[1]


class DashboardDataTests(unittest.TestCase):
    def setUp(self):
        self.record = SensorRecord("motor-01", "session-01", "unlabeled", "current", "A",
                                   datetime(2026, 10, 31, tzinfo=timezone.utc), 0, 1000, 0.25)

    def test_upload_roundtrip_through_shared_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_csv(Path(directory) / "test.csv", [self.record])
            self.assertEqual(read_upload(path.read_bytes()), [self.record])

    def test_upload_invalid_content(self):
        with self.assertRaises(DataValidationError):
            read_upload(b"invalid\n")
        with self.assertRaises(UnicodeError):
            read_upload(b"\xff\xff")

    def test_profile_from_recording(self):
        profile = recording_profile([self.record], "Belirtilmedi")
        self.assertEqual(profile.motor_id, self.record.motor_id)
        self.assertIsNone(profile.model_spec)
        profile.validate_record(self.record)
        with self.assertRaises(ContractError):
            recording_profile([], "DC")


@unittest.skipIf(AppTest is None, "Install requirements for dashboard tests")
class DashboardUITests(unittest.TestCase):
    def test_empty_state_and_navigation(self):
        app = AppTest.from_file(str(ROOT / "dashboard" / "app.py")).run()
        self.assertFalse(app.exception)
        self.assertIn("Model henüz yok", app.info[0].value)
        for page in ("Sensör ölçümleri", "Motor profili", "Kayıt geçmişi"):
            app.sidebar.radio[0].set_value(page).run()
            self.assertFalse(app.exception)

    def test_all_pages_with_valid_recording(self):
        from datetime import timedelta
        from dataclasses import replace
        first = SensorRecord("motor-01", "session-01", "unlabeled", "current", "A",
                             datetime(2026, 10, 31, tzinfo=timezone.utc), 0, 1000, 0.25)
        records = [first, replace(first, sample_index=2,
                   timestamp=first.timestamp + timedelta(milliseconds=2))]
        with tempfile.TemporaryDirectory() as directory:
            path = write_csv(Path(directory) / "test.csv", records)
            app = AppTest.from_file(str(ROOT / "dashboard" / "app.py")).run()
            # Exercise upload parsing without persisting fixtures in data/raw.
            class Upload:
                size = path.stat().st_size
                def getvalue(self):
                    return path.read_bytes()
            with patch("streamlit.file_uploader", return_value=Upload()):
                app.run()
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value, "2")
                for page in ("Sensör ölçümleri", "Motor profili", "Kayıt geçmişi"):
                    app.sidebar.radio[0].set_value(page).run()
                    self.assertFalse(app.exception)
                    if page == "Sensör ölçümleri":
                        self.assertIn("kesinti", app.warning[0].value)

    def test_invalid_upload_shows_error(self):
        class BadUpload:
            size = 8
            def getvalue(self):
                return b"invalid\n"
        with patch("streamlit.file_uploader", return_value=BadUpload()):
            app = AppTest.from_file(str(ROOT / "dashboard" / "app.py")).run()
            self.assertFalse(app.exception)
            self.assertIn("Kayıt açılamadı", app.error[0].value)


if __name__ == "__main__":
    unittest.main()
