# backend/tests/test_migrations.py
"""
Integration tests for the Alembic migrations and the database constraints on real PostgreSQL.

Requires TEST_DATABASE_URL pointing to a database with the `_test` suffix.
When the suite runs on SQLite, every test in this file is skipped (the `postgres` marker).
"""

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.postgres

TABLES = {"hosts", "users"}
EXPECTED_TABLES = TABLES | {"alembic_version"}

USER_COLUMNS = {"id", "first_name", "last_name", "username", "address", "created_at"}
HOST_COLUMNS = {
    "id", "hostname", "manufacturer", "model", "cpu", "cpu_count", "ram", "disk",
    "storage_type", "interfaces", "ips", "location", "user_id",
}

SQL_INSERT_USER = text(
    "INSERT INTO users (first_name, last_name, username, address) "
    "VALUES (:first_name, :last_name, :username, :address)"
)
SQL_INSERT_HOST = text(
    "INSERT INTO hosts (hostname, manufacturer, model, cpu, cpu_count, ram, disk, "
    "storage_type, interfaces, ips, location, user_id) VALUES "
    "('host-1', 'Dell', 'R740', 'Xeon', 2, '32GB', '1TB', 'SSD', 'Eth', '10.0.0.10', "
    "'Room A', :user_id)"
)


def _truncate_tables(engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE hosts, users RESTART IDENTITY CASCADE"))


def test_upgrade_head_creates_the_full_schema(alembic_config, engine):
    command.upgrade(alembic_config, "head")

    inspector = inspect(engine)
    assert EXPECTED_TABLES <= set(inspector.get_table_names())

    assert {column["name"] for column in inspector.get_columns("users")} == USER_COLUMNS
    assert {column["name"] for column in inspector.get_columns("hosts")} == HOST_COLUMNS

    host_indexes = {index["name"] for index in inspector.get_indexes("hosts")}
    assert {"ix_hosts_id", "ix_hosts_hostname"} <= host_indexes

    user_indexes = {index["name"]: index for index in inspector.get_indexes("users")}
    assert user_indexes["ix_users_username"]["unique"] is True

    foreign_keys = inspector.get_foreign_keys("hosts")
    user_foreign_keys = [fk for fk in foreign_keys if fk["referred_table"] == "users"]
    assert len(user_foreign_keys) == 1
    assert user_foreign_keys[0]["constrained_columns"] == ["user_id"]
    assert user_foreign_keys[0]["options"].get("ondelete") == "CASCADE"


def test_database_stays_at_the_alembic_head(alembic_config, engine):
    command.upgrade(alembic_config, "head")
    head_revision = ScriptDirectory.from_config(alembic_config).get_current_head()

    with engine.connect() as conn:
        current_revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    assert current_revision == head_revision


def test_downgrade_base_drops_tables_and_upgrade_recreates_them(alembic_config, engine):
    command.upgrade(alembic_config, "head")
    assert TABLES <= set(inspect(engine).get_table_names())

    command.downgrade(alembic_config, "base")

    assert TABLES.isdisjoint(set(inspect(engine).get_table_names()))

    # Restores the `head` state so the other tests are not affected.
    command.upgrade(alembic_config, "head")
    assert TABLES <= set(inspect(engine).get_table_names())


def test_username_is_unique_at_database_level(alembic_config, engine):
    command.upgrade(alembic_config, "head")
    _truncate_tables(engine)
    with engine.begin() as conn:
        conn.execute(
            SQL_INSERT_USER,
            {
                "first_name": "Ana",
                "last_name": "Silva",
                "username": "duplicated",
                "address": "1 Main Street",
            },
        )

    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                SQL_INSERT_USER,
                {
                    "first_name": "Bruno",
                    "last_name": "Souza",
                    "username": "duplicated",
                    "address": "2 Main Street",
                },
            )


def test_ondelete_cascade_removes_the_user_hosts(alembic_config, engine):
    command.upgrade(alembic_config, "head")
    _truncate_tables(engine)

    with engine.begin() as conn:
        conn.execute(
            SQL_INSERT_USER,
            {
                "first_name": "Ana",
                "last_name": "Silva",
                "username": "cascade",
                "address": "1 Main Street",
            },
        )
        user_id = conn.execute(
            text("SELECT id FROM users WHERE username = 'cascade'")
        ).scalar_one()
        conn.execute(SQL_INSERT_HOST, {"user_id": user_id})
        conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})

    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM hosts")).scalar_one() == 0
