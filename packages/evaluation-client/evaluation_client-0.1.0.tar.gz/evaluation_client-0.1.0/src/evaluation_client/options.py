from __future__ import annotations

"""
User-configurable switches for orchestration helpers.

RunOptions is intentionally lightweight so it can be forwarded directly from
command-line parsing or higher-level application code.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, model_validator


class RunOptions(BaseModel):
    """Optional parameters that influence how a suite is executed."""

    monitor: bool = True
    download_results: bool = True
    log_level: Literal["quiet", "normal", "verbose"] = "normal"
    download_root: Optional[Path] = None
    resume_dir: Optional[Path] = None
    seed_from: Optional[Path] = None
    plan_only: bool = False
    retry_failed_only: bool = False

    @model_validator(mode="after")
    def _expand(self) -> "RunOptions":
        if self.download_root is not None:
            self.download_root = Path(self.download_root).expanduser().resolve()
        if self.resume_dir is not None:
            self.resume_dir = Path(self.resume_dir).expanduser().resolve()
        if self.seed_from is not None:
            self.seed_from = Path(self.seed_from).expanduser().resolve()
        return self


__all__ = ["RunOptions"]
