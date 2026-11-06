"""Loopback-only server with graceful local shutdown for PowerShell on Windows."""
import argparse
import asyncio
from contextlib import suppress
from pathlib import Path
import uvicorn


async def serve(port: int, stop_file: Path) -> None:
    server = uvicorn.Server(uvicorn.Config("app.backend.main:app", host="127.0.0.1", port=port, access_log=False))

    async def watch_stop() -> None:
        while not server.should_exit:
            if stop_file.exists():
                server.should_exit = True
                return
            await asyncio.sleep(.2)

    watcher = asyncio.create_task(watch_stop())
    try:
        await server.serve()
    finally:
        watcher.cancel()
        with suppress(asyncio.CancelledError):
            await watcher


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--stop-file", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(serve(args.port, args.stop_file))


if __name__ == "__main__":
    main()
