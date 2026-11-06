"""Six-platform boundary; identifiers and independent evidence never collapse."""
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Generic, NewType, Protocol, TypeVar

AccountId = NewType("AccountId", str)
MediaId = NewType("MediaId", str)
ExternalProductId = NewType("ExternalProductId", str)
JobId = NewType("JobId", str)


class Platform(StrEnum):
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    WEIXIN = "weixin"
    TAOBAO = "taobao"
    JD = "jd"
    PDD = "pdd"


class Outcome(StrEnum):
    OK = "ok"
    UNSUPPORTED = "unsupported"
    MANUAL_REQUIRED = "manual_required"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ErrorCode(StrEnum):
    UNSUPPORTED = "unsupported"
    LOGIN_REQUIRED = "login_required"
    RISK_CHALLENGE = "risk_challenge"
    INVALID_CONTENT = "invalid_content"
    PRODUCT_NOT_FOUND = "product_not_found"
    PRODUCT_AMBIGUOUS = "product_ambiguous"
    PRODUCT_PERMISSION = "product_permission"
    IDENTITY_MISMATCH = "identity_mismatch"
    TRANSIENT_BEFORE_SUBMIT = "transient_before_submit"
    SUBMISSION_UNKNOWN = "submission_unknown"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"


@dataclass(frozen=True)
class ProductTarget:
    platform: Platform
    account_id: AccountId
    shop_id: str
    external_product_id: ExternalProductId

    def __post_init__(self) -> None:
        if any(not value or value != value.strip() for value in
               (self.account_id, self.shop_id, self.external_product_id)):
            raise ValueError("Target IDs must be nonempty exact strings")


@dataclass(frozen=True)
class Account:
    account_id: AccountId
    platform: Platform
    shop_id: str
    profile_key: str  # Opaque key only, never cookies or a browser profile payload.


@dataclass(frozen=True)
class PublishRequest:
    job_id: JobId
    media_id: MediaId
    target: ProductTarget
    title: str
    description: str = ""
    tags: tuple[str, ...] = ()
    platform_fields: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    job_id: JobId
    target: ProductTarget
    reference: str  # Local, redacted evidence key; never raw page/cookie data.


@dataclass(frozen=True)
class ProductResolution(Evidence):
    match_count: int


@dataclass(frozen=True)
class UploadEvidence(Evidence):
    upload_id: str


@dataclass(frozen=True)
class ProductAttachmentEvidence(Evidence):
    product_id_seen: ExternalProductId


@dataclass(frozen=True)
class SubmissionEvidence(Evidence):
    submission_id: str


@dataclass(frozen=True)
class PostVerification(Evidence):
    post_id: str
    verified: bool


@dataclass(frozen=True)
class ProductVerification(Evidence):
    post_id: str
    product_id_seen: ExternalProductId
    verified: bool


T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    outcome: Outcome
    data: T | None = None
    error: ErrorCode | None = None


@dataclass(frozen=True)
class AdapterContext:
    operation_id: str  # Worker-owned reference, no live browser object in API data.


class PlatformAdapter(Protocol):
    @property
    def platform(self) -> Platform: ...
    async def check_login(self, account: Account) -> Result[bool]: ...
    async def validate_content(self, job: PublishRequest) -> Result[bool]: ...
    async def resolve_product(self, job: PublishRequest) -> Result[ProductResolution]: ...
    async def upload_media(self, job: PublishRequest, context: AdapterContext) -> Result[UploadEvidence]: ...
    async def attach_product(self, job: PublishRequest, context: AdapterContext) -> Result[ProductAttachmentEvidence]: ...
    async def submit(self, job: PublishRequest, context: AdapterContext) -> Result[SubmissionEvidence]: ...
    async def verify_post(self, job: PublishRequest, context: AdapterContext) -> Result[PostVerification]: ...
    async def verify_product(self, job: PublishRequest, context: AdapterContext) -> Result[ProductVerification]: ...
