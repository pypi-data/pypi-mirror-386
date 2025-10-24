from typing import Any

from pydantic import BaseModel


class V1DiskNamingCRDSpec(BaseModel):
    disk_id: str


class V1DiskNamingCRDMetadata(BaseModel):
    name: str
    labels: dict[str, str] = {}
    namespace: str | None = None
    resourceVersion: str | None = None


class V1DiskNamingCRD(BaseModel):
    apiVersion: str = "neuromation.io/v1"
    kind: str = "DiskNaming"
    metadata: V1DiskNamingCRDMetadata
    spec: V1DiskNamingCRDSpec


class V1DiskNamingCRDList(BaseModel):
    apiVersion: str = "neuromation.io/v1"
    kind: str = "DiskNamingsList"
    items: list[V1DiskNamingCRD]


class V1UserBucketCRDSpec(BaseModel):
    provider_type: str | None
    provider_name: str | None
    created_at: str | None
    public: bool | None
    metadata: dict[str, Any] | None = None
    provider_id: str | None = None
    imported: bool | None = None
    credentials: dict[str, Any] | None = None


class V1UserBucketCRDMetadata(BaseModel):
    name: str
    labels: dict[str, str] = {}
    namespace: str | None = None
    resourceVersion: str | None = None


class V1UserBucketCRD(BaseModel):
    apiVersion: str = "neuromation.io/v1"
    kind: str = "UserBucket"
    metadata: V1UserBucketCRDMetadata
    spec: V1UserBucketCRDSpec


class V1UserBucketCRDList(BaseModel):
    apiVersion: str = "neuromation.io/v1"
    kind: str = "UserBucketsList"
    items: list[V1UserBucketCRD]


class V1PersistentBucketCredentialCRDSpec(BaseModel):
    provider_name: str
    provider_type: str
    credentials: dict[str, Any]
    bucket_ids: list[str]
    read_only: bool
    public: bool | None = None


class V1PersistentBucketCredentialCRDMetadata(BaseModel):
    name: str
    labels: dict[str, str] = {}
    namespace: str | None = None
    resourceVersion: str | None = None


class V1PersistentBucketCredentialCRD(BaseModel):
    apiVersion: str = "neuromation.io/v1"
    kind: str = "PersistentBucketCredential"
    metadata: V1PersistentBucketCredentialCRDMetadata
    spec: V1PersistentBucketCredentialCRDSpec


class V1PersistentBucketCredentialCRDList(BaseModel):
    apiVersion: str = "neuromation.io/v1"
    kind: str = "PersistentBucketCredentialsList"
    items: list[V1PersistentBucketCredentialCRD]
