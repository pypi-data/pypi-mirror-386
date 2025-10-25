from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple
from urllib.parse import urljoin

import requests


class ApiError(RuntimeError):
    def __init__(self, status_code: int, message: str, payload: Optional[Any] = None) -> None:
        super().__init__(f"{status_code} {message}")
        self.status_code = status_code
        self.payload = payload


@dataclass
class ApiClient:
    base_url: str
    token: Optional[str] = None
    timeout: Optional[float] = None
    verify: bool = True

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def request(self, method: str, path: str, *, stream: bool = False, **kwargs) -> requests.Response:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        kwargs.setdefault("headers", self._headers())
        kwargs.setdefault("verify", self.verify)
        if self.timeout is not None:
            kwargs.setdefault("timeout", self.timeout)
        resp = requests.request(method, url, stream=stream, **kwargs)
        if resp.status_code >= 400:
            detail: Any = None
            with contextlib.suppress(Exception):
                detail = resp.json()
                raise ApiError(resp.status_code, resp.reason, payload=detail)
            raise ApiError(resp.status_code, resp.reason)
        return resp

    def json(self, method: str, path: str, **kwargs) -> Any:
        resp = self.request(method, path, **kwargs)
        return resp.json()

    def stream(self, path: str, *, chunk_size: Optional[int] = None, **kwargs) -> Iterable[Tuple[str, str]]:
        resp = self.request("GET", path, stream=True, **kwargs)
        event_type: Optional[str] = None
        data: Optional[str] = None
        for raw in resp.iter_lines(decode_unicode=True, chunk_size=chunk_size):
            if raw is None:
                continue
            line = raw.strip()
            if not line:
                if data is not None:
                    yield event_type or "message", data
                event_type = None
                data = None
                continue
            if line.startswith("event:"):
                event_type = line[len("event:") :].strip()
            elif line.startswith("data:"):
                payload = line[len("data:") :].strip()
                data = payload if data is None else f"{data}\n{payload}"
        resp.close()
