"""Contract tests only: do not claim these execute hosted RAG or generation."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from app.services.product_runtime import get_product_runtime


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.pop(get_product_runtime, None)


def enter(client, **updates):
    sid = client.post('/v1/session').json()['session_id']
    payload = dict(session_id=sid, name='Test user', journey='pregnant',
                   timeline_mode='week', timeline_value='26', diets=['Vegetarian'],
                   allergies=['Peanut'], symptoms=['back ache'])
    payload.update(updates)
    assert client.post('/v1/onboarding', json=payload).status_code == 200
    return sid, payload


def test_missing_library_is_setup_error_never_fixture_answer(client):
    sid, _ = enter(client)
    with patch('api.main.run_compass', side_effect=AssertionError('fixture invoked')):
        for route, body in [('chat', {'text': 'What can I eat?'}), ('plan', {'focus': 'nutrition'})]:
            result = client.post('/v1/' + route, json={'session_id': sid, **body})
            assert result.status_code == 503
            assert result.json()['code'] == 'corpus_not_connected'
            assert 'not a medical safety restriction' in result.json()['detail']


def test_one_context_reaches_both_runtime_entry_points(client):
    sid, _ = enter(client)
    calls = []

    class CaptureRuntime:
        def chat(self, **kwargs):
            calls.append(kwargs)
            return {'display': {'summary': 'Test contract response'}}

        def plan(self, **kwargs):
            calls.append(kwargs)
            return {'display': {'summary': 'Test contract response'}}

    app.dependency_overrides[get_product_runtime] = lambda: CaptureRuntime()
    assert client.post('/v1/chat', json={'session_id': sid, 'text': 'What can I eat?'}).status_code == 200
    assert client.post('/v1/plan', json={'session_id': sid, 'focus': 'nutrition'}).status_code == 200
    assert len(calls) == 2
    for call in calls:
        context = call['context']
        assert context.journey.exact == 26
        assert context.diets == ('Vegetarian',)
        assert context.allergies == ('Peanut',)
        assert context.symptoms == ('back ache',)
        assert context.origin == 'user_entered_session'
    assert calls[0]['context'] == calls[1]['context']
    assert calls[1]['focus'] == 'nutrition'


def test_edit_replaces_context_and_increments_revision(client):
    sid, payload = enter(client)
    first = client.get(f'/v1/context/{sid}').json()
    response = client.post('/v1/onboarding', json={**payload, 'timeline_value': '5',
        'diets': ['Vegan'], 'allergies': [], 'symptoms': []})
    assert response.status_code == 200
    latest = client.get(f'/v1/context/{sid}').json()
    assert latest['state_version'] > first['state_version']
    assert latest['journey']['exact'] == 5
    assert latest['diets'] == ['Vegan']
    assert latest['symptoms'] == latest['allergies'] == []


def test_product_session_cannot_enter_fixture_routes(client):
    sid, payload = enter(client)
    with patch('api.main.run_compass', side_effect=AssertionError('fixture invoked')):
        assert client.post('/v1/demo/chat', json={'session_id': sid, 'text': 'hello'}).status_code == 409
        assert client.post('/v1/demo/plan', json={'session_id': sid}).status_code == 409
        assert client.post(f'/v1/demo/document-sample/{sid}').status_code == 409
        assert client.post('/v1/demo/onboarding', json={**payload, 'use_fictional_sample_record': True}).status_code == 409
    assert client.get(f'/v1/home/{sid}').json()['records'] == []


def test_requires_onboarding_and_keeps_sessions_separate(client):
    sid, _ = enter(client)
    # Separate browser capabilities: knowledge of a UUID must not grant access.
    other = TestClient(app)
    blank = other.post('/v1/session').json()['session_id']
    assert other.get(f'/v1/context/{blank}').status_code == 409
    assert other.post('/v1/chat', json={'session_id': blank, 'text': 'hello'}).status_code == 409
    assert other.get(f'/v1/context/{sid}').status_code == 403
    assert client.get(f'/v1/context/{sid}').json()['allergies'] == ['Peanut']


def test_demo_session_cannot_be_misrepresented_as_product_context(client):
    sid = client.post('/v1/demo/session').json()['session_id']
    assert client.get(f'/v1/context/{sid}').status_code == 409


def test_urgent_response_does_not_require_corpus(client):
    sid, _ = enter(client, symptoms=[])
    response = client.post('/v1/chat', json={'session_id': sid, 'text': 'I am bleeding heavily right now'})
    assert response.status_code == 200
    display = response.json()['display']
    assert display['route'] == 'urgent'
    assert display['ordinary_generation_calls'] == 0
    assert display['summary']


def test_blank_message_does_not_enter_runtime(client):
    sid, _ = enter(client)
    assert client.post('/v1/chat', json={'session_id': sid, 'text': '  '}).status_code == 422
