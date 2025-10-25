from typing import Annotated, ClassVar, Final
from pydantic import ConfigDict, Field
from .base import ResourceModel
from .utils import _default_if_none
from .v1_object_meta import V1ObjectMeta
from .v1_resource_claim_spec import V1ResourceClaimSpec
from pydantic import BeforeValidator

__all__ = ("V1ResourceClaimTemplateSpec",)


class V1ResourceClaimTemplateSpec(ResourceModel):
    """ResourceClaimTemplateSpec contains the metadata and fields for a ResourceClaim."""

    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    kubernetes_ref: ClassVar[Final[str]] = (
        "io.k8s.api.resource.v1.ResourceClaimTemplateSpec"
    )

    metadata: Annotated[
        V1ObjectMeta,
        Field(
            description="""ObjectMeta may contain labels and annotations that will be copied into the ResourceClaim when creating it. No other fields are allowed and will be rejected during validation.""",
            exclude_if=lambda v: v == V1ObjectMeta(),
        ),
        BeforeValidator(_default_if_none(V1ObjectMeta)),
    ] = V1ObjectMeta()

    spec: Annotated[
        V1ResourceClaimSpec,
        Field(
            description="""Spec for the ResourceClaim. The entire content is copied unchanged into the ResourceClaim that gets created from this template. The same fields as in a ResourceClaim are also valid here."""
        ),
    ]
