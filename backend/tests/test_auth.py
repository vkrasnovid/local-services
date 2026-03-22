import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/api/v1/auth/register", json={
        "phone": "+79009876543",
        "password": "SecurePass123!",
        "first_name": "Иван",
        "last_name": "Петров",
        "city": "Москва",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["phone"] == "+79009876543"
    assert data["first_name"] == "Иван"
    assert data["role"] == "client"


@pytest.mark.asyncio
async def test_register_duplicate_phone(client):
    payload = {
        "phone": "+79001111111",
        "password": "SecurePass123!",
        "first_name": "User1",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "phone": "+79002222222",
        "password": "SecurePass123!",
        "first_name": "LoginUser",
    })
    response = await client.post("/api/v1/auth/login", json={
        "phone": "+79002222222",
        "password": "SecurePass123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["phone"] == "+79002222222"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "phone": "+79003333333",
        "password": "SecurePass123!",
        "first_name": "User",
    })
    response = await client.post("/api/v1/auth/login", json={
        "phone": "+79003333333",
        "password": "WrongPassword!",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    await client.post("/api/v1/auth/register", json={
        "phone": "+79004444444",
        "password": "SecurePass123!",
        "first_name": "RefreshUser",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "phone": "+79004444444",
        "password": "SecurePass123!",
    })
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_get_me(client):
    # Register and login to get a token
    await client.post("/api/v1/auth/register", json={
        "phone": "+79005555555",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "phone": "+79005555555",
        "password": "SecurePass123!",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+79005555555"
    assert data["first_name"] == "Test"


@pytest.mark.asyncio
async def test_update_me(client):
    await client.post("/api/v1/auth/register", json={
        "phone": "+79006666666",
        "password": "SecurePass123!",
        "first_name": "Original",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "phone": "+79006666666",
        "password": "SecurePass123!",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.patch("/api/v1/auth/me", json={
        "first_name": "Updated",
        "city": "SPb",
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
    assert response.json()["city"] == "SPb"
