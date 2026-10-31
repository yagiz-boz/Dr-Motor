# Sensor source interface

`src/sensor_interface.py` separates the source of measurements from consumers.
`SensorSource.read_records()` returns an iterator of validated `SensorRecord`
objects. A source also supports `for record in source` through the same method.
Consumer code should accept `SensorSource`, rather than open CSV files itself.

## CSV usage

From the repository root, with a CSV following [the data contract](data-format.md):

```python
from src.sensor_interface import CsvSensorSource, SensorSource

def count_samples(source: SensorSource) -> int:
    return sum(1 for record in source)

source = CsvSensorSource("data/raw/session-01.csv")
print(count_samples(source))

for record in source:
    print(record.timestamp, record.channel, record.value, record.unit)
```

The example expects an existing recording; no measurements are fabricated.

## Reading behavior

- Construction stores the path without touching the file. Relative paths resolve
  from the working directory when reading; an absolute path avoids ambiguity.
- Each read reopens and validates the entire CSV using `data_manager.read_csv`.
  A corrupt file fails before any samples are returned. The batch is held in
  memory, so this adapter is intended for recordings that fit available memory.
- Independent reads have separate iterators. Normal iterator exhaustion marks
  the end of a recording. A new read starts from the beginning.
- Original row order, timestamps, motor/session IDs, labels, sample indices and
  channel sampling rates are preserved. There is no real-time playback, sorting,
  resampling or filling of missing channels.
- Invalid/empty recordings raise `DataValidationError`. Missing files and other
  I/O failures propagate their original exceptions. Errors are not interpreted
  as an empty recording. The adapter does not write or modify files.

## Future UNO Q adapter

Implement `SensorSource.read_records()` in a separate adapter after verifying
the board's transport and sensor format. It must emit the same validated
`SensorRecord` objects, normalize units, preserve stream ordering rules, and
report communication failures explicitly. Connection ownership, timeouts,
stopping and reconnection behavior must be defined with the real hardware.
No UNO Q adapter, serial protocol, connection simulation or driver dependency
is included in this step. A consumer using `SensorSource` can later receive
that adapter without changing its record-processing logic.
