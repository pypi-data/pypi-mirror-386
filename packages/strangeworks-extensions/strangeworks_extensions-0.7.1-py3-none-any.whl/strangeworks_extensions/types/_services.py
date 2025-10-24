"""_services.py."""

import time
import uuid
from enum import Enum

from pydantic import BaseModel, Field
from strangeworks_core.types import JobStatus

from strangeworks_extensions.types._artifact import Artifact


def _generate_id() -> str:
    """Generate Request ID

    Generaters a unique-enough string to be used as an identifier.

    Returns
    -------
    str
       a unique identifier
    """
    ts = int(time.time() * 1000)  # milliseconds
    return f"{ts:x}-{uuid.uuid4().hex[:8]}"


class IDType(str, Enum):
    JOB_SLUG = "job_slug"
    EXTERNAL_ID = "external_identifier"


class EventType(str, Enum):
    CREATE = "job_create"
    UPDATE = "job_update"
    CANCEL = "job_cancel"
    DELETE = "job_delete"
    COMPLETE = "job_completed"


class JobID(BaseModel):
    id: str
    type: IDType


class JobSlug(JobID):
    def __init__(self, *, id: str, **kwargs):
        super().__init__(id=id, type=IDType.JOB_SLUG)


class RemoteID(JobID):
    def __init__(self, *, id: str, **kwargs):
        super().__init__(id=id, type=IDType.EXTERNAL_ID)


class EventPayload(BaseModel):
    """Represents Job Status Reported by an Extension.

    Attributes
    ----------
    id: JobID | None
        Identifier. Used to access job record at a later time after its creation.
        Value can be the job slug from Strangeworks or the identifier assigened from
        external resource (hardware provider, etc). None if the job will not be updated
        at a future time or if the extension will track the job slug returned by the
        service for future updates.
    sw_status: JobStatus | None
        Represents a job status update using Strangeworks job enums. None value implies
        no change in Strangeworks job status.
    external_status: str | None
        Represents the job status provided by an external provider. None value implies
        no change in external status.
    tags: list[str] | None
        List of strings to tag the job with.
    artifacts: list[Artifact] | None
        List of artifacts associated with the event. These will be uploaded as files
        associated with the job. Job result, arguments, metdata, etc are examples of
        artifacts.
    """

    id: str = Field(default_factory=_generate_id)
    job_id: JobID | None = None
    sw_status: JobStatus | None = None
    external_status: str | None = None
    tags: list[str] | None = None
    # artifacts can be input args, results, etc.
    artifacts: list[Artifact] | None = None


class ExtensionEvent(BaseModel):
    """Job Event Object

    Attributes
    ----------
    product_slug: str
        Identifies the product which this event is for.
    resource_slug: str
        Identifies the resource for the job.
    event_type: EventType
        Describes the state change to track in a job running from an extension.
    payload: EventPayload
        Data associated with the job event.
    """

    product_slug: str
    resource_slug: str
    event_type: EventType
    payload: EventPayload
