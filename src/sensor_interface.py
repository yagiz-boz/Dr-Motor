"""Source-independent access to validated sensor records."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from .data_manager import SensorRecord, read_csv


class SensorSource(ABC):
    """Contract for CSV and future hardware adapters.

    Each call starts an independent read. Implementations yield validated
    SensorRecord objects, preserve sample identity and order, and propagate
    validation/I/O errors rather than substituting measurements. Finite sources
    end normally; hardware sources must document their stopping policy.
    """

    @abstractmethod
    def read_records(self) -> Iterator[SensorRecord]:
        """Return an iterator of records; never return dictionaries or ADC counts."""
        raise NotImplementedError

    def __iter__(self) -> Iterator[SensorRecord]:
        return self.read_records()


class CsvSensorSource(SensorSource):
    """Read a version-1 CSV using the existing data manager's validation.

    Construction does not access the file. Each read loads and validates the
    whole file before returning an iterator, so a corrupt recording cannot
    yield a valid-looking prefix. Rows retain file order; no timing simulation,
    interpolation, sorting, filtering, or hardware access is performed.
    """

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def read_records(self) -> Iterator[SensorRecord]:
        return iter(read_csv(self.path))
