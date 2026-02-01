import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest_asyncio
from src.main import app
from src.db.models import Base
from src.db.database import get_db
import src.views.routes as routes_module

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
class FakeRabbitMQClient:
    async def publish_task(self, task_id: int, payload: str) -> None:
        return None

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session



@pytest_asyncio.fixture
async def client(monkeypatch):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.dependency_overrides[get_db] = override_get_db

    monkeypatch.setattr(
        routes_module,
        "rabbitmq_client",
        FakeRabbitMQClient(),
    )


    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)




@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_create_task(client):
    response = await client.post(
        "/tasks",
        json={"payload": "test task"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "task_id" in data
    assert isinstance(data["task_id"], int)


@pytest.mark.asyncio
async def test_create_task_empty_payload(client):
    response = await client.post(
        "/tasks",
        json={"payload": ""}
    )
    assert response.status_code == 422  


@pytest.mark.asyncio
async def test_get_task(client):
    create_response = await client.post(
        "/tasks",
        json={"payload": "test task"}
    )
    task_id = create_response.json()["task_id"]
    
    response = await client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["payload"] == "test task"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_nonexistent_task(client):
    response = await client.get("/tasks/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
