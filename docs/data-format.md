# Sensor data contract — version 1

Each CSV row is one channel sample, not a combined snapshot of all sensors.
Channels may run at different sampling rates. A missing channel is not replaced
with a zero. No sensor protocol or hardware calibration is implemented here.

| Column | Meaning |
| --- | --- |
| schema_version | Always `1` |
| motor_id | Non-empty motor identifier |
| session_id | Non-empty recording session identifier |
| label | Non-empty experiment label; use `unlabeled` until verified |
| channel | One channel from the table below |
| unit | Exact canonical unit for that channel |
| timestamp | ISO 8601 datetime with UTC offset; UTC is recommended |
| sample_index | Non-negative integer, increasing within a motor/session/channel |
| sample_rate_hz | Positive finite nominal channel sampling frequency |
| value | Finite numeric measurement in the declared unit |

| Channel | Unit | Meaning |
| --- | --- | --- |
| acceleration_x / acceleration_y / acceleration_z | m/s^2 | Calibrated acceleration per axis |
| current | A | Calibrated current |
| acoustic | FS | Audio amplitude normalized to full scale, between -1 and 1; not dB or calibrated sound pressure |
| temperature | degC | Temperature in Celsius |

Raw ADC counts must be converted by the future source adapter before entering
this contract. If the chosen microphone only supplies a level/envelope, define
a new versioned channel contract before using it; do not label it as audio samples.

CSV headers must appear exactly in the listed order. Files are written as UTF-8;
UTF-8 with BOM is also accepted on reading. Extra or missing columns, non-finite
numbers, unknown channels, wrong units and timezone-free timestamps are rejected.
The label is constant within a motor/session; start a new session when it changes.
Within a channel stream, indices and timestamps must increase and the nominal
sample rate must remain constant. Index gaps are allowed and preserved, not
interpolated. Actual timing jitter and cross-channel synchronization are not
validated by this module. No physical-range limits are inferred for unselected
hardware, apart from normalized acoustic amplitude.

`write_csv` validates the entire batch before creating a file and uses exclusive
creation: it never overwrites or appends to an existing recording. Use a new
filename for each export. Storage errors are propagated to the caller; an I/O
failure during writing can leave an incomplete file, which should not be used.
`read_csv` returns validated records and raises `DataValidationError` for invalid
data; parsing failures include a CSV line number. Missing files and permission
errors retain their normal Python exception types. Both APIs load the batch in
memory; streaming acquisition is a later step.

Store original normalized measurements under `data/raw/` and future derived
outputs under `data/processed/`. Measurement files are ignored by Git; only the
directory placeholders are tracked. No real measurements are included.

## Usage

Run from the repository root. This example only demonstrates storage; the value
is illustrative, not a motor experiment or spectrum simulation.

```python
from datetime import datetime, timezone
from src.data_manager import SensorRecord, ensure_data_directories, read_csv, write_csv

paths = ensure_data_directories()
record = SensorRecord(
    motor_id="motor-01", session_id="session-01", label="unlabeled",
    channel="current", unit="A", timestamp=datetime.now(timezone.utc),
    sample_index=0, sample_rate_hz=1000, value=0.25,
)
path = write_csv(paths["raw"] / "session-01.csv", [record])
records = read_csv(path)
assert records == [record]
```

The future CSV and UNO Q adapters will emit the same `SensorRecord` type.
ML and dashboard code can consume that type without depending on the source.
