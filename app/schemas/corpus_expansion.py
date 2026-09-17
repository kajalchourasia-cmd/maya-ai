"""Review-only authoring extension for recovered text with incomplete source anchors.

The production EvidenceCandidate requires a complete applicability interval and
parsed-original blocks. Do not invent either to force recovered text through it.
These records are never accepted by the production ingestion/retrieval schema.
"""
from typing import Literal
from pydantic import Field, model_validator

from app.schemas.content import Applicability, Checksum, Contract, Domain, Identifier, Jurisdictions, Text
from app.schemas.ingestion import DisplaySlot, ReviewCheck, ReviewRole


class ExpansionUnit(Contract):
    schema_version: Literal['1.0.0'] = '1.0.0'
    unit_id: Identifier
    source_id: Identifier
    canonical_url: str = Field(pattern=r'^https://[^\s]+$')
    source_version: Text
    historical_artifact_sha256: Checksum
    source_governance_checksum: Checksum
    derivative_path: Text
    derivative_sha256: Checksum
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    locator: Text
    heading: Text
    original_text: Text
    text_sha256: Checksum
    normalized_search_text: Text
    domains: list[Domain] = Field(min_length=1)
    display_slots: list[DisplaySlot] = Field(min_length=1)
    source_jurisdiction: Jurisdictions
    proposed_target_jurisdiction: Jurisdictions
    stage_hint: Literal['pregnancy','postpartum']
    source_explicit_applicability: Applicability | None = None
    applicability_basis: Literal['source_literal_range_requires_reconciliation','broad_stage_no_exact_interval']
    inherited_approval: Literal[False] = False
    derivative_anchor_verified: Literal[True] = True
    original_document_anchor_verified: Literal[False] = False
    conditions_resolved: Literal[False] = False
    publication_eligible: Literal[False] = False
    embedding_eligible: Literal[False] = False
    state: Literal['draft_expansion'] = 'draft_expansion'
    required_checks: list[ReviewCheck]
    required_roles: list[ReviewRole]
    unresolved: list[Text] = Field(min_length=1)
    personal_fact_dependencies: list[Text]
    overlapping_existing_evidence_ids: list[Identifier] = Field(default_factory=list)
    related_source_condition_keys: list[Text] = Field(default_factory=list)
    unit_checksum: Checksum

    @model_validator(mode='after')
    def truthful_scope(self):
        if self.end <= self.start:
            raise ValueError('Invalid derivative offsets')
        if (self.source_explicit_applicability is None) != (self.applicability_basis == 'broad_stage_no_exact_interval'):
            raise ValueError('Source range and range basis disagree')
        if self.source_explicit_applicability and self.source_explicit_applicability.stage != self.stage_hint:
            raise ValueError('Source stage mismatch')
        return self
