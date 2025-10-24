from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .utils import _default_if_none
from .v1_label_selector import V1LabelSelector
from pydantic import BeforeValidator

__all__ = ("V1beta1ParamRef",)


class V1beta1ParamRef(BaseModel):
    """ParamRef describes how to locate the params to be used as input to expressions of rules applied by a policy binding."""

    model_config = ConfigDict(
        extra="forbid", validate_by_alias=True, validate_by_name=True
    )

    kubernetes_ref: ClassVar[Final[str]] = (
        "io.k8s.api.admissionregistration.v1beta1.ParamRef"
    )

    name: Annotated[
        str | None,
        Field(
            description="""name is the name of the resource being referenced.

One of `name` or `selector` must be set, but `name` and `selector` are mutually exclusive properties. If one is set, the other must be unset.

A single parameter used for all admission requests can be configured by setting the `name` field, leaving `selector` blank, and setting namespace if `paramKind` is namespace-scoped.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    namespace: Annotated[
        str | None,
        Field(
            description="""namespace is the namespace of the referenced resource. Allows limiting the search for params to a specific namespace. Applies to both `name` and `selector` fields.

A per-namespace parameter may be used by specifying a namespace-scoped `paramKind` in the policy and leaving this field empty.

- If `paramKind` is cluster-scoped, this field MUST be unset. Setting this field results in a configuration error.

- If `paramKind` is namespace-scoped, the namespace of the object being evaluated for admission will be used when this field is left unset. Take care that if this is left empty the binding must not match any cluster-scoped resources, which will result in an error.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    parameter_not_found_action: Annotated[
        str | None,
        Field(
            alias="parameterNotFoundAction",
            description="""`parameterNotFoundAction` controls the behavior of the binding when the resource exists, and name or selector is valid, but there are no parameters matched by the binding. If the value is set to `Allow`, then no matched parameters will be treated as successful validation by the binding. If set to `Deny`, then no matched parameters will be subject to the `failurePolicy` of the policy.

Allowed values are `Allow` or `Deny`

Required""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    selector: Annotated[
        V1LabelSelector,
        Field(
            description="""selector can be used to match multiple param objects based on their labels. Supply selector: {} to match all resources of the ParamKind.

If multiple params are found, they are all evaluated with the policy expressions and the results are ANDed together.

One of `name` or `selector` must be set, but `name` and `selector` are mutually exclusive properties. If one is set, the other must be unset.""",
            exclude_if=lambda v: v == V1LabelSelector(),
        ),
        BeforeValidator(_default_if_none(V1LabelSelector)),
    ] = V1LabelSelector()
