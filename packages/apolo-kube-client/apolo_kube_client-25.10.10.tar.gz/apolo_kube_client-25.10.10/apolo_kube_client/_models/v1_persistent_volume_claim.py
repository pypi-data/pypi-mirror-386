from typing import Annotated, ClassVar, Final
from pydantic import ConfigDict, Field
from .base import ResourceModel
from .utils import KubeMeta
from .utils import _default_if_none
from .v1_object_meta import V1ObjectMeta
from .v1_persistent_volume_claim_spec import V1PersistentVolumeClaimSpec
from .v1_persistent_volume_claim_status import V1PersistentVolumeClaimStatus
from pydantic import BeforeValidator

__all__ = ("V1PersistentVolumeClaim",)


class V1PersistentVolumeClaim(ResourceModel):
    """PersistentVolumeClaim is a user's request for and claim to a persistent volume"""

    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    kubernetes_ref: ClassVar[Final[str]] = "io.k8s.api.core.v1.PersistentVolumeClaim"

    kubernetes_meta: ClassVar[Final[tuple[KubeMeta, ...]]] = KubeMeta(
        group="", kind="PersistentVolumeClaim", version="v1"
    )

    api_version: Annotated[
        str | None,
        Field(
            alias="apiVersion",
            description="""APIVersion defines the versioned schema of this representation of an object. Servers should convert recognized schemas to the latest internal value, and may reject unrecognized values. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#resources""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    kind: Annotated[
        str | None,
        Field(
            description="""Kind is a string value representing the REST resource this object represents. Servers may infer this from the endpoint the client submits requests to. Cannot be updated. In CamelCase. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    metadata: Annotated[
        V1ObjectMeta,
        Field(
            description="""Standard object's metadata. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata""",
            exclude_if=lambda v: v == V1ObjectMeta(),
        ),
        BeforeValidator(_default_if_none(V1ObjectMeta)),
    ] = V1ObjectMeta()

    spec: Annotated[
        V1PersistentVolumeClaimSpec,
        Field(
            description="""spec defines the desired characteristics of a volume requested by a pod author. More info: https://kubernetes.io/docs/concepts/storage/persistent-volumes#persistentvolumeclaims""",
            exclude_if=lambda v: v == V1PersistentVolumeClaimSpec(),
        ),
        BeforeValidator(_default_if_none(V1PersistentVolumeClaimSpec)),
    ] = V1PersistentVolumeClaimSpec()

    status: Annotated[
        V1PersistentVolumeClaimStatus,
        Field(
            description="""status represents the current information/status of a persistent volume claim. Read-only. More info: https://kubernetes.io/docs/concepts/storage/persistent-volumes#persistentvolumeclaims""",
            exclude_if=lambda v: v == V1PersistentVolumeClaimStatus(),
        ),
        BeforeValidator(_default_if_none(V1PersistentVolumeClaimStatus)),
    ] = V1PersistentVolumeClaimStatus()
