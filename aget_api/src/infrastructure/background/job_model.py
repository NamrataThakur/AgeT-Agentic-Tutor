from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from datetime import datetime

class JobStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    FAILED = "failed"
    PENDING = "pending"
    REGENERATE = "regenerating"


class BackgroundJob(BaseModel):

    job_id : str

    dedup_key : str
    
    topic: str

    bucket : str

    task_name: str

    payload: dict[str, Any] = Field(default_factory=dict)

    status: JobStatus = JobStatus.PENDING

    result: dict | None = None

    error: str | None = None

    created_at: datetime

    started_at: datetime | None = None

    completed_at: datetime | None = None

    eta_secs : int = 180