from __future__ import annotations

"""
Utilities for describing artefacts that an evaluation run may need.

These data classes provide type-checked containers around user-supplied paths.
The evaluation client converts them into the SDK's upload specifications before
dispatching API calls.
"""

from pathlib import Path
from typing import Dict, Iterable, Optional, Union

from pydantic import BaseModel, Field, model_validator

from .sdk import (
    AppPromptSpec,
    DatasetUploadSpec,
    JudgeUploadSpec,
    PromptUploadSpec,
    RetrievalBundleSpec,
)


class PromptFiles(BaseModel):
    """
    Filesystem locations for a prompt's instruction and associated resources.

    The ``examples`` field accepts a single path, an iterable of paths, or a mapping
    of desired filenames to paths. Additional files can be provided via ``files``.
    All supporting files are preserved using their original filenames.
    """

    instruction: Path
    examples: Optional[Union[Path, Iterable[Union[str, Path]], Dict[str, Union[str, Path]]]] = None
    files: Union[Dict[str, Union[str, Path]], Iterable[Union[str, Path]]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _expand(self) -> "PromptFiles":
        self.instruction = Path(self.instruction).expanduser().resolve()

        def _normalise(
            source: Union[Dict[str, Union[str, Path]], Iterable[Union[str, Path]], Path, str, None]
        ) -> Dict[str, Path]:
            mapping: Dict[str, Path] = {}
            if source is None:
                return mapping
            if isinstance(source, (str, Path)):
                p = Path(source).expanduser().resolve()
                mapping[p.name] = p
                return mapping
            if isinstance(source, dict):
                for name, value in source.items():
                    mapping[str(name)] = Path(value).expanduser().resolve()
                return mapping
            # iterable
            for value in source:
                p = Path(value).expanduser().resolve()
                mapping[p.name] = p
            return mapping
        mapping: Dict[str, Path] = {}
        mapping.update(_normalise(self.examples))
        mapping.update(_normalise(self.files))
        if not mapping:
            raise ValueError("PromptFiles requires at least one resource file (examples).")
        self.files = mapping
        return self


class JudgeConfig(BaseModel):
    """Configuration payload for a judge artefact."""

    path: Path
    kind: str = "llm"

    @model_validator(mode="after")
    def _expand(self) -> "JudgeConfig":
        self.path = Path(self.path).expanduser().resolve()
        return self


class AssetBundle(BaseModel):
    """
    Group of optional artefacts that can be uploaded before running a suite.

    All fields are optional; callers may provide only the artefacts that need
    refreshing. Paths can be either ``Path`` instances or strings.
    """

    datasets: Dict[str, Union[str, Path]] = Field(default_factory=dict)
    prompts: Dict[str, Union[PromptFiles, Dict[str, Union[str, Path]]]] = Field(default_factory=dict)
    app_prompts: Dict[str, Union[str, Path]] = Field(default_factory=dict)
    retrieval_bundles: Dict[str, Union[str, Path]] = Field(default_factory=dict)
    judges: Dict[str, Union[JudgeConfig, Dict[str, Union[str, Path]], str, Path]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _normalise(self) -> "AssetBundle":
        self.datasets = {k: Path(v).expanduser().resolve() for k, v in self.datasets.items()}
        self.app_prompts = {k: Path(v).expanduser().resolve() for k, v in self.app_prompts.items()}
        self.retrieval_bundles = {k: Path(v).expanduser().resolve() for k, v in self.retrieval_bundles.items()}

        prompt_specs: Dict[str, PromptFiles] = {}
        for prompt_id, value in self.prompts.items():
            prompt_specs[prompt_id] = PromptFiles.model_validate(value)
        self.prompts = prompt_specs

        judge_specs: Dict[str, JudgeConfig] = {}
        for judge_id, value in self.judges.items():
            if isinstance(value, JudgeConfig):
                judge_specs[judge_id] = JudgeConfig.model_validate(value)
            elif isinstance(value, dict):
                judge_specs[judge_id] = JudgeConfig.model_validate(value)
            else:
                judge_specs[judge_id] = JudgeConfig(path=value)
        self.judges = judge_specs
        return self

    def dataset_specs(self) -> Iterable[DatasetUploadSpec]:
        for dataset_id, path in self.datasets.items():
            yield DatasetUploadSpec(dataset_id=dataset_id, path=path)

    def prompt_specs(self) -> Iterable[PromptUploadSpec]:
        for prompt_id, prompt in self.prompts.items():
            yield PromptUploadSpec(
                prompt_id=prompt_id,
                instruction_path=prompt.instruction,
                resource_files=prompt.files,
            )

    def app_prompt_specs(self) -> Iterable[AppPromptSpec]:
        for prompt_id, path in self.app_prompts.items():
            yield AppPromptSpec(prompt_id=prompt_id, path=path)

    def retrieval_specs(self) -> Iterable[RetrievalBundleSpec]:
        for bundle_id, path in self.retrieval_bundles.items():
            yield RetrievalBundleSpec(bundle_id=bundle_id, path=path)

    def judge_specs(self) -> Iterable[JudgeUploadSpec]:
        for judge_id, judge in self.judges.items():
            yield JudgeUploadSpec(judge_id=judge_id, path=judge.path, kind=judge.kind)


__all__ = ["PromptFiles", "JudgeConfig", "AssetBundle"]
