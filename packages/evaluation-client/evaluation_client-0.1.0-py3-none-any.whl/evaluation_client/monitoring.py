from __future__ import annotations

"""
Utilities for streaming run progress.

The monitor is separated from the core client so applications can replace it
with their own reporting layer if desired.
"""

import logging
from pathlib import Path
from typing import Callable, Iterable, Literal, Optional, Tuple

from chatbot_eval_common.events import DatasetProgress, RunEventEnvelope, RunLifecycle, StageLifecycle, StageStatus

from .sdk import RunJobHandle, RunJobStatus

LogLevel = Literal["quiet", "normal", "verbose"]
VERBOSITY_ORDER = {"quiet": 0, "normal": 1, "verbose": 2}


def monitor_job(
    *,
    job: RunJobHandle,
    suite_label: Optional[str],
    stream_events: Callable[[str], Iterable[Tuple[str, object]]],
    get_status: Callable[[str], RunJobStatus],
    on_complete: Optional[Callable[[RunJobStatus], None]],
    log_level: LogLevel,
    logger: logging.Logger,
) -> RunJobStatus:
    """
    Stream run events using Rich if available, falling back to log output otherwise.

    Parameters
    ----------
    job:
        The job handle returned by the API.
    suite_label:
        Human-readable identifier for the suite; used for logging/console display.
    stream_events:
        Callable that yields ``(event_type, payload)`` tuples until completion.
    get_status:
        Callable that fetches the final job status if it is not emitted by the event stream.
    on_complete:
        Optional callback executed after a terminal status is observed.
    log_level:
        Controls console verbosity (``quiet`` suppresses stage/dataset logs).
    logger:
        Logger instance used for debug messages.
    """

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
            TimeElapsedColumn,
        )
    except ImportError:  # pragma: no cover
        return _monitor_without_rich(
            job=job,
            suite_label=suite_label,
            stream_events=stream_events,
            get_status=get_status,
            on_complete=on_complete,
            log_level=log_level,
            logger=logger,
        )

    verbosity = VERBOSITY_ORDER.get(log_level, 1)

    console = Console()

    def should_log(required: Literal["quiet", "normal", "verbose"]) -> bool:
        return verbosity >= VERBOSITY_ORDER[required]

    label = suite_label or job.suite_uri
    if label and should_log("normal"):
        console.print(Panel.fit(label, title="Evaluation", border_style="cyan"))

    stage_tasks: dict[str, int] = {}
    dataset_tasks: dict[tuple[str, str], int] = {}
    final_status: Optional[RunJobStatus] = None

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
        refresh_per_second=8,
    )

    def stage_label(stage: StageLifecycle) -> str:
        return stage.stage.value.replace("_", " ").title()

    def dataset_label(scope) -> str:
        if hasattr(scope, "metric"):
            return f"metric/{scope.metric}[{scope.mode}]/{scope.dataset_id}"
        if hasattr(scope, "dataset_id"):
            return f"generation/{scope.dataset_id}"
        path = getattr(scope, "dataset_path", None) or "default"
        return f"retrieval/{Path(path).name if path else 'default'}"

    def ensure_stage_task(stage: StageLifecycle) -> int:
        key = stage.stage.value
        if key in stage_tasks:
            return stage_tasks[key]
        task_id = progress.add_task(stage_label(stage), total=1, start=False)
        stage_tasks[key] = task_id
        progress.start_task(task_id)
        return task_id

    def mark_task_complete(task_id: int) -> None:
        task = progress.tasks[task_id]
        total = task.total or task.completed or 1
        progress.update(task_id, total=total, completed=total)

    with progress:
        for event_type, payload in stream_events(job.job_id):
            if event_type == "run-event" and isinstance(payload, RunEventEnvelope):
                body = payload.payload
                if isinstance(body, RunLifecycle):
                    logger.debug("run_event", extra={"type": body.type, "status": body.status})
                    if should_log("normal"):
                        console.log(
                            f"[run] {body.status}"
                            + (f" (stage={body.stage.value})" if body.stage else "")
                        )
                elif isinstance(body, StageLifecycle):
                    task_id = ensure_stage_task(body)
                    if body.status == StageStatus.RUNNING:
                        if should_log("normal"):
                            console.log(f"[stage] {stage_label(body)} started")
                    elif body.status in {StageStatus.SUCCEEDED, StageStatus.SKIPPED}:
                        mark_task_complete(task_id)
                        if should_log("normal"):
                            console.log(f"[stage] {stage_label(body)} {body.status.value}")
                    elif body.status == StageStatus.FAILED:
                        mark_task_complete(task_id)
                        if should_log("normal"):
                            console.log(
                                f"[stage] {stage_label(body)} failed: {body.detail or body.metadata.get('error')}"
                            )
                elif isinstance(body, DatasetProgress) and should_log("verbose"):
                    scope_text = dataset_label(body.scope)
                    dataset_key = (body.scope.__class__.__name__, scope_text)
                    completed = body.progress.completed or 0
                    total = body.progress.total
                    task_id = dataset_tasks.get(dataset_key)
                    if task_id is None:
                        task_id = progress.add_task(
                            f"[dataset] {scope_text}",
                            total=total or (completed if completed else None),
                        )
                        dataset_tasks[dataset_key] = task_id
                        console.log(f"[dataset] {scope_text} started")
                    else:
                        task = progress.tasks[task_id]
                        if total and not task.total:
                            progress.update(task_id, total=float(total))
                    progress.update(task_id, completed=completed)
                    if body.status in {StageStatus.SUCCEEDED, StageStatus.SKIPPED, StageStatus.FAILED}:
                        mark_task_complete(task_id)
                        if body.status == StageStatus.FAILED:
                            console.log(f"[dataset] {scope_text} failed: {body.metadata.get('error')}")
                        else:
                            console.log(f"[dataset] {scope_text} {body.status.value}")
            elif event_type == "job-status" and isinstance(payload, RunJobStatus):
                final_status = payload
                break

    if final_status is None:
        final_status = get_status(job.job_id)

    if should_log("normal"):
        console.rule("[bold cyan]Run Summary")
        run_state = final_status.run_state.model_dump() if final_status.run_state else {}
        console.print(
            f"[success] status={run_state.get('state') or final_status.status} "
            f"run_dir={final_status.run_dir}"
        )

    if on_complete is not None:
        on_complete(final_status)

    return final_status


def _monitor_without_rich(
    *,
    job: RunJobHandle,
    suite_label: Optional[str],
    stream_events: Callable[[str], Iterable[Tuple[str, object]]],
    get_status: Callable[[str], RunJobStatus],
    on_complete: Optional[Callable[[RunJobStatus], None]],
    log_level: LogLevel,
    logger: logging.Logger,
) -> RunJobStatus:
    verbosity = VERBOSITY_ORDER.get(log_level, 1)

    final_status: Optional[RunJobStatus] = None
    for event_type, payload in stream_events(job.job_id):
        if event_type == "run-event" and isinstance(payload, RunEventEnvelope):
            body = payload.payload
            if isinstance(body, RunLifecycle) and verbosity >= VERBOSITY_ORDER["normal"]:
                logger.info("run_event status=%s stage=%s", body.status, getattr(body.stage, "value", None))
            elif isinstance(body, StageLifecycle) and verbosity >= VERBOSITY_ORDER["normal"]:
                logger.info(
                    "stage %s -> %s",
                    body.stage.value,
                    body.status.value,
                )
            elif isinstance(body, DatasetProgress) and verbosity >= VERBOSITY_ORDER["verbose"]:
                logger.info(
                    "dataset scope=%s status=%s %s/%s",
                    payload.payload.scope,
                    payload.payload.status,
                    payload.payload.progress.completed,
                    payload.payload.progress.total or "?",
                )
        elif event_type == "job-status" and isinstance(payload, RunJobStatus):
            final_status = payload
            break

    if final_status is None:
        final_status = get_status(job.job_id)

    label = suite_label or job.suite_uri
    if label and verbosity >= VERBOSITY_ORDER["normal"]:
        logger.info("suite=%s", label)
    logger.info("run summary status=%s run_dir=%s", final_status.status, final_status.run_dir)

    if on_complete is not None:
        on_complete(final_status)

    return final_status


__all__ = ["monitor_job", "LogLevel"]
