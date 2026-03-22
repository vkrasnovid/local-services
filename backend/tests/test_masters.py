import pytest


@pytest.mark.asyncio
async def test_list_masters(client):
    response = await client.get("/api/v1/masters/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_masters_with_filters(client):
    response = await client.get("/api/v1/masters/", params={
        "city": "Moscow",
        "sort_by": "rating",
        "page": 1,
        "page_size": 10,
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_switch_to_master(client):
    await client.post("/api/v1/auth/register", json={
        "phone": "+79007777777",
        "password": "SecurePass123!",
        "first_name": "MasterUser",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "phone": "+79007777777",
        "password": "SecurePass123!",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/v1/auth/switch-role", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "master"
