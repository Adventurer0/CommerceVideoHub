"""Disabled implementations deliberately prevent accidental live operations."""
from ..domain.contracts import (
    Account, AdapterContext, ErrorCode, Outcome, Platform, PlatformAdapter,
    PostVerification, ProductAttachmentEvidence, ProductResolution,
    ProductVerification, PublishRequest, Result, SubmissionEvidence, UploadEvidence,
)


class UnimplementedAdapter:
    def __init__(self, platform: Platform):
        self.platform = platform

    async def check_login(self, account: Account) -> Result[bool]:
        return Result(Outcome.MANUAL_REQUIRED, error=ErrorCode.LOGIN_REQUIRED)

    async def validate_content(self, job: PublishRequest) -> Result[bool]:
        return Result(Outcome.UNSUPPORTED, error=ErrorCode.UNSUPPORTED)

    async def resolve_product(self, job: PublishRequest) -> Result[ProductResolution]:
        return Result(Outcome.UNSUPPORTED, error=ErrorCode.UNSUPPORTED)

    async def upload_media(self, job: PublishRequest, context: AdapterContext) -> Result[UploadEvidence]:
        return Result(Outcome.UNSUPPORTED, error=ErrorCode.UNSUPPORTED)

    async def attach_product(self, job: PublishRequest, context: AdapterContext) -> Result[ProductAttachmentEvidence]:
        return Result(Outcome.UNSUPPORTED, error=ErrorCode.UNSUPPORTED)

    async def submit(self, job: PublishRequest, context: AdapterContext) -> Result[SubmissionEvidence]:
        return Result(Outcome.UNSUPPORTED, error=ErrorCode.UNSUPPORTED)

    async def verify_post(self, job: PublishRequest, context: AdapterContext) -> Result[PostVerification]:
        return Result(Outcome.MANUAL_REQUIRED, error=ErrorCode.VERIFICATION_UNAVAILABLE)

    async def verify_product(self, job: PublishRequest, context: AdapterContext) -> Result[ProductVerification]:
        return Result(Outcome.MANUAL_REQUIRED, error=ErrorCode.VERIFICATION_UNAVAILABLE)


REGISTRY: dict[Platform, PlatformAdapter] = {p: UnimplementedAdapter(p) for p in Platform}
