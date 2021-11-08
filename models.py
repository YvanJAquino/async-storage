from typing import List, Optional
from pydantic import BaseModel
from httpx import AsyncClient, Request

class BucketPolicyOnly(BaseModel):
    enabled: bool
    lockedTime: Optional[str] = None


class UniformBucketLevelAccess(BaseModel):
    enabled: bool
    lockedTime: Optional[str] = None


class IamConfiguration(BaseModel):
    bucketPolicyOnly: BucketPolicyOnly
    uniformBucketLevelAccess: UniformBucketLevelAccess
    publicAccessPrevention: str


class Versioning(BaseModel):
    enabled: bool


class Website(BaseModel):
    mainPageSuffix: str


class Cor(BaseModel):
    origin: List[str]
    method: List[str]
    responseHeader: Optional[List[str]] = None
    maxAgeSeconds: Optional[int] = None


class Action(BaseModel):
    type: str


class Condition(BaseModel):
    age: int


class RuleItem(BaseModel):
    action: Action
    condition: Condition


class Lifecycle(BaseModel):
    rule: List[RuleItem]


class Bucket(BaseModel):    
    kind: str
    selfLink: str
    id: str
    name: str
    projectNumber: str
    metageneration: str
    location: str
    storageClass: str
    etag: str
    timeCreated: str
    updated: str
    iamConfiguration: IamConfiguration
    locationType: str
    rpo: Optional[str] = None
    defaultEventBasedHold: Optional[bool] = None
    versioning: Optional[Versioning] = None
    satisfiesPZS: Optional[bool] = None
    website: Optional[Website] = None
    cors: Optional[List[Cor]] = None
    lifecycle: Optional[Lifecycle] = None

class Buckets(BaseModel):
    kind: str
    items: List[Bucket]


class Blob(BaseModel):
    kind: str
    id: str
    selfLink: str
    mediaLink: str
    name: str
    bucket: str
    generation: str
    metageneration: str
    contentType: str
    storageClass: str
    size: str
    md5Hash: str
    crc32c: str
    etag: str
    timeCreated: str
    updated: str
    timeStorageClassUpdated: str


class Blobs(BaseModel):
    kind: str
    items: List[Blob]
