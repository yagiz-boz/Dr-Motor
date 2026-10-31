"""Inference contracts and explicit unavailable-data/model outcomes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from .model_manager import FeatureVector
from .motor_profile import ContractError, ModelSpec, require_number, require_text


@dataclass(frozen=True)
class DetectionResult:
    status: Literal["ok", "model_unavailable", "insufficient_data"]
    reason: str
    model_spec: ModelSpec | None = None
    anomaly_score: float | None = None
    is_anomaly: bool | None = None

    def __post_init__(self):
        require_text("reason", self.reason)
        if self.model_spec is not None and not isinstance(self.model_spec, ModelSpec):
            raise ContractError("model_spec: ModelSpec or None required")
        if self.status == "ok":
            if self.model_spec is None or type(self.is_anomaly) is not bool:
                raise ContractError("ok result requires model metadata and a boolean decision")
            require_number("anomaly_score", self.anomaly_score)
        elif self.status in ("model_unavailable", "insufficient_data"):
            if self.anomaly_score is not None or self.is_anomaly is not None:
                raise ContractError("unavailable results cannot contain a diagnosis or score")
        else:
            raise ContractError("status: unsupported detection status")


class AnomalyDetector(ABC):
    """Future trained detector interface, with no placeholder diagnosis.

    Implementations must reject incompatible feature/model specs. Scores must
    increase with anomaly strength; their scale and decision threshold must be
    documented by the eventual model. A score is not a probability or health score.
    """

    @abstractmethod
    def predict(self, features: FeatureVector) -> DetectionResult:
        raise NotImplementedError
