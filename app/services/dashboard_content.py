"""Published weekly-card assembly; authored drafts never enter the dashboard."""

from app.schemas.content import Applicability, ContentBundle
from app.schemas.retrieval import JourneyPosition
from app.services.content_selection import select_content


SLOT_DOMAIN = {
    "what_may_change": ("health", "This week"),
    "nutrition_focus": ("nutrition", "Nutrition"),
    "movement_focus": ("movement", "Movement"),
    "wellbeing_focus": ("wellbeing", "Wellbeing"),
    "symptom_education": ("symptoms", "Symptoms"),
    "preparation": ("preparation", "Preparation"),
    "consider": ("health", "Consider"),
    "avoid": ("health", "Avoid"),
    "ask_a_professional": ("preparation", "Ask a professional"),
}


def _scope(journey: JourneyPosition) -> Applicability | None:
    if journey.stage == "pregnancy":
        start = journey.exact if journey.exact is not None else journey.range_start
        end = journey.exact if journey.exact is not None else journey.range_end
        if start is None or end is None:
            return None
        return Applicability(stage="pregnancy", unit="week", start=start, end=end)
    if journey.stage == "postpartum" and journey.exact is not None and 1 <= journey.exact <= 12:
        return Applicability(
            stage="postpartum", unit="week", start=journey.exact, end=journey.exact,
        )
    return None


def released_weekly_cards(bundle: ContentBundle, journey: JourneyPosition) -> list[dict]:
    """Return only published profile fragments with their exact source URLs."""

    scope = _scope(journey)
    if scope is None:
        return []
    selection = select_content(bundle, scope, "IN")
    fragments = {item.fragment_id: item for item in bundle.fragments}
    evidence = {item.evidence_id: item for item in bundle.evidence}
    sources = {item.source_id: item for item in bundle.sources}
    cards: list[dict] = []
    for profile_id in selection["profile_ids"]:
        for slot, entries in selection["profile_cards"][profile_id].items():
            domain, title = SLOT_DOMAIN[slot]
            for entry in entries:
                if entry["state"] != "shown" or entry["fragment_id"] is None:
                    continue
                fragment = fragments[entry["fragment_id"]]
                links = []
                for evidence_id in fragment.evidence_span_ids:
                    source = sources[evidence[evidence_id].source_id]
                    link = {"title": source.title, "url": source.canonical_url}
                    if link not in links:
                        links.append(link)
                cards.append({
                    "card_id": f"{profile_id}-{fragment.fragment_id}",
                    "domain": domain,
                    "title": title,
                    "summary": fragment.text,
                    "journey_scope": f"{scope.stage} {scope.unit} {scope.start}",
                    "evidence_ids": fragment.evidence_span_ids,
                    "review_state": "released",
                    "display_allowed": True,
                    "limitations": [
                        "Educational guidance, not a diagnosis or an individualized medical plan.",
                    ],
                    "source_links": links,
                    "suggested_action": "Ask Maya a related question",
                })
    return cards
