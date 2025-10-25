"""
Background daemon for the CLI Task Manager.

This module provides the background daemon service for handling
notifications, reminders, and automated tasks.
"""

from cli_task_manager.daemon.main import main

__all__ = ["main"]
