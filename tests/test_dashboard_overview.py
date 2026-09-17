from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from app.schemas.retrieval import JourneyPosition
from app.services.content_selection import MONTH_RANGES
from app.services.dashboard_overview import CATALOGUE, SOURCES, static_overview
from app.services.journey import SystemClock
from tests.test_dashboard_guidance import onboard


@pytest.mark.parametrize('week', range(1, 43))
def test_every_week_uses_existing_mapping_and_sourced_content(week):
    content = static_overview(JourneyPosition(stage='pregnancy', unit='week', exact=week))
    expected = next(m for m, (lo, hi) in MONTH_RANGES.items() if lo <= week <= hi)
    assert content['faq_month'] == expected
    assert len(content['faqs']) in (6, 7)
    assert content['baby_fact']['id'] == f'baby-week-{week}'
    for key in ('nutrition','energy','movement','baby_fact','maternal_fact'):
        assert content[key]['source_links'] and content[key]['body']
    assert len(content['nutrition']['title'].split(' + ')) == 2
    assert content['trace'] == dict(model_called=False, retrieval_called=False, selection='static_catalogue')
    assert content['clinical_approval'] is None


@pytest.mark.parametrize('month', range(1,10))
def test_month_input_never_fabricates_exact_week(month):
    lo, hi = MONTH_RANGES[month]
    content = static_overview(JourneyPosition(stage='pregnancy',unit='week',range_start=lo,range_end=hi))
    assert content['faq_month'] == month
    assert content['baby_fact'] is None
    assert len(content['faqs']) == 6


@pytest.mark.parametrize('week', range(1,13))
def test_postpartum_has_no_fetal_facts(week):
    content = static_overview(JourneyPosition(stage='postpartum',unit='week',exact=week))
    assert content['baby_fact'] is None
    assert content['faq_month'] is None
    assert all(q['id'].startswith('pp') for q in content['faqs'])


def test_catalogue_has_no_missing_sources_or_duplicate_week_ids():
    assert [r[0] for r in CATALOGUE['weekly_baby_facts']] == list(range(1,43))
    for row in CATALOGUE['weekly_baby_facts']:
        assert row[3] in SOURCES
    for record in [*CATALOGUE['faq_records'].values(), *CATALOGUE['maternal_facts'].values()]:
        assert all(s in SOURCES for s in record['source_ids'])
    for ids in CATALOGUE['monthly_faqs'].values():
        assert len(ids) == len(set(ids)) == 6
        assert all(key in CATALOGUE['faq_records'] for key in ids)
    assert all(s['url'].startswith('https://') for s in SOURCES.values())


def test_normal_api_no_provider_calls_and_shared_context_edits():
    client = TestClient(app)
    with patch('app.services.grounded_runtime._connected_runtime', side_effect=AssertionError('Static dashboard called generation')):
        sid, response = onboard(client, diets=['Vegan'], allergies=['Peanut'], restrictions=['No strenuous exercise'])
        home = response.json()
        content = home['dashboard_guidance']['overview_content']
        assert content['faq_month'] == 6
        assert content['movement']['title'] == 'Comfort and support'
        assert home['confirmed_context']['symptoms'] == []
        assert all(not set(food['tags']) & {'peanut','animal'} for section in home['dashboard_guidance']['nutrition'] for food in section['food_options'])
        changed = client.post('/v1/onboarding',json=dict(session_id=sid, name='', journey='pregnant',timeline_mode='week',timeline_value='6',diets=[],allergies=[],symptoms=[]))
        assert changed.status_code == 200
        newer = client.get(f'/v1/home/{sid}').json()['dashboard_guidance']['overview_content']
        assert newer['faq_month'] == 2
        assert newer['baby_fact']['id'] == 'baby-week-6'
        assert newer['movement']['title'] != content['movement']['title']


def test_due_date_matches_equivalent_week():
    client = TestClient(app)
    _, exact = onboard(client, timeline_value='26')
    due = (SystemClock().today() + timedelta(weeks=14)).isoformat()
    _, dated = onboard(client, timeline_mode='due', timeline_value=due)
    assert dated.status_code == 200
    assert dated.json()['dashboard_guidance']['overview_content'] == exact.json()['dashboard_guidance']['overview_content']


def test_positive_themes_do_not_predict_user_feelings():
    for record in CATALOGUE['profiles']:
        text = (record['energy'] + ' ' + record['energy_detail']).lower()
        assert not any(term in text for term in ('you will feel', 'you are calm', 'stressed', 'feeling low', 'hormone level'))
