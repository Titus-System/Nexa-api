import pytest
from app import create_app  # supondo que você tenha um factory
import json
from app.config import settings

@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def test_check_health(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["resposta"] == f"{settings.APP_NAME} backend está rodando."


def test_check_ws_connection_success(client):
    response = client.post(
        "/ws",
        data=json.dumps({"socket_session_id": "abc123"}),
        content_type="application/json"
    )
    assert response.status_code == 202
    data = response.get_json()
    assert data["socket_session_id"] == "abc123"
    assert data["message"] == "Conexão websocket ativa e saudável."


def test_check_ws_connection_missing_sid(client):
    response = client.post(
        "/ws",
        data=json.dumps({}),
        content_type="application/json"
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
