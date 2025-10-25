from __future__ import annotations

import contextlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from chatbot_eval_common.events import RunEventEnvelope

from .http import ApiClient
from .models import (
    RunHistoryEntry,
    RunJobHandle,
    RunJobStatus,
    RunRequest,
    RunStateSnapshot,
    RunDirectoryStatus,
    RunEventsResponse,
)
from .streaming import EventStream


class RunClient:
    def __init__(self, api: ApiClient, *, default_poll_interval: float = 5.0) -> None:
        self._api = api
        self._poll_interval = default_poll_interval

    # ------------------------------------------------------------------ #
    # Submission & status
    # ------------------------------------------------------------------ #
    def submit(self, request: RunRequest) -> RunJobHandle:
        payload = {
            "resume_dir": request.resume_dir,
            "seed_from": request.seed_from,
            "plan_only": request.plan_only,
            "retry_failed_only": request.retry_failed_only,
        }
        if request.suite_uri:
            payload["suite_uri"] = request.suite_uri
        elif request.suite_path:
            payload["suite"] = {
                "content": request.suite_path.read_text(encoding="utf-8"),
                "filename": request.suite_path.name,
            }
        elif request.suite_inline:
            payload["suite"] = request.suite_inline.model_dump()

        response = self._api.json("POST", "/runs", json=payload)
        return RunJobHandle.model_validate(response)

    def get(self, job_id: str) -> RunJobStatus:
        response = self._api.json("GET", f"/runs/jobs/{job_id}")
        return RunJobStatus.model_validate(response)

    def wait_for_completion(
        self,
        job_id: str,
        *,
        poll_interval: Optional[float] = None,
        timeout: Optional[float] = None,
        callback: Optional[Callable[[RunJobStatus], None]] = None,
    ) -> RunJobStatus:
        interval = poll_interval or self._poll_interval
        start = time.monotonic()
        while True:
            status = self.get(job_id)
            if callback:
                callback(status)
            if status.is_terminal:
                return status
            if timeout is not None and (time.monotonic() - start) > timeout:
                raise TimeoutError(f"Run {job_id} did not finish within {timeout} seconds")
            time.sleep(interval)

    # ------------------------------------------------------------------ #
    # Streaming
    # ------------------------------------------------------------------ #
    def stream(self, job_id: str) -> EventStream:
        return EventStream(self._api, job_id)

    def stream_events(self, job_id: str) -> Iterable[RunEventEnvelope]:
        yield from self.stream(job_id).envelopes()

    # ------------------------------------------------------------------ #
    # Run directory helpers
    # ------------------------------------------------------------------ #
    def fetch_status_snapshot(self, run_dir: str) -> RunDirectoryStatus:
        response = self._api.json("GET", "/runs/status", params={"run_dir": run_dir})
        return RunDirectoryStatus.model_validate(response)

    def fetch_events(self, run_dir: str, *, tail: Optional[int] = None) -> RunEventsResponse:
        params: Dict[str, Any] = {"run_dir": run_dir}
        if tail is not None:
            params["tail"] = tail
        response = self._api.json("GET", "/runs/events", params=params)
        return RunEventsResponse.model_validate(response)

    # ------------------------------------------------------------------ #
    # Run history helpers
    # ------------------------------------------------------------------ #
    def list_local_runs(
        self,
        root: Path,
        *,
        limit: Optional[int] = None,
        after: Optional[datetime] = None,
    ) -> List[RunHistoryEntry]:
        repo = LocalRunRepository(root)
        return repo.list_runs(limit=limit, after=after)


class LocalRunRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def list_runs(
        self,
        *,
        limit: Optional[int] = None,
        after: Optional[datetime] = None,
    ) -> List[RunHistoryEntry]:
        if not self.root.exists():
            return []
        run_dirs = [
            path
            for path in self.root.iterdir()
            if path.is_dir()
        ]
        run_dirs.sort(reverse=True)
        entries: List[RunHistoryEntry] = []
        for run_dir in run_dirs:
            entry = self._build_entry(run_dir)
            if after and entry.started_at and entry.started_at <= after:
                continue
            entries.append(entry)
            if limit and len(entries) >= limit:
                break
        return entries

    def _build_entry(self, run_dir: Path) -> RunHistoryEntry:
        manifest_path = run_dir / "manifest.yaml"
        aggregates_path = run_dir / "aggregates.json"
        status_path = run_dir / "status.json"
        run_state: Optional[RunStateSnapshot] = None
        started_at: Optional[datetime] = None
        completed_at: Optional[datetime] = None
        state: Optional[str] = None
        current_stage: Optional[str] = None
        metadata: dict = {}

        if status_path.exists():
            try:
                data = json.loads(status_path.read_text(encoding="utf-8"))
                run_state = RunStateSnapshot.model_validate(data)
                state = run_state.state
                current_stage = run_state.current_stage
                metadata = run_state.flags or {}
                if run_state.updated_at:
                    with contextlib.suppress(Exception):
                        completed_at = datetime.fromisoformat(run_state.updated_at)
                run_stage = run_state.stages.get("planning")
                if run_stage and run_stage.started_at:
                    with contextlib.suppress(Exception):
                        started_at = datetime.fromisoformat(run_stage.started_at)
            except Exception:
                run_state = None

        return RunHistoryEntry(
            run_dir=run_dir,
            manifest_path=manifest_path if manifest_path.exists() else None,
            aggregates_path=aggregates_path if aggregates_path.exists() else None,
            started_at=started_at,
            completed_at=completed_at,
            state=state,
            current_stage=current_stage,
            metadata=metadata,
        )
