from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .utils import _collection_if_none
from .utils import _default_if_none
from .v1beta1_opaque_device_configuration import V1beta1OpaqueDeviceConfiguration
from pydantic import BeforeValidator

__all__ = ("V1beta1DeviceClaimConfiguration",)


class V1beta1DeviceClaimConfiguration(BaseModel):
    """DeviceClaimConfiguration is used for configuration parameters in DeviceClaim."""

    model_config = ConfigDict(
        extra="forbid", validate_by_alias=True, validate_by_name=True
    )

    kubernetes_ref: ClassVar[Final[str]] = (
        "io.k8s.api.resource.v1beta1.DeviceClaimConfiguration"
    )

    opaque: Annotated[
        V1beta1OpaqueDeviceConfiguration | None,
        Field(
            description="""Opaque provides driver-specific configuration parameters.""",
            exclude_if=lambda v: v is None,
        ),
        BeforeValidator(_default_if_none(V1beta1OpaqueDeviceConfiguration)),
    ] = None

    requests: Annotated[
        list[str],
        Field(
            description="""Requests lists the names of requests where the configuration applies. If empty, it applies to all requests.

References to subrequests must include the name of the main request and may include the subrequest using the format <main request>[/<subrequest>]. If just the main request is given, the configuration applies to all subrequests.""",
            exclude_if=lambda v: v == [],
        ),
        BeforeValidator(_collection_if_none("[]")),
    ] = []
