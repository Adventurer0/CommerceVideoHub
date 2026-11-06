import pytest
from alembic import command
from sqlalchemy import insert, inspect, text
from sqlalchemy.exc import IntegrityError
from app.backend.models import (
    media_assets, products, shop_accounts, product_mappings,
    publish_drafts, publish_jobs, publish_evidence,
)


def seed(engine):
    with engine.begin() as c:
        c.execute(insert(media_assets), dict(id="m", path="fixture.mp4", sha256="a"*64, created_at="2026-11-06T00:00:00Z"))
        c.execute(insert(products), dict(id="p", internal_sku="SKU-1", name="fixture"))
        c.execute(insert(shop_accounts), [dict(id=a, platform="douyin", shop_id=a, name=a, profile_key=a) for a in ("a", "b")])
        c.execute(insert(product_mappings), [dict(id=a, internal_product_id="p", account_id=a, external_product_id=pid) for a, pid in (("a", "00017"), ("b", "different-17"))])
        c.execute(insert(publish_drafts), dict(id="d", media_id="m", title="fixture"))


def job(**changes):
    return dict(id="j", draft_id="d", account_id="a", mapping_id="a", publish_version=1,
                idempotency_key="key", target_snapshot={}) | changes


def test_migration_restart_wal_and_foreign_keys(database):
    engine, path, config = database
    command.upgrade(config, "head")
    assert set(inspect(engine).get_table_names()) == {
        "alembic_version", "media_assets", "products", "shop_accounts", "product_mappings",
        "publish_drafts", "publish_jobs", "publish_evidence", "job_events",
    }
    with engine.connect() as c:
        assert c.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"
        assert c.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        assert c.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0001"
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(config, "head")
    assert "publish_evidence" in inspect(engine).get_table_names()


def test_shop_specific_ids_and_cross_shop_job_rejected(database):
    engine, _, _ = database
    seed(engine)
    with engine.connect() as c:
        assert c.execute(text("SELECT external_product_id FROM product_mappings WHERE id='a'")).scalar_one() == "00017"
    with pytest.raises(IntegrityError):
        with engine.begin() as c:
            c.execute(insert(publish_jobs), job(mapping_id="b"))


@pytest.mark.parametrize("changes", [dict(id="other"), dict(id="other", idempotency_key="different")])
def test_duplicate_publish_blocked_by_database(database, changes):
    engine, _, _ = database
    seed(engine)
    with engine.begin() as c:
        c.execute(insert(publish_jobs), job())
    with pytest.raises(IntegrityError):
        with engine.begin() as c:
            c.execute(insert(publish_jobs), job(**changes))


def test_duplicate_product_mapping_rejected(database):
    engine, _, _ = database
    seed(engine)
    with pytest.raises(IntegrityError):
        with engine.begin() as c:
            c.execute(insert(product_mappings), dict(id="wrong", account_id="a", internal_product_id="p", external_product_id="other"))


def test_verification_records_are_separate_and_require_evidence(database):
    engine, _, _ = database
    seed(engine)
    with engine.begin() as c:
        c.execute(insert(publish_jobs), job())
        c.execute(insert(publish_evidence), dict(id="e", job_id="j", kind="post", verification_status="verified",
            post_id="remote-post", reference="local-evidence", observed_at="2026-11-06T00:00:00Z", target_snapshot={}))
        c.execute(insert(publish_evidence), dict(id="e2", job_id="j", kind="product", verification_status="manual_required",
            observed_at="2026-11-06T00:00:00Z", target_snapshot={}))
    with pytest.raises(IntegrityError):
        with engine.begin() as c:
            c.execute(insert(publish_evidence), dict(id="e3", job_id="j", kind="product", verification_status="verified",
                post_id="remote-post", reference="local", observed_at="2026-11-06T00:00:00Z", target_snapshot={}))
