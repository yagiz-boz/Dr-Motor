"""Model loading contract and ordered features; no training or model loader yet."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass

from .motor_profile import ContractError, ModelSpec, MotorProfile, require_number


class ModelUnavailableError(RuntimeError):
    """No trained compatible model is available."""


@dataclass(frozen=True)
class FeatureVector:
    spec: ModelSpec
    values: tuple[float, ...]

    def __post_init__(self):
        if not isinstance(self.spec, ModelSpec):
            raise ContractError("spec: ModelSpec required")
        if not isinstance(self.values, tuple) or len(self.values) != len(self.spec.feature_names):
            raise ContractError("values: tuple must match the declared feature count")
        for name, value in zip(self.spec.feature_names, self.values):
            require_number(name, value)

    @classmethod
    def from_mapping(cls, spec: ModelSpec, features: Mapping[str, float]):
        """Require exact keys and order values according to the model spec."""
        if not isinstance(spec, ModelSpec):
            raise ContractError("spec: ModelSpec required")
        if not isinstance(features, Mapping):
            raise ContractError("features: mapping of feature names to numeric values required")
        if set(features) != set(spec.feature_names):
            raise ContractError("features: missing or unexpected feature names")
        return cls(spec, tuple(features[name] for name in spec.feature_names))


class ModelManager(ABC):
    """Future model registry: load a detector or raise ModelUnavailableError.

    A loader must check model identity, version, feature order and preprocessing
    version against the profile. No artifact deserialization is implemented here.
    """

    @abstractmethod
    def load(self, profile: MotorProfile) -> "AnomalyDetector":
        raise NotImplementedError


# Only imported for static typing to avoid a runtime circular dependency.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .anomaly_detector import AnomalyDetector
