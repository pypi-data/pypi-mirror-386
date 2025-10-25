"""
Tests for the data models.

This module contains unit tests for all Pydantic models.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from cli_task_manager.models.task import Task, TaskPriority, TaskStatus, RecurrencePattern
from cli_task_manager.models.reminder import Reminder, ReminderType, ReminderStatus
from cli_task_manager.models.dependency import Dependency, DependencyType, DependencyStatus
from cli_task_manager.models.project import Project, ProjectStatus
from cli_task_manager.models.tag import Tag


class TestTask:
    """Test the Task model."""
    
    def test_create_task(self):
        """Test creating a basic task."""
        task = Task(
            title="Test task",
            description="A test task",
            priority=TaskPriority.HIGH
        )
        
        assert task.title == "Test task"
        assert task.description == "A test task"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.tags == []
        assert task.is_recurring == False
    
    def test_task_validation(self):
        """Test task validation rules."""
        # Empty title should fail
        with pytest.raises(ValueError):
            Task(title="")
        
        # Title too long should fail
        with pytest.raises(ValueError):
            Task(title="x" * 501)
    
    def test_task_completion(self):
        """Test task completion."""
        task = Task(title="Test task")
        assert task.status == TaskStatus.PENDING
        assert task.completed_at is None
        
        task.complete()
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
    
    def test_task_overdue(self):
        """Test overdue task detection."""
        # Past due date
        past_date = datetime.now() - timedelta(days=1)
        task = Task(title="Overdue task", due_date=past_date)
        assert task.is_overdue() == True
        
        # Future due date
        future_date = datetime.now() + timedelta(days=1)
        task = Task(title="Future task", due_date=future_date)
        assert task.is_overdue() == False
        
        # Completed task should not be overdue
        task.complete()
        assert task.is_overdue() == False
    
    def test_task_due_today(self):
        """Test due today detection."""
        today = datetime.now().date()
        task = Task(title="Today task", due_date=datetime.combine(today, datetime.min.time()))
        assert task.is_due_today() == True
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        task = Task(title="Tomorrow task", due_date=datetime.combine(tomorrow, datetime.min.time()))
        assert task.is_due_today() == False


class TestReminder:
    """Test the Reminder model."""
    
    def test_create_reminder(self):
        """Test creating a reminder."""
        task_id = uuid4()
        reminder_time = datetime.now() + timedelta(hours=1)
        
        reminder = Reminder(
            task_id=task_id,
            reminder_time=reminder_time,
            reminder_type=ReminderType.ABSOLUTE
        )
        
        assert reminder.task_id == task_id
        assert reminder.reminder_time == reminder_time
        assert reminder.reminder_type == ReminderType.ABSOLUTE
        assert reminder.status == ReminderStatus.PENDING
    
    def test_reminder_due(self):
        """Test reminder due detection."""
        # Past reminder
        past_time = datetime.now() - timedelta(minutes=1)
        reminder = Reminder(
            task_id=uuid4(),
            reminder_time=past_time,
            reminder_type=ReminderType.ABSOLUTE
        )
        assert reminder.is_due() == True
        
        # Future reminder
        future_time = datetime.now() + timedelta(minutes=1)
        reminder = Reminder(
            task_id=uuid4(),
            reminder_time=future_time,
            reminder_type=ReminderType.ABSOLUTE
        )
        assert reminder.is_due() == False
    
    def test_reminder_snooze(self):
        """Test reminder snoozing."""
        reminder = Reminder(
            task_id=uuid4(),
            reminder_time=datetime.now(),
            reminder_type=ReminderType.ABSOLUTE
        )
        
        reminder.snooze(15)  # Snooze for 15 minutes
        assert reminder.status == ReminderStatus.SNOOZED
        assert reminder.snoozed_until is not None


class TestDependency:
    """Test the Dependency model."""
    
    def test_create_dependency(self):
        """Test creating a dependency."""
        predecessor_id = uuid4()
        successor_id = uuid4()
        
        dependency = Dependency(
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            dependency_type=DependencyType.FINISH_TO_START
        )
        
        assert dependency.predecessor_id == predecessor_id
        assert dependency.successor_id == successor_id
        assert dependency.dependency_type == DependencyType.FINISH_TO_START
        assert dependency.status == DependencyStatus.ACTIVE
    
    def test_dependency_validation(self):
        """Test dependency validation."""
        task_id = uuid4()
        
        # Self-dependency should fail
        with pytest.raises(ValueError):
            Dependency(
                predecessor_id=task_id,
                successor_id=task_id,
                dependency_type=DependencyType.FINISH_TO_START
            )
    
    def test_dependency_satisfaction(self):
        """Test dependency satisfaction."""
        dependency = Dependency(
            predecessor_id=uuid4(),
            successor_id=uuid4(),
            dependency_type=DependencyType.FINISH_TO_START
        )
        
        # Should be satisfied when predecessor is completed
        assert dependency.is_satisfied("completed") == True
        assert dependency.is_satisfied("pending") == False
        assert dependency.is_satisfied("in_progress") == False


class TestProject:
    """Test the Project model."""
    
    def test_create_project(self):
        """Test creating a project."""
        project = Project(
            name="Test Project",
            description="A test project",
            color="#FF0000",
            icon="🚀"
        )
        
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.color == "#FF0000"
        assert project.icon == "🚀"
        assert project.status == ProjectStatus.ACTIVE
    
    def test_project_archive(self):
        """Test project archiving."""
        project = Project(name="Test Project")
        assert project.is_active() == True
        
        project.archive()
        assert project.is_archived() == True
        assert project.status == ProjectStatus.ARCHIVED


class TestTag:
    """Test the Tag model."""
    
    def test_create_tag(self):
        """Test creating a tag."""
        tag = Tag(
            name="work",
            description="Work-related tasks",
            color="#0000FF",
            icon="💼"
        )
        
        assert tag.name == "work"
        assert tag.description == "Work-related tasks"
        assert tag.color == "#0000FF"
        assert tag.icon == "💼"
        assert tag.usage_count == 0
    
    def test_tag_usage_tracking(self):
        """Test tag usage tracking."""
        tag = Tag(name="test")
        assert tag.usage_count == 0
        
        tag.increment_usage()
        assert tag.usage_count == 1
        
        tag.decrement_usage()
        assert tag.usage_count == 0
    
    def test_tag_hierarchy(self):
        """Test tag hierarchy."""
        parent_tag = Tag(name="work")
        child_tag = Tag(name="meetings", parent_tag="work")
        
        assert child_tag.is_child_of("work") == True
        assert child_tag.is_child_of("personal") == False
        assert child_tag.get_full_name() == "work/meetings"


class TestRecurrencePattern:
    """Test the RecurrencePattern model."""
    
    def test_daily_pattern(self):
        """Test daily recurrence pattern."""
        pattern = RecurrencePattern(
            type="daily",
            interval=1,
            skip_weekends=False
        )
        
        assert pattern.type == "daily"
        assert pattern.interval == 1
        assert pattern.skip_weekends == False
    
    def test_weekly_pattern(self):
        """Test weekly recurrence pattern."""
        pattern = RecurrencePattern(
            type="weekly",
            interval=1,
            days_of_week=[0, 2, 4],  # Monday, Wednesday, Friday
            skip_weekends=False
        )
        
        assert pattern.type == "weekly"
        assert pattern.days_of_week == [0, 2, 4]
    
    def test_monthly_pattern(self):
        """Test monthly recurrence pattern."""
        pattern = RecurrencePattern(
            type="monthly",
            interval=1,
            day_of_month=15,
            skip_weekends=False
        )
        
        assert pattern.type == "monthly"
        assert pattern.day_of_month == 15
    
    def test_pattern_validation(self):
        """Test pattern validation."""
        # Invalid day of week
        with pytest.raises(ValueError):
            RecurrencePattern(
                type="weekly",
                days_of_week=[7]  # Invalid day
            )
        
        # Invalid day of month
        with pytest.raises(ValueError):
            RecurrencePattern(
                type="monthly",
                day_of_month=32  # Invalid day
            )
