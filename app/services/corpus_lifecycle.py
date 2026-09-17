"""Versioned local corpus/index lifecycle used by Stage 1 promotion and Stage 5."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile, mkdtemp
from typing import Any, Literal

from pydantic import Field, model_validator

from app.schemas.content import Contract


class IndexedEvidence(Contract):
    evidence_id: str
    source_id: str
    source_snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    release_status: Literal["published"]
    source_status: Literal["published"]
    candidate_status: Literal["published"]
    span_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    payload: dict[str, Any] = Field(default_factory=dict)


class CorpusIndexManifest(Contract):
    schema_version: Literal["nestline-corpus-index-v1"] = "nestline-corpus-index-v1"
    index_version: str
    corpus_version: str
    release_version: str
    entries: list[IndexedEvidence] = Field(min_length=1)
    content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def unique_and_digest_valid(self):
        ids = [item.evidence_id for item in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("index evidence IDs must be unique")
        expected = index_digest(
            self.index_version,
            self.corpus_version,
            self.release_version,
            self.entries,
        )
        if self.content_digest != expected:
            raise ValueError("index content digest does not match its entries")
        return self


class ActiveIndexPointer(Contract):
    schema_version: Literal["nestline-active-index-v1"] = "nestline-active-index-v1"
    active_index_version: str
    previous_index_version: str | None = None
    generation: int = Field(ge=1)


def index_digest(
    index_version: str,
    corpus_version: str,
    release_version: str,
    entries: list[IndexedEvidence],
) -> str:
    payload = {
        "index_version": index_version,
        "corpus_version": corpus_version,
        "release_version": release_version,
        "entries": [
            item.model_dump(mode="json")
            for item in sorted(entries, key=lambda value: value.evidence_id)
        ],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


class VersionedCorpusIndexStore:
    """Immutable builds plus an atomic active pointer and one-step rollback."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.versions = root / "versions"
        self.pointer_path = root / "active.json"

    def build(
        self,
        *,
        index_version: str,
        corpus_version: str,
        release_version: str,
        entries: list[IndexedEvidence],
    ) -> tuple[CorpusIndexManifest, Literal["created", "unchanged"]]:
        manifest = CorpusIndexManifest(
            index_version=index_version,
            corpus_version=corpus_version,
            release_version=release_version,
            entries=sorted(entries, key=lambda value: value.evidence_id),
            content_digest=index_digest(
                index_version, corpus_version, release_version, entries
            ),
        )
        self.versions.mkdir(parents=True, exist_ok=True)
        target = self.versions / index_version
        raw = (
            json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
        if target.exists():
            existing = CorpusIndexManifest.model_validate_json(
                (target / "manifest.json").read_text(encoding="utf-8")
            )
            if existing != manifest:
                raise ValueError("immutable index version already has different content")
            return existing, "unchanged"
        temporary = Path(mkdtemp(prefix=f".{index_version}-", dir=self.versions))
        try:
            (temporary / "manifest.json").write_bytes(raw)
            temporary.replace(target)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return manifest, "created"

    def read_version(self, index_version: str) -> CorpusIndexManifest:
        path = self.versions / index_version / "manifest.json"
        if not path.is_file():
            raise FileNotFoundError(f"index version is unavailable: {index_version}")
        return CorpusIndexManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def active_pointer(self) -> ActiveIndexPointer | None:
        if not self.pointer_path.is_file():
            return None
        return ActiveIndexPointer.model_validate_json(
            self.pointer_path.read_text(encoding="utf-8")
        )

    def activate(self, index_version: str) -> ActiveIndexPointer:
        self.read_version(index_version)
        current = self.active_pointer()
        if current and current.active_index_version == index_version:
            return current
        pointer = ActiveIndexPointer(
            active_index_version=index_version,
            previous_index_version=(current.active_index_version if current else None),
            generation=(current.generation + 1 if current else 1),
        )
        self._write_pointer(pointer)
        return pointer

    def rollback(self) -> ActiveIndexPointer:
        current = self.active_pointer()
        if current is None or current.previous_index_version is None:
            raise ValueError("no previous valid index is available")
        self.read_version(current.previous_index_version)
        pointer = ActiveIndexPointer(
            active_index_version=current.previous_index_version,
            previous_index_version=current.active_index_version,
            generation=current.generation + 1,
        )
        self._write_pointer(pointer)
        return pointer

    def active_manifest(self) -> CorpusIndexManifest:
        pointer = self.active_pointer()
        if pointer is None:
            raise ValueError("no active index is configured")
        return self.read_version(pointer.active_index_version)

    def rebuild_without_source(
        self,
        *,
        source_id: str,
        new_index_version: str,
        new_corpus_version: str,
        new_release_version: str,
    ) -> CorpusIndexManifest:
        active = self.active_manifest()
        remaining = [item for item in active.entries if item.source_id != source_id]
        if len(remaining) == len(active.entries):
            raise ValueError("withdrawn source was not present in the active index")
        if not remaining:
            raise ValueError("cannot activate an empty public index")
        manifest, _ = self.build(
            index_version=new_index_version,
            corpus_version=new_corpus_version,
            release_version=new_release_version,
            entries=remaining,
        )
        self.activate(new_index_version)
        return manifest

    def _write_pointer(self, pointer: ActiveIndexPointer) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(pointer.model_dump(mode="json"), indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
        with NamedTemporaryFile("wb", dir=self.root, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        temporary.replace(self.pointer_path)
