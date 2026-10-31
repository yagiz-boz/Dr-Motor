import unittest
from dataclasses import replace
from datetime import datetime, timezone

from src.anomaly_detector import AnomalyDetector, DetectionResult
from src.data_manager import SensorRecord
from src.model_manager import FeatureVector, ModelManager
from src.motor_profile import ChannelConfig, ContractError, ModelSpec, MotorProfile


class MotorContractTests(unittest.TestCase):
    def setUp(self):
        self.spec = ModelSpec("baseline", "1", ("current_rms", "temperature_mean"), "1")
        self.profile = MotorProfile(
            "dc-profile", "motor-01", "DC",
            (ChannelConfig("current", "A", 1000), ChannelConfig("temperature", "degC", 1)),
            self.spec,
        )
        self.record = SensorRecord(
            "motor-01", "session-01", "unlabeled", "current", "A",
            datetime(2026, 10, 31, tzinfo=timezone.utc), 0, 1000, 0.25,
        )

    def test_profile_accepts_both_configured_sampling_rates(self):
        self.profile.validate_record(self.record)
        self.profile.validate_record(replace(
            self.record, channel="temperature", unit="degC", sample_rate_hz=1))

    def test_profile_rejects_other_motor_channel_or_rate(self):
        for changes in ({"motor_id": "motor-02"}, {"sample_rate_hz": 500},
                        {"channel": "acoustic", "unit": "FS"}):
            with self.subTest(changes=changes), self.assertRaises(ContractError):
                self.profile.validate_record(replace(self.record, **changes))

    def test_profile_can_exist_without_a_model(self):
        self.assertIsNone(replace(self.profile, model_spec=None).model_spec)

    def test_invalid_channel_config(self):
        for args in (("unknown", "A", 1), ("current", "mA", 1000),
                     ("current", "A", 0), ("current", "A", float("nan")),
                     ("current", "A", True)):
            with self.subTest(args=args), self.assertRaises(ContractError):
                ChannelConfig(*args)

    def test_invalid_profiles(self):
        for changes in ({"motor_id": " "}, {"channels": ()},
                        {"channels": (self.profile.channels[0],) * 2},
                        {"channels": ("current",)}, {"model_spec": "fake"}):
            with self.subTest(changes=changes), self.assertRaises(ContractError):
                replace(self.profile, **changes)

    def test_invalid_model_metadata(self):
        for changes in ({"version": ""}, {"preprocessing_version": ""},
                        {"feature_names": ()}, {"feature_names": ("rms", "rms")},
                        {"feature_names": ["rms"]}, {"feature_names": ("",)}):
            with self.subTest(changes=changes), self.assertRaises(ContractError):
                replace(self.spec, **changes)

    def test_mapping_order_is_canonicalized(self):
        vector = FeatureVector.from_mapping(
            self.spec, {"temperature_mean": 25, "current_rms": 0.2})
        self.assertEqual(vector.values, (0.2, 25))

    def test_feature_keys_count_and_values_are_checked(self):
        for mapping in ({"current_rms": 0.2},
                        {"current_rms": 0.2, "temperature_mean": 25, "extra": 1},
                        {"current_rms": float("inf"), "temperature_mean": 25}):
            with self.subTest(mapping=mapping), self.assertRaises(ContractError):
                FeatureVector.from_mapping(self.spec, mapping)
        with self.assertRaises(ContractError):
            FeatureVector(self.spec, (0.2,))

    def test_unavailable_outcomes_have_no_diagnosis(self):
        for status in ("model_unavailable", "insufficient_data"):
            result = DetectionResult(status, "Not ready")
            self.assertIsNone(result.anomaly_score)
            self.assertIsNone(result.is_anomaly)
            with self.assertRaises(ContractError):
                replace(result, is_anomaly=False)
            with self.assertRaises(ContractError):
                replace(result, anomaly_score=0)

    def test_success_requires_real_model_metadata_score_and_decision(self):
        result = DetectionResult("ok", "Threshold evaluated", self.spec, 2.5, True)
        self.assertTrue(result.is_anomaly)
        for changes in ({"model_spec": None}, {"anomaly_score": None},
                        {"anomaly_score": float("nan")}, {"is_anomaly": None},
                        {"status": "healthy"}, {"reason": ""}):
            with self.subTest(changes=changes), self.assertRaises(ContractError):
                replace(result, **changes)

    def test_no_fake_manager_or_detector_can_be_instantiated(self):
        for interface in (ModelManager, AnomalyDetector):
            with self.subTest(interface=interface), self.assertRaises(TypeError):
                interface()


if __name__ == "__main__":
    unittest.main()
