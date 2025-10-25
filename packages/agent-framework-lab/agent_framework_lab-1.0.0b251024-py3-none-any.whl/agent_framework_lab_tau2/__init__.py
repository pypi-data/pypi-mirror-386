# Copyright (c) Microsoft. All rights reserved.

"""Tau2 Benchmark for Agent Framework."""

import importlib.metadata

from ._tau2_utils import patch_env_set_state, unpatch_env_set_state
from .runner import ASSISTANT_AGENT_ID, ORCHESTRATOR_ID, USER_SIMULATOR_ID, TaskRunner

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

__all__ = [
    "ASSISTANT_AGENT_ID",
    "ORCHESTRATOR_ID",
    "USER_SIMULATOR_ID",
    "TaskRunner",
    "patch_env_set_state",
    "unpatch_env_set_state",
]
