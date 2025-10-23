"""_services.py."""

from enum import Enum

from strangeworks_extensions.types._artifact import Artifact
from pydantic import BaseModel
from strangeworks_core.types import JobStatus

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

class JobEvent(BaseModel): 
    """Represents Job Status Reported by an Extension.
    
    Attributes
    ----------
    event_type: EventType
        Describes the state change to track in a job running from an extension.
    id: JobID | None
        Identifier. Used to access job record at a later time after its creation.
        Value can be the job slug from Strangeworks or the identifier assigened from external
        resource (hardware provider, etc). None if the job will not be updated at a future time
        or if the extension will track the job slug returned by the service for future updates.
    sw_status: JobStatus | None
        Represents a job status update using Strangeworks job enums. None value implies no change in 
        Strangeworks job status.
    external_status: str | None
        Represents the job status provided by an external provider. None value implies no change 
        in external status.
    tags: list[str] | None
        List of strings to tag the job with. 
    artifacts: list[Artifact] | None
        List of artifacts associated with the event. These will be uploaded as files associated with 
        the job.
    """
    event_type: EventType
    id: JobID | None = None
    sw_status: JobStatus | None = None
    external_status: str | None = None
    tags: list[str] | None = None
    # artifacts can be input args, results, etc.
    artifacts: list[Artifact] | None = None

class JobEventRequest(BaseModel):
    product_slug: str
    resource_slug: str

    event: JobEvent



