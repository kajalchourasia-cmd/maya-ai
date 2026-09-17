"""Deterministic, source-linked overview content. Never calls a model or index.

Editorial highlights are not measured nutrient deficits, mood predictions or
clinical clearance. These records do not publish the separate draft RAG corpus.
"""
from copy import deepcopy
import json
from pathlib import Path

from app.services.content_selection import MONTH_RANGES

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = json.loads((ROOT / 'data/dashboard/overview_catalogue.json').read_text(encoding='utf-8'))
REFERENCE = json.loads((ROOT / 'data/dashboard/reference_catalogue.json').read_text(encoding='utf-8'))
SOURCES = {**REFERENCE['sources'], **CATALOGUE['sources']}
for week in range(4, 42):
    trimester = '1st' if week <= 12 else '2nd' if week <= 27 else '3rd'
    SOURCES[f'week{week}'] = {
        'title': f'NHS: week {week}',
        'url': f'https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/{trimester}-trimester/week-{week}/',
        'locator': 'What does my baby look like? / What is happening in my body?',
        'jurisdiction': 'UK general education; typical development, not an individual assessment',
    }


def sourced(record):
    result = deepcopy(record)
    result['source_links'] = [dict(id=key, **SOURCES[key]) for key in result.pop('source_ids')]
    return result


def static_overview(journey, *, movement_limited=False):
    """Input is the server-resolved timeline, never a client default week."""
    start = journey.exact if journey.exact is not None else journey.range_start
    end = journey.exact if journey.exact is not None else journey.range_end
    if start is None or end is None or start > end:
        raise ValueError('A resolved timeline is required')
    pregnant = journey.stage == 'pregnancy'
    if pregnant and not 1 <= start <= end <= 42:
        raise ValueError('Overview supports pregnancy weeks 1–42')
    if not pregnant and (journey.unit != 'week' or not 1 <= start <= end <= 12):
        raise ValueError('Overview supports postpartum weeks 1–12')
    months = [m for m, (lo, hi) in MONTH_RANGES.items() if lo <= end and hi >= start] if pregnant else []
    # Onboarding month ranges match MONTH_RANGES. Wider ranges never choose an
    # arbitrary month: only shared FAQs are returned with explicit range wording.
    faq_ids = CATALOGUE['monthly_faqs'][str(months[0])] if pregnant else CATALOGUE['postpartum_faqs']
    for month in months[1:]:
        faq_ids = [key for key in faq_ids if key in CATALOGUE['monthly_faqs'][str(month)]]
    faqs = [sourced(dict(id=key, **CATALOGUE['faq_records'][key])) for key in faq_ids]
    if pregnant:
        profiles = [p for p in CATALOGUE['profiles'] if p['start'] <= end and p['end'] >= start]
        if len(profiles) == 1:
            p = profiles[0]
        else:
            # Broad supported guidance, not an exact-week forecast at a boundary.
            p = dict(nutrition=['Protein','Calcium'], nutrition_detail='Two pregnancy-wide highlights within a varied diet.',
                     nutrition_sources=['diet','calcium'], energy='Make space for yourself',
                     energy_detail='Make time for a comfortable rest and something you enjoy.', energy_sources=['rest','wellbeing'],
                     movement='Move at your pace', movement_detail='Choose comfortable activity within your care-team advice.',
                     movement_sources=['exercise'], maternal='early')
        nutrition = sourced(dict(title=' + '.join(p['nutrition']), body=p['nutrition_detail'], source_ids=p['nutrition_sources']))
        energy = sourced(dict(title=p['energy'], body=p['energy_detail'], source_ids=p['energy_sources']))
        movement = sourced(dict(title=p['movement'], body=p['movement_detail'], source_ids=p['movement_sources']))
        maternal = sourced(CATALOGUE['maternal_facts'][p['maternal']])
        if start == end:
            w, title, body, source = next(row for row in CATALOGUE['weekly_baby_facts'] if row[0] == start)
            baby = sourced(dict(id=f'baby-week-{w}', title=title, body=body, source_ids=[source]))
            baby['timing_label'] = f'Week {w} · typical development' if w > 3 else f'Week {w} · understanding your timeline'
        else:
            # All range-selected facts retain their own week label; no claim
            # that every milestone occurs throughout an approximate month.
            baby = None
    else:
        nutrition = sourced(dict(title='Protein + calcium', body='Two food highlights within a varied recovery diet; not a breastfeeding intake target.', source_ids=['diet','calcium','postpartum']))
        energy = sourced(dict(title='Let care include you', body='Accept a helping hand and make room for rest where you can.', source_ids=['postnatal_rest']))
        movement = sourced(dict(title='Recover at your pace', body='Your recovery and birth experience guide the return to activity.', source_ids=['postpartum']))
        maternal = sourced(CATALOGUE['maternal_facts']['postpartum'])
        baby = None
    if movement_limited:
        movement = sourced(dict(title='Comfort and support', body='Keep your reported symptoms or restrictions in view. Ask your care team which activities suit you before increasing activity.', source_ids=['exercise'] if pregnant else ['postpartum']))
    maternal['timing_label'] = ('For your current stage' if start != end else f'Week {start} · for you') if pregnant else 'For your recovery'
    return dict(version=CATALOGUE['version'], source_checked_on=CATALOGUE['source_checked_on'],
                review_status=CATALOGUE['review_status'], clinical_approval=None,
                nutrition=nutrition, energy=energy, movement=movement, baby_fact=baby, maternal_fact=maternal,
                faq_label=(f'Month {months[0]} · questions you may have' if len(months)==1 else 'Questions for your stage') if pregnant else 'Questions after birth',
                faq_month=months[0] if len(months)==1 else None, faqs=faqs,
                timing_note=CATALOGUE['mapping_note'],
                trace=dict(model_called=False, retrieval_called=False, selection='static_catalogue'))
