from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .utils import _default_if_none
from .v1alpha1_apply_configuration import V1alpha1ApplyConfiguration
from .v1alpha1_json_patch import V1alpha1JSONPatch
from pydantic import BeforeValidator

__all__ = ("V1alpha1Mutation",)


class V1alpha1Mutation(BaseModel):
    """Mutation specifies the CEL expression which is used to apply the Mutation."""

    model_config = ConfigDict(
        extra="forbid", validate_by_alias=True, validate_by_name=True
    )

    kubernetes_ref: ClassVar[Final[str]] = (
        "io.k8s.api.admissionregistration.v1alpha1.Mutation"
    )

    apply_configuration: Annotated[
        V1alpha1ApplyConfiguration,
        Field(
            alias="applyConfiguration",
            description="""applyConfiguration defines the desired configuration values of an object. The configuration is applied to the admission object using [structured merge diff](https://github.com/kubernetes-sigs/structured-merge-diff). A CEL expression is used to create apply configuration.""",
            exclude_if=lambda v: v == V1alpha1ApplyConfiguration(),
        ),
        BeforeValidator(_default_if_none(V1alpha1ApplyConfiguration)),
    ] = V1alpha1ApplyConfiguration()

    json_patch: Annotated[
        V1alpha1JSONPatch,
        Field(
            alias="jsonPatch",
            description="""jsonPatch defines a [JSON patch](https://jsonpatch.com/) operation to perform a mutation to the object. A CEL expression is used to create the JSON patch.""",
            exclude_if=lambda v: v == V1alpha1JSONPatch(),
        ),
        BeforeValidator(_default_if_none(V1alpha1JSONPatch)),
    ] = V1alpha1JSONPatch()

    patch_type: Annotated[
        str,
        Field(
            alias="patchType",
            description="""patchType indicates the patch strategy used. Allowed values are "ApplyConfiguration" and "JSONPatch". Required.""",
        ),
    ]
