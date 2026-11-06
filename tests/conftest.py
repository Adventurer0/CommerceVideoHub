from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from app.backend.db import ROOT, make_engine


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setenv("CVH_RUNTIME_DIR", str(tmp_path))
    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    engine = make_engine(tmp_path / "app.db")
    yield engine, tmp_path, config
    engine.dispose()
