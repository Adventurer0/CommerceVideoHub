"""Pure transition policy only. No scheduler, retries, browser or publication."""
from enum import StrEnum
from .contracts import PostVerification, ProductVerification, PublishRequest


class JobState(StrEnum):
    PENDING = "pending"
    PREFLIGHT = "preflight"
    LOGIN_CHECK = "login_check"
    UPLOADING = "uploading"
    ATTACHING_PRODUCT = "attaching_product"
    SUBMITTING = "submitting"
    VERIFYING = "verifying"
    SUCCESS = "success"
    MANUAL_REQUIRED = "manual_required"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_PERMANENT = "failed_permanent"
    UNKNOWN = "unknown"
    CANCELLED = "cancelled"


FLOW = (JobState.PENDING, JobState.PREFLIGHT, JobState.LOGIN_CHECK,
        JobState.UPLOADING, JobState.ATTACHING_PRODUCT, JobState.SUBMITTING,
        JobState.VERIFYING, JobState.SUCCESS)
ALLOWED = {a: {b} for a, b in zip(FLOW, FLOW[1:])}
for state in FLOW[:5]:
    ALLOWED[state].update({JobState.MANUAL_REQUIRED, JobState.FAILED_RETRYABLE,
                           JobState.FAILED_PERMANENT, JobState.CANCELLED})
for state in (JobState.SUBMITTING, JobState.VERIFYING):
    ALLOWED[state].update({JobState.UNKNOWN, JobState.MANUAL_REQUIRED})
ALLOWED[JobState.UNKNOWN] = {JobState.VERIFYING, JobState.MANUAL_REQUIRED}
ALLOWED[JobState.FAILED_RETRYABLE] = {JobState.PREFLIGHT, JobState.CANCELLED}


def transition(current: JobState, desired: JobState, *, job: PublishRequest,
               post: PostVerification | None = None,
               product: ProductVerification | None = None) -> JobState:
    if desired not in ALLOWED.get(current, set()):
        raise ValueError(f"Forbidden transition: {current} -> {desired}")
    if desired == JobState.SUCCESS:
        if not post or not product or not post.verified or not product.verified:
            raise ValueError("Independent post and product verification required")
        if (post.job_id != job.job_id or product.job_id != job.job_id
                or post.target != job.target or product.target != job.target
                or not post.post_id or post.post_id != product.post_id
                or product.product_id_seen != job.target.external_product_id
                or not post.reference or not product.reference):
            raise ValueError("Evidence identity mismatch or missing evidence")
    return desired
