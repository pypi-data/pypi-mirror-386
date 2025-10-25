from __future__ import annotations

import json
from typing import Any, Iterable, Iterator, Tuple

from chatbot_eval_common.events import RunEventEnvelope

from .http import ApiClient
from .models import RunJobStatus


class EventStream:
    def __init__(self, client: ApiClient, job_id: str) -> None:
        self._client = client
        self._job_id = job_id

    def raw(self) -> Iterable[Tuple[str, str]]:
        yield from self._client.stream(f"/runs/jobs/{self._job_id}/events/stream")

    def envelopes(self) -> Iterator[RunEventEnvelope]:
        for event_type, payload in self.raw():
            if event_type != "run-event":
                continue
            try:
                yield RunEventEnvelope.model_validate_json(payload)
            except Exception:
                continue

    def with_status(self) -> Iterator[Tuple[str, Any]]:
        for event_type, payload in self.raw():
            if event_type == "run-event":
                try:
                    yield event_type, RunEventEnvelope.model_validate_json(payload)
                except Exception:
                    yield event_type, payload
            elif event_type == "job-status":
                try:
                    yield event_type, RunJobStatus.model_validate_json(payload)
                except Exception:
                    yield event_type, payload
            else:
                yield event_type, payload
