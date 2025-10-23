"""request.py."""

import time
import uuid
from typing import Any, Protocol, Tuple

from pydantic import BaseModel, Field
from strangeworks_core.types import JobStatus, Resource


class InputArgs(BaseModel):
    """Model for Arguments to Function."""

    name: str | None = None
    args: Tuple[Any] | None = None
    kwargs: dict[str, Any] | None = None


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


class BaseRequest(BaseModel):
    """Base Model."""

    id: str = Field(default_factory=_generate_id)
    product_slug: str
    resource_slug: str
    input_args: InputArgs | None = None


class SWJobInfo(BaseModel):
    """Strangeworks Job Settings."""

    status: JobStatus | None = None
    external_identifier: str | None = None
    external_status: str | None = None
    job_data: dict[str, Any] | None = None
    job_data_schema: str | None = None
    tags: list[str] | None = None


_DEFAULT_JOB_INFO_OBJ = SWJobInfo()


class ExtensionsRequest(BaseRequest):
    """Extension Request Model.

    We only support a payload of type dictionary for now ... a decision we will surely
    regret.

    This is to be used with simulators, etc where the result is available immediately.
    """

    sw_job_settings: SWJobInfo = _DEFAULT_JOB_INFO_OBJ
    result: dict[str, Any] | None = None


class ResultHander(Protocol):
    def __call__(
        self, resource: Resource, *args: Any, **kwds: Any
    ) -> ExtensionsRequest:
        """Generates ExtensionsRequest.

        Returns
        -------
        ExtensionsRequest
            Object to submit to the extensions service.
        """
        ...
