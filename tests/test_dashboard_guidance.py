from datetime import timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from app.services.dashboard_guidance import build_dashboard_guidance, food_constraints
from app.services.journey import SystemClock
from app.schemas.retrieval import JourneyPosition


def onboard(client, **updates):
    sid = client.post('/v1/session').json()['session_id']
    payload = dict(session_id=sid, name='Test', journey='pregnant', timeline_mode='week',
                   timeline_value='26', diets=[], allergies=[], symptoms=[])
    payload.update(updates)
    response = client.post('/v1/onboarding', json=payload)
    assert response.status_code == 200, response.text
    return sid, client.get(f'/v1/home/{sid}')


def test_blank_session_cannot_jump_to_default_week():
    client = TestClient(app)
    sid = client.post('/v1/session').json()['session_id']
    assert client.get(f'/v1/home/{sid}').status_code == 409


def test_ordinary_dashboard_does_not_invoke_fixture_or_model():
    client = TestClient(app)
    with patch('api.main.run_compass', side_effect=AssertionError('fixture called')):
        _, response = onboard(client)
    home = response.json()
    assert response.status_code == 200
    assert home['fictional'] is False
    guidance = home['dashboard_guidance']
    assert guidance['trace']['fixture_used'] is False
    assert len(guidance['nutrition']) >= 6
    assert len(guidance['movement']) >= 3
    assert all(section['source_links'] for section in guidance['nutrition'] + guidance['movement'])


def test_week_five_and_26_change_focus_and_progress_without_inventing_intake_changes():
    client = TestClient(app)
    _, early = onboard(client, timeline_value='5')
    _, later = onboard(client, timeline_value='26')
    a, b = [x.json()['dashboard_guidance'] for x in (early, later)]
    assert a['journey']['phase'] == 'First trimester'
    assert b['journey']['phase'] == 'Second trimester'
    assert a['journey']['progress_start'] == 12.5
    assert b['journey']['progress_start'] == 65
    assert a['nutrition_focus'] != b['nutrition_focus']
    assert a['nutrition'][0]['reference'] == b['nutrition'][0]['reference']


def test_every_supported_week_has_sourced_education():
    for week in range(1, 43):
        guidance = build_dashboard_guidance(JourneyPosition(stage='pregnancy', unit='week', exact=week), f'Pregnancy week {week}', diets=[], allergies=[], symptoms=[])
        assert guidance['nutrition'] and guidance['movement']


def test_vegetarian_peanut_and_soy_apply_to_all_food_options():
    client = TestClient(app)
    _, response = onboard(client, diets=['Vegetarian'], allergies=['Peanut', 'Soy'])
    sections = response.json()['dashboard_guidance']['nutrition']
    options = [food for section in sections for food in section['food_options']]
    assert options
    assert all(not set(food['tags']) & {'peanut', 'soy', 'meat', 'egg'} for food in options)


def test_vegan_dairy_free_gluten_free_never_offer_animal_or_gluten_foods():
    client = TestClient(app)
    _, response = onboard(client, diets=['Vegan', 'Gluten-free'], allergies=['Milk'])
    sections = response.json()['dashboard_guidance']['nutrition']
    assert all(not set(food['tags']) & {'animal', 'gluten', 'dairy'} for section in sections for food in section['food_options'])
    assert 'B12' in str(sections)


def test_nonvegetarian_does_not_accidentally_match_vegetarian():
    assert 'meat' not in food_constraints(['Non-vegetarian'], [])['excluded_tags']
    assert 'meat' in food_constraints(['Vegetarian', 'Non-vegetarian'], [])['excluded_tags']


def test_unrecognised_allergy_leaves_nutrient_information_visible():
    client = TestClient(app)
    _, response = onboard(client, allergies=['Peanut and mango'])
    guidance = response.json()['dashboard_guidance']
    assert guidance['unmatched_allergies'] == ['mango']
    assert next(item for item in guidance['nutrition'] if item['id'] == 'protein')['reference'] == '71 g / day'
    assert not any(item['food_options'] for item in guidance['nutrition'])


def test_backache_keeps_dashboard_open_but_does_not_prescribe_exercise():
    client = TestClient(app)
    _, response = onboard(client, symptoms=['Back ache'])
    assert response.status_code == 200
    guidance = response.json()['dashboard_guidance']
    assert guidance['nutrition']
    assert guidance['movement'][0]['id'] == 'back-adjustment'
    assert 'promptly' in str(guidance['movement'][0])
    assert all(section['reference'] != '150 min / week' for section in guidance['movement'])


def test_urgent_symptom_cannot_bypass_onboarding_via_home_endpoint():
    client = TestClient(app)
    _, response = onboard(client, symptoms=['I cannot breathe right now'])
    assert response.status_code == 409


def test_month_range_and_due_date_use_same_resolver_as_dashboard():
    client = TestClient(app)
    for mode, value in [('month', '6'), ('due', (SystemClock().today() + timedelta(weeks=14)).isoformat())]:
        preview = client.post('/v1/timeline', json=dict(journey='pregnant', timeline_mode=mode, timeline_value=value)).json()
        _, response = onboard(client, timeline_mode=mode, timeline_value=value)
        actual = response.json()['dashboard_guidance']['journey']
        assert preview == actual
        assert actual['start'] == (23 if mode == 'month' else 26)
        assert actual['end'] == (27 if mode == 'month' else 26)


def test_postpartum_has_recovery_content_and_no_pregnancy_protein_target():
    client = TestClient(app)
    _, response = onboard(client, journey='postpartum', timeline_mode='birth_date', timeline_value=(SystemClock().today() - timedelta(days=10)).isoformat())
    guidance = response.json()['dashboard_guidance']
    assert guidance['nutrition'] and guidance['movement']
    assert '71 g / day' not in str(guidance)
    assert '150 min / week' not in str(guidance)
    assert response.json()['comparison_preview']['eligible_context'] is False


def test_editing_context_replaces_old_values_and_sessions_remain_separate():
    client = TestClient(app)
    sid, _ = onboard(client, allergies=['Peanut'], symptoms=['Back ache'])
    other_client = TestClient(app)
    other_id, _ = onboard(other_client, allergies=['Soy'])
    client.post('/v1/onboarding', json=dict(session_id=sid, journey='pregnant', timeline_mode='week', timeline_value='5', diets=[], allergies=[], symptoms=[]))
    home = client.get(f'/v1/home/{sid}').json()
    assert home['confirmed_context']['allergies'] == []
    assert home['confirmed_context']['symptoms'] == []
    assert home['journey']['exact'] == 5
    assert other_client.get(f'/v1/home/{other_id}').json()['confirmed_context']['allergies'] == ['Soy']
    assert client.get(f'/v1/home/{other_id}').status_code == 403
