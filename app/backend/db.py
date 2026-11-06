from pathlib import Path
import os
import sqlite3
from sqlalchemy import Engine, URL, create_engine, event

ROOT = Path(__file__).resolve().parents[2]


def runtime_dir() -> Path:
    return Path(os.environ.get("CVH_RUNTIME_DIR", str(ROOT / "runtime"))).resolve()


def make_engine(path: Path) -> Engine:
    engine = create_engine(URL.create("sqlite", database=str(path)), connect_args={"timeout": 5})

    @event.listens_for(engine, "connect")
    def configure(connection: sqlite3.Connection, record: object) -> None:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA journal_mode=WAL")

    return engine
