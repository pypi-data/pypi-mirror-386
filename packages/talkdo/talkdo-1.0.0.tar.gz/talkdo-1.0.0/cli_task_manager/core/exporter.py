"""
Export and import functionality for the CLI Task Manager.

This module provides comprehensive export/import capabilities for tasks,
projects, and configuration data in multiple formats.
"""

import json
import csv
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from cli_task_manager.models.task import Task, TaskPriority, TaskStatus
from cli_task_manager.models.project import Project, ProjectStatus
from cli_task_manager.models.tag import Tag
from cli_task_manager.models.reminder import Reminder
from cli_task_manager.models.dependency import Dependency
from cli_task_manager.core.database import DatabaseManager


class TaskExporter:
    """Export tasks and related data to various formats."""
    
    def __init__(self, db: DatabaseManager):
        """Initialize exporter with database manager."""
        self.db = db
    
    def export_json(self, output_path: Path, include_completed: bool = True) -> Dict[str, Any]:
        """Export all data to JSON format."""
        export_data = {
            "metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "format": "json",
                "include_completed": include_completed
            },
            "tasks": [],
            "projects": [],
            "tags": [],
            "reminders": [],
            "dependencies": []
        }
        
        # Export tasks
        tasks = self.db.list_tasks() if include_completed else self.db.list_tasks(status=TaskStatus.PENDING)
        for task in tasks:
            task_data = task.dict()
            task_data['created_at'] = task.created_at.isoformat()
            task_data['updated_at'] = task.updated_at.isoformat()
            if task.completed_at:
                task_data['completed_at'] = task.completed_at.isoformat()
            if task.due_date:
                task_data['due_date'] = task.due_date.isoformat()
            if task.next_occurrence:
                task_data['next_occurrence'] = task.next_occurrence.isoformat()
            export_data["tasks"].append(task_data)
        
        # Export projects
        projects = self.db.list_projects()
        for project in projects:
            project_data = project.dict()
            project_data['created_at'] = project.created_at.isoformat()
            project_data['updated_at'] = project.updated_at.isoformat()
            if project.archived_at:
                project_data['archived_at'] = project.archived_at.isoformat()
            if project.completed_at:
                project_data['completed_at'] = project.completed_at.isoformat()
            export_data["projects"].append(project_data)
        
        # Export tags
        tags = self.db.list_tags()
        for tag in tags:
            tag_data = tag.dict()
            tag_data['created_at'] = tag.created_at.isoformat()
            tag_data['updated_at'] = tag.updated_at.isoformat()
            if tag.last_used_at:
                tag_data['last_used_at'] = tag.last_used_at.isoformat()
            export_data["tags"].append(tag_data)
        
        # Export reminders
        for task in tasks:
            reminders = self.db.get_reminders_for_task(task.id)
            for reminder in reminders:
                reminder_data = reminder.dict()
                reminder_data['created_at'] = reminder.created_at.isoformat()
                reminder_data['updated_at'] = reminder.updated_at.isoformat()
                reminder_data['reminder_time'] = reminder.reminder_time.isoformat()
                if reminder.sent_at:
                    reminder_data['sent_at'] = reminder.sent_at.isoformat()
                if reminder.snoozed_until:
                    reminder_data['snoozed_until'] = reminder.snoozed_until.isoformat()
                export_data["reminders"].append(reminder_data)
        
        # Export dependencies
        for task in tasks:
            dependencies = self.db.get_dependencies_for_task(task.id)
            for dependency in dependencies:
                dependency_data = dependency.dict()
                dependency_data['created_at'] = dependency.created_at.isoformat()
                dependency_data['updated_at'] = dependency.updated_at.isoformat()
                if dependency.satisfied_at:
                    dependency_data['satisfied_at'] = dependency.satisfied_at.isoformat()
                export_data["dependencies"].append(dependency_data)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return export_data
    
    def export_csv(self, output_path: Path, include_completed: bool = True) -> None:
        """Export tasks to CSV format."""
        tasks = self.db.list_tasks() if include_completed else self.db.list_tasks(status=TaskStatus.PENDING)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'ID', 'Title', 'Description', 'Status', 'Priority', 'Due Date',
                'Created', 'Updated', 'Completed', 'Project', 'Tags', 'Recurring'
            ])
            
            # Write tasks
            for task in tasks:
                writer.writerow([
                    str(task.id),
                    task.title,
                    task.description or '',
                    task.status.value,
                    task.priority.value,
                    task.due_date.isoformat() if task.due_date else '',
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else '',
                    task.project or '',
                    ', '.join(task.tags),
                    'Yes' if task.is_recurring else 'No'
                ])
    
    def export_markdown(self, output_path: Path, include_completed: bool = True) -> None:
        """Export tasks to Markdown format."""
        tasks = self.db.list_tasks() if include_completed else self.db.list_tasks(status=TaskStatus.PENDING)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Task Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"Total tasks: {len(tasks)}\n\n")
            
            # Group by status
            status_groups = {}
            for task in tasks:
                status = task.status.value
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(task)
            
            for status, status_tasks in status_groups.items():
                f.write(f"## {status.title()} Tasks ({len(status_tasks)})\n\n")
                
                for task in status_tasks:
                    f.write(f"### {task.title}\n")
                    f.write(f"**ID:** `{task.id}`\n")
                    f.write(f"**Priority:** {task.priority.value}\n")
                    
                    if task.description:
                        f.write(f"**Description:** {task.description}\n")
                    
                    if task.due_date:
                        f.write(f"**Due Date:** {task.due_date.strftime('%Y-%m-%d %H:%M')}\n")
                    
                    if task.project:
                        f.write(f"**Project:** {task.project}\n")
                    
                    if task.tags:
                        f.write(f"**Tags:** {', '.join(task.tags)}\n")
                    
                    if task.is_recurring:
                        f.write(f"**Recurring:** {task.recurrence_pattern.type if task.recurrence_pattern else 'Yes'}\n")
                    
                    f.write(f"**Created:** {task.created_at.strftime('%Y-%m-%d %H:%M')}\n")
                    f.write(f"**Updated:** {task.updated_at.strftime('%Y-%m-%d %H:%M')}\n")
                    
                    if task.completed_at:
                        f.write(f"**Completed:** {task.completed_at.strftime('%Y-%m-%d %H:%M')}\n")
                    
                    f.write("\n")
    
    def export_todo_txt(self, output_path: Path, include_completed: bool = False) -> None:
        """Export tasks to todo.txt format."""
        tasks = self.db.list_tasks() if include_completed else self.db.list_tasks(status=TaskStatus.PENDING)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for task in tasks:
                line_parts = []
                
                # Priority
                if task.priority == TaskPriority.URGENT:
                    line_parts.append("(A)")
                elif task.priority == TaskPriority.HIGH:
                    line_parts.append("(B)")
                elif task.priority == TaskPriority.MEDIUM:
                    line_parts.append("(C)")
                elif task.priority == TaskPriority.LOW:
                    line_parts.append("(D)")
                
                # Completion status
                if task.status == TaskStatus.COMPLETED:
                    line_parts.append("x")
                
                # Due date
                if task.due_date:
                    line_parts.append(task.due_date.strftime("%Y-%m-%d"))
                
                # Title
                line_parts.append(task.title)
                
                # Contexts (projects)
                if task.project:
                    line_parts.append(f"@{task.project}")
                
                # Tags
                for tag in task.tags:
                    line_parts.append(f"+{tag}")
                
                f.write(" ".join(line_parts) + "\n")
    
    def export_ical(self, output_path: Path, include_completed: bool = False) -> None:
        """Export tasks to iCalendar format."""
        tasks = self.db.list_tasks() if include_completed else self.db.list_tasks(status=TaskStatus.PENDING)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("BEGIN:VCALENDAR\n")
            f.write("VERSION:2.0\n")
            f.write("PRODID:-//CLI Task Manager//Task Export//EN\n")
            f.write("CALSCALE:GREGORIAN\n")
            
            for task in tasks:
                if task.due_date:
                    f.write("BEGIN:VEVENT\n")
                    f.write(f"UID:{task.id}@cli-task-manager.local\n")
                    f.write(f"DTSTART:{task.due_date.strftime('%Y%m%dT%H%M%SZ')}\n")
                    f.write(f"DTEND:{task.due_date.strftime('%Y%m%dT%H%M%SZ')}\n")
                    f.write(f"SUMMARY:{task.title}\n")
                    
                    if task.description:
                        f.write(f"DESCRIPTION:{task.description}\n")
                    
                    if task.project:
                        f.write(f"CATEGORIES:{task.project}\n")
                    
                    f.write(f"PRIORITY:{task.priority.value.upper()}\n")
                    f.write(f"STATUS:{task.status.value.upper()}\n")
                    f.write("END:VEVENT\n")
            
            f.write("END:VCALENDAR\n")


class TaskImporter:
    """Import tasks and related data from various formats."""
    
    def __init__(self, db: DatabaseManager):
        """Initialize importer with database manager."""
        self.db = db
    
    def import_json(self, input_path: Path) -> Dict[str, int]:
        """Import data from JSON format."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stats = {
            "tasks_imported": 0,
            "projects_imported": 0,
            "tags_imported": 0,
            "reminders_imported": 0,
            "dependencies_imported": 0,
            "errors": 0
        }
        
        # Import projects first
        for project_data in data.get("projects", []):
            try:
                # Convert datetime strings back to datetime objects
                if 'created_at' in project_data:
                    project_data['created_at'] = datetime.fromisoformat(project_data['created_at'])
                if 'updated_at' in project_data:
                    project_data['updated_at'] = datetime.fromisoformat(project_data['updated_at'])
                if 'archived_at' in project_data and project_data['archived_at']:
                    project_data['archived_at'] = datetime.fromisoformat(project_data['archived_at'])
                if 'completed_at' in project_data and project_data['completed_at']:
                    project_data['completed_at'] = datetime.fromisoformat(project_data['completed_at'])
                
                project = Project(**project_data)
                self.db.create_project(project)
                stats["projects_imported"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing project: {e}")
        
        # Import tags
        for tag_data in data.get("tags", []):
            try:
                if 'created_at' in tag_data:
                    tag_data['created_at'] = datetime.fromisoformat(tag_data['created_at'])
                if 'updated_at' in tag_data:
                    tag_data['updated_at'] = datetime.fromisoformat(tag_data['updated_at'])
                if 'last_used_at' in tag_data and tag_data['last_used_at']:
                    tag_data['last_used_at'] = datetime.fromisoformat(tag_data['last_used_at'])
                
                tag = Tag(**tag_data)
                self.db.create_tag(tag)
                stats["tags_imported"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing tag: {e}")
        
        # Import tasks
        for task_data in data.get("tasks", []):
            try:
                # Convert datetime strings back to datetime objects
                if 'created_at' in task_data:
                    task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
                if 'updated_at' in task_data:
                    task_data['updated_at'] = datetime.fromisoformat(task_data['updated_at'])
                if 'completed_at' in task_data and task_data['completed_at']:
                    task_data['completed_at'] = datetime.fromisoformat(task_data['completed_at'])
                if 'due_date' in task_data and task_data['due_date']:
                    task_data['due_date'] = datetime.fromisoformat(task_data['due_date'])
                if 'next_occurrence' in task_data and task_data['next_occurrence']:
                    task_data['next_occurrence'] = datetime.fromisoformat(task_data['next_occurrence'])
                
                task = Task(**task_data)
                self.db.create_task(task)
                stats["tasks_imported"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing task: {e}")
        
        # Import reminders
        for reminder_data in data.get("reminders", []):
            try:
                if 'created_at' in reminder_data:
                    reminder_data['created_at'] = datetime.fromisoformat(reminder_data['created_at'])
                if 'updated_at' in reminder_data:
                    reminder_data['updated_at'] = datetime.fromisoformat(reminder_data['updated_at'])
                if 'reminder_time' in reminder_data:
                    reminder_data['reminder_time'] = datetime.fromisoformat(reminder_data['reminder_time'])
                if 'sent_at' in reminder_data and reminder_data['sent_at']:
                    reminder_data['sent_at'] = datetime.fromisoformat(reminder_data['sent_at'])
                if 'snoozed_until' in reminder_data and reminder_data['snoozed_until']:
                    reminder_data['snoozed_until'] = datetime.fromisoformat(reminder_data['snoozed_until'])
                
                reminder = Reminder(**reminder_data)
                self.db.create_reminder(reminder)
                stats["reminders_imported"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing reminder: {e}")
        
        # Import dependencies
        for dependency_data in data.get("dependencies", []):
            try:
                if 'created_at' in dependency_data:
                    dependency_data['created_at'] = datetime.fromisoformat(dependency_data['created_at'])
                if 'updated_at' in dependency_data:
                    dependency_data['updated_at'] = datetime.fromisoformat(dependency_data['updated_at'])
                if 'satisfied_at' in dependency_data and dependency_data['satisfied_at']:
                    dependency_data['satisfied_at'] = datetime.fromisoformat(dependency_data['satisfied_at'])
                
                dependency = Dependency(**dependency_data)
                self.db.create_dependency(dependency)
                stats["dependencies_imported"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error importing dependency: {e}")
        
        return stats
    
    def import_csv(self, input_path: Path) -> Dict[str, int]:
        """Import tasks from CSV format."""
        stats = {
            "tasks_imported": 0,
            "errors": 0
        }
        
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse task data
                    task_data = {
                        'title': row['Title'],
                        'description': row['Description'] if row['Description'] else None,
                        'status': TaskStatus(row['Status']),
                        'priority': TaskPriority(row['Priority']),
                        'project': row['Project'] if row['Project'] else None,
                        'tags': [tag.strip() for tag in row['Tags'].split(',')] if row['Tags'] else [],
                        'is_recurring': row['Recurring'] == 'Yes'
                    }
                    
                    # Parse dates
                    if row['Due Date']:
                        task_data['due_date'] = datetime.fromisoformat(row['Due Date'])
                    if row['Created']:
                        task_data['created_at'] = datetime.fromisoformat(row['Created'])
                    if row['Updated']:
                        task_data['updated_at'] = datetime.fromisoformat(row['Updated'])
                    if row['Completed']:
                        task_data['completed_at'] = datetime.fromisoformat(row['Completed'])
                    
                    task = Task(**task_data)
                    self.db.create_task(task)
                    stats["tasks_imported"] += 1
                    
                except Exception as e:
                    stats["errors"] += 1
                    print(f"Error importing task: {e}")
        
        return stats
    
    def import_todo_txt(self, input_path: Path) -> Dict[str, int]:
        """Import tasks from todo.txt format."""
        stats = {
            "tasks_imported": 0,
            "errors": 0
        }
        
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse todo.txt format
                    parts = line.split()
                    task_data = {
                        'title': '',
                        'status': TaskStatus.PENDING,
                        'priority': TaskPriority.MEDIUM,
                        'tags': [],
                        'project': None
                    }
                    
                    # Parse priority
                    if parts and parts[0].startswith('(') and parts[0].endswith(')'):
                        priority_char = parts[0][1]
                        if priority_char == 'A':
                            task_data['priority'] = TaskPriority.URGENT
                        elif priority_char == 'B':
                            task_data['priority'] = TaskPriority.HIGH
                        elif priority_char == 'C':
                            task_data['priority'] = TaskPriority.MEDIUM
                        elif priority_char == 'D':
                            task_data['priority'] = TaskPriority.LOW
                        parts = parts[1:]
                    
                    # Parse completion status
                    if parts and parts[0] == 'x':
                        task_data['status'] = TaskStatus.COMPLETED
                        parts = parts[1:]
                    
                    # Parse due date
                    if parts and len(parts[0]) == 10 and parts[0].count('-') == 2:
                        try:
                            due_date = datetime.strptime(parts[0], '%Y-%m-%d')
                            task_data['due_date'] = due_date
                            parts = parts[1:]
                        except ValueError:
                            pass
                    
                    # Parse title and extract contexts/tags
                    title_parts = []
                    for part in parts:
                        if part.startswith('@'):
                            task_data['project'] = part[1:]
                        elif part.startswith('+'):
                            task_data['tags'].append(part[1:])
                        else:
                            title_parts.append(part)
                    
                    task_data['title'] = ' '.join(title_parts)
                    
                    task = Task(**task_data)
                    self.db.create_task(task)
                    stats["tasks_imported"] += 1
                    
                except Exception as e:
                    stats["errors"] += 1
                    print(f"Error importing line {line_num}: {e}")
        
        return stats
