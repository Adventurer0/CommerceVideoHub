"""G1 schema draft; business CRUD and the task engine are not implemented."""
from sqlalchemy import (
    JSON, CheckConstraint, Column, ForeignKey, ForeignKeyConstraint, Integer,
    MetaData, String, Table, Text, UniqueConstraint,
)
from ..domain.contracts import Platform
from ..domain.state_machine import JobState

metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s", "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s", "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

media_assets = Table("media_assets", metadata,
    Column("id", String, primary_key=True), Column("path", Text, nullable=False),
    Column("sha256", String(64), nullable=False, unique=True),
    Column("duration_ms", Integer), Column("width", Integer), Column("height", Integer),
    Column("cover_path", Text), Column("created_at", String, nullable=False),
)
products = Table("products", metadata,
    Column("id", String, primary_key=True), Column("internal_sku", String, nullable=False, unique=True),
    Column("name", String, nullable=False), Column("category", String), Column("attributes", JSON),
)
shop_accounts = Table("shop_accounts", metadata,
    Column("id", String, primary_key=True), Column("platform", String, nullable=False),
    Column("shop_id", String, nullable=False), Column("name", String, nullable=False),
    Column("profile_key", String, nullable=False, unique=True),
    Column("login_status", String, nullable=False, server_default="unverified"), Column("last_checked_at", String),
    UniqueConstraint("platform", "shop_id"),
    CheckConstraint("platform IN (" + ",".join(repr(p.value) for p in Platform) + ")", name="platform"),
)
product_mappings = Table("product_mappings", metadata,
    Column("id", String, primary_key=True), Column("internal_product_id", ForeignKey("products.id"), nullable=False),
    Column("account_id", ForeignKey("shop_accounts.id"), nullable=False),
    Column("external_product_id", String, nullable=False), Column("external_name", String),
    Column("url", Text), Column("verified_at", String),
    UniqueConstraint("account_id", "internal_product_id", name="uq_mapping_account_internal_product"),
    UniqueConstraint("account_id", "external_product_id", name="uq_mapping_account_external_product"),
    UniqueConstraint("id", "account_id"),
    CheckConstraint("length(trim(external_product_id)) > 0", name="external_id_nonempty"),
)
publish_drafts = Table("publish_drafts", metadata,
    Column("id", String, primary_key=True), Column("media_id", ForeignKey("media_assets.id"), nullable=False),
    Column("title", String, nullable=False), Column("description", Text, nullable=False, server_default=""),
    Column("tags", JSON), Column("cover_path", Text), Column("platform_fields", JSON),
    Column("version", Integer, nullable=False, server_default="1"),
    CheckConstraint("version > 0", name="positive_version"),
)
publish_jobs = Table("publish_jobs", metadata,
    Column("id", String, primary_key=True), Column("draft_id", ForeignKey("publish_drafts.id"), nullable=False),
    Column("account_id", ForeignKey("shop_accounts.id"), nullable=False), Column("mapping_id", String, nullable=False),
    Column("publish_version", Integer, nullable=False), Column("schedule_at", String),
    Column("status", String, nullable=False, server_default="pending"),
    Column("attempt_count", Integer, nullable=False, server_default="0"),
    Column("idempotency_key", String, nullable=False, unique=True),
    Column("target_snapshot", JSON, nullable=False),
    ForeignKeyConstraint(["mapping_id", "account_id"], ["product_mappings.id", "product_mappings.account_id"]),
    UniqueConstraint("draft_id", "account_id", "publish_version"),
    CheckConstraint("status IN (" + ",".join(repr(s.value) for s in JobState) + ")", name="status"),
    CheckConstraint("attempt_count >= 0 AND publish_version > 0", name="counters"),
)
publish_evidence = Table("publish_evidence", metadata,
    Column("id", String, primary_key=True), Column("job_id", ForeignKey("publish_jobs.id"), nullable=False),
    Column("kind", String, nullable=False), Column("verification_status", String, nullable=False),
    Column("post_id", String), Column("post_url", Text), Column("product_id_seen", String),
    Column("reference", Text), Column("observed_at", String, nullable=False),
    Column("target_snapshot", JSON, nullable=False),
    CheckConstraint("kind IN ('post','product')", name="kind"),
    CheckConstraint("verification_status IN ('unverified','verified','failed','manual_required','unknown')", name="verification_status"),
    CheckConstraint("verification_status != 'verified' OR (post_id IS NOT NULL AND length(post_id)>0 AND reference IS NOT NULL AND length(reference)>0)", name="verified_evidence"),
    CheckConstraint("kind != 'product' OR verification_status != 'verified' OR (product_id_seen IS NOT NULL AND length(product_id_seen)>0)", name="verified_product_id"),
)
job_events = Table("job_events", metadata,
    Column("id", String, primary_key=True), Column("job_id", ForeignKey("publish_jobs.id"), nullable=False),
    Column("timestamp", String, nullable=False), Column("stage", String, nullable=False),
    Column("outcome", String, nullable=False), Column("error_code", String), Column("message", Text),
)
