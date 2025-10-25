"""
Natural language parser for task input.

This module provides comprehensive natural language processing capabilities
for parsing task inputs and extracting structured information.
"""

import re
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import dateparser
from dateutil.relativedelta import relativedelta
from croniter import croniter

from cli_task_manager.models.task import Task, TaskPriority, RecurrencePattern
from cli_task_manager.models.reminder import Reminder, ReminderType


class ParseResult:
    """Result of natural language parsing."""
    
    def __init__(self):
        self.title: str = ""
        self.description: Optional[str] = None
        self.due_date: Optional[datetime] = None
        self.priority: TaskPriority = TaskPriority.MEDIUM
        self.tags: List[str] = []
        self.project: Optional[str] = None
        self.category: Optional[str] = None
        self.is_recurring: bool = False
        self.recurrence_pattern: Optional[RecurrencePattern] = None
        self.reminders: List[Reminder] = []
        self.confidence: float = 0.0
        self.raw_input: str = ""
        self.warnings: List[str] = []
        self.errors: List[str] = []


class NaturalLanguageParser:
    """Natural language parser for task inputs."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the parser with configuration."""
        self.config = config or {}
        
        # Priority patterns
        self.priority_patterns = {
            TaskPriority.URGENT: [
                r'\b(urgent|critical|asap|emergency|!!!)\b',
                r'\b(urgent|critical|asap|emergency)\s*:',
                r'!!!\s*'
            ],
            TaskPriority.HIGH: [
                r'\b(high\s*priority|important|!!)\b',
                r'\b(high\s*priority|important)\s*:',
                r'!!\s*'
            ],
            TaskPriority.LOW: [
                r'\b(low\s*priority|when\s*possible|someday|sometime)\b',
                r'\b(low\s*priority|when\s*possible|someday|sometime)\s*:',
                r'!\s*'
            ]
        }
        
        # Tag patterns
        self.tag_patterns = [
            r'with\s+tags?\s+([^,]+(?:,\s*[^,]+)*)',
            r'tags?\s*:\s*([^,]+(?:,\s*[^,]+)*)',
            r'#(\w+(?:/\w+)*)',
            r'@(\w+(?:/\w+)*)'
        ]
        
        # Project patterns
        self.project_patterns = [
            r'in\s+project\s+([a-zA-Z0-9_-]+)',
            r'for\s+project\s+([a-zA-Z0-9_-]+)',
            r'project\s*:\s*([a-zA-Z0-9_-]+)',
            r'proj\s*:\s*([a-zA-Z0-9_-]+)'
        ]
        
        # Recurrence patterns
        self.recurrence_patterns = {
            'daily': [
                r'\b(every\s+day|daily|each\s+day)\b',
                r'\b(every\s+day|daily|each\s+day)\s+at\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)',
            ],
            'weekly': [
                r'\b(every\s+week|weekly|each\s+week)\b',
                r'\b(every\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b',
                r'\b(every\s+(?:mon|tue|wed|thu|fri|sat|sun))\b',
                r'\b(every\s+weekday|every\s+business\s+day)\b',
                r'\b(every\s+weekend)\b',
            ],
            'monthly': [
                r'\b(every\s+month|monthly|each\s+month)\b',
                r'\b(every\s+month\s+on\s+the\s+(\d{1,2}(?:st|nd|rd|th)?))\b',
                r'\b(every\s+(\d{1,2}(?:st|nd|rd|th)?)\s+of\s+the\s+month)\b',
                r'\b(last\s+day\s+of\s+each\s+month)\b',
            ],
            'yearly': [
                r'\b(every\s+year|yearly|each\s+year|annually)\b',
                r'\b(every\s+year\s+on\s+(\w+\s+\d{1,2}))\b',
            ],
            'interval': [
                r'\b(every\s+(\d+)\s+days?)\b',
                r'\b(every\s+(\d+)\s+weeks?)\b',
                r'\b(every\s+(\d+)\s+months?)\b',
                r'\b(every\s+(\d+)\s+years?)\b',
            ]
        }
        
        # Time patterns
        self.time_patterns = [
            r'\b(at\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?))\b',
            r'\b(at\s+(\d{1,2}:\d{2}(?:\s*[ap]m)?))\b',
            r'\b(at\s+noon|at\s+midnight)\b',
            r'\b(morning|afternoon|evening|night)\b',
        ]
        
        # Date patterns
        self.date_patterns = [
            r'\b(tomorrow|today|yesterday)\b',
            r'\b(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b',
            r'\b(next\s+(?:mon|tue|wed|thu|fri|sat|sun))\b',
            r'\b(this\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b',
            r'\b(this\s+(?:mon|tue|wed|thu|fri|sat|sun))\b',
            r'\b(in\s+\d+\s+days?)\b',
            r'\b(in\s+\d+\s+weeks?)\b',
            r'\b(in\s+\d+\s+months?)\b',
            r'\b(in\s+\d+\s+years?)\b',
            r'\b(by\s+(?:friday|monday|tuesday|wednesday|thursday|saturday|sunday))\b',
            r'\b(by\s+(?:fri|mon|tue|wed|thu|sat|sun))\b',
            r'\b(before\s+\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)\b',
            r'\b(due\s+(?:tomorrow|today|next\s+\w+))\b',
        ]
        
        # Action word patterns to remove
        self.action_words = [
            r'\b(remind\s+me\s+to|remember\s+to|don\'t\s+forget\s+to|add\s+task\s+to|create\s+task\s+to)\s*',
            r'\b(add|create|make|set|schedule)\s+(?:a\s+)?(?:task\s+)?(?:to\s+)?',
            r'^(?:please\s+)?(?:can\s+you\s+)?(?:would\s+you\s+)?(?:could\s+you\s+)?',
        ]
    
    def parse(self, input_text: str) -> ParseResult:
        """Parse natural language input into structured task data."""
        result = ParseResult()
        result.raw_input = input_text.strip()
        
        if not result.raw_input:
            result.errors.append("Empty input")
            return result
        
        try:
            # Clean and normalize input
            cleaned_input = self._clean_input(input_text)
            
            # Extract priority
            result.priority = self._extract_priority(cleaned_input)
            
            # Extract tags
            result.tags = self._extract_tags(cleaned_input)
            
            # Extract project
            result.project = self._extract_project(cleaned_input)
            
            # Extract due date and time
            result.due_date = self._extract_due_date(cleaned_input)
            
            # Extract recurrence pattern
            recurrence_info = self._extract_recurrence(cleaned_input)
            if recurrence_info:
                result.is_recurring = True
                result.recurrence_pattern = recurrence_info
            
            # Extract reminders
            result.reminders = self._extract_reminders(cleaned_input, result.due_date)
            
            # Clean title (remove extracted metadata)
            result.title = self._extract_title(cleaned_input)
            
            # Calculate confidence
            result.confidence = self._calculate_confidence(result)
            
            # Validate result
            self._validate_result(result)
            
        except Exception as e:
            result.errors.append(f"Parsing error: {str(e)}")
            result.confidence = 0.0
        
        return result
    
    def _clean_input(self, input_text: str) -> str:
        """Clean and normalize input text."""
        # Remove action words
        cleaned = input_text
        for pattern in self.action_words:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _extract_priority(self, text: str) -> TaskPriority:
        """Extract priority from text."""
        text_lower = text.lower()
        
        for priority, patterns in self.priority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return priority
        
        return TaskPriority.MEDIUM
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract tags from text."""
        tags = []
        
        for pattern in self.tag_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    # Split by comma and clean
                    tag_list = [tag.strip().lower() for tag in match.split(',')]
                    tags.extend(tag_list)
        
        # Remove duplicates and empty tags
        return list(set(tag for tag in tags if tag))
    
    def _extract_project(self, text: str) -> Optional[str]:
        """Extract project from text."""
        for pattern in self.project_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_due_date(self, text: str) -> Optional[datetime]:
        """Extract due date and time from text."""
        # Try dateparser first for complex date parsing
        try:
            parsed_date = dateparser.parse(text, settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': datetime.now()
            })
            if parsed_date:
                return parsed_date
        except Exception:
            pass
        
        # Try specific patterns
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_text = match.group(0)
                try:
                    parsed_date = dateparser.parse(date_text, settings={
                        'PREFER_DATES_FROM': 'future',
                        'RELATIVE_BASE': datetime.now()
                    })
                    if parsed_date:
                        return parsed_date
                except Exception:
                    continue
        
        # Try time patterns
        for pattern in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_text = match.group(0)
                try:
                    parsed_time = dateparser.parse(time_text, settings={
                        'PREFER_DATES_FROM': 'future',
                        'RELATIVE_BASE': datetime.now()
                    })
                    if parsed_time:
                        return parsed_time
                except Exception:
                    continue
        
        return None
    
    def _extract_recurrence(self, text: str) -> Optional[RecurrencePattern]:
        """Extract recurrence pattern from text."""
        text_lower = text.lower()
        
        # Check for daily patterns
        for pattern in self.recurrence_patterns['daily']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return RecurrencePattern(
                    type="daily",
                    interval=1,
                    skip_weekends=False
                )
        
        # Check for weekly patterns
        for pattern in self.recurrence_patterns['weekly']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                if 'weekday' in match.group(0) or 'business day' in match.group(0):
                    return RecurrencePattern(
                        type="weekly",
                        interval=1,
                        days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
                        skip_weekends=True
                    )
                elif 'weekend' in match.group(0):
                    return RecurrencePattern(
                        type="weekly",
                        interval=1,
                        days_of_week=[5, 6],  # Saturday and Sunday
                        skip_weekends=False
                    )
                else:
                    # Extract specific day
                    day_match = re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)', match.group(0), re.IGNORECASE)
                    if day_match:
                        day_name = day_match.group(0).lower()
                        day_map = {
                            'monday': 0, 'mon': 0,
                            'tuesday': 1, 'tue': 1,
                            'wednesday': 2, 'wed': 2,
                            'thursday': 3, 'thu': 3,
                            'friday': 4, 'fri': 4,
                            'saturday': 5, 'sat': 5,
                            'sunday': 6, 'sun': 6
                        }
                        day_num = day_map.get(day_name)
                        if day_num is not None:
                            return RecurrencePattern(
                                type="weekly",
                                interval=1,
                                days_of_week=[day_num],
                                skip_weekends=False
                            )
        
        # Check for monthly patterns
        for pattern in self.recurrence_patterns['monthly']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                if 'last day' in match.group(0):
                    return RecurrencePattern(
                        type="monthly",
                        interval=1,
                        day_of_month=31,  # Will be adjusted to last day of month
                        skip_weekends=False
                    )
                else:
                    # Extract day of month
                    day_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?', match.group(0))
                    if day_match:
                        day = int(day_match.group(1))
                        return RecurrencePattern(
                            type="monthly",
                            interval=1,
                            day_of_month=day,
                            skip_weekends=False
                        )
        
        # Check for yearly patterns
        for pattern in self.recurrence_patterns['yearly']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return RecurrencePattern(
                    type="yearly",
                    interval=1,
                    skip_weekends=False
                )
        
        # Check for interval patterns
        for pattern in self.recurrence_patterns['interval']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                interval_text = match.group(0)
                if 'days' in interval_text:
                    interval_match = re.search(r'(\d+)', interval_text)
                    if interval_match:
                        interval = int(interval_match.group(1))
                        return RecurrencePattern(
                            type="custom",
                            interval=interval,
                            skip_weekends=False
                        )
                elif 'weeks' in interval_text:
                    interval_match = re.search(r'(\d+)', interval_text)
                    if interval_match:
                        interval = int(interval_match.group(1))
                        return RecurrencePattern(
                            type="weekly",
                            interval=interval,
                            skip_weekends=False
                        )
                elif 'months' in interval_text:
                    interval_match = re.search(r'(\d+)', interval_text)
                    if interval_match:
                        interval = int(interval_match.group(1))
                        return RecurrencePattern(
                            type="monthly",
                            interval=interval,
                            skip_weekends=False
                        )
                elif 'years' in interval_text:
                    interval_match = re.search(r'(\d+)', interval_text)
                    if interval_match:
                        interval = int(interval_match.group(1))
                        return RecurrencePattern(
                            type="yearly",
                            interval=interval,
                            skip_weekends=False
                        )
        
        return None
    
    def _extract_reminders(self, text: str, due_date: Optional[datetime]) -> List[Reminder]:
        """Extract reminders from text."""
        reminders = []
        
        # Look for reminder patterns
        reminder_patterns = [
            r'\b(remind\s+me\s+at\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?))\b',
            r'\b(remind\s+me\s+(\d+)\s+minutes?\s+before)\b',
            r'\b(remind\s+me\s+(\d+)\s+hours?\s+before)\b',
            r'\b(remind\s+me\s+(\d+)\s+days?\s+before)\b',
        ]
        
        for pattern in reminder_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if 'at' in match[0]:
                    # Absolute time reminder
                    time_text = match[1]
                    try:
                        reminder_time = dateparser.parse(time_text)
                        if reminder_time:
                            reminders.append(Reminder(
                                task_id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                                reminder_time=reminder_time,
                                reminder_type=ReminderType.ABSOLUTE
                            ))
                    except Exception:
                        continue
                else:
                    # Relative reminder
                    amount = int(match[1])
                    if 'minutes' in match[0]:
                        advance_minutes = amount
                    elif 'hours' in match[0]:
                        advance_minutes = amount * 60
                    elif 'days' in match[0]:
                        advance_minutes = amount * 24 * 60
                    else:
                        continue
                    
                    if due_date:
                        reminder_time = due_date - timedelta(minutes=advance_minutes)
                        reminders.append(Reminder(
                            task_id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                            reminder_time=reminder_time,
                            reminder_type=ReminderType.RELATIVE,
                            advance_minutes=advance_minutes
                        ))
        
        return reminders
    
    def _extract_title(self, text: str) -> str:
        """Extract clean title from text."""
        # Remove all extracted metadata
        cleaned = text
        
        # Remove priority indicators
        for patterns in self.priority_patterns.values():
            for pattern in patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove tag patterns
        for pattern in self.tag_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove project patterns
        for pattern in self.project_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove recurrence patterns
        for patterns in self.recurrence_patterns.values():
            for pattern in patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove date patterns
        for pattern in self.date_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove time patterns
        for pattern in self.time_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove reminder patterns
        reminder_patterns = [
            r'\b(remind\s+me\s+at\s+\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)\b',
            r'\b(remind\s+me\s+\d+\s+(?:minutes?|hours?|days?)\s+before)\b',
        ]
        for pattern in reminder_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'^[,.\s]+|[,.\s]+$', '', cleaned)
        
        return cleaned if cleaned else "Untitled Task"
    
    def _calculate_confidence(self, result: ParseResult) -> float:
        """Calculate parsing confidence score."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for successful extractions
        if result.title and result.title != "Untitled Task":
            confidence += 0.2
        
        if result.due_date:
            confidence += 0.2
        
        if result.tags:
            confidence += 0.1
        
        if result.project:
            confidence += 0.1
        
        if result.is_recurring:
            confidence += 0.1
        
        if result.reminders:
            confidence += 0.1
        
        # Reduce confidence for errors
        confidence -= len(result.errors) * 0.1
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def _validate_result(self, result: ParseResult) -> None:
        """Validate parsing result and add warnings/errors."""
        if not result.title or result.title == "Untitled Task":
            result.warnings.append("No clear task title found")
        
        if result.due_date and result.due_date < datetime.now():
            result.warnings.append("Due date is in the past")
        
        if result.is_recurring and not result.recurrence_pattern:
            result.warnings.append("Recurring task but no pattern found")
        
        if result.reminders and not result.due_date:
            result.warnings.append("Reminders set but no due date")
        
        # Check for potential parsing errors
        if len(result.raw_input) > 500:
            result.warnings.append("Input is very long, some details may be missed")
        
        if result.confidence < 0.3:
            result.errors.append("Low parsing confidence, please check the result")
    
    def suggest_corrections(self, result: ParseResult) -> List[str]:
        """Suggest corrections for parsing result."""
        suggestions = []
        
        if not result.title or result.title == "Untitled Task":
            suggestions.append("Try adding a clear task description")
        
        if result.due_date and result.due_date < datetime.now():
            suggestions.append("Consider using 'tomorrow' or a future date")
        
        if result.is_recurring and not result.recurrence_pattern:
            suggestions.append("Try 'every day', 'every Monday', or 'every week'")
        
        if result.confidence < 0.5:
            suggestions.append("Try rephrasing with simpler language")
        
        return suggestions
