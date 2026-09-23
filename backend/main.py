# backend/main.py
# This module is the web server of the API, built with the FastAPI framework.

import subprocess
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Imports the local modules of the project:
from database import engine, get_db, Base
from models import Host, User
from schemas import (
    HostCreate, HostResponse,
    UserCreate, UserResponse, UserSimpleResponse
)


def apply_startup_migrations():
    """
    Applies the pending Alembic migrations on server startup.
    If Alembic cannot run, it falls back to Base.metadata.create_all.
    """
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Alembic migrations successfully applied to PostgreSQL!")
    except Exception as error:
        print(f"Warning while running Alembic: {error}. Falling back to Base.metadata.create_all.")
        Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown handler used by FastAPI (replaces the deprecated on_event)."""
    apply_startup_migrations()
    yield


# Instantiates the main FastAPI application
app = FastAPI(
    title="Host and User Management API (PostgreSQL + ORM + Alembic)",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# USER ROUTES (/api/users)
# =====================================================================

@app.get("/api/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    """Returns every user along with their associated hosts."""
    return db.query(User).order_by(User.id.asc()).all()

@app.post("/api/users", response_model=UserSimpleResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user in the PostgreSQL database."""
    # Checks whether a user with the same username already exists
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail=f"A user with the username '{user_in.username}' already exists."
        )

    new_user = User(**user_in.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Returns the details of a specific user by id."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Deletes a user by id (their associated hosts are removed in cascade)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully", "id": user_id}


# =====================================================================
# HOST / SERVER ROUTES (/api/hosts)
# =====================================================================

@app.get("/api/hosts", response_model=List[HostResponse])
def list_hosts(db: Session = Depends(get_db)):
    """Returns every host registered through the SQLAlchemy ORM."""
    return db.query(Host).order_by(Host.id.asc()).all()

@app.post("/api/hosts", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
def create_host(host_in: HostCreate, db: Session = Depends(get_db)):
    """
    Inserts a new host in PostgreSQL through the ORM.
    When 'user_id' is provided, it validates that the user exists.
    """
    if host_in.user_id:
        user_exists = db.query(User).filter(User.id == host_in.user_id).first()
        if not user_exists:
            raise HTTPException(
                status_code=404, 
                detail=f"User with id={host_in.user_id} does not exist."
            )

    new_host = Host(**host_in.model_dump())
    db.add(new_host)
    db.commit()
    db.refresh(new_host)
    return new_host

@app.delete("/api/hosts/{host_id}", status_code=status.HTTP_200_OK)
def delete_host(host_id: int, db: Session = Depends(get_db)):
    """Removes a host by id from PostgreSQL through the ORM."""
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    
    db.delete(host)
    db.commit()
    return {"message": "Host deleted successfully", "id": host_id}
