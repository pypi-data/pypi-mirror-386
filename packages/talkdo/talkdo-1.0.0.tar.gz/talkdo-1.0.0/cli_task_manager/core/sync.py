"""
Sync and integration features for the CLI Task Manager.

This module provides synchronization capabilities with external services
and cloud platforms for seamless task management across devices.
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID
import requests
from cryptography.fernet import Fernet
import base64

from cli_task_manager.models.task import Task, TaskStatus, TaskPriority
from cli_task_manager.models.project import Project
from cli_task_manager.models.tag import Tag
from cli_task_manager.core.database import DatabaseManager
from cli_task_manager.core.config import Config


class SyncManager:
    """Manages synchronization with external services."""
    
    def __init__(self, db: DatabaseManager, config: Config):
        """Initialize sync manager."""
        self.db = db
        self.config = config
        self.sync_token: Optional[str] = None
        self.last_sync: Optional[datetime] = None
        self.conflict_resolution = "server_wins"  # or "client_wins", "manual"
    
    def generate_sync_token(self) -> str:
        """Generate a unique sync token for this device."""
        device_info = {
            "hostname": self._get_hostname(),
            "platform": self._get_platform(),
            "timestamp": datetime.utcnow().isoformat(),
            "random": str(UUID.uuid4())
        }
        
        token_data = json.dumps(device_info, sort_keys=True)
        return hashlib.sha256(token_data.encode()).hexdigest()
    
    def _get_hostname(self) -> str:
        """Get system hostname."""
        import socket
        return socket.gethostname()
    
    def _get_platform(self) -> str:
        """Get platform information."""
        import platform
        return f"{platform.system()}-{platform.release()}"
    
    def export_for_sync(self, include_completed: bool = True) -> Dict[str, Any]:
        """Export data for synchronization."""
        sync_data = {
            "metadata": {
                "sync_token": self.sync_token or self.generate_sync_token(),
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "device_info": {
                    "hostname": self._get_hostname(),
                    "platform": self._get_platform()
                }
            },
            "tasks": [],
            "projects": [],
            "tags": [],
            "deleted_items": {
                "tasks": [],
                "projects": [],
                "tags": []
            }
        }
        
        # Export tasks
        tasks = self.db.list_tasks() if include_completed else self.db.list_tasks(status=TaskStatus.PENDING)
        for task in tasks:
            task_data = self._serialize_task_for_sync(task)
            sync_data["tasks"].append(task_data)
        
        # Export projects
        projects = self.db.list_projects()
        for project in projects:
            project_data = self._serialize_project_for_sync(project)
            sync_data["projects"].append(project_data)
        
        # Export tags
        tags = self.db.list_tags()
        for tag in tags:
            tag_data = self._serialize_tag_for_sync(tag)
            sync_data["tags"].append(tag_data)
        
        return sync_data
    
    def _serialize_task_for_sync(self, task: Task) -> Dict[str, Any]:
        """Serialize task for synchronization."""
        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "tags": task.tags,
            "project": task.project,
            "category": task.category,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "is_recurring": task.is_recurring,
            "recurrence_pattern": task.recurrence_pattern.dict() if task.recurrence_pattern else None,
            "parent_task_id": str(task.parent_task_id) if task.parent_task_id else None,
            "next_occurrence": task.next_occurrence.isoformat() if task.next_occurrence else None,
            "occurrence_count": task.occurrence_count,
            "metadata": task.metadata,
            "sync_hash": self._calculate_sync_hash(task)
        }
    
    def _serialize_project_for_sync(self, project: Project) -> Dict[str, Any]:
        """Serialize project for synchronization."""
        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status.value,
            "color": project.color,
            "icon": project.icon,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "archived_at": project.archived_at.isoformat() if project.archived_at else None,
            "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            "metadata": project.metadata,
            "sync_hash": self._calculate_sync_hash(project)
        }
    
    def _serialize_tag_for_sync(self, tag: Tag) -> Dict[str, Any]:
        """Serialize tag for synchronization."""
        return {
            "id": str(tag.id),
            "name": tag.name,
            "description": tag.description,
            "color": tag.color,
            "icon": tag.icon,
            "parent_tag": tag.parent_tag,
            "usage_count": tag.usage_count,
            "created_at": tag.created_at.isoformat(),
            "updated_at": tag.updated_at.isoformat(),
            "last_used_at": tag.last_used_at.isoformat() if tag.last_used_at else None,
            "metadata": tag.metadata,
            "sync_hash": self._calculate_sync_hash(tag)
        }
    
    def _calculate_sync_hash(self, obj: Any) -> str:
        """Calculate hash for conflict detection."""
        # Create a hash based on the object's content
        content = json.dumps(obj.dict(), sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()
    
    def import_from_sync(self, sync_data: Dict[str, Any]) -> Dict[str, int]:
        """Import data from synchronization."""
        stats = {
            "tasks_imported": 0,
            "projects_imported": 0,
            "tags_imported": 0,
            "conflicts_resolved": 0,
            "errors": 0
        }
        
        # Import projects first
        for project_data in sync_data.get("projects", []):
            try:
                project = self._deserialize_project_from_sync(project_data)
                existing = self.db.get_project(project.name)
                
                if existing:
                    # Check for conflicts
                    if self._has_conflict(existing, project_data):
                        if self.conflict_resolution == "server_wins":
                            self.db.update_project(project)
                            stats["conflicts_resolved"] += 1
                        elif self.conflict_resolution == "client_wins":
                            # Keep existing, skip import
                            continue
                        else:  # manual
                            # For now, server wins
                            self.db.update_project(project)
                            stats["conflicts_resolved"] += 1
                    else:
                        self.db.update_project(project)
                else:
                    self.db.create_project(project)
                
                stats["projects_imported"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing project: {e}")
        
        # Import tags
        for tag_data in sync_data.get("tags", []):
            try:
                tag = self._deserialize_tag_from_sync(tag_data)
                existing = self.db.get_tag(tag.name)
                
                if existing:
                    if self._has_conflict(existing, tag_data):
                        if self.conflict_resolution == "server_wins":
                            self.db.update_tag(tag)
                            stats["conflicts_resolved"] += 1
                        elif self.conflict_resolution == "client_wins":
                            continue
                        else:
                            self.db.update_tag(tag)
                            stats["conflicts_resolved"] += 1
                    else:
                        self.db.update_tag(tag)
                else:
                    self.db.create_tag(tag)
                
                stats["tags_imported"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing tag: {e}")
        
        # Import tasks
        for task_data in sync_data.get("tasks", []):
            try:
                task = self._deserialize_task_from_sync(task_data)
                existing = self.db.get_task(task.id)
                
                if existing:
                    if self._has_conflict(existing, task_data):
                        if self.conflict_resolution == "server_wins":
                            self.db.update_task(task)
                            stats["conflicts_resolved"] += 1
                        elif self.conflict_resolution == "client_wins":
                            continue
                        else:
                            self.db.update_task(task)
                            stats["conflicts_resolved"] += 1
                    else:
                        self.db.update_task(task)
                else:
                    self.db.create_task(task)
                
                stats["tasks_imported"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing task: {e}")
        
        return stats
    
    def _deserialize_task_from_sync(self, task_data: Dict[str, Any]) -> Task:
        """Deserialize task from sync data."""
        # Convert datetime strings back to datetime objects
        if task_data.get('created_at'):
            task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
        if task_data.get('updated_at'):
            task_data['updated_at'] = datetime.fromisoformat(task_data['updated_at'])
        if task_data.get('completed_at'):
            task_data['completed_at'] = datetime.fromisoformat(task_data['completed_at'])
        if task_data.get('due_date'):
            task_data['due_date'] = datetime.fromisoformat(task_data['due_date'])
        if task_data.get('next_occurrence'):
            task_data['next_occurrence'] = datetime.fromisoformat(task_data['next_occurrence'])
        
        # Convert UUID strings back to UUID objects
        if task_data.get('id'):
            task_data['id'] = UUID(task_data['id'])
        if task_data.get('parent_task_id'):
            task_data['parent_task_id'] = UUID(task_data['parent_task_id'])
        
        # Remove sync-specific fields
        task_data.pop('sync_hash', None)
        
        return Task(**task_data)
    
    def _deserialize_project_from_sync(self, project_data: Dict[str, Any]) -> Project:
        """Deserialize project from sync data."""
        if project_data.get('created_at'):
            project_data['created_at'] = datetime.fromisoformat(project_data['created_at'])
        if project_data.get('updated_at'):
            project_data['updated_at'] = datetime.fromisoformat(project_data['updated_at'])
        if project_data.get('archived_at'):
            project_data['archived_at'] = datetime.fromisoformat(project_data['archived_at'])
        if project_data.get('completed_at'):
            project_data['completed_at'] = datetime.fromisoformat(project_data['completed_at'])
        
        if project_data.get('id'):
            project_data['id'] = UUID(project_data['id'])
        
        project_data.pop('sync_hash', None)
        
        return Project(**project_data)
    
    def _deserialize_tag_from_sync(self, tag_data: Dict[str, Any]) -> Tag:
        """Deserialize tag from sync data."""
        if tag_data.get('created_at'):
            tag_data['created_at'] = datetime.fromisoformat(tag_data['created_at'])
        if tag_data.get('updated_at'):
            tag_data['updated_at'] = datetime.fromisoformat(tag_data['updated_at'])
        if tag_data.get('last_used_at'):
            tag_data['last_used_at'] = datetime.fromisoformat(tag_data['last_used_at'])
        
        if tag_data.get('id'):
            tag_data['id'] = UUID(tag_data['id'])
        
        tag_data.pop('sync_hash', None)
        
        return Tag(**tag_data)
    
    def _has_conflict(self, existing: Any, sync_data: Dict[str, Any]) -> bool:
        """Check if there's a conflict between existing and sync data."""
        existing_hash = self._calculate_sync_hash(existing)
        sync_hash = sync_data.get('sync_hash', '')
        
        return existing_hash != sync_hash
    
    def sync_to_cloud(self, cloud_provider: str, credentials: Dict[str, str]) -> bool:
        """Sync data to cloud provider."""
        try:
            sync_data = self.export_for_sync()
            
            if cloud_provider == "dropbox":
                return self._sync_to_dropbox(sync_data, credentials)
            elif cloud_provider == "google_drive":
                return self._sync_to_google_drive(sync_data, credentials)
            elif cloud_provider == "onedrive":
                return self._sync_to_onedrive(sync_data, credentials)
            else:
                raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
        
        except Exception as e:
            print(f"Cloud sync failed: {e}")
            return False
    
    def _sync_to_dropbox(self, sync_data: Dict[str, Any], credentials: Dict[str, str]) -> bool:
        """Sync to Dropbox."""
        # This would require the Dropbox API
        # For now, just save to a local file
        sync_file = Path.home() / ".task-manager" / "sync" / "dropbox_sync.json"
        sync_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sync_file, 'w') as f:
            json.dump(sync_data, f, indent=2)
        
        return True
    
    def _sync_to_google_drive(self, sync_data: Dict[str, Any], credentials: Dict[str, str]) -> bool:
        """Sync to Google Drive."""
        # This would require the Google Drive API
        sync_file = Path.home() / ".task-manager" / "sync" / "google_drive_sync.json"
        sync_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sync_file, 'w') as f:
            json.dump(sync_data, f, indent=2)
        
        return True
    
    def _sync_to_onedrive(self, sync_data: Dict[str, Any], credentials: Dict[str, str]) -> bool:
        """Sync to OneDrive."""
        # This would require the OneDrive API
        sync_file = Path.home() / ".task-manager" / "sync" / "onedrive_sync.json"
        sync_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sync_file, 'w') as f:
            json.dump(sync_data, f, indent=2)
        
        return True
    
    def sync_from_cloud(self, cloud_provider: str, credentials: Dict[str, str]) -> Dict[str, int]:
        """Sync data from cloud provider."""
        try:
            if cloud_provider == "dropbox":
                sync_data = self._load_from_dropbox(credentials)
            elif cloud_provider == "google_drive":
                sync_data = self._load_from_google_drive(credentials)
            elif cloud_provider == "onedrive":
                sync_data = self._load_from_onedrive(credentials)
            else:
                raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
            
            if sync_data:
                return self.import_from_sync(sync_data)
            else:
                return {"tasks_imported": 0, "projects_imported": 0, "tags_imported": 0, "conflicts_resolved": 0, "errors": 1}
        
        except Exception as e:
            print(f"Cloud sync failed: {e}")
            return {"tasks_imported": 0, "projects_imported": 0, "tags_imported": 0, "conflicts_resolved": 0, "errors": 1}
    
    def _load_from_dropbox(self, credentials: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Load data from Dropbox."""
        sync_file = Path.home() / ".task-manager" / "sync" / "dropbox_sync.json"
        if sync_file.exists():
            with open(sync_file, 'r') as f:
                return json.load(f)
        return None
    
    def _load_from_google_drive(self, credentials: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Load data from Google Drive."""
        sync_file = Path.home() / ".task-manager" / "sync" / "google_drive_sync.json"
        if sync_file.exists():
            with open(sync_file, 'r') as f:
                return json.load(f)
        return None
    
    def _load_from_onedrive(self, credentials: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Load data from OneDrive."""
        sync_file = Path.home() / ".task-manager" / "sync" / "onedrive_sync.json"
        if sync_file.exists():
            with open(sync_file, 'r') as f:
                return json.load(f)
        return None
    
    def encrypt_sync_data(self, sync_data: Dict[str, Any], password: str) -> bytes:
        """Encrypt sync data for secure transmission."""
        # Generate key from password
        key = hashlib.sha256(password.encode()).digest()
        fernet = Fernet(base64.urlsafe_b64encode(key))
        
        # Encrypt the data
        json_data = json.dumps(sync_data).encode()
        encrypted_data = fernet.encrypt(json_data)
        
        return encrypted_data
    
    def decrypt_sync_data(self, encrypted_data: bytes, password: str) -> Dict[str, Any]:
        """Decrypt sync data."""
        # Generate key from password
        key = hashlib.sha256(password.encode()).digest()
        fernet = Fernet(base64.urlsafe_b64encode(key))
        
        # Decrypt the data
        decrypted_data = fernet.decrypt(encrypted_data)
        sync_data = json.loads(decrypted_data.decode())
        
        return sync_data
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_token": self.sync_token,
            "conflict_resolution": self.conflict_resolution,
            "device_info": {
                "hostname": self._get_hostname(),
                "platform": self._get_platform()
            }
        }
    
    def set_conflict_resolution(self, resolution: str) -> None:
        """Set conflict resolution strategy."""
        if resolution in ["server_wins", "client_wins", "manual"]:
            self.conflict_resolution = resolution
        else:
            raise ValueError("Invalid conflict resolution strategy")
    
    def cleanup_old_sync_data(self, days: int = 30) -> None:
        """Clean up old sync data files."""
        sync_dir = Path.home() / ".task-manager" / "sync"
        if sync_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for file_path in sync_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
