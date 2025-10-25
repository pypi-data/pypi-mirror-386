"""
CLI Task Manager - A professional command-line task management application.

This package provides a comprehensive task management system with natural language
processing capabilities, recurring tasks, reminders, and cross-platform support.
"""

__version__ = "1.0.0"
__author__ = "CLI Task Manager Team"
__email__ = "team@cli-task-manager.dev"
__license__ = "MIT"

from cli_task_manager.core.database import DatabaseManager
from cli_task_manager.core.config import Config
from cli_task_manager.models.task import Task, TaskPriority, TaskStatus
from cli_task_manager.models.reminder import Reminder
from cli_task_manager.models.dependency import Dependency

__all__ = [
    "DatabaseManager",
    "Config",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "Reminder",
    "Dependency",
]
