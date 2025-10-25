from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union, Literal

from pydantic import BaseModel, ConfigDict, Field


EVENT_SCHEMA_VERSION = "1.0.0"


class StageKind(str, Enum):
    PLANNING = "planning"
    RETRIEVAL = "retrieval"
    ARTIFACTS = "artifacts"
    GENERATION = "generation"
    METRICS = "metrics"
    REPORTING = "reporting"
    FINALIZE = "finalize"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProgressSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: int = 0
    total: Optional[int] = None
    unit: Optional[str] = None
    failed: Optional[int] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

    def fraction(self) -> Optional[float]:
        if self.total in (None, 0):
            return None
        return min(1.0, max(0.0, self.completed / self.total))


class MetricDatasetScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["metric-dataset"] = "metric-dataset"
    metric: str
    mode: str
    dataset_id: str


class GenerationDatasetScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["generation-dataset"] = "generation-dataset"
    dataset_id: str


class RetrievalScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["retrieval"] = "retrieval"
    dataset_path: Optional[str] = None


DatasetScope = Union[MetricDatasetScope, GenerationDatasetScope, RetrievalScope]


class RunLifecycle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["run.lifecycle"] = "run.lifecycle"
    status: Literal["queued", "started", "succeeded", "failed", "cancelled"]
    plan_only: Optional[bool] = None
    from_resume: Optional[bool] = None
    seed_from: Optional[str] = None
    retry_failed_only: Optional[bool] = None
    run_uri: Optional[str] = None
    minio_prefix: Optional[str] = None
    stage: Optional[StageKind] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StageLifecycle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["stage.lifecycle"] = "stage.lifecycle"
    stage: StageKind
    status: StageStatus
    detail: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StageProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["stage.progress"] = "stage.progress"
    stage: StageKind
    progress: ProgressSnapshot
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DatasetProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["dataset.progress"] = "dataset.progress"
    stage: StageKind
    scope: DatasetScope
    progress: ProgressSnapshot
    status: Optional[StageStatus] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["artifact.event"] = "artifact.event"
    action: str
    path: Optional[str] = None
    uri: Optional[str] = None
    detail: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SystemMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["system.message"] = "system.message"
    level: str = Field(default="info")
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


RunEventPayload = Union[
    RunLifecycle,
    StageLifecycle,
    StageProgress,
    DatasetProgress,
    ArtifactEvent,
    SystemMessage,
]


class RunEventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=EVENT_SCHEMA_VERSION)
    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_id: str
    source: str = Field(default="run-executor")
    payload: RunEventPayload


__all__ = [
    "EVENT_SCHEMA_VERSION",
    "StageKind",
    "StageStatus",
    "ProgressSnapshot",
    "DatasetScope",
    "MetricDatasetScope",
    "GenerationDatasetScope",
    "RetrievalScope",
    "RunLifecycle",
    "StageLifecycle",
    "StageProgress",
    "DatasetProgress",
    "ArtifactEvent",
    "SystemMessage",
    "RunEventPayload",
    "RunEventEnvelope",
]
