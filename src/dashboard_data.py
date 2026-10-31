"""Dashboard adapters; processing remains independent of Streamlit."""

import tempfile
from pathlib import Path

from .data_manager import SensorRecord
from .motor_profile import ChannelConfig, ContractError, MotorProfile
from .sensor_interface import CsvSensorSource


def read_upload(content: bytes) -> list[SensorRecord]:
    """Validate an upload through the shared source; remove the temporary copy."""
    with tempfile.TemporaryDirectory(prefix="dr-motor-") as directory:
        path = Path(directory) / "upload.csv"
        path.write_bytes(content)
        return list(CsvSensorSource(path))


def recording_profile(records: list[SensorRecord], motor_type: str) -> MotorProfile:
    """Describe one motor/session from its recording, not hardware verification."""
    if not records:
        raise ContractError("Profil oluşturmak için ölçüm gerekli.")
    first = records[0]
    if any((r.motor_id, r.session_id) != (first.motor_id, first.session_id) for r in records):
        raise ContractError("Profil için tek motor ve tek oturum seçilmeli.")
    configs = {}
    for record in records:
        config = ChannelConfig(record.channel, record.unit, record.sample_rate_hz)
        if record.channel in configs and configs[record.channel] != config:
            raise ContractError("Oturum içinde kanal ayarları değişiyor.")
        configs[record.channel] = config
    profile = MotorProfile(
        f"recording:{first.motor_id}:{first.session_id}", first.motor_id,
        motor_type, tuple(configs.values()),
    )
    for record in records:
        profile.validate_record(record)
    return profile
