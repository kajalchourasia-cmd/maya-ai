"""Authored presentation around live evidence, never replacement RAG results.

Week lookups are deterministic, as are dashboard facts. Plan enrichment runs
only AFTER the live runtime returns a validated schedule and preserves its trace.
"""
import re
from uuid import uuid4

from app.schemas.retrieval import JourneyPosition
from app.services.dashboard_overview import static_overview
from app.services.dashboard_guidance import build_dashboard_guidance, CATALOGUE


def week_lookup(context, text):
    normalized = text.strip().lower().rstrip('?.!')
    # Natural phrasing maps to the same source-linked catalogue, not a model
    # response or a change to the user's onboarding timeline.
    match = re.fullmatch(r'how is my baby (?:developing|growing) (?:in |during )?(this week|week \d{1,2})', normalized)
    if match:
        normalized = 'tell me about ' + match.group(1)
    normalized = re.sub(r'^(?:and )?what about (week \d{1,2})$',r'tell me about \1',normalized)
    if not re.fullmatch(r'(?:what(?: is|\'s| happens (?:in|during))|tell me about|explain|what should i know about) (?:pregnancy )?(?:this week|weeks? \d{1,2}(?:\s*(?:and|or|,|/)\s*\d{1,2})?)(?: (?:all )?about)?', normalized):
        return None
    if context.journey.stage != 'pregnancy':
        return None
    weeks = [int(value) for value in re.findall(r'\d+', normalized)]
    if not weeks:
        if context.journey.exact is None:
            return None  # Do not silently collapse a month to one week.
        weeks = [context.journey.exact]
    if any(not 1 <= week <= 42 for week in weeks):
        return None
    paragraphs, citations = [], {}
    for week in dict.fromkeys(weeks):
        content = static_overview(JourneyPosition(stage='pregnancy', unit='week', exact=week))
        facts = [('Baby development', content['baby_fact']), ('For you', content['maternal_fact']),
                 ('Nutrition focus', content['nutrition']), ('Movement focus', content['movement'])]
        paragraphs.append(f'Week {week}\n' + '\n\n'.join(f'{label}: {fact["body"]}' for label, fact in facts if fact))
        for _, fact in facts:
            if not fact:
                continue
            for source in fact['source_links']:
                citations[source['id']] = dict(evidence_id=source['id'], source_id=source['id'],
                    source_title=source['title'], publisher=source['title'].split(':')[0],
                    source_type='catalogue_education', url=source['url'], review_status='source_checked_education',
                    current_status='source_checked', journey_applicability=f'Pregnancy week {week}',
                    locator=source['locator'], supporting_passage='Educational paraphrase: ' + fact['body'], supports_claim=True)
    return dict(mode='private_development', fictional=False, publication_eligible=False,
        display=dict(route='non_urgent', title='Your week-by-week guide', summary='\n\n'.join(paragraphs),
            provenance_sections={}, citations=list(citations.values()),
            uncertainties=['Typical development, not an assessment of your baby. Exploring a week does not change your onboarding timeline. General activity guidance does not override symptoms or restrictions.'],
            applied_constraints=[context.journey_label], proposed_actions=[], validation_display_allowed=True, ordinary_generation_calls=0),
        trace=dict(fixture_used=False, model_called=False, retrieval_called=False, selection='static_week_catalogue', requested_weeks=weeks))


def enrich_plan(response, context):
    schedule = response.get('schedule')
    if not schedule or not schedule.get('items'):
        return response
    guidance = build_dashboard_guidance(context.journey, context.journey_label, diets=list(context.diets),
        allergies=list(context.allergies), symptoms=list(context.symptoms), restrictions=list(context.restrictions + context.active_conditions))
    original = list(schedule['items'])
    live_domains = {item['domain'] for item in original}
    domains = live_domains | set(response.get('trace', {}).get('requested_domains', []))
    missing_domains = sorted(domains - live_domains)
    response['focus'] = next(iter(domains)) if len(domains) == 1 else 'balanced'
    if missing_domains:
        response['display'].setdefault('uncertainties', []).append('No accepted retrieved contribution for ' + ', '.join(missing_domains) + '. Those daily components use the separately cited educational catalogue, not generated claims.')
    days = sorted({item['day'] for item in original}, key=int)
    extras = []
    source_ids = set()
    def add(day, slot, domain, text, sources):
        source_ids.update(sources)
        extras.append(dict(schedule_item_id=str(uuid4()), day=day, start='', end='', slot=slot, domain=domain,
            item=text, evidence_ids=['catalogue-' + key for key in sources], optional=True, origin='source_linked_catalogue',
            constraint_notes=list(context.allergies)))
    if 'nutrition' in domains:
        protein = next((s for s in guidance['nutrition'] if s['id'] in ('protein', 'recovery-meals')), None)
        options = protein['food_options'] if protein else []
        for index, day in enumerate(days):
            for offset, meal in enumerate(('Breakfast', 'Lunch', 'Dinner')):
                selected = [options[(index + offset + j) % len(options)]['label'] for j in range(min(3, len(options)))] if options else []
                text = ('Choose a protein component: ' + ' OR '.join(selected) + '. Add a suitable starchy food and vegetables or fruit to make a varied meal; check all ingredients.') if selected else 'Keep a regular meal routine. Specific food options are withheld because your reported allergens could not be matched reliably; ask your care team for suitable alternatives.'
                add(day, meal, 'nutrition', text, ['diet', 'food_safety'])
            hydration = next((s for s in guidance['nutrition'] if s['id'] == 'hydration'), None)
            add(day, 'Through the day', 'nutrition', hydration['summary'] + ' ' + ' '.join(hydration['bullets']) if hydration else 'Keep drinks within reach. Follow your care team’s fluid advice.', ['water'] if hydration else ['postpartum'])
            add(day, 'Your existing routine', 'nutrition', 'If a supplement was prescribed, follow its existing instructions. This schedule does not add supplements or change doses.', ['pregnancy_nutrients'])
    if 'wellbeing' in domains:
        activities = ['do something you enjoy', 'talk to someone you trust', 'ask for a practical helping hand', 'make time for a quiet pause', 'share how you feel', 'enjoy a relaxing activity', 'reflect on what support would help next week']
        for index, day in enumerate(days):
            add(day, 'Self-love · optional 5-minute pause', 'wellbeing', f'If it suits your day, {activities[index % 7]}. Five minutes is a flexible planning suggestion, not a clinical treatment or target.', ['mental_health'])
    if 'movement' in domains:
        limited = guidance['movement'][0]['tone'] == 'context' or bool(context.restrictions or context.active_conditions)
        for day in days:
            if limited or context.journey.stage != 'pregnancy':
                add(day, 'Movement · your comfort first', 'movement', 'Keep to the activities and limits already agreed with your care team. This plan does not assign a new exercise duration for your symptoms, restrictions or recovery.', ['exercise'] if context.journey.stage == 'pregnancy' else ['postpartum'])
            else:
                add(day, 'Movement · optional starter walk', 'movement', 'If your maternity clinician has said exercise is suitable and you are starting gently, consider a comfortable 10-minute walk. This is an optional starting example, not a personalised target. Stop if you feel unwell; do not push through pain.', ['starter_activity', 'exercise'])
    if 'nutrition' in domains:
        for section in guidance['nutrition']:
            if section['id'] in ('heartburn-adjustment', 'nausea-adjustment', 'allergy-exclusions'):
                for day in days:
                    add(day, section['title'], 'nutrition', section['summary'] + ' ' + ' '.join(section['bullets']), [s['id'] for s in section['source_links']])
    # Retain every accepted live claim and its original citations. Catalogue
    # suggestions are independently labelled and do not count as retrieved claims.
    schedule['items'] = [item for day in days for item in extras + original if item['day'] == day]
    response['display']['title'] = 'Your weekly plan · ' + context.journey_label if len(days) == 7 else 'Your daily plan · ' + context.journey_label
    response['display']['summary'] = 'A flexible schedule using your current timeline and selected context.'
    if 'nutrition' in domains:
        response['display']['summary'] += ' Meal components are suggestions, not a calculated nutritionally complete menu.'
    if 'movement' in domains:
        response['display']['summary'] += ' Any activity duration is conditional guidance, not personal exercise clearance.'
    if domains == {'wellbeing'}:
        response['display']['summary'] += ' Choose one small act of self-care each day; adjust the optional time to suit you.'
    if protein_ref := next((s for s in guidance['nutrition'] if s['id'] == 'protein'), None):
        if 'nutrition' in domains:
            response['display']['summary'] += f' Protein reference: {protein_ref["reference"]} across pregnancy; individual needs vary. This menu has not been calculated to meet that amount.'
    for key in sorted(source_ids):
        source = CATALOGUE['sources'][key]
        response['display']['citations'].append(dict(evidence_id='catalogue-' + key, source_id=key,
            source_title=source['title'], publisher=source['title'].split(':')[0], source_type='catalogue_education',
            url=source['url'], review_status='source_checked_education', current_status='source_checked',
            journey_applicability=context.journey_label, locator=source['locator'],
            supporting_passage='Authored planning suggestions based on this source. Meal allocation and optional self-care time are editorial choices, not quotations or clinical prescriptions.', supports_claim=True))
    response['trace']['presentation'] = dict(kind='live_RAG_with_authored_schedule_components', catalogue_version=guidance['version'], added_items=len(extras), catalogue_only_domains=missing_domains)
    return response
