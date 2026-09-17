"""Build the visible Stage 10 development-evaluation manifest from focused tests."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_state_lifecycle import StateCommitterTests


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evals/stage10_state_lifecycle.jsonl"


def _domain(name: str) -> str:
    for token, domain in (
        ("review", "simulated_review"), ("reminder", "follow_up"),
        ("follow_up", "follow_up"), ("plan", "plan_lifecycle"),
        ("fact", "fact_confirmation"), ("allergen", "constraint_validation"),
        ("workspace", "authorization"), ("agent", "authorization"),
        ("idempot", "idempotency"), ("concurrent", "concurrency"),
        ("audit", "privacy"),
    ):
        if token in name:
            return domain
    return "contract"


def cases() -> list[dict]:
    names = sorted(name for name in dir(StateCommitterTests) if name.startswith("test_"))
    return [{
        "case_id": name.removeprefix("test_"),
        "test_method": name,
        "domain": _domain(name),
        "critical": any(token in name for token in (
            "unauthorized", "cross_workspace", "stale", "conflict", "allergen",
            "medication", "urgent", "agent", "provenance", "rollback",
        )),
        "expected": "pass",
        "fictional": True,
    } for name in names]


def main() -> int:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in cases()), encoding="utf-8")
    print(json.dumps({"valid": True, "cases": len(cases()), "manifest": str(MANIFEST.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
