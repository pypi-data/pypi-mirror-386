from typing import Optional

from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    name: Optional[str] = None
    function: str
    kwargs: dict = {}
    notify_on: list = []
    topic: Optional[str] = None

    allow_concurrent: Optional[bool] = True
    max_retries: Optional[int] = 0
    retry_delay: Optional[int] = 3

class CreateScheduledTaskRequest(CreateTaskRequest):
    cron: Optional[str] = None
    interval: Optional[int] = None

class UpdateScheduledTaskRequest(BaseModel):
    name: Optional[str] = None
    function: Optional[str] = None
    cron: Optional[str] = None
    interval: Optional[int] = None
    kwargs: Optional[dict] = None
    enabled: Optional[bool] = None
    allow_concurrent: Optional[bool] = None