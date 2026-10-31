# Motor profiles and model contracts

Step 4 defines configuration and input/output contracts. It does not train,
load or execute a model. No features, FFT, health score or diagnosis are computed.
All modules use Python's standard library.

## MotorProfile

`src/motor_profile.py` contains immutable configuration objects:

- `ChannelConfig`: canonical channel/unit and positive nominal sampling rate.
- `ModelSpec`: model identity, version, ordered feature names and preprocessing
  version. This is a compatibility declaration, not proof that a model exists.
- `MotorProfile`: profile ID, physical motor ID, motor type, unique configured
  channels and optional model specification. A profile can exist before training.

The channel names/units are shared with [the sensor data contract](data-format.md).
No hardware sampling rates are assumed: callers supply verified settings.
`validate_record` checks a sensor record's motor, configured channel, unit and
sampling rate. It does not check whole-window completeness or synchronization.
Version 1 of this profile is a Python API; JSON persistence is not implemented.

```python
from src.motor_profile import ChannelConfig, MotorProfile
from src.sensor_interface import CsvSensorSource

# Illustrative configuration only; use the actual recording's settings.
profile = MotorProfile(
    profile_id="dc-demo", motor_id="motor-01", motor_type="DC",
    channels=(ChannelConfig("current", "A", 1000),),
)
for record in CsvSensorSource("data/raw/session-01.csv"):
    profile.validate_record(record)
```

## Model inputs

`src/model_manager.py` defines `FeatureVector` and the abstract
`ModelManager.load(profile)` interface. The eventual loader must raise
`ModelUnavailableError` if no compatible trained model exists. No serialization
format, artifact loader or training implementation is included.

`FeatureVector` holds a `ModelSpec` and a tuple of finite numeric values.
`from_mapping` requires exactly the declared feature keys and orders values by
`ModelSpec.feature_names`, regardless of dictionary insertion order. It rejects
missing/extra features instead of filling zeros. Feature extraction and window
sufficiency checks will be implemented later.

```python
from src.model_manager import FeatureVector
from src.motor_profile import ModelSpec

# These names and values illustrate the contract, not extracted measurements.
spec = ModelSpec("baseline", "1", ("current_rms", "temperature_mean"), "1")
vector = FeatureVector.from_mapping(
    spec, {"temperature_mean": 25, "current_rms": 0.2}
)
assert vector.values == (0.2, 25)
```

## Model outputs and unavailable states

`src/anomaly_detector.py` defines abstract `AnomalyDetector.predict(features)`
and validated `DetectionResult` objects:

| Status | Meaning | Score / decision |
| --- | --- | --- |
| ok | A trained compatible model evaluated the features | Finite score, boolean decision and ModelSpec required |
| model_unavailable | No compatible trained model is available | Both must be None |
| insufficient_data | Required data/features cannot yet be produced | Both must be None |

All outcomes require an explanatory reason. Invalid configurations raise
`ContractError`; they must not be converted into a healthy diagnosis.
The application may translate `ModelUnavailableError` into a `model_unavailable`
result. No automatic orchestration is implemented at this stage.

The future detector must compare the full feature spec (identity, model version,
feature order and preprocessing version) to its loaded model and reject mismatch.
Successful outputs carry that same spec for traceability. Runtime model matching
will be tested when a real loader/detector exists; the abstract classes cannot
be instantiated and make no prediction by default.

Anomaly scores must increase with anomaly strength, but their range and threshold
are model-specific and must be documented during training. Scores are not
probabilities, confidence percentages or Motor Health Scores. Classification,
calibrated confidence, Motor Passport storage and model training are later steps.
