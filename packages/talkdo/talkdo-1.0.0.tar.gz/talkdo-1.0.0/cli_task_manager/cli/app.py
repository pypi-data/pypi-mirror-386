"""
Main CLI application using Typer.

This module defines the main CLI application with all commands
and subcommands for task management.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from cli_task_manager.core.config import Config
from cli_task_manager.core.database import DatabaseManager
from cli_task_manager.core.parser import NaturalLanguageParser
from cli_task_manager.core.exporter import TaskExporter, TaskImporter
from cli_task_manager.core.analytics import ProductivityAnalytics
from cli_task_manager.core.themes import ThemeManager, ThemeType
from cli_task_manager.core.sync import SyncManager
from cli_task_manager.core.security import SecurityManager
from cli_task_manager.core.mobile import MobileCompanion
from cli_task_manager.models.task import Task, TaskPriority, TaskStatus
from cli_task_manager.models.project import Project, ProjectStatus
from cli_task_manager.models.tag import Tag
from cli_task_manager.models.reminder import Reminder, ReminderType, ReminderStatus

# Initialize console
console = Console()

# Initialize app
app = typer.Typer(
    name="talkdo",
    help="Talkdo - Talk your to-dos. A professional CLI task manager with natural language processing",
    no_args_is_help=True,
    rich_markup_mode="rich"
)

# Global state
_config: Optional[Config] = None
_db: Optional[DatabaseManager] = None
_parser: Optional[NaturalLanguageParser] = None
_exporter: Optional[TaskExporter] = None
_importer: Optional[TaskImporter] = None
_analytics: Optional[ProductivityAnalytics] = None
_theme_manager: Optional[ThemeManager] = None
_sync_manager: Optional[SyncManager] = None
_security_manager: Optional[SecurityManager] = None
_mobile_companion: Optional[MobileCompanion] = None


def get_config() -> Config:
    """Get or create configuration."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def get_database() -> DatabaseManager:
    """Get or create database manager."""
    global _db
    if _db is None:
        config = get_config()
        db_path = config.get_database_path()
        _db = DatabaseManager(db_path)
    return _db


def get_parser() -> NaturalLanguageParser:
    """Get or create natural language parser."""
    global _parser
    if _parser is None:
        config = get_config()
        _parser = NaturalLanguageParser(config.parser.dict())
    return _parser


def get_exporter() -> TaskExporter:
    """Get or create task exporter."""
    global _exporter
    if _exporter is None:
        _exporter = TaskExporter(get_database())
    return _exporter


def get_importer() -> TaskImporter:
    """Get or create task importer."""
    global _importer
    if _importer is None:
        _importer = TaskImporter(get_database())
    return _importer


def get_analytics() -> ProductivityAnalytics:
    """Get or create productivity analytics."""
    global _analytics
    if _analytics is None:
        _analytics = ProductivityAnalytics(get_database())
    return _analytics


def get_theme_manager() -> ThemeManager:
    """Get or create theme manager."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def get_sync_manager() -> SyncManager:
    """Get or create sync manager."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager(get_database(), get_config())
    return _sync_manager


def get_security_manager() -> SecurityManager:
    """Get or create security manager."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager(get_config())
    return _security_manager


def get_mobile_companion() -> MobileCompanion:
    """Get or create mobile companion."""
    global _mobile_companion
    if _mobile_companion is None:
        _mobile_companion = MobileCompanion(get_database(), get_config())
    return _mobile_companion


def format_task(task: Task, show_id: bool = False) -> str:
    """Format a task for display."""
    # Status icons
    status_icons = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.CANCELLED: "❌"
    }
    
    # Priority icons
    priority_icons = {
        TaskPriority.LOW: "🔵",
        TaskPriority.MEDIUM: "⚪",
        TaskPriority.HIGH: "🟡",
        TaskPriority.URGENT: "🔴"
    }
    
    icon = status_icons.get(task.status, "⏳")
    priority = priority_icons.get(task.priority, "⚪")
    
    # Due date info
    due_info = ""
    if task.due_date:
        if task.is_overdue():
            due_info = " [red](OVERDUE)[/red]"
        elif task.is_due_today():
            due_info = " [yellow](TODAY)[/yellow]"
        else:
            days = task.get_days_until_due()
            if days is not None:
                if days == 1:
                    due_info = " [blue](tomorrow)[/blue]"
                elif days > 1:
                    due_info = f" [blue]({days}d)[/blue]"
    
    # Tags
    tags_info = ""
    if task.tags:
        tags_info = f" [dim]#{' '.join(task.tags)}[/dim]"
    
    # Project
    project_info = ""
    if task.project:
        project_info = f" [cyan]@{task.project}[/cyan]"
    
    # ID
    id_info = f" [dim]{task.id}[/dim]" if show_id else ""
    
    return f"{icon} {priority} {task.title}{due_info}{tags_info}{project_info}{id_info}"


def create_task_table(tasks: List[Task], show_id: bool = False) -> Table:
    """Create a Rich table for tasks."""
    table = Table(show_header=True, header_style="bold magenta")
    
    if show_id:
        table.add_column("ID", style="dim", width=8)
    
    table.add_column("Status", width=8)
    table.add_column("Priority", width=8)
    table.add_column("Title", style="cyan")
    table.add_column("Due Date", style="blue", width=12)
    table.add_column("Project", style="green", width=12)
    table.add_column("Tags", style="yellow")
    
    for task in tasks:
        row = []
        
        if show_id:
            row.append(str(task.id)[:8])
        
        # Status
        status_icon = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.CANCELLED: "❌"
        }
        row.append(status_icon.get(task.status, "⏳"))
        
        # Priority
        priority_icon = {
            TaskPriority.LOW: "🔵",
            TaskPriority.MEDIUM: "⚪",
            TaskPriority.HIGH: "🟡",
            TaskPriority.URGENT: "🔴"
        }
        row.append(priority_icon.get(task.priority, "⚪"))
        
        # Title
        title = task.title
        if len(title) > 50:
            title = title[:47] + "..."
        row.append(title)
        
        # Due date
        if task.due_date:
            due_str = task.due_date.strftime("%Y-%m-%d %H:%M")
            if task.is_overdue():
                due_str = f"[red]{due_str}[/red]"
            elif task.is_due_today():
                due_str = f"[yellow]{due_str}[/yellow]"
            row.append(due_str)
        else:
            row.append("-")
        
        # Project
        row.append(task.project or "-")
        
        # Tags
        row.append(", ".join(task.tags) if task.tags else "-")
        
        table.add_row(*row)
    
    return table


@app.command()
def add(
    input_text: str = typer.Argument(..., help="Natural language task description"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode for complex tasks"),
    confirm: bool = typer.Option(True, "--confirm/--no-confirm", help="Confirm before creating task")
):
    """Add a new task using natural language."""
    try:
        parser = get_parser()
        result = parser.parse(input_text)
        
        if result.errors:
            console.print("[red]Parsing errors:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)
        
        if result.warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")
        
        # Show parsed information
        console.print("\n[bold]Parsed Task Information:[/bold]")
        console.print(f"Title: {result.title}")
        if result.description:
            console.print(f"Description: {result.description}")
        if result.due_date:
            console.print(f"Due Date: {result.due_date.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"Priority: {result.priority.value}")
        if result.tags:
            console.print(f"Tags: {', '.join(result.tags)}")
        if result.project:
            console.print(f"Project: {result.project}")
        if result.is_recurring:
            console.print(f"Recurring: {result.recurrence_pattern.type if result.recurrence_pattern else 'Yes'}")
        if result.reminders:
            console.print(f"Reminders: {len(result.reminders)}")
        
        console.print(f"\nConfidence: {result.confidence:.1%}")
        
        if result.confidence < 0.5:
            suggestions = parser.suggest_corrections(result)
            if suggestions:
                console.print("\n[yellow]Suggestions:[/yellow]")
                for suggestion in suggestions:
                    console.print(f"  • {suggestion}")
        
        if confirm and not typer.confirm("\nCreate this task?"):
            console.print("Task creation cancelled.")
            raise typer.Exit(0)
        
        # Create task
        task = Task(
            title=result.title,
            description=result.description,
            due_date=result.due_date,
            priority=result.priority,
            tags=result.tags,
            project=result.project,
            is_recurring=result.is_recurring,
            recurrence_pattern=result.recurrence_pattern
        )
        
        db = get_database()
        created_task = db.create_task(task)
        
        # Create reminders
        for reminder in result.reminders:
            reminder.task_id = created_task.id
            db.create_reminder(reminder)
        
        console.print(f"\n[green]✅ Task created successfully![/green]")
        console.print(f"ID: {created_task.id}")
        
    except Exception as e:
        console.print(f"[red]Error creating task: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (pending, in_progress, completed, cancelled)"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="Filter by priority (low, medium, high, urgent)"),
    project: Optional[str] = typer.Option(None, "--project", help="Filter by project"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    today: bool = typer.Option(False, "--today", help="Show tasks due today"),
    week: bool = typer.Option(False, "--week", help="Show tasks due this week"),
    overdue: bool = typer.Option(False, "--overdue", help="Show overdue tasks"),
    completed: bool = typer.Option(False, "--completed", help="Show completed tasks"),
    all: bool = typer.Option(False, "--all", help="Show all tasks including completed"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of tasks to show"),
    show_id: bool = typer.Option(False, "--id", help="Show task IDs"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, compact, detailed, json)")
):
    """List tasks with optional filtering."""
    try:
        db = get_database()
        
        # Parse filters
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status.lower())
            except ValueError:
                console.print(f"[red]Invalid status: {status}[/red]")
                raise typer.Exit(1)
        
        priority_filter = None
        if priority:
            try:
                priority_filter = TaskPriority(priority.lower())
            except ValueError:
                console.print(f"[red]Invalid priority: {priority}[/red]")
                raise typer.Exit(1)
        
        # Get tasks
        tasks = db.list_tasks(
            status=status_filter,
            priority=priority_filter,
            project=project,
            tag=tag,
            due_today=today,
            due_this_week=week,
            overdue=overdue,
            limit=limit if not all else None
        )
        
        if not tasks:
            console.print("[yellow]No tasks found.[/yellow]")
            return
        
        # Show tasks
        if format == "table":
            table = create_task_table(tasks, show_id=show_id)
            console.print(table)
        elif format == "compact":
            for task in tasks:
                console.print(format_task(task, show_id=show_id))
        elif format == "detailed":
            for task in tasks:
                console.print(f"\n[bold]{task.title}[/bold]")
                if task.description:
                    console.print(f"Description: {task.description}")
                console.print(f"Status: {task.status.value}")
                console.print(f"Priority: {task.priority.value}")
                if task.due_date:
                    console.print(f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}")
                if task.project:
                    console.print(f"Project: {task.project}")
                if task.tags:
                    console.print(f"Tags: {', '.join(task.tags)}")
                console.print(f"ID: {task.id}")
        elif format == "json":
            import json
            task_dicts = [task.dict() for task in tasks]
            console.print(json.dumps(task_dicts, indent=2, default=str))
        else:
            console.print(f"[red]Invalid format: {format}[/red]")
            raise typer.Exit(1)
        
        # Show count
        console.print(f"\n[dim]Showing {len(tasks)} task(s)[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error listing tasks: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def complete(
    task_id: str = typer.Argument(..., help="Task ID to complete"),
    confirm: bool = typer.Option(True, "--confirm/--no-confirm", help="Confirm before completing")
):
    """Mark a task as completed."""
    try:
        from uuid import UUID
        
        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            console.print(f"[red]Invalid task ID: {task_id}[/red]")
            raise typer.Exit(1)
        
        db = get_database()
        task = db.get_task(task_uuid)
        
        if not task:
            console.print(f"[red]Task not found: {task_id}[/red]")
            raise typer.Exit(1)
        
        if task.status == TaskStatus.COMPLETED:
            console.print(f"[yellow]Task is already completed: {task.title}[/yellow]")
            return
        
        if confirm and not typer.confirm(f"Complete task '{task.title}'?"):
            console.print("Task completion cancelled.")
            return
        
        # Complete task
        task.complete()
        db.update_task(task)
        
        console.print(f"[green]✅ Task completed: {task.title}[/green]")
        
        # Handle recurring tasks
        if task.is_recurring and task.recurrence_pattern:
            console.print("[blue]Creating next occurrence...[/blue]")
            # TODO: Implement recurring task logic
            console.print("[yellow]Recurring task logic not yet implemented[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error completing task: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def delete(
    task_id: str = typer.Argument(..., help="Task ID to delete"),
    force: bool = typer.Option(False, "--force", help="Delete without confirmation")
):
    """Delete a task."""
    try:
        from uuid import UUID
        
        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            console.print(f"[red]Invalid task ID: {task_id}[/red]")
            raise typer.Exit(1)
        
        db = get_database()
        task = db.get_task(task_uuid)
        
        if not task:
            console.print(f"[red]Task not found: {task_id}[/red]")
            raise typer.Exit(1)
        
        if not force and not typer.confirm(f"Delete task '{task.title}'?"):
            console.print("Task deletion cancelled.")
            return
        
        # Delete task
        success = db.delete_task(task_uuid)
        
        if success:
            console.print(f"[green]✅ Task deleted: {task.title}[/green]")
        else:
            console.print(f"[red]Failed to delete task: {task.title}[/red]")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Error deleting task: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def show(
    task_id: str = typer.Argument(..., help="Task ID to show")
):
    """Show detailed information about a task."""
    try:
        from uuid import UUID
        
        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            console.print(f"[red]Invalid task ID: {task_id}[/red]")
            raise typer.Exit(1)
        
        db = get_database()
        task = db.get_task(task_uuid)
        
        if not task:
            console.print(f"[red]Task not found: {task_id}[/red]")
            raise typer.Exit(1)
        
        # Show task details
        console.print(f"\n[bold]{task.title}[/bold]")
        console.print(f"ID: {task.id}")
        console.print(f"Status: {task.status.value}")
        console.print(f"Priority: {task.priority.value}")
        
        if task.description:
            console.print(f"Description: {task.description}")
        
        if task.due_date:
            console.print(f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}")
            if task.is_overdue():
                console.print("[red]⚠️  OVERDUE[/red]")
            elif task.is_due_today():
                console.print("[yellow]⚠️  Due Today[/yellow]")
        
        if task.project:
            console.print(f"Project: {task.project}")
        
        if task.category:
            console.print(f"Category: {task.category}")
        
        if task.tags:
            console.print(f"Tags: {', '.join(task.tags)}")
        
        if task.is_recurring:
            console.print(f"Recurring: {task.recurrence_pattern.type if task.recurrence_pattern else 'Yes'}")
        
        console.print(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        if task.completed_at:
            console.print(f"Completed: {task.completed_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Show reminders
        reminders = db.get_reminders_for_task(task.id)
        if reminders:
            console.print(f"\n[bold]Reminders:[/bold]")
            for reminder in reminders:
                console.print(f"  • {reminder.reminder_time.strftime('%Y-%m-%d %H:%M')} ({reminder.status.value})")
        
    except Exception as e:
        console.print(f"[red]Error showing task: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of results")
):
    """Search tasks by title and description."""
    try:
        db = get_database()
        tasks = db.search_tasks(query, limit=limit)
        
        if not tasks:
            console.print(f"[yellow]No tasks found for query: {query}[/yellow]")
            return
        
        console.print(f"[bold]Search results for '{query}':[/bold]")
        table = create_task_table(tasks)
        console.print(table)
        
        console.print(f"\n[dim]Found {len(tasks)} task(s)[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error searching tasks: {e}[/red]")
        raise typer.Exit(1)


# Project commands
@app.command()
def project_list():
    """List all projects."""
    try:
        db = get_database()
        projects = db.list_projects()
        
        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Status", width=12)
        table.add_column("Description", style="dim")
        table.add_column("Created", style="blue", width=12)
        
        for project in projects:
            table.add_row(
                project.name,
                project.status.value,
                project.description or "-",
                project.created_at.strftime("%Y-%m-%d")
            )
        
        console.print(table)
        console.print(f"\n[dim]Showing {len(projects)} project(s)[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error listing projects: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def project_create(
    name: str = typer.Argument(..., help="Project name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Project description"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="Project color (hex code)"),
    icon: Optional[str] = typer.Option(None, "--icon", "-i", help="Project icon/emoji")
):
    """Create a new project."""
    try:
        project = Project(
            name=name,
            description=description,
            color=color,
            icon=icon
        )
        
        db = get_database()
        created_project = db.create_project(project)
        
        console.print(f"[green]✅ Project created: {created_project.name}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error creating project: {e}[/red]")
        raise typer.Exit(1)


# Statistics commands
@app.command()
def stats():
    """Show task statistics."""
    try:
        db = get_database()
        stats = db.get_statistics()
        
        console.print("[bold]Task Statistics[/bold]")
        console.print(f"Total Tasks: {stats['total_tasks']}")
        console.print(f"Completed: {stats['completed_tasks']}")
        console.print(f"Pending: {stats['pending_tasks']}")
        console.print(f"Overdue: {stats['overdue_tasks']}")
        console.print(f"Projects: {stats['total_projects']}")
        console.print(f"Tags: {stats['total_tags']}")
        
        if stats['total_tasks'] > 0:
            completion_rate = (stats['completed_tasks'] / stats['total_tasks']) * 100
            console.print(f"Completion Rate: {completion_rate:.1f}%")
        
    except Exception as e:
        console.print(f"[red]Error getting statistics: {e}[/red]")
        raise typer.Exit(1)


# Configuration commands
@app.command()
def config_show():
    """Show current configuration."""
    try:
        config = get_config()
        
        console.print("[bold]Configuration[/bold]")
        console.print(f"Database: {config.get_database_path()}")
        console.print(f"Backup Directory: {config.get_backup_directory()}")
        console.print(f"Log Directory: {config.get_log_directory()}")
        
        console.print(f"\n[bold]General Settings[/bold]")
        console.print(f"Default Priority: {config.general.default_priority}")
        console.print(f"Default View: {config.general.default_view}")
        console.print(f"Timezone: {config.general.timezone}")
        
        console.print(f"\n[bold]Notifications[/bold]")
        console.print(f"Enabled: {config.notifications.enabled}")
        console.print(f"Desktop: {config.notifications.desktop_notifications}")
        console.print(f"Sound: {config.notifications.sound_notifications}")
        
    except Exception as e:
        console.print(f"[red]Error showing configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from cli_task_manager import __version__
    console.print(f"Talkdo v{__version__}")
    console.print("Talk your to-dos - Natural language task management")


# Advanced Export/Import Commands
@app.command()
def export(
    output_path: str = typer.Argument(..., help="Output file path"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, csv, markdown, todo, ical)"),
    include_completed: bool = typer.Option(True, "--include-completed/--no-completed", help="Include completed tasks")
):
    """Export tasks to various formats."""
    try:
        exporter = get_exporter()
        output_file = Path(output_path)
        
        if format == "json":
            exporter.export_json(output_file, include_completed)
        elif format == "csv":
            exporter.export_csv(output_file, include_completed)
        elif format == "markdown":
            exporter.export_markdown(output_file, include_completed)
        elif format == "todo":
            exporter.export_todo_txt(output_file, include_completed)
        elif format == "ical":
            exporter.export_ical(output_file, include_completed)
        else:
            console.print(f"[red]Unsupported format: {format}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]✅ Exported to {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def import_data(
    input_path: str = typer.Argument(..., help="Input file path"),
    format: str = typer.Option("json", "--format", "-f", help="Import format (json, csv, todo)")
):
    """Import tasks from various formats."""
    try:
        importer = get_importer()
        input_file = Path(input_path)
        
        if not input_file.exists():
            console.print(f"[red]File not found: {input_file}[/red]")
            raise typer.Exit(1)
        
        if format == "json":
            stats = importer.import_json(input_file)
        elif format == "csv":
            stats = importer.import_csv(input_file)
        elif format == "todo":
            stats = importer.import_todo_txt(input_file)
        else:
            console.print(f"[red]Unsupported format: {format}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]✅ Import completed![/green]")
        console.print(f"Tasks: {stats['tasks_imported']}")
        console.print(f"Projects: {stats['projects_imported']}")
        console.print(f"Tags: {stats['tags_imported']}")
        if stats['errors'] > 0:
            console.print(f"[yellow]Errors: {stats['errors']}[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Import failed: {e}[/red]")
        raise typer.Exit(1)


# Analytics Commands
@app.command()
def analytics(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed analytics")
):
    """Show productivity analytics."""
    try:
        analytics = get_analytics()
        insights = analytics.get_productivity_insights(days)
        
        console.print(f"[bold]📊 Productivity Analytics ({days} days)[/bold]")
        
        # Overview
        overview = insights['overview']
        console.print(f"\n[bold]Overview[/bold]")
        console.print(f"Total Tasks: {overview['total_tasks']}")
        console.print(f"Completed: {overview['completed_tasks']} ({overview['completion_rate']:.1f}%)")
        console.print(f"Pending: {overview['pending_tasks']}")
        console.print(f"Active: {overview['active_tasks']}")
        
        # Productivity metrics
        productivity = insights['productivity']
        console.print(f"\n[bold]Productivity[/bold]")
        console.print(f"Score: {productivity['productivity_score']}/100")
        console.print(f"Avg Completion Time: {productivity['average_completion_time_hours']:.1f}h")
        console.print(f"Tasks/Day: {productivity['tasks_completed_per_day']:.1f}")
        
        if detailed:
            # Work patterns
            patterns = insights['patterns']
            console.print(f"\n[bold]Work Patterns[/bold]")
            console.print(f"Most Productive Day: {patterns['most_productive_day']}")
            console.print(f"Most Productive Hour: {patterns['most_productive_hour']}")
            console.print(f"Weekend Activity: {patterns['weekend_activity']} tasks")
            
            # Recommendations
            recommendations = insights['recommendations']
            if recommendations:
                console.print(f"\n[bold]Recommendations[/bold]")
                for rec in recommendations:
                    console.print(f"• {rec}")
        
    except Exception as e:
        console.print(f"[red]Analytics failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def weekly_report():
    """Generate weekly productivity report."""
    try:
        analytics = get_analytics()
        report = analytics.get_weekly_report()
        
        console.print(f"[bold]📈 Weekly Report[/bold]")
        console.print(f"Week: {report['week_start']} to {report['week_end']}")
        console.print(f"Created: {report['total_created']} tasks")
        console.print(f"Completed: {report['total_completed']} tasks")
        console.print(f"Completion Rate: {report['completion_rate']:.1f}%")
        console.print(f"Most Productive Day: {report['most_productive_day']}")
        console.print(f"Tasks Remaining: {report['tasks_remaining']}")
        
    except Exception as e:
        console.print(f"[red]Weekly report failed: {e}[/red]")
        raise typer.Exit(1)


# Theme Commands
@app.command()
def theme_list():
    """List available themes."""
    try:
        theme_manager = get_theme_manager()
        themes = theme_manager.list_themes()
        
        console.print("[bold]Available Themes[/bold]")
        for theme in themes:
            console.print(f"• {theme['name']} ({theme['type']}) - {theme['description']}")
        
    except Exception as e:
        console.print(f"[red]Theme listing failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def theme_set(
    theme_name: str = typer.Argument(..., help="Theme name to set")
):
    """Set the current theme."""
    try:
        theme_manager = get_theme_manager()
        theme_type = ThemeType(theme_name)
        theme_manager.set_theme(theme_type)
        
        console.print(f"[green]✅ Theme set to {theme_name}[/green]")
        
    except Exception as e:
        console.print(f"[red]Theme setting failed: {e}[/red]")
        raise typer.Exit(1)


# Security Commands
@app.command()
def security_status():
    """Show security status."""
    try:
        security = get_security_manager()
        status = security.check_security_status()
        
        console.print("[bold]🔒 Security Status[/bold]")
        console.print(f"Encryption: {'✅ Enabled' if status['encryption_enabled'] else '❌ Disabled'}")
        console.print(f"Secure Mode: {'✅ Enabled' if status['secure_mode'] else '❌ Disabled'}")
        console.print(f"Database Encrypted: {'✅ Yes' if status['database_encrypted'] else '❌ No'}")
        console.print(f"Audit Logging: {'✅ Enabled' if status['audit_logging'] else '❌ Disabled'}")
        
    except Exception as e:
        console.print(f"[red]Security status failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def security_enable_encryption(
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Master password")
):
    """Enable database encryption."""
    try:
        security = get_security_manager()
        if security.enable_encryption(password):
            console.print("[green]✅ Encryption enabled successfully[/green]")
        else:
            console.print("[red]❌ Encryption setup failed[/red]")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Encryption setup failed: {e}[/red]")
        raise typer.Exit(1)


# Mobile Commands
@app.command()
def mobile_qr(
    output_path: str = typer.Option("mobile_qr.png", "--output", "-o", help="Output QR code file")
):
    """Generate QR code for mobile app connection."""
    try:
        mobile = get_mobile_companion()
        qr_path = Path(output_path)
        
        if mobile.generate_mobile_qr(qr_path):
            console.print(f"[green]✅ QR code generated: {qr_path}[/green]")
        else:
            console.print("[red]❌ QR code generation failed[/red]")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Mobile QR generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def mobile_export(
    output_path: str = typer.Argument(..., help="Output file path")
):
    """Export data for mobile app."""
    try:
        mobile = get_mobile_companion()
        output_file = Path(output_path)
        
        if mobile.create_mobile_backup(output_file):
            console.print(f"[green]✅ Mobile export created: {output_file}[/green]")
        else:
            console.print("[red]❌ Mobile export failed[/red]")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Mobile export failed: {e}[/red]")
        raise typer.Exit(1)


# Sync Commands
@app.command()
def sync_status():
    """Show sync status."""
    try:
        sync = get_sync_manager()
        status = sync.get_sync_status()
        
        console.print("[bold]🔄 Sync Status[/bold]")
        console.print(f"Last Sync: {status['last_sync'] or 'Never'}")
        console.print(f"Device: {status['device_info']['hostname']} ({status['device_info']['platform']})")
        console.print(f"Conflict Resolution: {status['conflict_resolution']}")
        
    except Exception as e:
        console.print(f"[red]Sync status failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def sync_export(
    output_path: str = typer.Argument(..., help="Output sync file path")
):
    """Export data for synchronization."""
    try:
        sync = get_sync_manager()
        output_file = Path(output_path)
        
        sync_data = sync.export_for_sync()
        with open(output_file, 'w') as f:
            json.dump(sync_data, f, indent=2)
        
        console.print(f"[green]✅ Sync data exported: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Sync export failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
