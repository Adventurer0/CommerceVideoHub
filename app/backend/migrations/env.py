from alembic import context
from app.backend.db import make_engine, runtime_dir
from app.backend.models import metadata


def run() -> None:
    directory = runtime_dir()
    if not directory.is_dir():
        raise RuntimeError("Runtime directory missing; use start.ps1 to initialize restricted storage")
    engine = make_engine(directory / "app.db")
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=metadata, render_as_batch=True)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run()
