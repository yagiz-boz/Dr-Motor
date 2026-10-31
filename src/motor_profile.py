"""Motor configuration and model compatibility, without hardware assumptions."""

from dataclasses import dataclass
import math

from .data_manager import CHANNEL_UNITS, SensorRecord


class ContractError(ValueError):
    """Configuration or model data violates the shared contract."""


def require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name}: non-empty text required")


def require_number(name: str, value: float) -> None:
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ContractError(f"{name}: finite number required")


@dataclass(frozen=True)
class ChannelConfig:
    channel: str
    unit: str
    sample_rate_hz: float

    def __post_init__(self):
        require_text("channel", self.channel)
        if self.channel not in CHANNEL_UNITS or self.unit != CHANNEL_UNITS[self.channel]:
            raise ContractError("channel/unit: unsupported combination")
        require_number("sample_rate_hz", self.sample_rate_hz)
        if self.sample_rate_hz <= 0:
            raise ContractError("sample_rate_hz: must be positive")


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    version: str
    feature_names: tuple[str, ...]
    preprocessing_version: str

    def __post_init__(self):
        for name in ("model_id", "version", "preprocessing_version"):
            require_text(name, getattr(self, name))
        if not isinstance(self.feature_names, tuple) or not self.feature_names:
            raise ContractError("feature_names: non-empty tuple required")
        for name in self.feature_names:
            require_text("feature_name", name)
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ContractError("feature_names: duplicates are not allowed")


@dataclass(frozen=True)
class MotorProfile:
    profile_id: str
    motor_id: str
    motor_type: str
    channels: tuple[ChannelConfig, ...]
    model_spec: ModelSpec | None = None

    def __post_init__(self):
        for name in ("profile_id", "motor_id", "motor_type"):
            require_text(name, getattr(self, name))
        if not isinstance(self.channels, tuple) or not self.channels:
            raise ContractError("channels: non-empty tuple required")
        if any(not isinstance(channel, ChannelConfig) for channel in self.channels):
            raise ContractError("channels: ChannelConfig entries required")
        if len({channel.channel for channel in self.channels}) != len(self.channels):
            raise ContractError("channels: duplicate channels are not allowed")
        if self.model_spec is not None and not isinstance(self.model_spec, ModelSpec):
            raise ContractError("model_spec: ModelSpec or None required")

    def validate_record(self, record: SensorRecord) -> None:
        """Check one record; window completeness belongs to later processing."""
        if not isinstance(record, SensorRecord):
            raise ContractError("record: SensorRecord required")
        record.__post_init__()
        if record.motor_id != self.motor_id:
            raise ContractError("motor_id: record belongs to another motor")
        config = next((item for item in self.channels if item.channel == record.channel), None)
        if config is None:
            raise ContractError("channel: absent from motor profile")
        if (record.unit, record.sample_rate_hz) != (config.unit, config.sample_rate_hz):
            raise ContractError("record unit/sample rate does not match motor profile")
