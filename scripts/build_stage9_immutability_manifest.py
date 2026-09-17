"""Freeze cross-platform-stable hashes for Stage 9 UI surfaces excluded from this pass."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/stage9_ui_immutability_manifest.json"
PREFIXES = (
    "streamlit_app.py",
    ".streamlit",
    "app/pages_and_components",
    "assets",
    "docs/stage9-ui-evidence",
)
TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".md", ".py", ".svg", ".toml", ".txt"}


def paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", *PREFIXES],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return sorted(ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item)


def stable_sha256(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    if path.suffix.casefold() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return sha256(data).hexdigest(), "normalized_lf_sha256"
    return sha256(data).hexdigest(), "raw_sha256"


def main() -> int:
    rows = []
    for path in paths():
        digest, hash_mode = stable_sha256(path)
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": digest,
                "hash_mode": hash_mode,
            }
        )
    payload = {
        "schema_version": "stage9-ui-immutability-v2",
        "base_commit": "796c05cd29a055188e86685990078709fca0bfbc",
        "files": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"stage9 excluded files frozen: {len(rows)}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
