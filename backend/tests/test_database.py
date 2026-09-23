# backend/tests/test_database.py
"""Unit tests for the database connection plumbing (database.py)."""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from database import SessionLocal, get_db


def test_get_db_yields_a_session_and_closes_it_at_the_end():
    with patch.object(Session, "close") as close_session:
        generator = get_db()
        session = next(generator)
        assert isinstance(session, Session)

        # When the generator is exhausted (end of the request) the session must be closed.
        with pytest.raises(StopIteration):
            next(generator)

    close_session.assert_called_once_with()


def test_session_local_is_configured_without_autocommit_and_autoflush():
    assert SessionLocal.kw["autocommit"] is False
    assert SessionLocal.kw["autoflush"] is False
