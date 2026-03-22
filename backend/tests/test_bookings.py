import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_booking_slot_not_found(client):
    # Register and login
    await client.post("/api/v1/auth/register", json={
        "phone": "+79008888888",
        "password": "SecurePass123!",
        "first_name": "BookingUser",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "phone": "+79008888888",
        "password": "SecurePass123!",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/v1/bookings/", json={
        "service_id": str(uuid4()),
        "slot_id": str(uuid4()),
    }, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_bookings(client):
    await client.post("/api/v1/auth/register", json={
        "phone": "+79009999999",
        "password": "SecurePass123!",
        "first_name": "ListUser",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "phone": "+79009999999",
        "password": "SecurePass123!",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/bookings/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
