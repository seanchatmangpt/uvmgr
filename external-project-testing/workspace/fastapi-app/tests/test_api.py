
import pytest
from fastapi.testclient import TestClient
from fastapi_external_test.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_item():
    item_data = {
        "name": "Test Item",
        "price": 10.5,
        "is_offer": True
    }
    response = client.post("/items/", json=item_data)
    assert response.status_code == 200
    assert response.json()["item"]["name"] == "Test Item"

def test_read_item():
    response = client.get("/items/1?q=test")
    assert response.status_code == 200
    assert response.json()["item_id"] == 1
    assert response.json()["q"] == "test"
