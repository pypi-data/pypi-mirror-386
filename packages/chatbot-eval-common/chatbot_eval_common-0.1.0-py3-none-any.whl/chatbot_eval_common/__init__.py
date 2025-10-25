from __future__ import annotations

"""
Public exports for the chatbot_eval_common package.
"""

from importlib import metadata as _metadata

from .events import (
    EVENT_SCHEMA_VERSION,
    ArtifactEvent,
    DatasetProgress,
    DatasetScope,
    GenerationDatasetScope,
    MetricDatasetScope,
    ProgressSnapshot,
    RetrievalScope,
    RunEventEnvelope,
    RunEventPayload,
    RunLifecycle,
    StageKind,
    StageLifecycle,
    StageProgress,
    StageStatus,
    SystemMessage,
)

try:
    __version__ = _metadata.version("chatbot-eval-common")
except Exception:  # pragma: no cover - fallback for local edits
    __version__ = "0.0.0"

__all__ = [
    "EVENT_SCHEMA_VERSION",
    "ArtifactEvent",
    "DatasetProgress",
    "DatasetScope",
    "GenerationDatasetScope",
    "MetricDatasetScope",
    "ProgressSnapshot",
    "RetrievalScope",
    "RunEventEnvelope",
    "RunEventPayload",
    "RunLifecycle",
    "StageKind",
    "StageLifecycle",
    "StageProgress",
    "StageStatus",
    "SystemMessage",
    "__version__",
]
