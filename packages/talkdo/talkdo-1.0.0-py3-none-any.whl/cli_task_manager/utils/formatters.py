"""
Formatting utilities for the CLI Task Manager.

This module provides formatting functions for dates, durations,
priorities, and other data types.
"""

from datetime import datetime, timedelta
from typing import Optional

from cli_task_manager.models.task import TaskPriority


def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format a datetime object."""
    if dt is None:
        return "-"
    return dt.strftime(format_str)


def format_duration(delta: timedelta) -> str:
    """Format a timedelta object as human-readable duration."""
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}m"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"
    else:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        if hours > 0:
            return f"{days}d {hours}h"
        return f"{days}d"


def format_priority(priority: TaskPriority) -> str:
    """Format a priority with icon."""
    icons = {
        TaskPriority.LOW: "🔵",
        TaskPriority.MEDIUM: "⚪", 
        TaskPriority.HIGH: "🟡",
        TaskPriority.URGENT: "🔴"
    }
    
    icon = icons.get(priority, "⚪")
    return f"{icon} {priority.value.title()}"


def format_status(status: str) -> str:
    """Format a status with icon."""
    icons = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "cancelled": "❌"
    }
    
    icon = icons.get(status, "⏳")
    return f"{icon} {status.title().replace('_', ' ')}"


def format_relative_time(dt: datetime) -> str:
    """Format a datetime as relative time (e.g., '2 hours ago')."""
    now = datetime.now()
    delta = now - dt
    
    if delta.total_seconds() < 60:
        return "just now"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif delta.days < 7:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
