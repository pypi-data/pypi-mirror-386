"""
Configuration management for the CLI Task Manager.

This module handles loading, saving, and validating configuration settings
from YAML files with sensible defaults.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import time
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class NotificationSettings(BaseModel):
    """Notification configuration settings."""
    
    enabled: bool = Field(default=True, description="Enable notifications")
    desktop_notifications: bool = Field(default=True, description="Enable desktop notifications")
    sound_notifications: bool = Field(default=True, description="Enable sound notifications")
    email_notifications: bool = Field(default=False, description="Enable email notifications")
    
    # Email settings
    smtp_server: Optional[str] = Field(default=None, description="SMTP server for email notifications")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    email_from: Optional[str] = Field(default=None, description="From email address")
    email_to: Optional[str] = Field(default=None, description="To email address")
    
    # Timing settings
    advance_warnings: List[int] = Field(default=[60, 1440], description="Advance warning minutes")
    quiet_hours_start: Optional[time] = Field(default=None, description="Quiet hours start time")
    quiet_hours_end: Optional[time] = Field(default=None, description="Quiet hours end time")
    snooze_duration: int = Field(default=15, ge=1, description="Default snooze duration in minutes")
    max_reminders_per_task: int = Field(default=5, ge=1, le=20, description="Maximum reminders per task")


class DisplaySettings(BaseModel):
    """Display configuration settings."""
    
    theme: str = Field(default="auto", description="Color theme: auto, light, dark")
    show_icons: bool = Field(default=True, description="Show icons and emojis")
    compact_mode: bool = Field(default=False, description="Use compact display mode")
    date_format: str = Field(default="%Y-%m-%d", description="Date format string")
    time_format: str = Field(default="%H:%M", description="Time format string")
    table_style: str = Field(default="grid", description="Table style: grid, simple, minimal")
    
    # Priority colors
    priority_colors: Dict[str, str] = Field(
        default={
            "urgent": "red",
            "high": "yellow", 
            "medium": "white",
            "low": "blue"
        },
        description="Priority color mapping"
    )
    
    # Status colors
    status_colors: Dict[str, str] = Field(
        default={
            "pending": "white",
            "in_progress": "yellow",
            "completed": "green",
            "cancelled": "red"
        },
        description="Status color mapping"
    )


class BackupSettings(BaseModel):
    """Backup configuration settings."""
    
    enabled: bool = Field(default=True, description="Enable automatic backups")
    frequency: str = Field(default="daily", description="Backup frequency: daily, weekly, monthly")
    keep_count: int = Field(default=7, ge=1, le=30, description="Number of backups to keep")
    location: Optional[str] = Field(default=None, description="Custom backup location")


class ParserSettings(BaseModel):
    """Natural language parser settings."""
    
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Parser confidence threshold")
    auto_tag_enabled: bool = Field(default=True, description="Enable automatic tagging")
    smart_scheduling: bool = Field(default=True, description="Enable smart scheduling")
    fuzzy_matching: bool = Field(default=True, description="Enable fuzzy matching for search")
    
    # Date parsing
    prefer_future_dates: bool = Field(default=True, description="Prefer future dates when ambiguous")
    relative_date_base: str = Field(default="now", description="Base for relative dates: now, today")
    
    # Time zones
    timezone: str = Field(default="local", description="Timezone for date parsing")


class GeneralSettings(BaseModel):
    """General application settings."""
    
    default_priority: str = Field(default="medium", description="Default priority for new tasks")
    default_view: str = Field(default="table", description="Default view format")
    first_day_of_week: int = Field(default=0, ge=0, le=6, description="First day of week (0=Monday)")
    timezone: str = Field(default="local", description="Application timezone")
    
    # Data settings
    auto_save: bool = Field(default=True, description="Auto-save changes")
    confirm_deletions: bool = Field(default=True, description="Confirm before deleting tasks")
    show_completed_tasks: bool = Field(default=False, description="Show completed tasks by default")
    
    # Performance
    max_tasks_display: int = Field(default=1000, ge=100, le=10000, description="Maximum tasks to display")
    cache_size: int = Field(default=1000, ge=100, le=10000, description="Cache size for performance")


class Config(BaseModel):
    """Main configuration model."""
    
    # Sub-configurations
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    display: DisplaySettings = Field(default_factory=DisplaySettings)
    backup: BackupSettings = Field(default_factory=BackupSettings)
    parser: ParserSettings = Field(default_factory=ParserSettings)
    
    # Metadata
    version: str = Field(default="1.0.0", description="Configuration version")
    created_at: str = Field(default="", description="Configuration creation timestamp")
    updated_at: str = Field(default="", description="Configuration last update timestamp")
    
    @model_validator(mode='after')
    def validate_general_settings(self):
        """Validate general settings."""
        valid_priorities = ["low", "medium", "high", "urgent"]
        if self.general.default_priority not in valid_priorities:
            raise ValueError(f"Invalid default priority: {self.general.default_priority}")
        
        valid_views = ["table", "compact", "detailed", "json", "csv"]
        if self.general.default_view not in valid_views:
            raise ValueError(f"Invalid default view: {self.general.default_view}")
        
        return self
    
    @model_validator(mode='after')
    def validate_notification_settings(self):
        """Validate notification settings."""
        if self.notifications.email_notifications and not self.notifications.smtp_server:
            raise ValueError("Email notifications require SMTP server configuration")
        
        if self.notifications.quiet_hours_start and self.notifications.quiet_hours_end:
            if self.notifications.quiet_hours_start == self.notifications.quiet_hours_end:
                raise ValueError("Quiet hours start and end cannot be the same")
        
        return self
    
    @model_validator(mode='after')
    def validate_display_settings(self):
        """Validate display settings."""
        valid_themes = ["auto", "light", "dark"]
        if self.display.theme not in valid_themes:
            raise ValueError(f"Invalid theme: {self.display.theme}")
        
        valid_styles = ["grid", "simple", "minimal"]
        if self.display.table_style not in valid_styles:
            raise ValueError(f"Invalid table style: {self.display.table_style}")
        
        return self
    
    @model_validator(mode='after')
    def validate_backup_settings(self):
        """Validate backup settings."""
        valid_frequencies = ["daily", "weekly", "monthly"]
        if self.backup.frequency not in valid_frequencies:
            raise ValueError(f"Invalid backup frequency: {self.backup.frequency}")
        
        return self
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file."""
        if config_path is None:
            config_path = cls.get_default_config_path()
        
        if not config_path.exists():
            # Create default configuration
            config = cls()
            config.save(config_path)
            return config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                data = {}
            
            return cls(**data)
        
        except Exception as e:
            # If loading fails, create default config
            print(f"Warning: Failed to load config from {config_path}: {e}")
            config = cls()
            config.save(config_path)
            return config
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = self.get_default_config_path()
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update timestamps
        from datetime import datetime
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.dict(), f, default_flow_style=False, sort_keys=False)
        
        except Exception as e:
            raise RuntimeError(f"Failed to save config to {config_path}: {e}")
    
    @staticmethod
    def get_default_config_path() -> Path:
        """Get the default configuration file path."""
        home = Path.home()
        config_dir = home / ".task-manager"
        return config_dir / "config.yaml"
    
    @staticmethod
    def get_data_directory() -> Path:
        """Get the data directory path."""
        home = Path.home()
        data_dir = home / ".task-manager"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def get_database_path(self) -> Path:
        """Get the database file path."""
        return self.get_data_directory() / "tasks.db"
    
    def get_backup_directory(self) -> Path:
        """Get the backup directory path."""
        backup_dir = self.get_data_directory() / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    def get_log_directory(self) -> Path:
        """Get the log directory path."""
        log_dir = self.get_data_directory() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict()
    
    def update_setting(self, key_path: str, value: Any) -> None:
        """Update a specific setting using dot notation."""
        keys = key_path.split('.')
        current = self
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                raise KeyError(f"Invalid setting path: {key_path}")
        
        # Set the final value
        final_key = keys[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
        else:
            raise KeyError(f"Invalid setting: {key_path}")
    
    def get_setting(self, key_path: str) -> Any:
        """Get a specific setting using dot notation."""
        keys = key_path.split('.')
        current = self
        
        for key in keys:
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                raise KeyError(f"Invalid setting path: {key_path}")
        
        return current
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
