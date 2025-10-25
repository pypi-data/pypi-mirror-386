"""
Tag model for task organization.

This module defines the Tag model for organizing tasks with tags.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class Tag(BaseModel):
    """Tag model for organizing tasks."""
    
    # Core properties
    id: UUID = Field(default_factory=uuid4, description="Unique tag identifier")
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    description: Optional[str] = Field(default=None, max_length=200, description="Tag description")
    
    # Appearance
    color: Optional[str] = Field(default=None, description="Tag color (hex code)")
    icon: Optional[str] = Field(default=None, max_length=10, description="Tag icon/emoji")
    
    # Hierarchy
    parent_tag: Optional[str] = Field(default=None, max_length=50, description="Parent tag name")
    
    # Usage tracking
    usage_count: int = Field(default=0, ge=0, description="Number of tasks using this tag")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_used_at: Optional[datetime] = Field(default=None, description="Last time tag was used")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate and clean tag name."""
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        return v.strip().lower()
    
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
    
    @field_validator('parent_tag')
    @classmethod
    def validate_parent_tag(cls, v):
        """Validate parent tag name."""
        if v is not None:
            return v.strip().lower() if v.strip() else None
        return v
    
    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def decrement_usage(self) -> None:
        """Decrement usage count."""
        if self.usage_count > 0:
            self.usage_count -= 1
            self.updated_at = datetime.utcnow()
    
    def get_display_name(self) -> str:
        """Get display name with icon if available."""
        if self.icon:
            return f"{self.icon} {self.name}"
        return self.name
    
    def get_full_name(self) -> str:
        """Get full hierarchical name."""
        if self.parent_tag:
            return f"{self.parent_tag}/{self.name}"
        return self.name
    
    def is_child_of(self, parent_name: str) -> bool:
        """Check if this tag is a child of the specified parent."""
        return self.parent_tag == parent_name.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tag to dictionary."""
        return self.dict()
    
    def to_summary(self) -> str:
        """Get a short summary of the tag."""
        usage_info = f" ({self.usage_count} tasks)" if self.usage_count > 0 else ""
        return f"{self.get_display_name()}{usage_info}"
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
