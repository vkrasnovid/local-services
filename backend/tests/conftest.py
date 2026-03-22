import asyncio
import sqlite3
import uuid as uuid_mod
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import String, Text, event as sa_event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.security import hash_password, create_access_token
from app.models import Base, User
from app.core.database import get_db
from app.main import app

# Register UUID adapter for SQLite
sqlite3.register_adapter(uuid_mod.UUID, lambda u: str(u))
sqlite3.register_converter("UUID", lambda b: uuid_mod.UUID(b.decode()))
sqlite3.register_converter("CHAR(36)", lambda b: b.decode())

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:test.db?mode=memory&cache=shared&uri=true"

_patched = False


def _patch_pg_types_for_sqlite():
    """Replace PostgreSQL-specific column types with SQLite-compatible ones."""
    global _patched
    if _patched:
        return
    _patched = True

    from sqlalchemy.dialects.postgresql import UUID, JSONB

    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, UUID):
                column.type = String(36)
            elif isinstance(column.type, JSONB):
                column.type = Text()
            if column.server_default is not None:
                try:
                    text = str(column.server_default.arg)
                    if "gen_random_uuid" in text:
                        column.server_default = None
                except Exception:
                    pass


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    _patch_pg_types_for_sqlite()
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    user = User(
        id=uuid4(),
        phone="+79001234567",
        email="test@example.com",
        password_hash=hash_password("TestPass123!"),
        first_name="Test",
        last_name="User",
        role="client",
        city="Moscow",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(str(test_user.id), test_user.role)
    return {"Authorization": f"Bearer {token}"}
