"""Read-only inventory; archive comments are provenance hints, not git HEAD."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sources = {}
for name in ("mpau", "commerce-publisher", "multipublish"):
    source = (ROOT / "refs" / name).resolve()
    archive = source.with_suffix(".zip")
    result = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True)
    hashes = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(source.rglob("*")) if p.is_file()}
    with zipfile.ZipFile(archive) as z:
        archived = {"/".join(n.split("/")[1:]): hashlib.sha256(z.read(n)).hexdigest()
                    for n in z.namelist() if not n.endswith("/")}
        comment = z.comment.decode("ascii")
    sources[name] = {
        "source": str(source), "archive": str(archive), "archive_commit_hint": comment,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "git_exit_code": result.returncode, "git_stdout": result.stdout.strip(),
        "git_stderr": result.stderr.strip(), "files": hashes,
        "archive_matches_directory": archived == hashes,
        "tree_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
    }
out = ROOT / "docs" / "SOURCE_MANIFEST.json"
if out.exists():
    before = json.loads(out.read_text(encoding="utf-8"))
    for name in sources:
        if before[name]["files"] != sources[name]["files"]:
            raise SystemExit(f"REFERENCE CHANGED: {name}")
else:
    out.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")
for name, value in sources.items():
    print(name, value["archive_commit_hint"], "archive_matches=", value["archive_matches_directory"],
          "files=", len(value["files"]), "git_exit=", value["git_exit_code"])
