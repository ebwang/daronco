# backend/tests/test_startup.py
"""Tests for the API startup handler (Alembic migrations execution)."""

from unittest.mock import patch

import main


def test_startup_handler_runs_alembic_upgrade_head():
    with patch("main.subprocess.run") as subprocess_run:
        main.apply_startup_migrations()

    subprocess_run.assert_called_once_with(["alembic", "upgrade", "head"], check=True)


def test_startup_handler_creates_tables_when_alembic_fails():
    with patch("main.subprocess.run", side_effect=FileNotFoundError("alembic")), patch.object(
        main.Base.metadata, "create_all"
    ) as create_all:
        main.apply_startup_migrations()

    create_all.assert_called_once_with(bind=main.engine)
