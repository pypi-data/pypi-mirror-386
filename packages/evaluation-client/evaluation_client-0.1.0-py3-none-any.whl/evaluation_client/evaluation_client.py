from __future__ import annotations

"""
High-level orchestration client for the evaluation API.

The EvaluationClient composes the lower-level SDK clients with convenience
helpers that upload artefacts, submit suites, monitor execution, and retrieve
results. It intentionally avoids hard-coded configuration so applications stay
in control of all runtime parameters.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, Literal, Optional, Union

from .assets import AssetBundle
from .config import ApiConfig, LocalPaths
from .monitoring import LogLevel, monitor_job
from .options import RunOptions
from .suite import SuiteInput
from .sdk import (
    ApiClient,
    ApiError,
    ArtifactClient,
    EventStream,
    RunClient,
    RunEventEnvelope,
    RunHistoryEntry,
    RunJobHandle,
    RunJobStatus,
    RunRequest,
    DatasetUploadSpec,
    EvaluationSpec,
    RunDirectoryStatus,
    RunEventsResponse,
)

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 1.0


class EvaluationClient:
    """Facade around the API, artefact, and run clients."""

    def __init__(
        self,
        *,
        api_client: ApiClient,
        artifact_client: Optional[ArtifactClient] = None,
        run_client: Optional[RunClient] = None,
        runs_root: Optional[Path] = None,
        download_root: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.api = api_client
        self.artifacts = artifact_client or ArtifactClient(self.api)
        self.runs = run_client or RunClient(self.api)
        self.default_runs_root = _resolve_optional_path(runs_root)
        self.default_download_root = _resolve_optional_path(download_root) or self.default_runs_root
        self.logger = logger or logging.getLogger("evaluation_client")
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO)

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def build(
        cls,
        *,
        base_url: str,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        verify: bool = True,
        runs_root: Optional[Path] = None,
        download_root: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> "EvaluationClient":
        api_client = ApiClient(
            base_url=base_url.rstrip("/"),
            token=token,
            timeout=timeout,
            verify=verify,
        )
        return cls(
            api_client=api_client,
            runs_root=_resolve_optional_path(runs_root),
            download_root=_resolve_optional_path(download_root),
            logger=logger,
        )

    @classmethod
    def from_configs(
        cls,
        api_config: ApiConfig,
        *,
        local: Optional[LocalPaths] = None,
        logger: Optional[logging.Logger] = None,
    ) -> "EvaluationClient":
        return cls.build(
            base_url=api_config.base_url,
            token=api_config.token,
            timeout=api_config.timeout,
            verify=api_config.verify,
            runs_root=local.runs_root if local else None,
            download_root=local.download_root if local else None,
            logger=logger,
        )

    # ------------------------------------------------------------------ #
    # High-level workflow
    # ------------------------------------------------------------------ #
    def run_suite_with_assets(
        self,
        *,
        suite: Union[SuiteInput, Path, str],
        assets: Optional[AssetBundle] = None,
        options: Optional[RunOptions] = None,
    ) -> RunJobStatus:
        """
        Upload artefacts (if provided), submit a run, and optionally monitor it.

        Parameters
        ----------
        suite:
            Identifier for the suite to execute. Can be a ``Path`` to a YAML
            file, a URI understood by the API, or an explicit ``SuiteInput``.
        assets:
            Optional bundle describing artefacts that should be uploaded before
            scheduling the run.
        options:
            Behavioural switches such as whether to stream events, where to
            download results, and whether to retry failed cases only.
        """

        suite_input = SuiteInput.from_value(suite)
        opts = options or RunOptions()
        bundle = assets or AssetBundle()

        spec = EvaluationSpec(
            suite=suite_input.to_suite_spec(),
            datasets=list(bundle.dataset_specs()),
            prompts=list(bundle.prompt_specs()),
            app_prompts=list(bundle.app_prompt_specs()),
            retrieval_bundles=list(bundle.retrieval_specs()),
            judges=list(bundle.judge_specs()),
            resume_dir=opts.resume_dir,
            seed_from=opts.seed_from,
            plan_only=opts.plan_only,
            retry_failed_only=opts.retry_failed_only,
        )

        root = opts.download_root or self.default_download_root

        if opts.monitor:
            return self.run_spec(
                spec,
                monitor=True,
                download_root=root,
                monitor_log_level=opts.log_level,
            )

        status = self.run_spec(
            spec,
            monitor=False,
            download_root=root,
        )
        if opts.download_results and root and status.run_uri:
            dest = _resolve_download_destination(root, status)
            self.download_run(status.run_uri, dest, overwrite=True)
        return status

    # ------------------------------------------------------------------ #
    # Run helpers
    # ------------------------------------------------------------------ #
    def submit_run(
        self,
        *,
        suite_uri: Optional[str] = None,
        suite_path: Optional[Path] = None,
        resume_dir: Optional[str] = None,
        seed_from: Optional[str] = None,
        plan_only: bool = False,
        retry_failed_only: bool = False,
    ) -> RunJobHandle:
        request = RunRequest(
            suite_uri=suite_uri,
            suite_path=suite_path,
            resume_dir=resume_dir,
            seed_from=seed_from,
            plan_only=plan_only,
            retry_failed_only=retry_failed_only,
        )
        job = self.runs.submit(request)
        self.logger.info("submit_run", extra={"job_id": job.job_id, "suite_uri": job.suite_uri})
        return job

    def wait_for_completion(
        self,
        job_id: str,
        *,
        poll_interval: Optional[float] = None,
        timeout: Optional[float] = None,
        callback: Optional[Callable[[RunJobStatus], None]] = None,
    ) -> RunJobStatus:
        status = self.runs.wait_for_completion(
            job_id,
            poll_interval=poll_interval,
            timeout=timeout,
            callback=callback,
        )
        self.logger.info("wait_for_completion", extra={"job_id": job_id, "status": status.status})
        return status

    def get_run(self, job_id: str) -> RunJobStatus:
        return self.runs.get(job_id)

    def stream_events(self, job_id: str) -> EventStream:
        return self.runs.stream(job_id)

    def iterate_run_events(self, job_id: str) -> Iterator[RunEventEnvelope]:
        return self.runs.stream_events(job_id)

    def stream_job_events(self, job_id: str):
        return self.stream_events(job_id).with_status()

    def run_suite(
        self,
        suite: Union[Path, str, SuiteInput],
        *,
        datasets: Optional[Dict[str, Union[str, Path]]] = None,
        resume_dir: Optional[Path] = None,
        seed_from: Optional[Path] = None,
        plan_only: bool = False,
        retry_failed_only: bool = False,
        monitor: bool = False,
        download_root: Optional[Path] = None,
        monitor_log_level: LogLevel = "normal",
    ) -> RunJobStatus:
        suite_spec = SuiteInput.from_value(suite).to_suite_spec()
        dataset_specs = [
            DatasetUploadSpec(
                dataset_id=dataset_id,
                path=Path(path).expanduser().resolve(),
            )
            for dataset_id, path in (datasets or {}).items()
        ]
        spec = EvaluationSpec(
            suite=suite_spec,
            datasets=dataset_specs,
            resume_dir=str(resume_dir.expanduser().resolve()) if resume_dir else None,
            seed_from=str(seed_from.expanduser().resolve()) if seed_from else None,
            plan_only=plan_only,
            retry_failed_only=retry_failed_only,
        )
        return self.run_spec(
            spec,
            monitor=monitor,
            download_root=download_root,
            monitor_log_level=monitor_log_level,
        )

    def run_spec(
        self,
        spec: EvaluationSpec,
        *,
        monitor: bool = False,
        download_root: Optional[Path] = None,
        monitor_log_level: LogLevel = "normal",
    ) -> RunJobStatus:
        suite_label = spec.suite.label
        suite_uri_override = self._materialize_spec(spec)
        request = spec.to_run_request(suite_uri_override=suite_uri_override)
        job = self.runs.submit(request)

        root = _resolve_optional_path(download_root) or self.default_download_root

        if monitor:
            download_hook = _make_download_hook(root, self.download_run) if root else None
            return monitor_job(
                job=job,
                suite_label=suite_label,
                stream_events=self.stream_job_events,
                get_status=self.get_run,
                on_complete=download_hook,
                log_level=monitor_log_level,
                logger=self.logger,
            )

        status = self.wait_for_completion(job.job_id)
        if root and status.run_uri:
            dest = _resolve_download_destination(root, status)
            self.download_run(status.run_uri, dest, overwrite=True)
        return status

    def _materialize_spec(self, spec: EvaluationSpec) -> Optional[str]:
        suite_uri_override: Optional[str] = None
        if spec.suite.path is not None and spec.suite.uri is None and spec.suite.inline is None:
            upload = self.upload_suite(spec.suite.path)
            suite_uri_override = upload["uri"]

        # Upload any accompanying artefacts declared on the specification.
        for dataset in spec.datasets:
            self.logger.debug(
                "upload_dataset",
                extra={"dataset_id": dataset.dataset_id, "path": str(dataset.path)},
            )
            self.upload_dataset(dataset.dataset_id, dataset.path)

        for prompt in spec.prompts:
            self.logger.debug(
                "upload_prompt",
                extra={"prompt_id": prompt.prompt_id, "instruction": str(prompt.instruction_path)},
            )
            self.upload_prompt(prompt.prompt_id, prompt.instruction_path, prompt.resource_files)

        for app_prompt in spec.app_prompts:
            self.logger.debug(
                "upload_app_prompt",
                extra={"prompt_id": app_prompt.prompt_id, "path": str(app_prompt.path)},
            )
            self.upload_app_prompt(app_prompt.prompt_id, app_prompt.path)

        for bundle in spec.retrieval_bundles:
            self.logger.debug(
                "upload_retrieval_bundle",
                extra={"bundle_id": bundle.bundle_id, "path": str(bundle.path)},
            )
            self.upload_retrieval_bundle(bundle.bundle_id, bundle.path)

        for judge in spec.judges:
            self.logger.debug(
                "upload_judge",
                extra={"judge_id": judge.judge_id, "path": str(judge.path), "kind": judge.kind},
            )
            self.upload_judge(judge.judge_id, judge.path, kind=judge.kind)

        return suite_uri_override

    # ------------------------------------------------------------------ #
    # Artefact helpers
    # ------------------------------------------------------------------ #
    def upload_suite(self, suite_path: Path) -> dict:
        return self.artifacts.upload_suite(Path(suite_path).expanduser().resolve())

    def upload_dataset(self, dataset_id: str, dataset_path: Path) -> dict:
        return self.artifacts.upload_dataset(dataset_id, Path(dataset_path).expanduser().resolve())

    def upload_prompt(self, prompt_id: str, instruction_path: Path, resource_files: Dict[str, Path]) -> dict:
        resolved_instruction = Path(instruction_path).expanduser().resolve()
        resolved_resources = {
            name: Path(path).expanduser().resolve() for name, path in resource_files.items()
        }
        return self.artifacts.upload_prompt(prompt_id, resolved_instruction, resolved_resources)

    def upload_app_prompt(self, prompt_id: str, prompt_path: Path) -> dict:
        return self.artifacts.upload_app_prompt(prompt_id, Path(prompt_path).expanduser().resolve())

    def upload_retrieval_bundle(self, bundle_id: str, bundle_path: Path) -> dict:
        return self.artifacts.upload_retrieval_bundle(bundle_id, Path(bundle_path).expanduser().resolve())

    def upload_judge(self, judge_id: str, judge_path: Path, *, kind: str = "llm") -> dict:
        return self.artifacts.upload_judge(judge_id, Path(judge_path).expanduser().resolve(), kind=kind)

    def upload_custom_file(self, target_path: str, source_path: Path, *, content_type: Optional[str] = None) -> dict:
        return self.artifacts.upload_custom_file(target_path, Path(source_path).expanduser().resolve(), content_type=content_type)

    def download_run(
        self,
        run_uri: str,
        dest_dir: Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        destination = Path(dest_dir).expanduser().resolve()
        try:
            return self.artifacts.download_run_directory(
                run_uri,
                destination,
                overwrite=overwrite,
            )
        except ApiError as exc:
            if exc.status_code == 404:
                self.logger.info(
                    "download_run skipped (artifact not found)",
                    extra={"run_uri": run_uri, "destination": str(destination)},
                )
                return destination
            raise

    # ------------------------------------------------------------------ #
    # Run inspection helpers
    # ------------------------------------------------------------------ #
    def get_run_directory_status(self, run_dir: str) -> RunDirectoryStatus:
        return self.runs.fetch_status_snapshot(run_dir)

    def get_run_events(self, run_dir: str, *, tail: Optional[int] = None) -> RunEventsResponse:
        return self.runs.fetch_events(run_dir, tail=tail)

    def list_local_runs(
        self,
        root: Optional[Path] = None,
        *,
        limit: Optional[int] = None,
        after: Optional[datetime] = None,
    ) -> Iterable[RunHistoryEntry]:
        target_root = Path(root).expanduser().resolve() if root else self.default_runs_root
        if not target_root:
            raise ValueError("runs_root not provided; supply root or configure LocalPaths.runs_root")
        return self.runs.list_local_runs(root=target_root, limit=limit, after=after)


def _resolve_optional_path(value: Optional[Path]) -> Optional[Path]:
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def _make_download_hook(
    root: Path,
    downloader: Callable[[str, Path], Path],
) -> Callable[[RunJobStatus], None]:
    root = Path(root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    def _callback(status: RunJobStatus) -> None:
        if not status.run_uri:
            return
        dest = _resolve_download_destination(root, status)
        downloader(status.run_uri, dest, overwrite=True)

    return _callback


def _resolve_download_destination(root: Path, status: RunJobStatus) -> Path:
    root = Path(root).expanduser().resolve()
    run_name = status.run_dir or (Path(status.run_uri).name if status.run_uri else "run")
    dest = root / run_name
    # Ensure an output directory exists for subsequent file transfers.
    dest.mkdir(parents=True, exist_ok=True)
    return dest


__all__ = ["EvaluationClient", "DEFAULT_BASE_URL", "DEFAULT_TIMEOUT_SECONDS"]
