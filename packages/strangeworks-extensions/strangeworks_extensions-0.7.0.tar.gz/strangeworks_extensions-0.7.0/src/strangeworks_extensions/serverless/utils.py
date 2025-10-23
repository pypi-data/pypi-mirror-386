"""utils.py."""

from typing import Any

from strangeworks_core.types import JobStatus

from strangeworks_extensions.types import SWJobInfo


def sw_job_info(
    tags: list[str] | None = None, remote_id: str | None = None
) -> SWJobInfo:
    """Generate a SWJobInfo object.

    Parameters
    ----------
    tags : list[str] | None, optional
        tags to apply to the job. Defaults to None.
    remote_id : str | None, optional
        remote id for the job. typically used for a job that was submitted on an
        external resource. Defaults to None.

    Returns
    -------
    SWJobInfo
        A SWJobInfo object.
    """
    _args: dict[str, Any] = {
        "status": JobStatus.COMPLETED,
    }
    if tags:
        _args["tags"] = tags
    if remote_id:
        _args["external_identifier"] = remote_id
    return SWJobInfo(**_args)
