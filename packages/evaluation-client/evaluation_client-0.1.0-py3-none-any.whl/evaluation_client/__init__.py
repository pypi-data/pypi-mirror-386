from __future__ import annotations

"""
Public entrypoints for the evaluation client library.
"""

from importlib import metadata as _metadata

from .assets import AssetBundle, JudgeConfig, PromptFiles
from .config import ApiConfig, LocalPaths
from .evaluation_client import EvaluationClient
from .options import RunOptions
from .suite import SuiteInput

__all__ = [
    "EvaluationClient",
    "AssetBundle",
    "PromptFiles",
    "JudgeConfig",
    "SuiteInput",
    "RunOptions",
    "ApiConfig",
    "LocalPaths",
]

try:
    __version__ = _metadata.version("evaluation-client")
except Exception:  # pragma: no cover - fallback for local edits
    __version__ = "0.0.0"

__all__.append("__version__")
