"""
Project model for task organization.

This module defines the Project model for organizing tasks into projects.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, model_validator


class ProjectStatus(str, Enum):
    """Project status values."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(BaseModel):
    """Project model for organizing tasks."""
    
    # Core properties
    id: UUID = Field(default_factory=uuid4, description="Unique project identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(default=None, max_length=1000, description="Project description")
    
    # Status and organization
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    color: Optional[str] = Field(default=None, description="Project color (hex code)")
    icon: Optional[str] = Field(default=None, max_length=10, description="Project icon/emoji")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    archived_at: Optional[datetime] = Field(default=None, description="Archival timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate and clean project name."""
        if not v or not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate and clean description."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validate color hex code."""
        if v is not None:
            v = v.strip().lower()
            if not v.startswith('#'):
                v = '#' + v
            if len(v) != 7 or not all(c in '0123456789abcdef' for c in v[1:]):
                raise ValueError("Color must be a valid hex code")
        return v
    
    @field_validator('icon')
    @classmethod
    def validate_icon(cls, v):
        """Validate and clean icon."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @model_validator(mode='after')
    def validate_completion(self):
        """Validate completion-related fields."""
        if self.status == ProjectStatus.COMPLETED and self.completed_at is None:
            self.completed_at = datetime.utcnow()
        elif self.status != ProjectStatus.COMPLETED and self.completed_at is not None:
            self.completed_at = None
            
        return self
    
    def archive(self) -> None:
        """Archive the project."""
        self.status = ProjectStatus.ARCHIVED
        self.archived_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete(self) -> None:
        """Mark project as completed."""
        self.status = ProjectStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel the project."""
        self.status = ProjectStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if project is active."""
        return self.status == ProjectStatus.ACTIVE
    
    def is_archived(self) -> bool:
        """Check if project is archived."""
        return self.status == ProjectStatus.ARCHIVED
    
    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self.status == ProjectStatus.COMPLETED
    
    def get_display_name(self) -> str:
        """Get display name with icon if available."""
        if self.icon:
            return f"{self.icon} {self.name}"
        return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary."""
        return self.dict()
    
    def to_summary(self) -> str:
        """Get a short summary of the project."""
        status_icon = {
            ProjectStatus.ACTIVE: "🟢",
            ProjectStatus.ARCHIVED: "📦",
            ProjectStatus.COMPLETED: "✅",
            ProjectStatus.CANCELLED: "❌"
        }
        
        icon = status_icon.get(self.status, "🟢")
        return f"{icon} {self.get_display_name()}"
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
