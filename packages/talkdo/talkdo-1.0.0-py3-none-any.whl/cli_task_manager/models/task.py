"""
Task model and related enums.

This module defines the core Task model with all its properties,
validation rules, and helper methods.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RecurrencePattern(BaseModel):
    """Recurrence pattern for recurring tasks."""
    type: str = Field(..., description="Type of recurrence: daily, weekly, monthly, yearly, custom")
    interval: int = Field(default=1, ge=1, description="Interval between occurrences")
    days_of_week: Optional[List[int]] = Field(default=None, description="Days of week (0=Monday, 6=Sunday)")
    day_of_month: Optional[int] = Field(default=None, ge=1, le=31, description="Day of month")
    end_date: Optional[datetime] = Field(default=None, description="End date for recurrence")
    max_occurrences: Optional[int] = Field(default=None, ge=1, description="Maximum number of occurrences")
    skip_weekends: bool = Field(default=False, description="Skip weekends in recurrence")
    
    @field_validator('days_of_week')
    @classmethod
    def validate_days_of_week(cls, v):
        if v is not None:
            for day in v:
                if not 0 <= day <= 6:
                    raise ValueError("Days of week must be between 0 (Monday) and 6 (Sunday)")
        return v


class Task(BaseModel):
    """Core Task model with all properties and validation."""
    
    # Core properties
    id: UUID = Field(default_factory=uuid4, description="Unique task identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    description: Optional[str] = Field(default=None, max_length=2000, description="Task description")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    
    # Scheduling
    due_date: Optional[datetime] = Field(default=None, description="Due date and time")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    
    # Organization
    tags: List[str] = Field(default_factory=list, description="Task tags")
    project: Optional[str] = Field(default=None, max_length=100, description="Project name")
    category: Optional[str] = Field(default=None, max_length=100, description="Task category")
    
    # Recurrence
    is_recurring: bool = Field(default=False, description="Whether task is recurring")
    recurrence_pattern: Optional[RecurrencePattern] = Field(default=None, description="Recurrence pattern")
    parent_task_id: Optional[UUID] = Field(default=None, description="Parent task ID for recurring tasks")
    next_occurrence: Optional[datetime] = Field(default=None, description="Next occurrence date")
    occurrence_count: int = Field(default=0, ge=0, description="Number of occurrences created")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate and clean title."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate and clean description."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags."""
        if v:
            # Remove duplicates and empty tags
            cleaned_tags = list(set(tag.strip().lower() for tag in v if tag.strip()))
            return cleaned_tags
        return []
    
    @field_validator('project', 'category')
    @classmethod
    def validate_names(cls, v):
        """Validate project and category names."""
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                return None
            return cleaned
        return v
    
    @model_validator(mode='after')
    def validate_recurrence(self):
        """Validate recurrence-related fields."""
        if self.is_recurring and not self.recurrence_pattern:
            raise ValueError("Recurring tasks must have a recurrence pattern")
        
        if self.is_recurring and self.parent_task_id is None:
            # This is a parent recurring task
            self.parent_task_id = self.id
        
        return self
    
    @model_validator(mode='after')
    def validate_completion(self):
        """Validate completion-related fields."""
        if self.status == TaskStatus.COMPLETED and self.completed_at is None:
            self.completed_at = datetime.utcnow()
        elif self.status != TaskStatus.COMPLETED and self.completed_at is not None:
            self.completed_at = None
            
        return self
    
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date or self.status == TaskStatus.COMPLETED:
            return False
        return datetime.utcnow() > self.due_date
    
    def is_due_today(self) -> bool:
        """Check if task is due today."""
        if not self.due_date:
            return False
        today = datetime.utcnow().date()
        return self.due_date.date() == today
    
    def is_due_this_week(self) -> bool:
        """Check if task is due this week."""
        if not self.due_date:
            return False
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start.date() <= self.due_date.date() <= week_end.date()
    
    def get_age_days(self) -> int:
        """Get age of task in days."""
        return (datetime.utcnow() - self.created_at).days
    
    def get_days_until_due(self) -> Optional[int]:
        """Get days until due date."""
        if not self.due_date:
            return None
        delta = self.due_date.date() - datetime.utcnow().date()
        return delta.days
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the task."""
        if tag.strip() and tag.strip().lower() not in self.tags:
            self.tags.append(tag.strip().lower())
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the task."""
        tag_lower = tag.strip().lower()
        if tag_lower in self.tags:
            self.tags.remove(tag_lower)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def complete(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def start(self) -> None:
        """Mark task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return self.dict()
    
    def to_summary(self) -> str:
        """Get a short summary of the task."""
        status_icon = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄", 
            TaskStatus.COMPLETED: "✅",
            TaskStatus.CANCELLED: "❌"
        }
        
        priority_icon = {
            TaskPriority.LOW: "🔵",
            TaskPriority.MEDIUM: "⚪",
            TaskPriority.HIGH: "🟡",
            TaskPriority.URGENT: "🔴"
        }
        
        icon = status_icon.get(self.status, "⏳")
        priority = priority_icon.get(self.priority, "⚪")
        
        due_info = ""
        if self.due_date:
            if self.is_overdue():
                due_info = " (OVERDUE)"
            elif self.is_due_today():
                due_info = " (TODAY)"
            else:
                days = self.get_days_until_due()
                if days is not None:
                    due_info = f" ({days}d)"
        
        return f"{icon} {priority} {self.title}{due_info}"
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
