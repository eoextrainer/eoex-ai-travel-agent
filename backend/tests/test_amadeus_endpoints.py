import json

def test_health_endpoint(client):
    resp = client.get('/api/amadeus/health')
    assert resp.status_code == 200
    data = resp.json()
    assert 'status' in data

