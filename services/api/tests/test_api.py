from fastapi.testclient import TestClient
from jarvis_api.main import create_app
from jarvis_api.policy import evaluate

client = TestClient(create_app())


def test_live():
    response = client.get('/api/v1/health/live')
    assert response.status_code == 200
    assert response.json()['status'] == 'alive'
    assert response.headers.get('X-Request-ID')


def test_ready_fails_closed_when_not_configured(monkeypatch):
    monkeypatch.delenv('JARVIS_DATABASE_URL', raising=False)
    response = client.get('/api/v1/health/ready')
    assert response.status_code == 503
    assert response.json()['error']['code'] == 'DATABASE_NOT_CONFIGURED'
    assert response.json()['error']['request_id'] == response.headers['X-Request-ID']


def test_policy_denies_by_default():
    assert not evaluate(permission='files:write', grants=frozenset()).allowed
    assert not evaluate(permission='', grants=frozenset({'files:write'})).allowed


def test_policy_only_grants_exact_permission():
    grants = frozenset({'system:read'})
    assert evaluate(permission='system:read', grants=grants).allowed
    assert not evaluate(permission='system:write', grants=grants).allowed


def test_openapi_contains_health_routes():
    paths = client.get('/openapi.json').json()['paths']
    assert '/api/v1/health/live' in paths
    assert '/api/v1/health/ready' in paths
