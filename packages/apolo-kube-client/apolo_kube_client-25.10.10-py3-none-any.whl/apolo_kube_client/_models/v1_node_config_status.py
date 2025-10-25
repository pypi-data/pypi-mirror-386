from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .utils import _default_if_none
from .v1_node_config_source import V1NodeConfigSource
from pydantic import BeforeValidator

__all__ = ("V1NodeConfigStatus",)


class V1NodeConfigStatus(BaseModel):
    """NodeConfigStatus describes the status of the config assigned by Node.Spec.ConfigSource."""

    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    kubernetes_ref: ClassVar[Final[str]] = "io.k8s.api.core.v1.NodeConfigStatus"

    active: Annotated[
        V1NodeConfigSource,
        Field(
            description="""Active reports the checkpointed config the node is actively using. Active will represent either the current version of the Assigned config, or the current LastKnownGood config, depending on whether attempting to use the Assigned config results in an error.""",
            exclude_if=lambda v: v == V1NodeConfigSource(),
        ),
        BeforeValidator(_default_if_none(V1NodeConfigSource)),
    ] = V1NodeConfigSource()

    assigned: Annotated[
        V1NodeConfigSource,
        Field(
            description="""Assigned reports the checkpointed config the node will try to use. When Node.Spec.ConfigSource is updated, the node checkpoints the associated config payload to local disk, along with a record indicating intended config. The node refers to this record to choose its config checkpoint, and reports this record in Assigned. Assigned only updates in the status after the record has been checkpointed to disk. When the Kubelet is restarted, it tries to make the Assigned config the Active config by loading and validating the checkpointed payload identified by Assigned.""",
            exclude_if=lambda v: v == V1NodeConfigSource(),
        ),
        BeforeValidator(_default_if_none(V1NodeConfigSource)),
    ] = V1NodeConfigSource()

    error: Annotated[
        str | None,
        Field(
            description="""Error describes any problems reconciling the Spec.ConfigSource to the Active config. Errors may occur, for example, attempting to checkpoint Spec.ConfigSource to the local Assigned record, attempting to checkpoint the payload associated with Spec.ConfigSource, attempting to load or validate the Assigned config, etc. Errors may occur at different points while syncing config. Earlier errors (e.g. download or checkpointing errors) will not result in a rollback to LastKnownGood, and may resolve across Kubelet retries. Later errors (e.g. loading or validating a checkpointed config) will result in a rollback to LastKnownGood. In the latter case, it is usually possible to resolve the error by fixing the config assigned in Spec.ConfigSource. You can find additional information for debugging by searching the error message in the Kubelet log. Error is a human-readable description of the error state; machines can check whether or not Error is empty, but should not rely on the stability of the Error text across Kubelet versions.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    last_known_good: Annotated[
        V1NodeConfigSource,
        Field(
            alias="lastKnownGood",
            description="""LastKnownGood reports the checkpointed config the node will fall back to when it encounters an error attempting to use the Assigned config. The Assigned config becomes the LastKnownGood config when the node determines that the Assigned config is stable and correct. This is currently implemented as a 10-minute soak period starting when the local record of Assigned config is updated. If the Assigned config is Active at the end of this period, it becomes the LastKnownGood. Note that if Spec.ConfigSource is reset to nil (use local defaults), the LastKnownGood is also immediately reset to nil, because the local default config is always assumed good. You should not make assumptions about the node's method of determining config stability and correctness, as this may change or become configurable in the future.""",
            exclude_if=lambda v: v == V1NodeConfigSource(),
        ),
        BeforeValidator(_default_if_none(V1NodeConfigSource)),
    ] = V1NodeConfigSource()
