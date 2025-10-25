"""
Advanced analytics and reporting for the CLI Task Manager.

This module provides comprehensive analytics, insights, and reporting
capabilities for productivity tracking and optimization.
"""

from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics

from cli_task_manager.models.task import Task, TaskPriority, TaskStatus
from cli_task_manager.models.project import Project, ProjectStatus
from cli_task_manager.core.database import DatabaseManager


class ProductivityAnalytics:
    """Advanced analytics for productivity insights."""
    
    def __init__(self, db: DatabaseManager):
        """Initialize analytics with database manager."""
        self.db = db
    
    def get_productivity_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive productivity insights."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all tasks in the period
        all_tasks = self.db.list_tasks()
        period_tasks = [
            task for task in all_tasks
            if task.created_at >= start_date or (task.completed_at and task.completed_at >= start_date)
        ]
        
        insights = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "overview": self._get_overview_stats(period_tasks),
            "productivity": self._get_productivity_metrics(period_tasks),
            "patterns": self._get_work_patterns(period_tasks),
            "recommendations": self._get_recommendations(period_tasks),
            "trends": self._get_trends(all_tasks, days),
            "focus_areas": self._get_focus_areas(period_tasks)
        }
        
        return insights
    
    def _get_overview_stats(self, tasks: List[Task]) -> Dict[str, Any]:
        """Get overview statistics."""
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
        in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "active_tasks": pending_tasks + in_progress_tasks
        }
    
    def _get_productivity_metrics(self, tasks: List[Task]) -> Dict[str, Any]:
        """Get productivity metrics."""
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        
        if not completed_tasks:
            return {
                "average_completion_time": 0,
                "fastest_completion": 0,
                "slowest_completion": 0,
                "productivity_score": 0
            }
        
        # Calculate completion times
        completion_times = []
        for task in completed_tasks:
            if task.completed_at and task.created_at:
                duration = (task.completed_at - task.created_at).total_seconds() / 3600  # hours
                completion_times.append(duration)
        
        # Calculate productivity score (0-100)
        avg_completion = statistics.mean(completion_times) if completion_times else 0
        productivity_score = max(0, 100 - (avg_completion / 24 * 10))  # Penalty for long completion times
        
        return {
            "average_completion_time_hours": round(avg_completion, 2),
            "fastest_completion_hours": round(min(completion_times), 2) if completion_times else 0,
            "slowest_completion_hours": round(max(completion_times), 2) if completion_times else 0,
            "productivity_score": round(productivity_score, 1),
            "tasks_completed_per_day": len(completed_tasks) / 30 if completed_tasks else 0
        }
    
    def _get_work_patterns(self, tasks: List[Task]) -> Dict[str, Any]:
        """Analyze work patterns."""
        # Group by day of week
        day_patterns = defaultdict(int)
        hour_patterns = defaultdict(int)
        priority_patterns = defaultdict(int)
        
        for task in tasks:
            # Day of week patterns
            day_of_week = task.created_at.weekday()
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_patterns[day_names[day_of_week]] += 1
            
            # Hour patterns
            hour = task.created_at.hour
            hour_patterns[hour] += 1
            
            # Priority patterns
            priority_patterns[task.priority.value] += 1
        
        # Find most productive day and hour
        most_productive_day = max(day_patterns.items(), key=lambda x: x[1]) if day_patterns else ("None", 0)
        most_productive_hour = max(hour_patterns.items(), key=lambda x: x[1]) if hour_patterns else (0, 0)
        
        return {
            "day_patterns": dict(day_patterns),
            "hour_patterns": dict(hour_patterns),
            "priority_distribution": dict(priority_patterns),
            "most_productive_day": most_productive_day[0],
            "most_productive_hour": f"{most_productive_hour[0]:02d}:00",
            "weekend_activity": day_patterns.get('Saturday', 0) + day_patterns.get('Sunday', 0)
        }
    
    def _get_recommendations(self, tasks: List[Task]) -> List[str]:
        """Generate productivity recommendations."""
        recommendations = []
        
        # Analyze completion rates
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        total = len(tasks)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        if completion_rate < 50:
            recommendations.append("Consider breaking down large tasks into smaller, manageable chunks")
        elif completion_rate > 80:
            recommendations.append("Great job! You're maintaining high productivity")
        
        # Analyze overdue tasks
        overdue = len([t for t in tasks if t.is_overdue()])
        if overdue > 0:
            recommendations.append(f"You have {overdue} overdue tasks. Consider reprioritizing or delegating")
        
        # Analyze priority distribution
        urgent_tasks = len([t for t in tasks if t.priority == TaskPriority.URGENT])
        if urgent_tasks > total * 0.3:
            recommendations.append("Too many urgent tasks. Consider better planning to reduce urgency")
        
        # Analyze project distribution
        projects = set(t.project for t in tasks if t.project)
        if len(projects) > 5:
            recommendations.append("You're working on many projects. Consider focusing on fewer projects")
        
        return recommendations
    
    def _get_trends(self, all_tasks: List[Task], days: int) -> Dict[str, Any]:
        """Analyze productivity trends."""
        # Group tasks by week
        weekly_stats = defaultdict(lambda: {"created": 0, "completed": 0})
        
        for task in all_tasks:
            week_start = task.created_at - timedelta(days=task.created_at.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            weekly_stats[week_key]["created"] += 1
            
            if task.completed_at:
                week_start = task.completed_at - timedelta(days=task.completed_at.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                weekly_stats[week_key]["completed"] += 1
        
        # Calculate trends
        weeks = sorted(weekly_stats.keys())
        if len(weeks) >= 2:
            recent_weeks = weeks[-2:]
            old_created = weekly_stats[recent_weeks[0]]["created"]
            new_created = weekly_stats[recent_weeks[1]]["created"]
            old_completed = weekly_stats[recent_weeks[0]]["completed"]
            new_completed = weekly_stats[recent_weeks[1]]["completed"]
            
            creation_trend = ((new_created - old_created) / old_created * 100) if old_created > 0 else 0
            completion_trend = ((new_completed - old_completed) / old_completed * 100) if old_completed > 0 else 0
        else:
            creation_trend = 0
            completion_trend = 0
        
        return {
            "weekly_stats": dict(weekly_stats),
            "creation_trend_percent": round(creation_trend, 1),
            "completion_trend_percent": round(completion_trend, 1),
            "trend_direction": "improving" if completion_trend > 0 else "declining"
        }
    
    def _get_focus_areas(self, tasks: List[Task]) -> Dict[str, Any]:
        """Identify focus areas and bottlenecks."""
        # Analyze by project
        project_stats = defaultdict(lambda: {"total": 0, "completed": 0, "overdue": 0})
        for task in tasks:
            project = task.project or "No Project"
            project_stats[project]["total"] += 1
            if task.status == TaskStatus.COMPLETED:
                project_stats[project]["completed"] += 1
            if task.is_overdue():
                project_stats[project]["overdue"] += 1
        
        # Calculate project completion rates
        project_rates = {}
        for project, stats in project_stats.items():
            rate = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            project_rates[project] = {
                "completion_rate": round(rate, 1),
                "total_tasks": stats["total"],
                "overdue_tasks": stats["overdue"]
            }
        
        # Find focus areas
        focus_areas = sorted(project_rates.items(), key=lambda x: x[1]["total_tasks"], reverse=True)[:5]
        bottlenecks = [p for p, stats in project_rates.items() if stats["overdue_tasks"] > 0]
        
        return {
            "project_performance": project_rates,
            "top_focus_areas": focus_areas,
            "bottlenecks": bottlenecks,
            "recommended_focus": focus_areas[0][0] if focus_areas else "No projects"
        }
    
    def get_weekly_report(self) -> Dict[str, Any]:
        """Generate weekly productivity report."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get tasks from the past week
        all_tasks = self.db.list_tasks()
        week_tasks = [
            task for task in all_tasks
            if task.created_at >= start_date or (task.completed_at and task.completed_at >= start_date)
        ]
        
        # Calculate daily productivity
        daily_stats = defaultdict(lambda: {"created": 0, "completed": 0})
        for task in week_tasks:
            day = task.created_at.strftime("%Y-%m-%d")
            daily_stats[day]["created"] += 1
            
            if task.completed_at and task.completed_at >= start_date:
                day = task.completed_at.strftime("%Y-%m-%d")
                daily_stats[day]["completed"] += 1
        
        # Calculate weekly metrics
        total_created = len([t for t in week_tasks if t.created_at >= start_date])
        total_completed = len([t for t in week_tasks if t.status == TaskStatus.COMPLETED and t.completed_at >= start_date])
        
        return {
            "week_start": start_date.strftime("%Y-%m-%d"),
            "week_end": end_date.strftime("%Y-%m-%d"),
            "daily_breakdown": dict(daily_stats),
            "total_created": total_created,
            "total_completed": total_completed,
            "completion_rate": (total_completed / total_created * 100) if total_created > 0 else 0,
            "most_productive_day": max(daily_stats.items(), key=lambda x: x[1]["completed"])[0] if daily_stats else "None",
            "tasks_remaining": len([t for t in week_tasks if t.status != TaskStatus.COMPLETED])
        }
    
    def get_goal_tracking(self, goal_tasks: List[str]) -> Dict[str, Any]:
        """Track progress towards specific goals."""
        all_tasks = self.db.list_tasks()
        goal_progress = {}
        
        for goal in goal_tasks:
            # Find tasks related to this goal
            related_tasks = [
                task for task in all_tasks
                if goal.lower() in task.title.lower() or goal.lower() in (task.description or "").lower()
            ]
            
            if related_tasks:
                completed = len([t for t in related_tasks if t.status == TaskStatus.COMPLETED])
                total = len(related_tasks)
                progress = (completed / total * 100) if total > 0 else 0
                
                goal_progress[goal] = {
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "progress_percent": round(progress, 1),
                    "status": "completed" if progress == 100 else "in_progress" if progress > 0 else "not_started"
                }
            else:
                goal_progress[goal] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "progress_percent": 0,
                    "status": "not_started"
                }
        
        return goal_progress
    
    def get_time_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze time patterns and productivity windows."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        all_tasks = self.db.list_tasks()
        period_tasks = [
            task for task in all_tasks
            if task.created_at >= start_date
        ]
        
        # Analyze by hour of day
        hour_analysis = defaultdict(lambda: {"created": 0, "completed": 0})
        for task in period_tasks:
            hour = task.created_at.hour
            hour_analysis[hour]["created"] += 1
            
            if task.completed_at and task.completed_at >= start_date:
                hour = task.completed_at.hour
                hour_analysis[hour]["completed"] += 1
        
        # Find peak hours
        peak_creation_hour = max(hour_analysis.items(), key=lambda x: x[1]["created"])[0] if hour_analysis else 0
        peak_completion_hour = max(hour_analysis.items(), key=lambda x: x[1]["completed"])[0] if hour_analysis else 0
        
        # Analyze work-life balance
        weekday_tasks = len([t for t in period_tasks if t.created_at.weekday() < 5])
        weekend_tasks = len([t for t in period_tasks if t.created_at.weekday() >= 5])
        
        return {
            "analysis_period_days": days,
            "hourly_patterns": dict(hour_analysis),
            "peak_creation_hour": f"{peak_creation_hour:02d}:00",
            "peak_completion_hour": f"{peak_completion_hour:02d}:00",
            "work_life_balance": {
                "weekday_tasks": weekday_tasks,
                "weekend_tasks": weekend_tasks,
                "weekend_ratio": (weekend_tasks / (weekday_tasks + weekend_tasks) * 100) if (weekday_tasks + weekend_tasks) > 0 else 0
            },
            "recommendations": self._get_time_recommendations(hour_analysis, weekday_tasks, weekend_tasks)
        }
    
    def _get_time_recommendations(self, hour_analysis: Dict, weekday_tasks: int, weekend_tasks: int) -> List[str]:
        """Generate time-based recommendations."""
        recommendations = []
        
        # Analyze peak hours
        if hour_analysis:
            morning_tasks = sum(hour_analysis[h]["created"] for h in range(6, 12))
            afternoon_tasks = sum(hour_analysis[h]["created"] for h in range(12, 18))
            evening_tasks = sum(hour_analysis[h]["created"] for h in range(18, 24))
            
            if morning_tasks > afternoon_tasks and morning_tasks > evening_tasks:
                recommendations.append("You're most productive in the morning. Schedule important tasks then.")
            elif afternoon_tasks > morning_tasks and afternoon_tasks > evening_tasks:
                recommendations.append("You're most productive in the afternoon. Use mornings for planning.")
            elif evening_tasks > morning_tasks and evening_tasks > afternoon_tasks:
                recommendations.append("You're most productive in the evening. Consider flexible scheduling.")
        
        # Work-life balance recommendations
        weekend_ratio = (weekend_tasks / (weekday_tasks + weekend_tasks) * 100) if (weekday_tasks + weekend_tasks) > 0 else 0
        if weekend_ratio > 30:
            recommendations.append("Consider reducing weekend work to maintain work-life balance.")
        elif weekend_ratio < 5:
            recommendations.append("Good work-life balance! You're keeping weekends for rest.")
        
        return recommendations
