"""Option schemas for router strategies."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Sequence

from pydantic import BaseModel, Field, ValidationError, model_validator


class DirectRouterOptions(BaseModel):
    """Options for the direct router."""

    default_backend: str = Field(..., min_length=1)
    allow_unknown: bool = False


class WeightedBackendConfig(BaseModel):
    """Configuration entry for a weighted backend."""

    backend_id: str = Field(..., min_length=1)
    weight: float = Field(..., gt=0.0)
    capacity: Optional[int] = Field(default=None, ge=1)


class WeightedRouterOptions(BaseModel):
    """Options for weighted routing."""

    backends: List[WeightedBackendConfig]
    seed: Optional[int] = None

    @model_validator(mode="after")
    def _validate(self) -> "WeightedRouterOptions":
        total_weight = sum(backend.weight for backend in self.backends)
        if not self.backends:
            msg = "Weighted router requires at least one backend"
            raise ValueError(msg)
        if total_weight <= 0:
            msg = "Weighted router total weight must be positive"
            raise ValueError(msg)
        backend_ids = {backend.backend_id for backend in self.backends}
        if len(backend_ids) != len(self.backends):
            msg = "Weighted router backends must be unique"
            raise ValueError(msg)
        return self


class FailoverRouterOptions(BaseModel):
    """Options for failover routing."""

    primary: str = Field(..., min_length=1)
    fallbacks: List[str] = Field(default_factory=list)
    recheck_interval_s: float = Field(default=10.0, ge=0.0)

    @property
    def ordered_backends(self) -> List[str]:
        """Primary backend followed by fallbacks."""
        return [self.primary, *self.fallbacks]


PredicateSource = Literal["tags", "metadata", "parameters"]
PredicateOperator = Literal["eq", "in", "gte", "lte", "regex"]


class RulePredicate(BaseModel):
    """Single predicate used by the rules router."""

    source: PredicateSource
    operator: PredicateOperator
    key: Optional[str] = None
    value: Any

    @model_validator(mode="after")
    def _validate_key(self) -> "RulePredicate":
        if self.source == "tags" and self.key:
            msg = "Tags predicates do not accept a key"
            raise ValueError(msg)
        if self.source in {"metadata", "parameters"} and not self.key:
            msg = f"{self.source} predicates require a key"
            raise ValueError(msg)
        return self


class RuleConfig(BaseModel):
    """A single routing rule definition."""

    backend: str = Field(..., min_length=1)
    predicates: Sequence[RulePredicate] = Field(default_factory=list)
    rule_id: Optional[str] = None


class RulesRouterOptions(BaseModel):
    """Configuration for metadata-driven routing."""

    rules: List[RuleConfig] = Field(default_factory=list)
    default_backend: Optional[str] = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _ensure_non_empty(self) -> "RulesRouterOptions":
        if not self.rules and not self.default_backend:
            msg = "Rules router requires at least one rule or a default backend"
            raise ValueError(msg)
        return self


def parse_options(model: type[BaseModel], payload: Dict[str, Any] | BaseModel | None) -> BaseModel:
    """Utility to normalise router option payloads."""
    if payload is None:
        return model()
    if isinstance(payload, model):
        return payload
    if isinstance(payload, BaseModel):
        return model.model_validate(payload.model_dump())
    if isinstance(payload, dict):
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
    msg = f"Unsupported router configuration payload: {type(payload)!r}"
    raise TypeError(msg)
