from __future__ import annotations

"""
Helpers for describing how a suite specification should be supplied.
"""

from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, model_validator

from .sdk import InlineSuite, SuiteSpec


class SuiteInput(BaseModel):
    """
    Wrapper around the different ways callers can target a suite.

    Exactly one of ``uri``, ``path`` or ``inline`` must be provided.
    """

    uri: Optional[str] = None
    path: Optional[Path] = None
    inline: Optional[InlineSuite] = None

    @model_validator(mode="after")
    def _ensure_source(self) -> "SuiteInput":
        if not any([self.uri, self.path, self.inline]):
            raise ValueError("SuiteInput requires uri, path, or inline content")
        if self.path is not None:
            self.path = Path(self.path).expanduser().resolve()
        return self

    @classmethod
    def from_value(cls, value: Union["SuiteInput", Path, str, InlineSuite]) -> "SuiteInput":
        if isinstance(value, SuiteInput):
            return value
        if isinstance(value, InlineSuite):
            return cls(inline=value)
        if isinstance(value, Path):
            return cls(path=value)
        if str(value).startswith(("file://", "minio://")):
            return cls(uri=str(value))
        return cls(path=Path(value))

    def to_suite_spec(self) -> SuiteSpec:
        return SuiteSpec(uri=self.uri, path=self.path, inline=self.inline)


__all__ = ["SuiteInput"]
