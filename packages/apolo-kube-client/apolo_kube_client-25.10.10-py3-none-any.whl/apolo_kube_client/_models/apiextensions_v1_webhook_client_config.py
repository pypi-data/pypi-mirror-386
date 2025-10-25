from typing import Annotated, ClassVar, Final
from pydantic import BaseModel, ConfigDict, Field
from .apiextensions_v1_service_reference import ApiextensionsV1ServiceReference
from .utils import _default_if_none
from pydantic import BeforeValidator

__all__ = ("ApiextensionsV1WebhookClientConfig",)


class ApiextensionsV1WebhookClientConfig(BaseModel):
    """WebhookClientConfig contains the information to make a TLS connection with the webhook."""

    model_config = ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    kubernetes_ref: ClassVar[Final[str]] = (
        "io.k8s.apiextensions-apiserver.pkg.apis.apiextensions.v1.WebhookClientConfig"
    )

    ca_bundle: Annotated[
        str | None,
        Field(
            alias="caBundle",
            description="""caBundle is a PEM encoded CA bundle which will be used to validate the webhook's server certificate. If unspecified, system trust roots on the apiserver are used.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None

    service: Annotated[
        ApiextensionsV1ServiceReference | None,
        Field(
            description="""service is a reference to the service for this webhook. Either service or url must be specified.

If the webhook is running within the cluster, then you should use `service`.""",
            exclude_if=lambda v: v is None,
        ),
        BeforeValidator(_default_if_none(ApiextensionsV1ServiceReference)),
    ] = None

    url: Annotated[
        str | None,
        Field(
            description="""url gives the location of the webhook, in standard URL form (`scheme://host:port/path`). Exactly one of `url` or `service` must be specified.

The `host` should not refer to a service running in the cluster; use the `service` field instead. The host might be resolved via external DNS in some apiservers (e.g., `kube-apiserver` cannot resolve in-cluster DNS as that would be a layering violation). `host` may also be an IP address.

Please note that using `localhost` or `127.0.0.1` as a `host` is risky unless you take great care to run this webhook on all hosts which run an apiserver which might need to make calls to this webhook. Such installs are likely to be non-portable, i.e., not easy to turn up in a new cluster.

The scheme must be "https"; the URL must begin with "https://".

A path is optional, and if present may be any string permissible in a URL. You may use the path to pass an arbitrary string to the webhook, for example, a cluster identifier.

Attempting to use a user or basic auth e.g. "user:password@" is not allowed. Fragments ("#...") and query parameters ("?...") are not allowed, either.""",
            exclude_if=lambda v: v is None,
        ),
    ] = None
