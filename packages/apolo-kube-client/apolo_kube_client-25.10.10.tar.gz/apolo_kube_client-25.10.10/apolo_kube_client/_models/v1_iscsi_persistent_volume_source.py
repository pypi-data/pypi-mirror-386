from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .utils import _collection_if_none
from .utils import _default_if_none
from .v1_secret_reference import V1SecretReference
from pydantic import BeforeValidator

__all__ = ("V1ISCSIPersistentVolumeSource",)


class V1ISCSIPersistentVolumeSource(BaseModel):
    """ISCSIPersistentVolumeSource represents an ISCSI disk. ISCSI volumes can only be mounted as read/write once. ISCSI volumes support ownership management and SELinux relabeling."""

    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    kubernetes_ref: ClassVar[Final[str]] = (
        "io.k8s.api.core.v1.ISCSIPersistentVolumeSource"
    )

    chap_auth_discovery: Annotated[
        bool | None,
        Field(
            alias="chapAuthDiscovery",
            description="""chapAuthDiscovery defines whether support iSCSI Discovery CHAP authentication""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    chap_auth_session: Annotated[
        bool | None,
        Field(
            alias="chapAuthSession",
            description="""chapAuthSession defines whether support iSCSI Session CHAP authentication""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    fs_type: Annotated[
        str | None,
        Field(
            alias="fsType",
            description="""fsType is the filesystem type of the volume that you want to mount. Tip: Ensure that the filesystem type is supported by the host operating system. Examples: "ext4", "xfs", "ntfs". Implicitly inferred to be "ext4" if unspecified. More info: https://kubernetes.io/docs/concepts/storage/volumes#iscsi""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    initiator_name: Annotated[
        str | None,
        Field(
            alias="initiatorName",
            description="""initiatorName is the custom iSCSI Initiator Name. If initiatorName is specified with iscsiInterface simultaneously, new iSCSI interface <target portal>:<volume name> will be created for the connection.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    iqn: Annotated[str, Field(description="""iqn is Target iSCSI Qualified Name.""")]

    iscsi_interface: Annotated[
        str | None,
        Field(
            alias="iscsiInterface",
            description="""iscsiInterface is the interface Name that uses an iSCSI transport. Defaults to 'default' (tcp).""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    lun: Annotated[int, Field(description="""lun is iSCSI Target Lun number.""")]

    portals: Annotated[
        list[str],
        Field(
            description="""portals is the iSCSI Target Portal List. The Portal is either an IP or ip_addr:port if the port is other than default (typically TCP ports 860 and 3260).""",
            exclude_if=lambda v: v == [],
        ),
        BeforeValidator(_collection_if_none("[]")),
    ] = []

    read_only: Annotated[
        bool | None,
        Field(
            alias="readOnly",
            description="""readOnly here will force the ReadOnly setting in VolumeMounts. Defaults to false.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    secret_ref: Annotated[
        V1SecretReference,
        Field(
            alias="secretRef",
            description="""secretRef is the CHAP Secret for iSCSI target and initiator authentication""",
            exclude_if=lambda v: v == V1SecretReference(),
        ),
        BeforeValidator(_default_if_none(V1SecretReference)),
    ] = V1SecretReference()

    target_portal: Annotated[
        str,
        Field(
            alias="targetPortal",
            description="""targetPortal is iSCSI Target Portal. The Portal is either an IP or ip_addr:port if the port is other than default (typically TCP ports 860 and 3260).""",
        ),
    ]
