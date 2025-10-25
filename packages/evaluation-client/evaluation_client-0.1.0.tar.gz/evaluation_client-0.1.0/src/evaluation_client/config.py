from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ApiConfig(BaseModel):
    base_url: str
    token: Optional[str] = None
    timeout: Optional[float] = Field(default=None, ge=0)
    verify: bool = True


class LocalPaths(BaseModel):
    runs_root: Optional[Path] = None
    download_root: Optional[Path] = None

    @model_validator(mode="after")
    def _expand(self) -> "LocalPaths":
        if self.runs_root is not None:
            self.runs_root = self.runs_root.expanduser().resolve()
            if self.download_root is None:
                self.download_root = self.runs_root
        if self.download_root is not None:
            self.download_root = self.download_root.expanduser().resolve()
        return self


__all__ = [
    "ApiConfig",
    "LocalPaths",
]
