"""
Tests for the natural language parser.

This module contains unit tests for the natural language parser.
"""

import pytest
from datetime import datetime, timedelta

from cli_task_manager.core.parser import NaturalLanguageParser, ParseResult
from cli_task_manager.models.task import TaskPriority
from cli_task_manager.models.reminder import ReminderType


class TestNaturalLanguageParser:
    """Test the NaturalLanguageParser class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.parser = NaturalLanguageParser()
    
    def test_simple_task(self):
        """Test parsing a simple task."""
        result = self.parser.parse("buy milk")
        
        assert result.title == "buy milk"
        assert result.priority == TaskPriority.MEDIUM
        assert result.tags == []
        assert result.project is None
        assert result.due_date is None
        assert result.is_recurring == False
        assert result.confidence > 0.5
    
    def test_task_with_priority(self):
        """Test parsing task with priority."""
        result = self.parser.parse("urgent: fix production bug")
        
        assert result.title == "fix production bug"
        assert result.priority == TaskPriority.URGENT
        assert result.confidence > 0.5
    
    def test_task_with_tags(self):
        """Test parsing task with tags."""
        result = self.parser.parse("buy groceries with tags shopping, personal")
        
        assert result.title == "buy groceries"
        assert "shopping" in result.tags
        assert "personal" in result.tags
    
    def test_task_with_hashtags(self):
        """Test parsing task with hashtags."""
        result = self.parser.parse("review PRs #work #urgent")
        
        assert result.title == "review PRs"
        assert "work" in result.tags
        assert "urgent" in result.tags
    
    def test_task_with_project(self):
        """Test parsing task with project."""
        result = self.parser.parse("deploy feature in project mobile-app")
        
        assert result.title == "deploy feature"
        assert result.project == "mobile-app"
    
    def test_task_with_due_date(self):
        """Test parsing task with due date."""
        result = self.parser.parse("call dentist tomorrow at 3pm")
        
        assert result.title == "call dentist"
        assert result.due_date is not None
        # Due date should be tomorrow at 3pm
        tomorrow = datetime.now().date() + timedelta(days=1)
        assert result.due_date.date() == tomorrow
    
    def test_task_with_relative_date(self):
        """Test parsing task with relative date."""
        result = self.parser.parse("submit report in 2 days")
        
        assert result.title == "submit report"
        assert result.due_date is not None
        # Due date should be 2 days from now
        expected_date = datetime.now() + timedelta(days=2)
        assert abs((result.due_date - expected_date).total_seconds()) < 3600  # Within 1 hour
    
    def test_recurring_task_daily(self):
        """Test parsing daily recurring task."""
        result = self.parser.parse("water plants every day")
        
        assert result.title == "water plants"
        assert result.is_recurring == True
        assert result.recurrence_pattern is not None
        assert result.recurrence_pattern.type == "daily"
    
    def test_recurring_task_weekly(self):
        """Test parsing weekly recurring task."""
        result = self.parser.parse("team meeting every Monday at 10am")
        
        assert result.title == "team meeting"
        assert result.is_recurring == True
        assert result.recurrence_pattern is not None
        assert result.recurrence_pattern.type == "weekly"
        assert result.recurrence_pattern.days_of_week == [0]  # Monday
    
    def test_recurring_task_weekdays(self):
        """Test parsing weekday recurring task."""
        result = self.parser.parse("daily standup every weekday")
        
        assert result.title == "daily standup"
        assert result.is_recurring == True
        assert result.recurrence_pattern is not None
        assert result.recurrence_pattern.type == "weekly"
        assert result.recurrence_pattern.days_of_week == [0, 1, 2, 3, 4]  # Monday to Friday
        assert result.recurrence_pattern.skip_weekends == True
    
    def test_recurring_task_monthly(self):
        """Test parsing monthly recurring task."""
        result = self.parser.parse("monthly report on the 15th")
        
        assert result.title == "monthly report"
        assert result.is_recurring == True
        assert result.recurrence_pattern is not None
        assert result.recurrence_pattern.type == "monthly"
        assert result.recurrence_pattern.day_of_month == 15
    
    def test_task_with_reminder(self):
        """Test parsing task with reminder."""
        result = self.parser.parse("call mom tomorrow at 3pm remind me at 2pm")
        
        assert result.title == "call mom"
        assert result.due_date is not None
        assert len(result.reminders) > 0
        assert result.reminders[0].reminder_type == ReminderType.ABSOLUTE
    
    def test_complex_task(self):
        """Test parsing a complex task with multiple elements."""
        result = self.parser.parse(
            "urgent: deploy feature X by Friday 5pm with tags deployment, urgent in project mobile-app"
        )
        
        assert result.title == "deploy feature X"
        assert result.priority == TaskPriority.URGENT
        assert "deployment" in result.tags
        assert "urgent" in result.tags
        assert result.project == "mobile-app"
        assert result.due_date is not None
        # Should be Friday at 5pm
        assert result.due_date.weekday() == 4  # Friday
        assert result.due_date.hour == 17  # 5pm
    
    def test_clean_title_extraction(self):
        """Test that title is properly cleaned of metadata."""
        result = self.parser.parse("urgent: call mom tomorrow at 3pm with tags personal #family")
        
        # Title should be clean without priority, date, or tags
        assert result.title == "call mom"
        assert "urgent" not in result.title
        assert "tomorrow" not in result.title
        assert "personal" not in result.title
        assert "family" not in result.title
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # High confidence task
        result = self.parser.parse("buy milk tomorrow at 3pm urgent")
        assert result.confidence > 0.7
        
        # Low confidence task (ambiguous)
        result = self.parser.parse("thing")
        assert result.confidence < 0.5
    
    def test_error_handling(self):
        """Test error handling for invalid input."""
        result = self.parser.parse("")
        assert len(result.errors) > 0
        assert result.confidence == 0.0
    
    def test_warning_generation(self):
        """Test warning generation for edge cases."""
        # Past due date
        result = self.parser.parse("call mom yesterday")
        assert len(result.warnings) > 0
        assert "past" in " ".join(result.warnings).lower()
    
    def test_suggestion_generation(self):
        """Test suggestion generation for low confidence."""
        result = self.parser.parse("thing")
        suggestions = self.parser.suggest_corrections(result)
        assert len(suggestions) > 0
    
    def test_action_word_removal(self):
        """Test removal of action words."""
        test_cases = [
            "remind me to buy milk",
            "remember to call mom",
            "don't forget to water plants",
            "add task to review code",
            "create task to deploy feature"
        ]
        
        for input_text in test_cases:
            result = self.parser.parse(input_text)
            # Title should not contain action words
            assert "remind" not in result.title.lower()
            assert "remember" not in result.title.lower()
            assert "don't forget" not in result.title.lower()
            assert "add task" not in result.title.lower()
            assert "create task" not in result.title.lower()
    
    def test_time_parsing(self):
        """Test various time formats."""
        time_cases = [
            ("meeting at 3pm", "meeting"),
            ("call at 14:30", "call"),
            ("lunch at noon", "lunch"),
            ("meeting at 3:30pm", "meeting"),
        ]
        
        for input_text, expected_title in time_cases:
            result = self.parser.parse(input_text)
            assert result.title == expected_title
            assert result.due_date is not None
    
    def test_date_parsing(self):
        """Test various date formats."""
        date_cases = [
            ("call tomorrow", "call"),
            ("meeting next Tuesday", "meeting"),
            ("submit in 3 days", "submit"),
            ("due by Friday", "due"),
        ]
        
        for input_text, expected_title in date_cases:
            result = self.parser.parse(input_text)
            assert result.title == expected_title
            assert result.due_date is not None
    
    def test_priority_detection(self):
        """Test priority detection patterns."""
        priority_cases = [
            ("urgent: fix bug", TaskPriority.URGENT),
            ("critical: deploy", TaskPriority.URGENT),
            ("asap: call boss", TaskPriority.URGENT),
            ("high priority: review", TaskPriority.HIGH),
            ("important: meeting", TaskPriority.HIGH),
            ("low priority: cleanup", TaskPriority.LOW),
            ("someday: organize", TaskPriority.LOW),
            ("regular task", TaskPriority.MEDIUM),
        ]
        
        for input_text, expected_priority in priority_cases:
            result = self.parser.parse(input_text)
            assert result.priority == expected_priority
    
    def test_tag_extraction(self):
        """Test tag extraction patterns."""
        tag_cases = [
            ("task with tags work, urgent", ["work", "urgent"]),
            ("task tags: personal, shopping", ["personal", "shopping"]),
            ("task #work #urgent", ["work", "urgent"]),
            ("task @meetings @work", ["meetings", "work"]),
        ]
        
        for input_text, expected_tags in tag_cases:
            result = self.parser.parse(input_text)
            for tag in expected_tags:
                assert tag in result.tags
    
    def test_project_extraction(self):
        """Test project extraction patterns."""
        project_cases = [
            ("task in project website", "website"),
            ("task for project mobile-app", "mobile-app"),
            ("task project: backend", "backend"),
            ("task proj: frontend", "frontend"),
        ]
        
        for input_text, expected_project in project_cases:
            result = self.parser.parse(input_text)
            assert result.project == expected_project
