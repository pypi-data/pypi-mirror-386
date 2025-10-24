from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .utils import _collection_if_none
from .utils import _default_if_none
from .v1_opaque_device_configuration import V1OpaqueDeviceConfiguration
from pydantic import BeforeValidator

__all__ = ("V1DeviceAllocationConfiguration",)


class V1DeviceAllocationConfiguration(BaseModel):
    """DeviceAllocationConfiguration gets embedded in an AllocationResult."""

    model_config = ConfigDict(
        extra="forbid", validate_by_alias=True, validate_by_name=True
    )

    kubernetes_ref: ClassVar[Final[str]] = (
        "io.k8s.api.resource.v1.DeviceAllocationConfiguration"
    )

    opaque: Annotated[
        V1OpaqueDeviceConfiguration | None,
        Field(
            description="""Opaque provides driver-specific configuration parameters.""",
            exclude_if=lambda v: v is None,
        ),
        BeforeValidator(_default_if_none(V1OpaqueDeviceConfiguration)),
    ] = None

    requests: Annotated[
        list[str],
        Field(
            description="""Requests lists the names of requests where the configuration applies. If empty, its applies to all requests.

References to subrequests must include the name of the main request and may include the subrequest using the format <main request>[/<subrequest>]. If just the main request is given, the configuration applies to all subrequests.""",
            exclude_if=lambda v: v == [],
        ),
        BeforeValidator(_collection_if_none("[]")),
    ] = []

    source: Annotated[
        str,
        Field(
            description="""Source records whether the configuration comes from a class and thus is not something that a normal user would have been able to set or from a claim."""
        ),
    ]
