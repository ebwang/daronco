# backend/database.py
# This module is responsible for setting up the connection "plumbing" with the PostgreSQL database.

import os  # Python's native module used to read environment variables from the system/Docker
from sqlalchemy import create_engine  # SQLAlchemy helper that creates the connection engine
from sqlalchemy.orm import sessionmaker, declarative_base  # Helpers to manage sessions and tables

# 1. Reads the PostgreSQL address from the DATABASE_URL environment variable.
# When the variable is not set (e.g. running locally without Docker), it falls back to the
# default local PostgreSQL URL.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/hosts_db"
)

# 2. Creates the SQLAlchemy "Engine".
# The Engine is the central object that manages connections to PostgreSQL.
engine = create_engine(DATABASE_URL)

# 3. Creates the 'SessionLocal' session factory.
# Every HTTP request opens one instance of this session to read/write in the database.
# - autocommit=False: changes are only persisted when db.commit() is explicitly called.
# - autoflush=False: prevents SQLAlchemy from sending partial data before the right moment.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Creates the declarative 'Base' class.
# Every database model class (like Host and User in models.py) inherits from this 'Base'.
Base = declarative_base()

# 5. Generator function (dependency injection) used to obtain one database session per route.
def get_db():
    """
    Creates a new database session for the request and guarantees the session is
    closed at the end (avoiding connection leaks).
    """
    db = SessionLocal()  # Opens the connection/session
    try:
        yield db         # Temporarily hands the session to the route that needs it
    finally:
        db.close()       # Always closes the session at the end of the request
