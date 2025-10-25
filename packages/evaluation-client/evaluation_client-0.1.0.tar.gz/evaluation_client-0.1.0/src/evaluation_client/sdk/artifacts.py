from __future__ import annotations

from dataclasses import dataclass
import mimetypes
import shutil
import tempfile
import zipfile
from contextlib import ExitStack
from pathlib import Path
from typing import Dict, Optional
from .http import ApiClient


@dataclass
class ArtifactClient:
    api: ApiClient

    def upload_suite(self, suite_path: Path) -> Dict:
        with suite_path.open("rb") as fh:
            files = {"file": (suite_path.name, fh, "application/x-yaml")}
            return self.api.json("POST", "/artifacts/suites", files=files)

    def upload_dataset(self, dataset_id: str, dataset_path: Path) -> Dict:
        with dataset_path.open("rb") as fh:
            files = {
                "dataset_id": (None, dataset_id),
                "file": (dataset_path.name, fh, "application/json"),
            }
            return self.api.json("POST", "/artifacts/datasets", files=files)

    def upload_prompt(self, prompt_id: str, instruction_path: Path, resource_files: Dict[str, Path]) -> Dict:
        with ExitStack() as stack:
            inst_handle = stack.enter_context(instruction_path.open("rb"))
            files = [
                (
                    "instruction",
                    (instruction_path.name, inst_handle, "text/markdown"),
                )
            ]
            data = {"prompt_id": prompt_id}

            for idx, (name, path) in enumerate(resource_files.items()):
                handle = stack.enter_context(path.open("rb"))
                mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                field = "examples" if idx == 0 else "files"
                files.append((field, (name, handle, mime)))

            return self.api.json("POST", "/artifacts/prompts", data=data, files=files)

    def upload_app_prompt(self, prompt_id: str, prompt_path: Path) -> Dict:
        with prompt_path.open("rb") as fh:
            files = {
                "prompt_id": (None, prompt_id),
                "file": (prompt_path.name, fh, "text/markdown"),
            }
            return self.api.json("POST", "/artifacts/app-prompts", files=files)

    def upload_retrieval_bundle(self, bundle_id: str, bundle_path: Path) -> Dict:
        with bundle_path.open("rb") as fh:
            files = {
                "bundle_id": (None, bundle_id),
                "file": (bundle_path.name, fh, "application/x-yaml"),
            }
            return self.api.json("POST", "/artifacts/retrieval-bundles", files=files)

    def upload_judge(self, judge_id: str, judge_path: Path, *, kind: str = "llm") -> Dict:
        with judge_path.open("rb") as fh:
            files = {
                "judge_id": (None, judge_id),
                "kind": (None, kind),
                "file": (judge_path.name, fh, "application/x-yaml"),
            }
            return self.api.json("POST", "/artifacts/judges", files=files)

    def upload_custom_file(self, target_path: str, source_path: Path, *, content_type: Optional[str] = None) -> Dict:
        guessed_type, _ = mimetypes.guess_type(str(source_path))
        media_type = content_type or guessed_type or "application/octet-stream"
        payload = {"target_path": target_path}
        if content_type:
            payload["content_type"] = content_type
        with source_path.open("rb") as fh:
            files = {"file": (source_path.name, fh, media_type)}
            return self.api.json("POST", "/artifacts/files", data=payload, files=files)

    def download_run_directory(
        self,
        run_uri: str,
        dest_dir: Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        dest_dir = dest_dir.resolve()
        if overwrite and dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        response = self.api.request(
            "GET",
            "/artifacts/runs/download",
            params={"run_uri": run_uri},
            stream=True,
        )

        tmp_zip: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_zip = Path(tmp.name)
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        tmp.write(chunk)
        finally:
            response.close()

        if tmp_zip is None:
            raise RuntimeError("Failed to materialize run archive from API response.")

        try:
            with zipfile.ZipFile(tmp_zip, mode="r") as archive:
                archive.extractall(dest_dir)
        finally:
            tmp_zip.unlink(missing_ok=True)

        return dest_dir
