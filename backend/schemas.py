# backend/schemas.py
# This module defines the Pydantic schemas used for request validation and response serialization.

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# --- USER SCHEMAS ---

class UserBase(BaseModel):
    first_name: str = Field(..., json_schema_extra={"example": "John"})
    last_name: str = Field(..., json_schema_extra={"example": "Doe"})
    username: str = Field(..., json_schema_extra={"example": "jdoe"})
    address: str = Field(..., json_schema_extra={"example": "123 Main Street - NY"})

class UserCreate(UserBase):
    pass

class UserSimpleResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- HOST SCHEMAS ---

class HostBase(BaseModel):
    hostname: str = Field(..., json_schema_extra={"example": "host1"})
    manufacturer: str = Field(..., json_schema_extra={"example": "Dell"})
    model: str = Field(..., json_schema_extra={"example": "PowerEdge R740"})
    cpu: str = Field(..., json_schema_extra={"example": "Intel Xeon E5-2698 v4"})
    cpu_count: int = Field(..., json_schema_extra={"example": 2})
    ram: str = Field(..., json_schema_extra={"example": "32GB"})
    disk: str = Field(..., json_schema_extra={"example": "1TB"})
    storage_type: str = Field(..., json_schema_extra={"example": "SSD"})
    interfaces: str = Field(..., json_schema_extra={"example": "Ethernet, iSCSI"})
    ips: str = Field(..., json_schema_extra={"example": "192.168.1.10"})
    location: str = Field(..., json_schema_extra={"example": "Room A"})
    user_id: Optional[int] = Field(None, json_schema_extra={"example": 1})  # optional owner id

class HostCreate(HostBase):
    pass

class HostResponse(HostBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# --- USER RESPONSE SCHEMA WITH THE NESTED HOST LIST ---

class UserResponse(UserBase):
    id: int
    created_at: datetime
    hosts: List[HostResponse] = []

    model_config = ConfigDict(from_attributes=True)
