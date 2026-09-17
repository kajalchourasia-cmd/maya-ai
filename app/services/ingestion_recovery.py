"""Fail-safe source refresh with last-known-good preservation and quarantine."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable


@dataclass(frozen=True)
class RecoveryResult:
    source_id: str
    status: str
    active_sha256: str | None
    quarantine_reason: str | None


class SourceRecoveryStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.active = root / "active"
        self.quarantine = root / "quarantine"

    def refresh(
        self,
        *,
        source_id: str,
        fetch: Callable[[], bytes],
        parse: Callable[[bytes], object],
        expected_sha256: str | None = None,
    ) -> RecoveryResult:
        try:
            raw = fetch()
        except Exception as exc:
            return self._quarantine(source_id, "fetch_failed", None, type(exc).__name__)
        actual = sha256(raw).hexdigest()
        if expected_sha256 is not None and actual != expected_sha256:
            return self._quarantine(source_id, "hash_changed", actual, None)
        try:
            parse(raw)
        except Exception as exc:
            return self._quarantine(source_id, "parse_failed", actual, type(exc).__name__)

        self.active.mkdir(parents=True, exist_ok=True)
        target = self.active / f"{source_id}.json"
        record = {"source_id": source_id, "sha256": actual, "byte_size": len(raw)}
        if target.is_file():
            existing = json.loads(target.read_text(encoding="utf-8"))
            if existing == record:
                return RecoveryResult(source_id, "unchanged", actual, None)
        with NamedTemporaryFile(
            "w", dir=self.active, delete=False, encoding="utf-8"
        ) as stream:
            temporary = Path(stream.name)
            json.dump(record, stream, sort_keys=True)
            stream.write("\n")
        temporary.replace(target)
        return RecoveryResult(source_id, "promoted", actual, None)

    def active_sha256(self, source_id: str) -> str | None:
        path = self.active / f"{source_id}.json"
        if not path.is_file():
            return None
        return str(json.loads(path.read_text(encoding="utf-8"))["sha256"])

    def _quarantine(
        self,
        source_id: str,
        reason: str,
        candidate_sha256: str | None,
        error_type: str | None,
    ) -> RecoveryResult:
        self.quarantine.mkdir(parents=True, exist_ok=True)
        active = self.active_sha256(source_id)
        record = {
            "source_id": source_id,
            "reason": reason,
            "candidate_sha256": candidate_sha256,
            "error_type": error_type,
            "preserved_active_sha256": active,
        }
        sequence = len(list(self.quarantine.glob(f"{source_id}-*.json"))) + 1
        path = self.quarantine / f"{source_id}-{sequence:04d}.json"
        path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return RecoveryResult(source_id, "quarantined", active, reason)
