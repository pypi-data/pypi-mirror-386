"""
Mobile companion features for the CLI Task Manager.

This module provides mobile-friendly features, QR code generation,
and mobile app integration capabilities.
"""

import json
import qrcode
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import base64
import hashlib

from cli_task_manager.models.task import Task, TaskStatus, TaskPriority
from cli_task_manager.models.project import Project
from cli_task_manager.core.database import DatabaseManager
from cli_task_manager.core.config import Config


class MobileCompanion:
    """Mobile companion features for CLI Task Manager."""
    
    def __init__(self, db: DatabaseManager, config: Config):
        """Initialize mobile companion."""
        self.db = db
        self.config = config
        self.mobile_token: Optional[str] = None
        self.mobile_sync_enabled = False
    
    def generate_mobile_qr(self, output_path: Path) -> bool:
        """Generate QR code for mobile app connection."""
        try:
            # Generate mobile connection data
            connection_data = {
                "app_name": "CLI Task Manager",
                "version": "1.0.0",
                "connection_token": self._generate_connection_token(),
                "server_info": {
                    "hostname": self._get_hostname(),
                    "platform": self._get_platform(),
                    "timestamp": datetime.utcnow().isoformat()
                },
                "capabilities": [
                    "task_management",
                    "project_organization",
                    "tag_system",
                    "reminder_system",
                    "sync_support"
                ]
            }
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            qr.add_data(json.dumps(connection_data))
            qr.make(fit=True)
            
            # Generate QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(output_path)
            
            return True
        
        except Exception as e:
            print(f"QR code generation failed: {e}")
            return False
    
    def _generate_connection_token(self) -> str:
        """Generate a secure connection token."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _get_hostname(self) -> str:
        """Get system hostname."""
        import socket
        return socket.gethostname()
    
    def _get_platform(self) -> str:
        """Get platform information."""
        import platform
        return f"{platform.system()}-{platform.release()}"
    
    def generate_mobile_export(self, format_type: str = "json") -> Dict[str, Any]:
        """Generate mobile-friendly export."""
        # Get all data
        tasks = self.db.list_tasks()
        projects = self.db.list_projects()
        tags = self.db.list_tags()
        
        # Create mobile-optimized structure
        mobile_data = {
            "metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "format": format_type,
                "version": "1.0.0",
                "total_tasks": len(tasks),
                "total_projects": len(projects),
                "total_tags": len(tags)
            },
            "tasks": [],
            "projects": [],
            "tags": [],
            "quick_stats": self._generate_quick_stats(tasks)
        }
        
        # Process tasks for mobile
        for task in tasks:
            mobile_task = {
                "id": str(task.id),
                "title": task.title,
                "description": task.description or "",
                "status": task.status.value,
                "priority": task.priority.value,
                "tags": task.tags,
                "project": task.project or "",
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "is_overdue": task.is_overdue(),
                "is_recurring": task.is_recurring,
                "mobile_friendly": True
            }
            mobile_data["tasks"].append(mobile_task)
        
        # Process projects for mobile
        for project in projects:
            mobile_project = {
                "id": str(project.id),
                "name": project.name,
                "description": project.description or "",
                "status": project.status.value,
                "color": project.color or "#007bff",
                "icon": project.icon or "📁",
                "task_count": len([t for t in tasks if t.project == project.name]),
                "mobile_friendly": True
            }
            mobile_data["projects"].append(mobile_project)
        
        # Process tags for mobile
        for tag in tags:
            mobile_tag = {
                "id": str(tag.id),
                "name": tag.name,
                "description": tag.description or "",
                "color": tag.color or "#6c757d",
                "icon": tag.icon or "🏷️",
                "usage_count": tag.usage_count,
                "mobile_friendly": True
            }
            mobile_data["tags"].append(mobile_tag)
        
        return mobile_data
    
    def _generate_quick_stats(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate quick statistics for mobile display."""
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
        overdue_tasks = len([t for t in tasks if t.is_overdue()])
        
        # Priority distribution
        priority_counts = {
            "urgent": len([t for t in tasks if t.priority == TaskPriority.URGENT]),
            "high": len([t for t in tasks if t.priority == TaskPriority.HIGH]),
            "medium": len([t for t in tasks if t.priority == TaskPriority.MEDIUM]),
            "low": len([t for t in tasks if t.priority == TaskPriority.LOW])
        }
        
        # Recent activity
        recent_tasks = [
            t for t in tasks
            if t.created_at >= datetime.now() - timedelta(days=7)
        ]
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "priority_distribution": priority_counts,
            "recent_activity": len(recent_tasks),
            "productivity_score": self._calculate_productivity_score(tasks)
        }
    
    def _calculate_productivity_score(self, tasks: List[Task]) -> int:
        """Calculate a simple productivity score (0-100)."""
        if not tasks:
            return 0
        
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        overdue = len([t for t in tasks if t.is_overdue()])
        total = len(tasks)
        
        # Base score from completion rate
        completion_score = (completed / total) * 60
        
        # Penalty for overdue tasks
        overdue_penalty = (overdue / total) * 20
        
        # Bonus for recent activity
        recent_tasks = len([
            t for t in tasks
            if t.created_at >= datetime.now() - timedelta(days=7)
        ])
        activity_bonus = min(recent_tasks * 2, 20)
        
        score = max(0, min(100, completion_score - overdue_penalty + activity_bonus))
        return int(score)
    
    def generate_mobile_widget_data(self) -> Dict[str, Any]:
        """Generate data for mobile widgets."""
        tasks = self.db.list_tasks()
        
        # Today's tasks
        today = datetime.now().date()
        today_tasks = [
            t for t in tasks
            if t.due_date and t.due_date.date() == today
        ]
        
        # Overdue tasks
        overdue_tasks = [t for t in tasks if t.is_overdue()]
        
        # High priority tasks
        high_priority_tasks = [
            t for t in tasks
            if t.priority in [TaskPriority.URGENT, TaskPriority.HIGH]
            and t.status != TaskStatus.COMPLETED
        ]
        
        # Recent completions
        recent_completions = [
            t for t in tasks
            if t.status == TaskStatus.COMPLETED
            and t.completed_at
            and t.completed_at >= datetime.now() - timedelta(days=7)
        ]
        
        return {
            "today_tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "priority": t.priority.value,
                    "due_time": t.due_date.strftime("%H:%M") if t.due_date else None
                }
                for t in today_tasks[:5]  # Limit to 5
            ],
            "overdue_tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "priority": t.priority.value,
                    "days_overdue": (datetime.now().date() - t.due_date.date()).days if t.due_date else 0
                }
                for t in overdue_tasks[:3]  # Limit to 3
            ],
            "high_priority_tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "priority": t.priority.value,
                    "project": t.project or ""
                }
                for t in high_priority_tasks[:3]  # Limit to 3
            ],
            "recent_completions": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "completed_at": t.completed_at.strftime("%H:%M") if t.completed_at else None
                }
                for t in recent_completions[:5]  # Limit to 5
            ],
            "quick_stats": {
                "total_pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
                "overdue_count": len(overdue_tasks),
                "today_count": len(today_tasks),
                "completion_rate": self._calculate_completion_rate(tasks)
            }
        }
    
    def _calculate_completion_rate(self, tasks: List[Task]) -> float:
        """Calculate completion rate."""
        if not tasks:
            return 0.0
        
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        return (completed / len(tasks)) * 100
    
    def generate_mobile_shortcuts(self) -> List[Dict[str, Any]]:
        """Generate mobile shortcuts for quick actions."""
        return [
            {
                "name": "Add Quick Task",
                "description": "Add a simple task quickly",
                "action": "add_task",
                "icon": "➕",
                "color": "#28a745"
            },
            {
                "name": "View Today",
                "description": "See today's tasks",
                "action": "view_today",
                "icon": "📅",
                "color": "#007bff"
            },
            {
                "name": "View Overdue",
                "description": "See overdue tasks",
                "action": "view_overdue",
                "icon": "⚠️",
                "color": "#dc3545"
            },
            {
                "name": "Quick Stats",
                "description": "View productivity stats",
                "action": "view_stats",
                "icon": "📊",
                "color": "#6f42c1"
            },
            {
                "name": "Sync Data",
                "description": "Sync with desktop",
                "action": "sync",
                "icon": "🔄",
                "color": "#17a2b8"
            }
        ]
    
    def generate_mobile_notifications(self) -> List[Dict[str, Any]]:
        """Generate mobile notification data."""
        tasks = self.db.list_tasks()
        notifications = []
        
        # Overdue tasks
        overdue_tasks = [t for t in tasks if t.is_overdue()]
        if overdue_tasks:
            notifications.append({
                "type": "overdue",
                "title": f"{len(overdue_tasks)} Overdue Task(s)",
                "message": f"You have {len(overdue_tasks)} overdue tasks that need attention.",
                "priority": "high",
                "action": "view_overdue",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Today's tasks
        today = datetime.now().date()
        today_tasks = [
            t for t in tasks
            if t.due_date and t.due_date.date() == today
            and t.status != TaskStatus.COMPLETED
        ]
        if today_tasks:
            notifications.append({
                "type": "today",
                "title": f"{len(today_tasks)} Task(s) Due Today",
                "message": f"You have {len(today_tasks)} tasks due today.",
                "priority": "medium",
                "action": "view_today",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # High priority tasks
        high_priority_tasks = [
            t for t in tasks
            if t.priority == TaskPriority.URGENT
            and t.status != TaskStatus.COMPLETED
        ]
        if high_priority_tasks:
            notifications.append({
                "type": "urgent",
                "title": f"{len(high_priority_tasks)} Urgent Task(s)",
                "message": f"You have {len(high_priority_tasks)} urgent tasks.",
                "priority": "high",
                "action": "view_urgent",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return notifications
    
    def create_mobile_backup(self, output_path: Path) -> bool:
        """Create a mobile-friendly backup."""
        try:
            mobile_data = self.generate_mobile_export()
            
            # Add mobile-specific metadata
            mobile_data["mobile_metadata"] = {
                "backup_type": "mobile",
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "device_info": {
                    "platform": self._get_platform(),
                    "hostname": self._get_hostname()
                }
            }
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(mobile_data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Mobile backup creation failed: {e}")
            return False
    
    def restore_mobile_backup(self, backup_path: Path) -> Dict[str, int]:
        """Restore from mobile backup."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                mobile_data = json.load(f)
            
            stats = {
                "tasks_imported": 0,
                "projects_imported": 0,
                "tags_imported": 0,
                "errors": 0
            }
            
            # Import projects
            for project_data in mobile_data.get("projects", []):
                try:
                    project = Project(
                        name=project_data["name"],
                        description=project_data.get("description"),
                        status=ProjectStatus(project_data.get("status", "active")),
                        color=project_data.get("color"),
                        icon=project_data.get("icon")
                    )
                    self.db.create_project(project)
                    stats["projects_imported"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    print(f"Error importing project: {e}")
            
            # Import tags
            for tag_data in mobile_data.get("tags", []):
                try:
                    tag = Tag(
                        name=tag_data["name"],
                        description=tag_data.get("description"),
                        color=tag_data.get("color"),
                        icon=tag_data.get("icon")
                    )
                    self.db.create_tag(tag)
                    stats["tags_imported"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    print(f"Error importing tag: {e}")
            
            # Import tasks
            for task_data in mobile_data.get("tasks", []):
                try:
                    task = Task(
                        title=task_data["title"],
                        description=task_data.get("description"),
                        status=TaskStatus(task_data.get("status", "pending")),
                        priority=TaskPriority(task_data.get("priority", "medium")),
                        tags=task_data.get("tags", []),
                        project=task_data.get("project"),
                        due_date=datetime.fromisoformat(task_data["due_date"]) if task_data.get("due_date") else None
                    )
                    self.db.create_task(task)
                    stats["tasks_imported"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    print(f"Error importing task: {e}")
            
            return stats
        
        except Exception as e:
            print(f"Mobile backup restoration failed: {e}")
            return {"tasks_imported": 0, "projects_imported": 0, "tags_imported": 0, "errors": 1}
    
    def generate_mobile_api_data(self) -> Dict[str, Any]:
        """Generate data for mobile API endpoints."""
        return {
            "endpoints": {
                "tasks": "/api/tasks",
                "projects": "/api/projects",
                "tags": "/api/tags",
                "stats": "/api/stats",
                "sync": "/api/sync"
            },
            "authentication": {
                "type": "token",
                "token": self.mobile_token or "not_configured"
            },
            "capabilities": [
                "read_tasks",
                "create_tasks",
                "update_tasks",
                "delete_tasks",
                "sync_data",
                "view_stats"
            ],
            "rate_limits": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000
            }
        }
