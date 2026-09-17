"""Real local hybrid search in the explicitly authorised PRIVATE development lane.

No public RPC, application credentials, fabricated approvals, medical generation,
or fixture repository. SQL execution is injected by the local operator command.
Production RetrievalGateway retains its authenticated/released-content policy.
"""
from copy import deepcopy
import math
from time import perf_counter
from typing import Literal

from pydantic import Field

from app.schemas.content import Contract, Domain
from app.schemas.retrieval import JourneyPosition
from app.services.corpus_import import json_sql
from app.services.development_corpus import validate_packet, MODEL, DIMENSIONS
from app.services.foundation import fingerprint
from app.services.retrieval import reciprocal_rank_score

SEARCH_VERSION = 'operator-hybrid-v1'
# Engineering noise floor, NOT a calibrated clinical support/confidence score.
MIN_SIMILARITY = 0.30


class DevelopmentQuery(Contract):
    question: str = Field(min_length=1, max_length=2000)
    domain: Domain
    journey: JourneyPosition
    jurisdiction: Literal['IN', 'US', 'GB'] = 'IN'
    require_known_jurisdiction: bool = False
    active_conditions: list[str] = Field(default_factory=list, max_length=40)
    diets: list[str] = Field(default_factory=list, max_length=20)
    allergies: list[str] = Field(default_factory=list, max_length=40)
    symptoms: list[str] = Field(default_factory=list, max_length=40)
    restrictions: list[str] = Field(default_factory=list, max_length=40)
    session_scope: str = Field(min_length=1, max_length=100)
    state_version: int = Field(ge=1)
    limit: int = Field(default=5, ge=1, le=20)


class DevelopmentRetrievalFailure(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def checked_vector(vector):
    if (not isinstance(vector, list) or len(vector) != DIMENSIONS or
            any(type(v) not in (float, int) or not math.isfinite(v) for v in vector) or
            not any(v != 0 for v in vector)):
        raise DevelopmentRetrievalFailure('invalid_query_embedding')
    return vector


def candidate_filter(record, query):
    """Filter BEFORE ranking/limit. Unknown metadata remains an explicit flag."""
    if record['stage'] != query.journey.stage:
        return 'wrong_stage'
    if query.domain not in record['domains']:
        return 'wrong_domain'
    applies = record['applicability']
    if applies is not None:
        if applies['unit'] != query.journey.unit:
            return 'different_timing_unit'
        if query.journey.start is not None and not (
                applies['start'] <= query.journey.start <= query.journey.end <= applies['end']):
            return 'outside_full_requested_interval'
    jurisdictions = record['origin'].get('candidate', {}).get('jurisdiction', [])
    if jurisdictions and query.jurisdiction not in jurisdictions:
        return 'jurisdiction_mismatch'
    if not jurisdictions and query.require_known_jurisdiction:
        return 'jurisdiction_unresolved'
    active = set(query.active_conditions)
    if not set(record['conditions_required']).issubset(active):
        return 'required_condition_not_reported'
    if set(record['conditions_excluded']) & active:
        return 'excluded_condition_present'
    return None


def source_citation(record):
    origin = record['origin']
    if 'candidate' in origin:
        c = origin['candidate']
        anchor = dict(kind='retained_selection', locator=c['source_locator'],
                      block_ids=c['source_block_ids'], artifact_sha256=c['artifact_sha256'])
        version = c['source_version']
    else:
        c = origin['unit']
        anchor = dict(kind='recovered_derivative', locator=c['locator'],
                      derivative_path=c['derivative_path'], derivative_sha256=c['derivative_sha256'],
                      character_start=c['start'], character_end=c['end'])
        version = c['source_version']
    return dict(source_id=record['source_id'], url=record['canonical_url'],
                source_version=version, text_sha256=record['text_sha256'],
                attribution=record['permission_basis']['attribution'], anchor=anchor)


class OperatorDevelopmentRetrieval:
    """Private query-to-source engine, never an answer/approval adapter.

    No result cache: every call checks database provenance. The caller may reuse
    query vectors only with an exact query/model/corpus checksum match.
    """
    def __init__(self, *, packet, execute_sql):
        validate_packet(packet)
        self.packet = deepcopy(packet)
        self.records = {r['id']: r for r in self.packet['records']}
        self.sql = execute_sql

    def search(self, query: DevelopmentQuery, query_vector: list[float]):
        if not query.question.strip():
            raise DevelopmentRetrievalFailure('invalid_context')
        checked_vector(query_vector)
        started = perf_counter()
        payload = dict(packet=self.packet['packet_checksum'], question=query.question,
                       vector=query_vector, model=MODEL)
        # JSON-as-hex uses the existing safe SQL helper; no query/source text is
        # concatenated into executable SQL. Transaction is read-only and bounded.
        statement = f"""begin read only; set local statement_timeout='5000ms';
        with input as (select {json_sql(payload)} as j),
        terms as (select string_agg(quote_literal(t), ' | ') as q from input,
          unnest(tsvector_to_array(to_tsvector('english',j->>'question'))) t),
        scores as (select e.evidence_id,e.payload,
          ts_rank_cd(e.search_vector,to_tsquery('english',coalesce(terms.q,''))) as fts,
          1-(v.embedding OPERATOR(extensions.<=>) ((input.j->'vector')::text)::extensions.vector) as similarity,
          v.receipt->>'record_checksum' as vector_record_checksum
          from input cross join terms join private.development_evidence e
            on e.packet_checksum=input.j->>'packet'
          join private.development_vectors v on v.packet_checksum=e.packet_checksum
            and v.evidence_id=e.evidence_id and v.model=input.j->>'model')
        select jsonb_build_object('rows',coalesce(jsonb_agg(scores order by evidence_id),'[]'::jsonb)) from scores;
        rollback;"""
        try:
            rows = self.sql(statement)[0]['rows']
        except Exception as exc:
            raise DevelopmentRetrievalFailure('database_unavailable_or_timeout') from exc
        if (len(rows) != len(self.records) or
                {r['evidence_id'] for r in rows} != set(self.records)):
            raise DevelopmentRetrievalFailure('index_incomplete')
        accepted, rejected = [], {}
        for row in rows:
            record = self.records[row['evidence_id']]
            if row['payload'] != record or row['vector_record_checksum'] != record['record_checksum']:
                raise DevelopmentRetrievalFailure('source_integrity_failure')
            if any(type(row[k]) not in (float, int) or not math.isfinite(row[k]) for k in ('fts','similarity')):
                raise DevelopmentRetrievalFailure('invalid_database_score')
            reason = candidate_filter(record, query)
            if reason:
                rejected[record['id']] = reason
            else:
                accepted.append(row)
        components = {
            'full_text': sorted((r for r in accepted if r['fts'] > 0), key=lambda r:(-r['fts'], r['evidence_id'])),
            'vector': sorted((r for r in accepted if r['similarity'] >= MIN_SIMILARITY), key=lambda r:(-r['similarity'], r['evidence_id'])),
        }
        ranks = {}
        for component, hits in components.items():
            for rank, row in enumerate(hits, 1):
                ranks.setdefault(row['evidence_id'], {})[component] = rank
        scored = {r['evidence_id']: r for r in accepted}
        ordered = sorted(ranks, key=lambda rid:(-reciprocal_rank_score(ranks[rid].values()), rid))
        chosen, suppressed = [], {}
        for rid in ordered:
            r = self.records[rid]
            duplicate = next((other for other in chosen if (
                other in r['overlap_ids'] or rid in self.records[other]['overlap_ids'] or
                (r['source_id'] == self.records[other]['source_id'] and r['text_sha256'] == self.records[other]['text_sha256']))), None)
            if duplicate:
                suppressed[rid] = duplicate
            else:
                chosen.append(rid)
        hits = []
        for rid in chosen[:query.limit]:
            r = self.records[rid]
            flags = ['unpublished_development_evidence']
            if r['applicability'] is None:
                flags.append('broad_stage_only_not_exact_week')
            if r['condition_status'].startswith('unresolved'):
                flags.append('conditions_unresolved_not_unconditional')
            if not r['origin'].get('candidate', {}).get('jurisdiction'):
                flags.append('jurisdiction_unresolved')
            hits.append(dict(id=rid, text=r['text'], citation=source_citation(r),
                applicability=r['applicability'], required_conditions=r['conditions_required'],
                excluded_conditions=r['conditions_excluded'], flags=flags,
                component_ranks=ranks[rid], rrf_score=reciprocal_rank_score(ranks[rid].values()),
                lexical_score=scored[rid]['fts'], cosine_similarity=scored[rid]['similarity'],
                eligible_for_generation=False))
        return dict(schema_version=SEARCH_VERSION, packet_checksum=self.packet['packet_checksum'],
            query_context_checksum=fingerprint(query.model_dump(mode='json')),
            lane='private_operator_development', publication_eligible=False,
            outcome='review_restriction' if hits else 'evidence_gap', hits=hits,
            component_counts={k:len(v) for k,v in components.items()},
            rejected=rejected, suppressed_overlaps=suppressed, latency_ms=round((perf_counter()-started)*1000,2),
            answer_generated=False, graph_status='not_available_no_verified_graph_in_development_index',
            constraints=dict(diets=query.diets, allergies=query.allergies, symptoms=query.symptoms,
                             restrictions=query.restrictions, active_conditions=query.active_conditions),
            constraints_applied_to_generated_answer=False)
