"""Build the Stage 0 publication-readiness ledger from governed repository data."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/weekly/weekly_content_manifest.jsonl"
FRAGMENTS = ROOT / "data/guidelines/guidance_fragments.jsonl"
SPANS = ROOT / "data/guidelines/section_manifest.jsonl"
SOURCES = ROOT / "data/guidelines/source_registry.csv"
DECISIONS = ROOT / "data/reviews/ingestion_decisions.json"
COMPARISONS = ROOT / "data/catalogues/fetal_size_comparisons.csv"
OUT_JSON = ROOT / "docs/STAGE-0-PUBLICATION-READINESS-LEDGER.json"
OUT_MD = ROOT / "docs/STAGE-0-PUBLICATION-READINESS-SUMMARY.md"


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def decision_status(evidence_ids: list[str], by_evidence, role: str) -> str:
    if not evidence_ids:
        return "not_applicable"
    accepted = {
        evidence_id
        for evidence_id in evidence_ids
        if any(row["role"] == role and row["decision"] == "accepted" for row in by_evidence[evidence_id])
    }
    if accepted == set(evidence_ids):
        return "accepted"
    if accepted:
        return "partial"
    return "pending"


def main() -> int:
    profiles = jsonl(MANIFEST)
    fragments = {row["fragment_id"]: row for row in jsonl(FRAGMENTS)}
    spans = {row["evidence_id"]: row for row in jsonl(SPANS)}
    sources = {row["source_id"]: row for row in csv_rows(SOURCES)}
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))["decisions"]
    by_evidence = defaultdict(list)
    for row in decisions:
        by_evidence[row["evidence_id"]].append(row)
    comparisons = {}
    for row in csv_rows(COMPARISONS):
        details = json.loads(row["details"])
        comparisons[details["profile_id"]] = {
            "item_id": row["item_id"],
            "status": row["status"],
            "measurement_basis": details.get("measurement_basis"),
            "measurement_value": details.get("measurement_value"),
            "object_dimension_mm": details.get("object_dimension_mm"),
            "illustrative_only": details.get("illustrative_only"),
            "clinical_review_status": details.get("clinical_review_status", "pending"),
            "product_editorial_review_status": details.get("editorial_review_status", "pending"),
            "proposal_source": details.get("proposal_source"),
            "hide_reason": details.get("hide_reason"),
            "eligible_for_display": bool(
                row["status"] == "published"
                and details.get("measurement_value") is not None
                and details.get("object_dimension_mm") is not None
                and details.get("clinical_review_status") == "accepted"
                and details.get("editorial_review_status") == "accepted"
            ),
        }

    ledger_profiles = []
    for profile in sorted(profiles, key=lambda row: row["profile_id"]):
        evidence_ids = sorted(set(profile["source_evidence_ids"]))
        fragment_ids = sorted(set(profile["guidance_fragment_ids"]))
        source_spans = []
        source_ids = set()
        for evidence_id in evidence_ids:
            span = spans[evidence_id]
            source_ids.add(span["source_id"])
            source_spans.append({
                "evidence_id": evidence_id,
                "source_id": span["source_id"],
                "locator": span["locator"],
                "page": span.get("page"),
                "text_checksum": span["text_checksum"],
                "status": span["status"],
            })
        source_governance = []
        for source_id in sorted(source_ids):
            source = sources[source_id]
            source_governance.append({
                "source_id": source_id,
                "source_status": source["status"],
                "reuse_status": source["reuse_status"],
                "allowed_use": json.loads(source["allowed_use"] or "[]"),
                "attribution_text": source["attribution_text"],
                "revalidation_status": source["revalidation_status"],
                "next_review_at": source["next_review_at"] or None,
            })
        categories = sorted({fragments[item]["domain"] for item in fragment_ids})
        content_status = decision_status(evidence_ids, by_evidence, "content")
        product_status = decision_status(evidence_ids, by_evidence, "product")
        licence_ready = all(
            item["reuse_status"] == "permitted"
            and item["source_status"] != "excluded"
            and "display" in item["allowed_use"]
            for item in source_governance
        )
        currency_ready = all(
            item["revalidation_status"] == "current_capture"
            for item in source_governance
        )
        comparison = comparisons.get(profile["profile_id"])
        blockers = list(profile.get("publication_blockers") or [])
        explicit_blockers = []
        if content_status != "accepted":
            explicit_blockers.append("content review incomplete")
        if product_status != "accepted":
            explicit_blockers.append("product/editorial review incomplete")
        explicit_blockers.extend([
            "clinical review pending",
            "India-localisation review pending",
        ])
        if not licence_ready:
            explicit_blockers.append("source reuse/licence decision incomplete")
        if not currency_ready:
            explicit_blockers.append("source currency review incomplete")
        if comparison and not comparison["eligible_for_display"]:
            explicit_blockers.append("comparison measurement/editorial review incomplete; hidden")
        ledger_profiles.append({
            "profile_id": profile["profile_id"],
            "journey_state": profile["applies_to"],
            "content_categories": categories,
            "fragment_ids": fragment_ids,
            "source_evidence_ids": evidence_ids,
            "source_spans": source_spans,
            "source_governance": source_governance,
            "review_status": {
                "content": content_status,
                "clinical": "pending",
                "india_localisation": "pending",
                "product_editorial": product_status,
                "licence_reuse": "ready_from_registry" if licence_ready else "pending_or_blocked",
                "source_currency": "current_capture" if currency_ready else "pending_or_blocked",
            },
            "comparison": comparison or {"status": "not_applicable", "eligible_for_display": False},
            "publication_status": profile["status"],
            "publication_eligible": False,
            "blocked_reasons": sorted(set(blockers + explicit_blockers)),
        })

    counts = {
        "profiles": len(ledger_profiles),
        "sources": len(sources),
        "source_spans": len(spans),
        "guidance_fragments": len(fragments),
        "published_profiles": sum(row["publication_status"] == "published" for row in ledger_profiles),
        "publication_eligible_profiles": sum(row["publication_eligible"] for row in ledger_profiles),
        "comparisons": len(comparisons),
        "display_eligible_comparisons": sum(row["eligible_for_display"] for row in comparisons.values()),
        "content_accepted_profiles": sum(row["review_status"]["content"] == "accepted" for row in ledger_profiles),
        "product_accepted_profiles": sum(row["review_status"]["product_editorial"] == "accepted" for row in ledger_profiles),
    }
    assert counts["profiles"] == 63
    assert counts["sources"] == 31
    assert counts["source_spans"] == 55
    assert counts["guidance_fragments"] == 56
    assert counts["published_profiles"] == 0
    assert counts["display_eligible_comparisons"] == 0
    ledger = {
        "schema_version": "nestline-publication-readiness-v1",
        "generated_from": [str(path.relative_to(ROOT)).replace("\\", "/") for path in (
            MANIFEST, FRAGMENTS, SPANS, SOURCES, DECISIONS, COMPARISONS
        )],
        "counts": counts,
        "demonstration_slice": ["PC00", "P10", "PP01"],
        "human_authority_truth": {
            "clinical": "pending",
            "india_localisation": "pending",
            "licence": "pending where registry is not fully permitted/current",
            "product_content": "accepted only where governed Kajal decisions exist",
        },
        "profiles": ledger_profiles,
    }
    OUT_JSON.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    review_counts = Counter(row["review_status"]["product_editorial"] for row in ledger_profiles)
    lines = [
        "# Stage 0 publication-readiness summary",
        "",
        "This file is generated by `python -m scripts.build_publication_readiness`. It is a governance ledger, not a clinical or publication approval.",
        "",
        "## Reconciliation",
        "",
        f"- Authoring profiles: **{counts['profiles']}**",
        f"- Source-registry entries: **{counts['sources']}**",
        f"- Exact source spans: **{counts['source_spans']}**",
        f"- Guidance fragments: **{counts['guidance_fragments']}**",
        f"- Genuinely published profiles: **{counts['published_profiles']}**",
        f"- Display-eligible fetal comparisons: **{counts['display_eligible_comparisons']} / {counts['comparisons']}**",
        f"- Profiles with complete governed product/editorial decisions: **{review_counts['accepted']} / {counts['profiles']}**",
        "",
        "PC00, P10 and PP01 contain governed Kajal product/content decisions, but clinical, India-localisation and remaining licence/currency decisions are still pending. They remain draft and unavailable to public retrieval. All fetal comparisons remain hidden because measurement/object-dimension and specialist review fields are incomplete.",
        "",
        "## Profile status",
        "",
        "| Profile | Journey | Categories | Content | Clinical | India | Product | Licence/currency | Comparison | Publication |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in ledger_profiles:
        journey = row["journey_state"]
        timing = journey["stage"]
        if journey.get("start") is not None:
            timing += f" {journey['unit']} {journey['start']}–{journey['end']}"
        comparison = row["comparison"]
        comparison_status = (
            "eligible" if comparison.get("eligible_for_display") else comparison.get("status", "hidden")
        )
        source_ready = (
            f"{row['review_status']['licence_reuse']}/{row['review_status']['source_currency']}"
        )
        lines.append(
            f"| {row['profile_id']} | {timing} | {', '.join(row['content_categories']) or 'none'} | "
            f"{row['review_status']['content']} | pending | pending | "
            f"{row['review_status']['product_editorial']} | {source_ready} | "
            f"{comparison_status} | {row['publication_status']} |"
        )
    lines.extend([
        "",
        "The machine-readable ledger contains every evidence ID, exact locator/page/checksum, source reuse decision, attribution field and blocker.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
