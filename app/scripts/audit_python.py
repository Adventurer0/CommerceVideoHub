"""Execute original tests without writing into references or opening the network."""
import importlib
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
name = sys.argv[1]
source = (ROOT / "refs" / name).resolve()
sys.path.insert(0, str(source))
with tempfile.TemporaryDirectory(prefix="cvh-audit-") as tmp:
    os.environ["PUBLISHER_RUNTIME_ROOT"] = tmp
    os.environ["PUBLISHER_NOTIFY_URL"] = ""
    config = importlib.import_module("utils.config" if name == "mpau" else "conf")
    config.BASE_DIR = Path(tmp)

    def guard(event, args):
        if event in {"socket.connect", "socket.bind"} and args[1][0] not in {"127.0.0.1", "::1"}:
            raise RuntimeError(f"Offline audit blocked: {event}")
        if event in {"subprocess.Popen", "os.system"}:
            raise RuntimeError(f"Offline audit blocked: {event}")
        if event == "open" and isinstance(args[0], (str, bytes)):
            path = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(x in mode for x in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if writing and path.is_relative_to(source):
                raise RuntimeError("Read-only reference write blocked")

    sys.addaudithook(guard)
    import pytest
    selected = sys.argv[2:]
    paths = [str(source / "tests" / p) for p in selected] if selected else [str(source / "tests")]
    args = [*paths, "-q", "-o", "addopts=", "-p", "no:cacheprovider", "--tb=short"]
    try:
        code = pytest.main(args)
    finally:
        if "loguru" in sys.modules:
            sys.modules["loguru"].logger.remove()
    raise SystemExit(code)
