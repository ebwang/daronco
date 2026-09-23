# backend/models.py
# This module defines the database table structures using the SQLAlchemy ORM.

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base

# 1. Model for the 'users' table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True, index=True)
    address = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # One-to-many relationship: a single User can own many Hosts
    hosts = relationship("Host", back_populates="owner", cascade="all, delete-orphan")


# 2. Model for the 'hosts' table (with the user_id foreign key)
class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hostname = Column(String, nullable=False, index=True)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    cpu = Column(String, nullable=False)
    cpu_count = Column(Integer, nullable=False, default=1)
    ram = Column(String, nullable=False)
    disk = Column(String, nullable=False)
    storage_type = Column(String, nullable=False)  # e.g. SSD, HDD, NVMe, Hybrid
    interfaces = Column(String, nullable=False)    # e.g. Ethernet, iSCSI
    ips = Column(String, nullable=False)           # e.g. 192.168.1.10
    location = Column(String, nullable=False)      # e.g. Room A

    # Foreign key (FK) connecting the Host to a User
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # Many-to-one relationship: many Hosts belong to a single User
    owner = relationship("User", back_populates="hosts")
