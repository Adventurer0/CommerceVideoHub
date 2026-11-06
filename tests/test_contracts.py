import asyncio
from dataclasses import replace
import pytest
from app.backend.adapters import REGISTRY
from app.backend.domain.contracts import (
    Account, AccountId, AdapterContext, ExternalProductId, JobId, MediaId,
    Outcome, Platform, PostVerification, ProductTarget, ProductVerification, PublishRequest,
)
from app.backend.domain.state_machine import JobState as S, transition


def request(platform=Platform.DOUYIN):
    return PublishRequest(JobId("j"), MediaId("m"),
        ProductTarget(platform, AccountId("a"), "shop-1", ExternalProductId("00017")), "fixture")


def proofs(job):
    post = PostVerification(job.job_id, job.target, "post-evidence", "post-1", True)
    product = ProductVerification(job.job_id, job.target, "product-evidence", "post-1", job.target.external_product_id, True)
    return post, product


@pytest.mark.parametrize("platform", list(Platform))
def test_every_adapter_is_disabled_and_never_reports_verified(platform):
    async def check():
        adapter = REGISTRY[platform]
        job = request(platform)
        context = AdapterContext("mock")
        assert (await adapter.check_login(Account(AccountId("a"), platform, "shop-1", "key"))).outcome == Outcome.MANUAL_REQUIRED
        assert (await adapter.validate_content(job)).outcome == Outcome.UNSUPPORTED
        assert (await adapter.resolve_product(job)).outcome == Outcome.UNSUPPORTED
        for action in (adapter.upload_media, adapter.attach_product, adapter.submit):
            result = await action(job, context)
            assert result.outcome == Outcome.UNSUPPORTED and result.data is None
        for verify in (adapter.verify_post, adapter.verify_product):
            result = await verify(job, context)
            assert result.outcome == Outcome.MANUAL_REQUIRED and result.data is None
    asyncio.run(check())


def test_success_requires_two_matching_proofs():
    job = request()
    post, product = proofs(job)
    assert transition(S.VERIFYING, S.SUCCESS, job=job, post=post, product=product) == S.SUCCESS
    with pytest.raises(ValueError):
        transition(S.VERIFYING, S.SUCCESS, job=job, post=post)


@pytest.mark.parametrize("field,value", [
    ("post_id", "another-post"), ("product_id_seen", ExternalProductId("17")),
    ("verified", False), ("reference", ""), ("job_id", JobId("other-job")),
    ("target", ProductTarget(Platform.KUAISHOU, AccountId("b"), "other-shop", ExternalProductId("00017"))),
])
def test_mismatched_or_missing_product_evidence_never_success(field, value):
    job = request()
    post, product = proofs(job)
    with pytest.raises(ValueError):
        transition(S.VERIFYING, S.SUCCESS, job=job, post=post, product=replace(product, **{field: value}))


@pytest.mark.parametrize("source,destination", [
    (S.UNKNOWN, S.PENDING), (S.UNKNOWN, S.SUBMITTING), (S.UNKNOWN, S.FAILED_RETRYABLE),
    (S.SUBMITTING, S.FAILED_RETRYABLE), (S.SUBMITTING, S.CANCELLED),
    (S.VERIFYING, S.FAILED_RETRYABLE), (S.PENDING, S.SUCCESS), (S.SUCCESS, S.SUBMITTING),
])
def test_unknown_or_submitted_jobs_cannot_republish(source, destination):
    with pytest.raises(ValueError):
        transition(source, destination, job=request())


def test_unknown_can_only_reconcile_or_stop():
    assert transition(S.UNKNOWN, S.VERIFYING, job=request()) == S.VERIFYING
    assert transition(S.UNKNOWN, S.MANUAL_REQUIRED, job=request()) == S.MANUAL_REQUIRED


@pytest.mark.parametrize("product_id", ["", " ", " 17"])
def test_empty_or_silently_normalized_ids_rejected(product_id):
    with pytest.raises(ValueError):
        ProductTarget(Platform.DOUYIN, AccountId("a"), "shop", ExternalProductId(product_id))
