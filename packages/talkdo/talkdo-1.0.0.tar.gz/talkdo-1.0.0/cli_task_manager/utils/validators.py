"""
Validation utilities for the CLI Task Manager.

This module provides validation functions for various data types
and input validation.
"""

import re
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from cli_task_manager.models.task import TaskPriority, TaskStatus
from cli_task_manager.models.project import ProjectStatus


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID string format."""
    try:
        UUID(uuid_string)
        return True
    except ValueError:
        return False


def validate_date(date_string: str) -> bool:
    """Validate date string format."""
    try:
        datetime.fromisoformat(date_string)
        return True
    except ValueError:
        return False


def validate_priority(priority: str) -> bool:
    """Validate priority string."""
    return priority.lower() in [p.value for p in TaskPriority]


def validate_status(status: str) -> bool:
    """Validate status string."""
    return status.lower() in [s.value for s in TaskStatus]


def validate_project_status(status: str) -> bool:
    """Validate project status string."""
    return status.lower() in [s.value for s in ProjectStatus]


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_hex_color(color: str) -> bool:
    """Validate hex color code."""
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, color))


def validate_time(time_string: str) -> bool:
    """Validate time string format (HH:MM or HH:MM:SS)."""
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$'
    return bool(re.match(pattern, time_string))


def validate_tag_name(tag: str) -> bool:
    """Validate tag name format."""
    if not tag or len(tag) > 50:
        return False
    
    # Allow alphanumeric, hyphens, underscores, and forward slashes
    pattern = r'^[a-zA-Z0-9_-/]+$'
    return bool(re.match(pattern, tag))


def validate_project_name(name: str) -> bool:
    """Validate project name format."""
    if not name or len(name) > 100:
        return False
    
    # Allow alphanumeric, hyphens, underscores, and spaces
    pattern = r'^[a-zA-Z0-9_- ]+$'
    return bool(re.match(pattern, name))


def validate_task_title(title: str) -> bool:
    """Validate task title format."""
    return bool(title and len(title.strip()) > 0 and len(title) <= 500)


def validate_recurrence_pattern(pattern: str) -> bool:
    """Validate recurrence pattern format."""
    valid_patterns = [
        'daily', 'weekly', 'monthly', 'yearly',
        'weekday', 'weekend', 'business_day'
    ]
    
    # Check for interval patterns like "every_3_days"
    interval_pattern = r'^every_\d+_(days?|weeks?|months?|years?)$'
    
    return pattern.lower() in valid_patterns or bool(re.match(interval_pattern, pattern.lower()))


def validate_reminder_time(reminder_time: datetime, due_date: Optional[datetime] = None) -> bool:
    """Validate reminder time is in the future and before due date."""
    now = datetime.now()
    
    if reminder_time <= now:
        return False
    
    if due_date and reminder_time > due_date:
        return False
    
    return True


def validate_dependency_cycle(predecessor_id: str, successor_id: str, db) -> bool:
    """Validate that adding a dependency won't create a cycle."""
    if predecessor_id == successor_id:
        return False
    
    # TODO: Implement cycle detection algorithm
    # This would require traversing the dependency graph
    return True


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize user input by removing potentially harmful characters."""
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Truncate if necessary
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_config_value(key: str, value: Any) -> bool:
    """Validate configuration value based on key."""
    validators = {
        'general.default_priority': lambda v: validate_priority(v),
        'general.default_view': lambda v: v in ['table', 'compact', 'detailed', 'json', 'csv'],
        'general.timezone': lambda v: isinstance(v, str) and len(v) > 0,
        'notifications.enabled': lambda v: isinstance(v, bool),
        'notifications.desktop_notifications': lambda v: isinstance(v, bool),
        'notifications.sound_notifications': lambda v: isinstance(v, bool),
        'display.theme': lambda v: v in ['auto', 'light', 'dark'],
        'display.show_icons': lambda v: isinstance(v, bool),
        'backup.enabled': lambda v: isinstance(v, bool),
        'backup.frequency': lambda v: v in ['daily', 'weekly', 'monthly'],
        'backup.keep_count': lambda v: isinstance(v, int) and 1 <= v <= 30,
        'parser.confidence_threshold': lambda v: isinstance(v, (int, float)) and 0 <= v <= 1,
    }
    
    validator = validators.get(key)
    if validator:
        try:
            return validator(value)
        except Exception:
            return False
    
    return True
