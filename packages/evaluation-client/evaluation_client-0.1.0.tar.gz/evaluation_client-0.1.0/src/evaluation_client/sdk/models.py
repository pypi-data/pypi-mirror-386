from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from chatbot_eval_common.events import RunEventEnvelope


class InlineSuite(BaseModel):
    content: str
    filename: Optional[str] = None


class SuiteSpec(BaseModel):
    uri: Optional[str] = None
    path: Optional[Path] = None
    inline: Optional[InlineSuite] = None

    @model_validator(mode="after")
    def _ensure_source(self) -> "SuiteSpec":
        if not any([self.uri, self.path, self.inline]):
            raise ValueError("Suite specification requires uri, path, or inline content")
        if self.path is not None:
            self.path = self.path.expanduser().resolve()
        return self

    @property
    def label(self) -> str:
        if self.path is not None:
            return str(self.path)
        if self.uri is not None:
            return self.uri
        if self.inline is not None:
            return self.inline.filename or "<inline suite>"
        return "<suite>"


class DatasetUploadSpec(BaseModel):
    dataset_id: str
    path: Path

    @model_validator(mode="after")
    def _expand(self) -> "DatasetUploadSpec":
        self.path = self.path.expanduser().resolve()
        return self


class PromptUploadSpec(BaseModel):
    prompt_id: str
    instruction_path: Path
    resource_files: Dict[str, Path] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _expand(self) -> "PromptUploadSpec":
        self.instruction_path = self.instruction_path.expanduser().resolve()
        self.resource_files = {
            name: Path(path).expanduser().resolve() for name, path in self.resource_files.items()
        }
        if not self.resource_files:
            raise ValueError("PromptUploadSpec requires at least one resource file.")
        return self


class AppPromptSpec(BaseModel):
    prompt_id: str
    path: Path

    @model_validator(mode="after")
    def _expand(self) -> "AppPromptSpec":
        self.path = self.path.expanduser().resolve()
        return self


class RetrievalBundleSpec(BaseModel):
    bundle_id: str
    path: Path

    @model_validator(mode="after")
    def _expand(self) -> "RetrievalBundleSpec":
        self.path = self.path.expanduser().resolve()
        return self


class JudgeUploadSpec(BaseModel):
    judge_id: str
    path: Path
    kind: str = "llm"

    @model_validator(mode="after")
    def _expand(self) -> "JudgeUploadSpec":
        self.path = self.path.expanduser().resolve()
        return self


class EvaluationSpec(BaseModel):
    suite: SuiteSpec
    datasets: List[DatasetUploadSpec] = Field(default_factory=list)
    prompts: List[PromptUploadSpec] = Field(default_factory=list)
    app_prompts: List[AppPromptSpec] = Field(default_factory=list)
    retrieval_bundles: List[RetrievalBundleSpec] = Field(default_factory=list)
    judges: List[JudgeUploadSpec] = Field(default_factory=list)
    resume_dir: Optional[Union[Path, str]] = None
    seed_from: Optional[Union[Path, str]] = None
    plan_only: bool = False
    retry_failed_only: bool = False

    def _resolve_optional_path(self, value: Optional[Union[Path, str]]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, Path):
            return str(value.expanduser().resolve())
        return value

    def to_run_request(self, *, suite_uri_override: Optional[str] = None) -> RunRequest:
        resume_dir = self._resolve_optional_path(self.resume_dir)
        seed_from = self._resolve_optional_path(self.seed_from)
        return RunRequest(
            suite_uri=suite_uri_override or self.suite.uri,
            suite_path=None if suite_uri_override else self.suite.path,
            suite_inline=self.suite.inline,
            resume_dir=resume_dir,
            seed_from=seed_from,
            plan_only=self.plan_only,
            retry_failed_only=self.retry_failed_only,
        )

class RunRequest(BaseModel):
    suite_uri: Optional[str] = None
    suite_path: Optional[Path] = None
    suite_inline: Optional[InlineSuite] = None
    resume_dir: Optional[str] = None
    seed_from: Optional[str] = None
    plan_only: bool = False
    retry_failed_only: bool = False

    @model_validator(mode="after")
    def validate_source(self) -> "RunRequest":
        sources = [self.suite_uri, self.suite_path, self.suite_inline]
        if not any(sources):
            raise ValueError("Provide suite_uri, suite_path, or suite_inline")
        return self


class RunJobHandle(BaseModel):
    job_id: str
    suite_uri: str
    status: str
    run_dir: Optional[str] = None
    status_url: Optional[str] = None
    events_url: Optional[str] = None
    result_url: Optional[str] = None


class RunStateDataset(BaseModel):
    scope: Dict[str, Any]
    progress: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class RunStateStage(BaseModel):
    status: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    detail: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    progress: Optional[Dict[str, Any]] = None
    datasets: Dict[str, RunStateDataset] = Field(default_factory=dict)


class RunStateSnapshot(BaseModel):
    run_id: str
    state: str
    current_stage: Optional[str] = None
    flags: Dict[str, Any] = Field(default_factory=dict)
    stages: Dict[str, RunStateStage] = Field(default_factory=dict)
    latest_event: Optional[Dict[str, Any]] = None
    updated_at: Optional[str] = None
    run_uri: Optional[str] = None
    minio_prefix: Optional[str] = None
    error: Optional[str] = None


class RunJobStatus(BaseModel):
    job_id: str
    status: str
    suite_uri: str
    run_dir: Optional[str] = None
    run_uri: Optional[str] = None
    minio_prefix: Optional[str] = None
    plan_only: Optional[bool] = None
    error: Optional[str] = None
    manifest_path: Optional[str] = None
    lock_path: Optional[str] = None
    aggregates_path: Optional[str] = None
    state: Optional[str] = None
    current_stage: Optional[str] = None
    run_state: Optional[RunStateSnapshot] = None

    @field_validator("run_state", mode="before")
    @classmethod
    def _coerce_state(cls, value):
        if value is None or isinstance(value, RunStateSnapshot):
            return value
        if isinstance(value, dict) and value:
            return RunStateSnapshot.model_validate(value)
        return None

    @property
    def is_terminal(self) -> bool:
        return self.status in {"succeeded", "failed"}


class RunHistoryEntry(BaseModel):
    run_dir: Path
    manifest_path: Optional[Path] = None
    aggregates_path: Optional[Path] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    state: Optional[str] = None
    current_stage: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunEvent(BaseModel):
    envelope: RunEventEnvelope

    @property
    def payload(self):
        return self.envelope.payload


class RunDirectoryStatus(BaseModel):
    run_dir: str
    status: RunStateSnapshot

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, value):
        if isinstance(value, RunStateSnapshot):
            return value
        if isinstance(value, dict):
            return RunStateSnapshot.model_validate(value)
        raise TypeError("status must be a mapping")


class RunEventsResponse(BaseModel):
    run_dir: str
    events: List[RunEventEnvelope]

    @field_validator("events", mode="before")
    @classmethod
    def _coerce_events(cls, value):
        events: List[RunEventEnvelope] = []
        for item in value or []:
            if isinstance(item, RunEventEnvelope):
                events.append(item)
            else:
                events.append(RunEventEnvelope.model_validate(item))
        return events
