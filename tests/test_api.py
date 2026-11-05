import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import Store, store


@pytest.fixture(autouse=True)
def fresh_store():
    # 테스트마다 주문 상태를 초기화
    fresh = Store()
    store._orders = fresh._orders
    store._next_id = fresh._next_id
    yield


client = TestClient(app)


def place(items):
    return client.post("/api/orders", json={"items": items})


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_index_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "키오스크" in res.text


def test_menu_list_and_filter():
    all_items = client.get("/api/menu").json()
    assert len(all_items) >= 1
    burgers = client.get("/api/menu", params={"category": "버거"}).json()
    assert burgers and all(m["category"] == "버거" for m in burgers)


def test_menu_item_not_found():
    assert client.get("/api/menu/9999").status_code == 404


def test_create_order_computes_total_on_server():
    res = place([{"menu_id": 1, "quantity": 2}, {"menu_id": 6, "quantity": 1}])
    assert res.status_code == 201
    order = res.json()
    assert order["total"] == 6500 * 2 + 2000
    assert order["status"] == "received"
    assert order["number"] == 1


def test_order_numbers_increment():
    first = place([{"menu_id": 1, "quantity": 1}]).json()
    second = place([{"menu_id": 1, "quantity": 1}]).json()
    assert second["number"] == first["number"] + 1


def test_unknown_menu_rejected():
    assert place([{"menu_id": 9999, "quantity": 1}]).status_code == 404


def test_sold_out_rejected():
    assert place([{"menu_id": 8, "quantity": 1}]).status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"items": []},
        {"items": [{"menu_id": 1, "quantity": 0}]},
        {"items": [{"menu_id": 1, "quantity": 100}]},
        {},
    ],
)
def test_invalid_order_payload(payload):
    assert client.post("/api/orders", json=payload).status_code == 422


def test_get_and_list_orders():
    order = place([{"menu_id": 2, "quantity": 1}]).json()
    assert client.get(f"/api/orders/{order['id']}").json()["id"] == order["id"]
    assert len(client.get("/api/orders").json()) == 1
    assert client.get("/api/orders/999").status_code == 404


def test_status_flow_and_filter():
    order = place([{"menu_id": 2, "quantity": 1}]).json()
    url = f"/api/orders/{order['id']}/status"
    for status in ("preparing", "ready", "completed"):
        res = client.patch(url, json={"status": status})
        assert res.status_code == 200
        assert res.json()["status"] == status
    assert len(client.get("/api/orders", params={"status": "completed"}).json()) == 1
    assert client.get("/api/orders", params={"status": "received"}).json() == []


def test_invalid_status_transition():
    order = place([{"menu_id": 2, "quantity": 1}]).json()
    url = f"/api/orders/{order['id']}/status"
    assert client.patch(url, json={"status": "completed"}).status_code == 409
    client.patch(url, json={"status": "cancelled"})
    assert client.patch(url, json={"status": "preparing"}).status_code == 409


def test_update_status_unknown_order():
    res = client.patch("/api/orders/999/status", json={"status": "preparing"})
    assert res.status_code == 404
