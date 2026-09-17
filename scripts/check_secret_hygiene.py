from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai_key": re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b"),
    "xai_key": re.compile(r"\bxai-[A-Za-z0-9_-]{20,}\b"),
    "supabase_secret": re.compile(r"\bsb_secret_[A-Za-z0-9_-]{20,}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
}
SAFE_MARKERS = ("fake", "fictional", "fixture", "example", "placeholder", "redacted", "test-only")


def repository_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    findings: list[dict[str, object]] = []
    scanned = 0
    for path in repository_files():
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for pattern_name, pattern in PATTERNS.items():
                for match in pattern.finditer(line):
                    window = lowered[max(0, match.start() - 40) : match.end() + 40]
                    if any(marker in window for marker in SAFE_MARKERS):
                        continue
                    findings.append(
                        {"file": path.relative_to(ROOT).as_posix(), "line": line_number, "pattern": pattern_name}
                    )
    ignored_env = subprocess.run(
        ["git", "check-ignore", "-q", ".env"], cwd=ROOT, check=False
    ).returncode == 0
    valid = not findings and ignored_env
    print(
        json.dumps(
            {
                "valid": valid,
                "files_scanned": scanned,
                "credential_findings": len(findings),
                "env_ignored": ignored_env,
                "findings": findings,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if valid else 1

if __name__ == "__main__":
    raise SystemExit(main())
