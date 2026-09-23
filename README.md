# Host and User Management System

This application is a complete Full Stack system for registering and managing hosts/servers and users. The architecture is composed of a dynamic HTML/JS/Bootstrap frontend, a RESTful Python backend built with **FastAPI**, **SQLAlchemy** and **Alembic**, and a relational **PostgreSQL** database, all orchestrated through **Docker Compose** (with support for a **Kubernetes environment via Kind**).

---

## 🏗️ Project Structure

Below is the directory and file map of the project:

```text
.
├── README.md
├── docker-compose.yml
├── kind-config.yaml
├── openapi.json
├── scripts/
│   └── smoke_test.sh
├── backend/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── database.py
│   ├── export_openapi.py
│   ├── main.py
│   ├── models.py
│   ├── openapi.json
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── schemas.py
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 001_initial_hosts_migration.py
│   │       ├── 002_add_usuario_table.py
│   │       └── 003_rename_schema_to_english.py
│   └── tests/
│       ├── conftest.py
│       ├── test_contract.py
│       ├── test_database.py
│       ├── test_hosts.py
│       ├── test_migrations.py
│       ├── test_startup.py
│       └── test_users.py
└── frontend/
    ├── Dockerfile
    ├── index.html
    └── script.js
```

---

## 📄 Component and File Details

### 🌐 Project Root (Infrastructure & Configuration)

- **[`README.md`](file:///home/ebwang/repos/daronco/README.md)**: Main project documentation with the architecture overview, a detailed component description and the execution guide.
- **[`docker-compose.yml`](file:///home/ebwang/repos/daronco/docker-compose.yml)**: Docker orchestration file that defines and connects the 3 microservices of the application:
  - `postgres`: PostgreSQL 15-alpine database (port `5432`).
  - `backend`: Python/FastAPI API service built from the `./backend` directory (port `8000`), configured to wait for the database health check before starting.
  - `frontend`: Nginx web server built from the `./frontend` directory (port `80`).
- **[`kind-config.yaml`](file:///home/ebwang/repos/daronco/kind-config.yaml)**: Configuration file used to provision a local Kubernetes cluster with Kind (*Kubernetes in Docker*), setting up 1 *control-plane* node and 2 *worker* nodes with a port mapping to the host (port `30000`).
- **[`scripts/smoke_test.sh`](file:///home/ebwang/repos/daronco/scripts/smoke_test.sh)**: Manual smoke test that exercises the whole flow against the running API through `curl` (user creation, duplicated username, linked host, error responses and cascade deletion), cleaning up the data it creates.

---

### ⚙️ Backend (`/backend`) — Python API & Database

- **[`backend/main.py`](file:///home/ebwang/repos/daronco/backend/main.py)**: Entry point of the API web server built with FastAPI.
  - Configures the CORS middleware to allow requests from external origins.
  - Applies the pending Alembic migrations on startup through the `lifespan` handler.
  - Defines the REST routes of the application:
    - **Users** (`GET /api/users`, `POST /api/users`, `GET /api/users/{id}`, `DELETE /api/users/{id}`).
    - **Hosts** (`GET /api/hosts`, `POST /api/hosts`, `DELETE /api/hosts/{id}`).
- **[`backend/database.py`](file:///home/ebwang/repos/daronco/backend/database.py)**: Sets up the connection plumbing with PostgreSQL using SQLAlchemy.
  - Reads the database URL from the `DATABASE_URL` environment variable (with a local fallback).
  - Creates the engine, the session factory (`SessionLocal`) and the declarative base class (`Base`).
  - Provides the `get_db()` dependency that safely opens and closes one session per HTTP request.
- **[`backend/models.py`](file:///home/ebwang/repos/daronco/backend/models.py)**: Object-Relational Mapping (ORM) of the PostgreSQL tables.
  - `User`: Declarative class for the `users` table (id, first name, last name, username, address, creation date) with a one-to-many relationship and cascade deletion of hosts.
  - `Host`: Declarative class for the `hosts` table (hostname, manufacturer, model, technical specifications, `user_id` foreign key and a many-to-one relationship with the user).
- **[`backend/schemas.py`](file:///home/ebwang/repos/daronco/backend/schemas.py)**: Schemas defined with **Pydantic v2** for request validation and JSON response serialization.
  - User schemas (`UserBase`, `UserCreate`, `UserResponse`, `UserSimpleResponse`).
  - Host schemas (`HostBase`, `HostCreate`, `HostResponse`).
- **[`backend/requirements.txt`](file:///home/ebwang/repos/daronco/backend/requirements.txt)**: Python dependencies required to run the project (`fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `psycopg2-binary`, `alembic`).
- **[`backend/requirements-dev.txt`](file:///home/ebwang/repos/daronco/backend/requirements-dev.txt)**: Extra dependencies used only for development/testing (`pytest`, `httpx2`, `pytest-cov`); they are not installed in the production image.
- **[`backend/Dockerfile`](file:///home/ebwang/repos/daronco/backend/Dockerfile)**: Docker image for the API based on `python:3.11-slim`. It installs the `requirements.txt` dependencies, copies the source code and starts the Uvicorn server listening on port `8000`.
- **[`backend/alembic.ini`](file:///home/ebwang/repos/daronco/backend/alembic.ini)**: Global configuration file of the Alembic database migration tool.
- **[`backend/alembic/env.py`](file:///home/ebwang/repos/daronco/backend/alembic/env.py)**: Alembic environment script that integrates the SQLAlchemy models (`Base.metadata`) and the database URL for online and offline migrations.
- **[`backend/alembic/script.py.mako`](file:///home/ebwang/repos/daronco/backend/alembic/script.py.mako)**: Code template used by Alembic when generating new migration revisions.
- **[`backend/alembic/versions/001_initial_hosts_migration.py`](file:///home/ebwang/repos/daronco/backend/alembic/versions/001_initial_hosts_migration.py)**: First database migration, responsible for creating the `hosts` table and its indexes.
- **[`backend/alembic/versions/002_add_usuario_table.py`](file:///home/ebwang/repos/daronco/backend/alembic/versions/002_add_usuario_table.py)**: Second database migration, responsible for creating the `usuarios` table and adding the `user_id` column/foreign key to the `hosts` table.
- **[`backend/alembic/versions/003_rename_schema_to_english.py`](file:///home/ebwang/repos/daronco/backend/alembic/versions/003_rename_schema_to_english.py)**: Third database migration, which renames the `usuarios` table to `users` and the Portuguese column names to English ones, preserving every existing row (with a complete `downgrade` that reverts each rename).

---

### 🎨 Frontend (`/frontend`) — Web Interface

- **[`frontend/index.html`](file:///home/ebwang/repos/daronco/frontend/index.html)**: Visual interface of the application written in HTML5 and styled with Bootstrap 5 and Bootstrap Icons. It contains the form to register new hosts, the dynamic visualization table and the API status alerts.
- **[`frontend/script.js`](file:///home/ebwang/repos/daronco/frontend/script.js)**: *Client-side* JavaScript logic. It performs HTTP requests (`fetch`) against the backend REST API to fetch the server list, register new hosts and delete existing hosts, keeping the DOM updated without reloading the page.
- **[`frontend/Dockerfile`](file:///home/ebwang/repos/daronco/frontend/Dockerfile)**: Docker image for the web container based on `nginx:alpine`. It copies the static files (`index.html` and `script.js`) into the publishable Nginx directory on port `80`.

---

## 🚀 How to Run

### With Docker Compose

1. Make sure Docker and Docker Compose are installed on your machine.
2. From the repository root, run:
   ```bash
   docker-compose up --build
   ```
3. Access the available services:
   - **Frontend interface**: [http://localhost](http://localhost)
   - **Backend API (Swagger documentation)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Automated Tests (Backend)

The suite lives in **[`backend/tests`](file:///home/ebwang/repos/daronco/backend/tests)** and uses **pytest** + **FastAPI TestClient**, with full database isolation for every test. By default it runs on in-memory SQLite (no Docker needed); setting `TEST_DATABASE_URL` makes it run against a real PostgreSQL and enables the migration/constraint tests.

### Suite structure

| File | Coverage |
| --- | --- |
| `tests/conftest.py` | Engine/session/HTTP client fixtures, payload factories and the test database switch (`TEST_DATABASE_URL`) |
| `tests/test_users.py` | `/api/users` CRUD, duplicated username `400`, `404`/`422` and cascade deletion of hosts |
| `tests/test_hosts.py` | `/api/hosts` CRUD, `user_id` validation, payload `422` and ordering by `id` |
| `tests/test_migrations.py` | `postgres` marker: schema/indexes/FK created by Alembic, `upgrade`/`downgrade` and real PostgreSQL constraints |
| `tests/test_contract.py` | Contract guard: routes exposed in OpenAPI, Swagger (`/docs`) and versioned `openapi.json` synchronization |
| `tests/test_database.py` | `get_db()` session lifecycle and `SessionLocal` configuration |
| `tests/test_startup.py` | API startup handler (Alembic execution and `Base.metadata.create_all` fallback) |

### Installing the test dependencies

```bash
cd backend
../.venv/bin/python -m pip install -r requirements-dev.txt
```

### 1) Fast suite — in-memory SQLite (no Docker/PostgreSQL)

```bash
cd backend
../.venv/bin/python -m pytest -q
```

### 2) Integration suite — real PostgreSQL (includes migrations and constraints)

```bash
# Creates the test database (only once)
docker exec hosts_postgres createdb -U postgres hosts_db_test

cd backend
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hosts_db_test \
  ../.venv/bin/python -m pytest -q
```

- Without `TEST_DATABASE_URL`, the tests marked with `@pytest.mark.postgres` are skipped automatically.
- **Data protection**: the suite aborts when `TEST_DATABASE_URL` does not end with `_test`, preventing accidental `DROP`/`TRUNCATE` on the development database (`hosts_db`).

### 3) Manual smoke test against the Docker Compose stack (recommended before delivering)

```bash
cd /home/ebwang/repos/daronco
./scripts/smoke_test.sh                                # uses http://localhost:8000
API=http://192.168.0.10:8000 ./scripts/smoke_test.sh   # another host/port
```

The script exercises the whole flow against the real API (user creation, duplicated username, linked host, 404/422 responses and cascade deletion) and **removes the data it created at the end**, leaving the database as it was. It exits with code `0` when every step passes.

### Code coverage (optional)

```bash
cd backend
../.venv/bin/python -m pytest -q \
  --cov=main --cov=models --cov=schemas --cov=database --cov-report=term-missing
```
