from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .utils import _collection_if_none
from .utils import _default_if_none
from .v1_capacity_requirements import V1CapacityRequirements
from .v1_device_selector import V1DeviceSelector
from .v1_device_toleration import V1DeviceToleration
from pydantic import BeforeValidator

__all__ = ("V1DeviceSubRequest",)


class V1DeviceSubRequest(BaseModel):
    """DeviceSubRequest describes a request for device provided in the claim.spec.devices.requests[].firstAvailable array. Each is typically a request for a single resource like a device, but can also ask for several identical devices.

    DeviceSubRequest is similar to ExactDeviceRequest, but doesn't expose the AdminAccess field as that one is only supported when requesting a specific device."""

    model_config = ConfigDict(
        extra="forbid", validate_by_alias=True, validate_by_name=True
    )

    kubernetes_ref: ClassVar[Final[str]] = "io.k8s.api.resource.v1.DeviceSubRequest"

    allocation_mode: Annotated[
        str | None,
        Field(
            alias="allocationMode",
            description="""AllocationMode and its related fields define how devices are allocated to satisfy this subrequest. Supported values are:

- ExactCount: This request is for a specific number of devices.
  This is the default. The exact number is provided in the
  count field.

- All: This subrequest is for all of the matching devices in a pool.
  Allocation will fail if some devices are already allocated,
  unless adminAccess is requested.

If AllocationMode is not specified, the default mode is ExactCount. If the mode is ExactCount and count is not specified, the default count is one. Any other subrequests must specify this field.

More modes may get added in the future. Clients must refuse to handle requests with unknown modes.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    capacity: Annotated[
        V1CapacityRequirements,
        Field(
            description="""Capacity define resource requirements against each capacity.

If this field is unset and the device supports multiple allocations, the default value will be applied to each capacity according to requestPolicy. For the capacity that has no requestPolicy, default is the full capacity value.

Applies to each device allocation. If Count > 1, the request fails if there aren't enough devices that meet the requirements. If AllocationMode is set to All, the request fails if there are devices that otherwise match the request, and have this capacity, with a value >= the requested amount, but which cannot be allocated to this request.""",
            exclude_if=lambda v: v == V1CapacityRequirements(),
        ),
        BeforeValidator(_default_if_none(V1CapacityRequirements)),
    ] = V1CapacityRequirements()

    count: Annotated[
        int | None,
        Field(
            description="""Count is used only when the count mode is "ExactCount". Must be greater than zero. If AllocationMode is ExactCount and this field is not specified, the default is one.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    device_class_name: Annotated[
        str,
        Field(
            alias="deviceClassName",
            description="""DeviceClassName references a specific DeviceClass, which can define additional configuration and selectors to be inherited by this subrequest.

A class is required. Which classes are available depends on the cluster.

Administrators may use this to restrict which devices may get requested by only installing classes with selectors for permitted devices. If users are free to request anything without restrictions, then administrators can create an empty DeviceClass for users to reference.""",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="""Name can be used to reference this subrequest in the list of constraints or the list of configurations for the claim. References must use the format <main request>/<subrequest>.

Must be a DNS label."""
        ),
    ]

    selectors: Annotated[
        list[V1DeviceSelector],
        Field(
            description="""Selectors define criteria which must be satisfied by a specific device in order for that device to be considered for this subrequest. All selectors must be satisfied for a device to be considered.""",
            exclude_if=lambda v: v == [],
        ),
        BeforeValidator(_collection_if_none("[]")),
    ] = []

    tolerations: Annotated[
        list[V1DeviceToleration],
        Field(
            description="""If specified, the request's tolerations.

Tolerations for NoSchedule are required to allocate a device which has a taint with that effect. The same applies to NoExecute.

In addition, should any of the allocated devices get tainted with NoExecute after allocation and that effect is not tolerated, then all pods consuming the ResourceClaim get deleted to evict them. The scheduler will not let new pods reserve the claim while it has these tainted devices. Once all pods are evicted, the claim will get deallocated.

The maximum number of tolerations is 16.

This is an alpha field and requires enabling the DRADeviceTaints feature gate.""",
            exclude_if=lambda v: v == [],
        ),
        BeforeValidator(_collection_if_none("[]")),
    ] = []
