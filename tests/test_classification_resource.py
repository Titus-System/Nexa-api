# Teste unitário de ClassificationResource para verificar:
# se a rota existe,
# se valida o payload,
# se retorna o status code correto,


import json
import pytest
from app import create_app
from app.containers import Container


class FakeService:
    def start_single_classification(self, schema):
        return "fake-task-id"


@pytest.fixture
def client():
    # substitui a dependência antes de criar o app
    container = Container()
    container.classification_service.override(FakeService())

    app = create_app(container)
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


payload = {
    "partnumber": "1234",
    "description": "descr",
    "manufacturer": "manuf",
}


def test_classification_resource_success(client):
    response = client.post(
        "/classify-partnumber",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 202
    data = response.get_json()
    assert data["message"] == "Seu pedido de classificação foi aceito..."
    assert data["task_id"] == "fake-task-id"


def test_classification_resource_invalid_payload(client):
    response = client.post(
        "/classify-partnumber",
        data=json.dumps({}),
        content_type="application/json"
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "errors" in data
