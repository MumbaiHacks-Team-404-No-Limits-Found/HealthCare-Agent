"""Pydantic models and MongoDB document schemas."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2."""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> ObjectId:
            if ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError("Invalid ObjectId")
        
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(validate_from_str),
        ])
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}


# Volunteer Models
class AvailabilitySlot(BaseModel):
    """Availability slot for a volunteer."""
    date: str  # ISO date string
    slots: List[str]  # List of time slot strings


class VolunteerInput(BaseModel):
    """Input model for creating a volunteer."""
    name: str = Field(..., min_length=1, max_length=200, description="Volunteer name")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number in E.164 format")
    skills: List[str] = Field(default_factory=list, description="List of skills/roles")
    availability: List[AvailabilitySlot] = Field(default_factory=list, description="Availability slots")
    no_show_rate: float = Field(default=0.2, ge=0.0, le=1.0, description="No-show probability (0-1)")


class Volunteer(BaseModel):
    """Volunteer model."""
    id: PyObjectId = Field(default_factory=lambda: ObjectId(), alias="_id")
    name: str
    phone: str
    skills: List[str] = []
    availability: List[AvailabilitySlot] = []
    no_show_rate: float = 0.2
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


# Camp Models
class Requirement(BaseModel):
    """Camp requirement for a role and slot."""
    role: str = Field(..., min_length=1, max_length=100, description="Required role (e.g., 'doctor', 'nurse')")
    count: int = Field(..., ge=0, description="Number of volunteers needed (non-negative)")
    slot: str = Field(..., min_length=1, max_length=50, description="Time slot (e.g., 'morning', 'afternoon')")


class CampInput(BaseModel):
    """Input model for creating a camp."""
    name: str = Field(..., min_length=1, max_length=200, description="Camp name")
    location: str = Field(..., min_length=1, max_length=200, description="Camp location")
    start: str = Field(..., description="Start datetime in ISO 8601 format")
    end: str = Field(..., description="End datetime in ISO 8601 format")
    requirements: List[Requirement] = Field(default_factory=list, description="List of role requirements")


class Camp(BaseModel):
    """Camp model."""
    id: PyObjectId = Field(default_factory=lambda: ObjectId(), alias="_id")
    name: str
    location: str
    start: str  # ISO datetime string
    end: str  # ISO datetime string
    requirements: List[Requirement] = []
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


# Assignment Models
class AssignmentInput(BaseModel):
    """Input model for creating an assignment."""
    camp_id: str
    volunteer_id: str
    role: str
    slot: str
    status: str = "assigned"
    is_backup: bool = False


class Assignment(BaseModel):
    """Assignment model."""
    id: PyObjectId = Field(default_factory=lambda: ObjectId(), alias="_id")
    camp_id: PyObjectId
    volunteer_id: PyObjectId
    role: str
    slot: str
    status: str = "assigned"  # "assigned" | "confirmed" | "cancelled" | "backup"
    is_backup: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


# Forecast Models
class ForecastResult(BaseModel):
    """Forecast result for a requirement."""
    slot: str
    role: str
    mean: float
    upper_90: float
    lower_10: float


# Activity Log Models
class ActivityLog(BaseModel):
    """Activity log entry."""
    id: PyObjectId = Field(default_factory=lambda: ObjectId(), alias="_id")
    camp_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event: str
    meta: Dict[str, Any] = {}
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

