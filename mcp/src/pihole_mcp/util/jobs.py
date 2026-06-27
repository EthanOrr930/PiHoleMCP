"""In-memory async job tracker for long-running tasks (e.g. gravity update)."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Awaitable, Callable, Literal

JobStatus = Literal["pending", "running", "done", "error"]

_RETENTION_S = 3600.0


class _Job:
    __slots__ = ("id", "status", "progress", "result", "error", "task", "finished_at")

    def __init__(self, job_id: str) -> None:
        self.id: str = job_id
        self.status: JobStatus = "pending"
        self.progress: list[str] = []
        self.result: Any | None = None
        self.error: str | None = None
        self.task: asyncio.Task[Any] | None = None
        self.finished_at: float | None = None


class JobTracker:
    """Spawns background tasks, tracks status, and reaps old entries."""

    def __init__(self, retention_s: float = _RETENTION_S) -> None:
        self._jobs: dict[str, _Job] = {}
        self._retention_s = retention_s

    def start_job(self, factory: Callable[[list[str]], Awaitable[Any]]) -> str:
        job_id = uuid.uuid4().hex
        job = _Job(job_id)
        self._jobs[job_id] = job
        job.task = asyncio.create_task(self._run(job, factory))
        self._reap()
        return job_id

    def get_status(self, job_id: str) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        out: dict[str, Any] = {
            "job_id": job.id,
            "status": job.status,
            "progress": list(job.progress),
        }
        if job.status == "done":
            out["result"] = job.result
        if job.status == "error":
            out["error"] = job.error
        return out

    async def _run(self, job: _Job, factory: Callable[[list[str]], Awaitable[Any]]) -> None:
        job.status = "running"
        try:
            job.result = await factory(job.progress)
            job.status = "done"
        except Exception as e:
            job.error = f"{type(e).__name__}: {e}"
            job.status = "error"
        finally:
            job.finished_at = time.monotonic()

    def _reap(self) -> None:
        now = time.monotonic()
        for jid in [j.id for j in self._jobs.values() if j.finished_at and now - j.finished_at > self._retention_s]:
            self._jobs.pop(jid, None)
