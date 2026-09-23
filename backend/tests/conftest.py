# backend/tests/conftest.py
"""
Shared configuration for the backend test suite.

Database strategy:
- By default the suite runs on in-memory SQLite (`sqlite://` + StaticPool): fast and
  with no dependency on Docker/PostgreSQL.
- Setting the TEST_DATABASE_URL environment variable to a PostgreSQL URL
  (e.g. postgresql://postgres:postgres@localhost:5432/hosts_db_test) makes the suite run
  against a real database and enables the tests marked with @pytest.mark.postgres.

IMPORTANT: the development database `hosts_db` is never touched. If the given URL does
not end with `_test`, the suite aborts with an error (protection against data loss).
"""

import os
import sys

# ---------------------------------------------------------------------------
# 1. Backend path (the project modules use flat imports: `from database import ...`)
#    and test database configuration. All of it runs before importing the app modules.
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")
IS_SQLITE = TEST_DATABASE_URL.startswith("sqlite")

if not IS_SQLITE:
    _database_name = TEST_DATABASE_URL.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
    if not _database_name.endswith("_test"):
        raise RuntimeError(
            "TEST_DATABASE_URL points to a database without the '_test' suffix "
            f"({TEST_DATABASE_URL!r}). The suite recreates and drops tables and, for "
            "safety, only runs against test databases (e.g. hosts_db_test)."
        )

# Makes sure the application (database.py / alembic) uses the test database.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# ---------------------------------------------------------------------------
# 2. Application imports (after adjusting sys.path and DATABASE_URL)
# ---------------------------------------------------------------------------
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import NullPool, StaticPool  # noqa: E402

import models  # noqa: E402,F401  (registers the tables in Base.metadata)
from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402


# ---------------------------------------------------------------------------
# 3. pytest hooks
# ---------------------------------------------------------------------------
def pytest_collection_modifyitems(config, items):
    """Automatically skips the `postgres` tests when the suite runs on SQLite."""
    if not IS_SQLITE:
        return
    skip = pytest.mark.skip(
        reason="Requires a real PostgreSQL: run with TEST_DATABASE_URL pointing to hosts_db_test"
    )
    for item in items:
        if "postgres" in item.keywords:
            item.add_marker(skip)


# ---------------------------------------------------------------------------
# 4. Infrastructure fixtures
# ---------------------------------------------------------------------------
def _build_engine():
    """Engine isolated for the test suite (never reuses the application engine)."""
    if IS_SQLITE:
        # StaticPool + check_same_thread=False: shares the same connection (and therefore the
        # same in-memory database) between the test thread and the threads used by TestClient.
        return create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(TEST_DATABASE_URL, poolclass=NullPool)


@pytest.fixture(scope="session")
def engine():
    eng = _build_engine()
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def test_database_url():
    """URL of the database used by the suite (in-memory SQLite or the test PostgreSQL)."""
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def alembic_config():
    """Alembic configuration pointing to the test database."""
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    return cfg


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_database(alembic_config):
    """
    In PostgreSQL mode it makes sure the database is at the Alembic `head`, validating
    from the start that the real migrations can be applied to the test database.
    """
    if IS_SQLITE:
        return
    command.upgrade(alembic_config, "head")


def _reset_schema(engine):
    """
    Leaves the schema ready and empty before each test.

    - SQLite: recreates the schema from scratch (strongest possible isolation).
    - PostgreSQL: preserves the schema created by the Alembic migrations (including the
      real constraint name `fk_hosts_user_id`, validated in test_migrations.py) and only
      clears the data with TRUNCATE ... RESTART IDENTITY CASCADE.
    """
    if IS_SQLITE:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    if not IS_SQLITE:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE hosts, users RESTART IDENTITY CASCADE"))


@pytest.fixture
def db_session(engine):
    """SQLAlchemy session over a clean database (full isolation between tests)."""
    _reset_schema(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """
    HTTP test client with the `get_db` dependency overridden to use the test session.

    The TestClient is intentionally used WITHOUT the `with` context manager: that way the
    FastAPI startup handler (`apply_startup_migrations`, which runs `alembic upgrade head`
    through subprocess) is not executed. That behavior is covered in test_startup.py.
    """
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 5. Data fixtures (factories)
# ---------------------------------------------------------------------------
DEFAULT_USER_PAYLOAD = {
    "first_name": "John",
    "last_name": "Doe",
    "username": "jdoe",
    "address": "123 Main Street - NY",
}

DEFAULT_HOST_PAYLOAD = {
    "hostname": "host1",
    "manufacturer": "Dell",
    "model": "PowerEdge R740",
    "cpu": "Intel Xeon E5-2698 v4",
    "cpu_count": 2,
    "ram": "32GB",
    "disk": "1TB",
    "storage_type": "SSD",
    "interfaces": "Ethernet, iSCSI",
    "ips": "192.168.1.10",
    "location": "Room A",
}


@pytest.fixture
def user_payload():
    return dict(DEFAULT_USER_PAYLOAD)


@pytest.fixture
def host_payload():
    return dict(DEFAULT_HOST_PAYLOAD)


@pytest.fixture
def create_user(client):
    """Creates a user through the API and returns the response JSON."""
    def _create(**overrides):
        payload = {**DEFAULT_USER_PAYLOAD, **overrides}
        response = client.post("/api/users", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture
def create_host(client):
    """Creates a host through the API and returns the response JSON."""
    def _create(**overrides):
        payload = {**DEFAULT_HOST_PAYLOAD, **overrides}
        response = client.post("/api/hosts", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _create
