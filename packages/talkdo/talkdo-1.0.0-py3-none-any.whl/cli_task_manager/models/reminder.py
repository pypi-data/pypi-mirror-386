"""
Reminder model for task notifications.

This module defines the Reminder model for managing task reminders
and notifications.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class ReminderType(str, Enum):
    """Types of reminders."""
    ABSOLUTE = "absolute"  # At specific time
    RELATIVE = "relative"   # Relative to due date
    ADVANCE = "advance"     # Advance warning


class ReminderStatus(str, Enum):
    """Reminder status values."""
    PENDING = "pending"
    SENT = "sent"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"


class Reminder(BaseModel):
    """Reminder model for task notifications."""
    
    # Core properties
    id: UUID = Field(default_factory=uuid4, description="Unique reminder identifier")
    task_id: UUID = Field(..., description="Associated task ID")
    
    # Timing
    reminder_time: datetime = Field(..., description="When to send the reminder")
    reminder_type: ReminderType = Field(..., description="Type of reminder")
    advance_minutes: Optional[int] = Field(default=None, ge=0, description="Minutes before due date")
    
    # Status
    status: ReminderStatus = Field(default=ReminderStatus.PENDING, description="Reminder status")
    sent_at: Optional[datetime] = Field(default=None, description="When reminder was sent")
    snoozed_until: Optional[datetime] = Field(default=None, description="Snooze until time")
    
    # Content
    message: Optional[str] = Field(default=None, max_length=500, description="Custom reminder message")
    title: Optional[str] = Field(default=None, max_length=200, description="Reminder title")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """Validate and clean message."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate and clean title."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    def is_due(self) -> bool:
        """Check if reminder is due to be sent."""
        if self.status != ReminderStatus.PENDING:
            return False
        return datetime.utcnow() >= self.reminder_time
    
    def is_snoozed(self) -> bool:
        """Check if reminder is currently snoozed."""
        if self.status != ReminderStatus.SNOOZED:
            return False
        if not self.snoozed_until:
            return False
        return datetime.utcnow() < self.snoozed_until
    
    def can_send(self) -> bool:
        """Check if reminder can be sent."""
        return self.status == ReminderStatus.PENDING and self.is_due()
    
    def mark_sent(self) -> None:
        """Mark reminder as sent."""
        self.status = ReminderStatus.SENT
        self.sent_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def snooze(self, minutes: int) -> None:
        """Snooze reminder for specified minutes."""
        self.status = ReminderStatus.SNOOZED
        self.snoozed_until = datetime.utcnow() + timedelta(minutes=minutes)
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel the reminder."""
        self.status = ReminderStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def get_display_message(self) -> str:
        """Get the display message for the reminder."""
        if self.message:
            return self.message
        
        # Default message based on type
        if self.reminder_type == ReminderType.ADVANCE:
            return f"Task reminder: {self.advance_minutes} minutes before due"
        elif self.reminder_type == ReminderType.RELATIVE:
            return f"Task reminder: {self.advance_minutes} minutes before due"
        else:
            return "Task reminder"
    
    def get_display_title(self) -> str:
        """Get the display title for the reminder."""
        if self.title:
            return self.title
        return "Task Reminder"
    
    def to_dict(self) -> dict:
        """Convert reminder to dictionary."""
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
