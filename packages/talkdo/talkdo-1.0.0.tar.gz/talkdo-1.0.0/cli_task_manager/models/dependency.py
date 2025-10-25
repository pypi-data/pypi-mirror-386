"""
Dependency model for task relationships.

This module defines the Dependency model for managing task dependencies
and blocking relationships.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, model_validator


class DependencyType(str, Enum):
    """Types of task dependencies."""
    FINISH_TO_START = "finish_to_start"  # Task B starts when Task A finishes
    START_TO_START = "start_to_start"   # Task B starts when Task A starts
    FINISH_TO_FINISH = "finish_to_finish"  # Task B finishes when Task A finishes


class DependencyStatus(str, Enum):
    """Dependency status values."""
    ACTIVE = "active"
    SATISFIED = "satisfied"
    CANCELLED = "cancelled"


class Dependency(BaseModel):
    """Dependency model for task relationships."""
    
    # Core properties
    id: UUID = Field(default_factory=uuid4, description="Unique dependency identifier")
    predecessor_id: UUID = Field(..., description="ID of the task that must be completed first")
    successor_id: UUID = Field(..., description="ID of the task that depends on the predecessor")
    
    # Relationship
    dependency_type: DependencyType = Field(..., description="Type of dependency")
    status: DependencyStatus = Field(default=DependencyStatus.ACTIVE, description="Dependency status")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    satisfied_at: Optional[datetime] = Field(default=None, description="When dependency was satisfied")
    
    @field_validator('predecessor_id', 'successor_id')
    @classmethod
    def validate_task_ids(cls, v):
        """Validate task IDs are not the same."""
        return v
    
    @model_validator(mode='after')
    def validate_different_tasks(self):
        """Ensure predecessor and successor are different tasks."""
        if self.predecessor_id == self.successor_id:
            raise ValueError("A task cannot depend on itself")
        
        return self
    
    def is_satisfied(self, predecessor_status: str) -> bool:
        """Check if dependency is satisfied based on predecessor status."""
        if self.status != DependencyStatus.ACTIVE:
            return False
        
        if self.dependency_type == DependencyType.FINISH_TO_START:
            return predecessor_status == "completed"
        elif self.dependency_type == DependencyType.START_TO_START:
            return predecessor_status in ["in_progress", "completed"]
        elif self.dependency_type == DependencyType.FINISH_TO_FINISH:
            return predecessor_status == "completed"
        
        return False
    
    def mark_satisfied(self) -> None:
        """Mark dependency as satisfied."""
        self.status = DependencyStatus.SATISFIED
        self.satisfied_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel the dependency."""
        self.status = DependencyStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def get_description(self) -> str:
        """Get a human-readable description of the dependency."""
        type_descriptions = {
            DependencyType.FINISH_TO_START: "must finish before",
            DependencyType.START_TO_START: "must start with",
            DependencyType.FINISH_TO_FINISH: "must finish with"
        }
        
        return f"Task {self.successor_id} {type_descriptions[self.dependency_type]} task {self.predecessor_id}"
    
    def to_dict(self) -> dict:
        """Convert dependency to dictionary."""
        return self.dict()
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
