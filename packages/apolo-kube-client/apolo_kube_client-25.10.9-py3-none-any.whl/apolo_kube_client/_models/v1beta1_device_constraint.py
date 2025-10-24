from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .utils import _collection_if_none
from pydantic import BeforeValidator

__all__ = ("V1beta1DeviceConstraint",)


class V1beta1DeviceConstraint(BaseModel):
    """DeviceConstraint must have exactly one field set besides Requests."""

    model_config = ConfigDict(
        extra="forbid", validate_by_alias=True, validate_by_name=True
    )

    kubernetes_ref: ClassVar[Final[str]] = (
        "io.k8s.api.resource.v1beta1.DeviceConstraint"
    )

    distinct_attribute: Annotated[
        str | None,
        Field(
            alias="distinctAttribute",
            description="""DistinctAttribute requires that all devices in question have this attribute and that its type and value are unique across those devices.

This acts as the inverse of MatchAttribute.

This constraint is used to avoid allocating multiple requests to the same device by ensuring attribute-level differentiation.

This is useful for scenarios where resource requests must be fulfilled by separate physical devices. For example, a container requests two network interfaces that must be allocated from two different physical NICs.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    match_attribute: Annotated[
        str | None,
        Field(
            alias="matchAttribute",
            description="""MatchAttribute requires that all devices in question have this attribute and that its type and value are the same across those devices.

For example, if you specified "dra.example.com/numa" (a hypothetical example!), then only devices in the same NUMA node will be chosen. A device which does not have that attribute will not be chosen. All devices should use a value of the same type for this attribute because that is part of its specification, but if one device doesn't, then it also will not be chosen.

Must include the domain qualifier.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    requests: Annotated[
        list[str],
        Field(
            description="""Requests is a list of the one or more requests in this claim which must co-satisfy this constraint. If a request is fulfilled by multiple devices, then all of the devices must satisfy the constraint. If this is not specified, this constraint applies to all requests in this claim.

References to subrequests must include the name of the main request and may include the subrequest using the format <main request>[/<subrequest>]. If just the main request is given, the constraint applies to all subrequests.""",
            exclude_if=lambda v: v == [],
        ),
        BeforeValidator(_collection_if_none("[]")),
    ] = []
