"""
Database management for the CLI Task Manager.

This module handles all database operations using SQLAlchemy with SQLite,
including CRUD operations, filtering, searching, and data persistence.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, 
    create_engine, func, or_, and_, desc, asc
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm.exc import NoResultFound

from cli_task_manager.models.task import Task, TaskPriority, TaskStatus, RecurrencePattern
from cli_task_manager.models.reminder import Reminder, ReminderType, ReminderStatus
from cli_task_manager.models.dependency import Dependency, DependencyType, DependencyStatus
from cli_task_manager.models.project import Project, ProjectStatus
from cli_task_manager.models.tag import Tag

# Configure logging
logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()


class TaskModel(Base):
    """SQLAlchemy model for tasks."""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    due_date = Column(DateTime)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    project = Column(String(100))
    category = Column(String(100))
    is_recurring = Column(Boolean, default=False)
    parent_task_id = Column(String)
    next_occurrence = Column(DateTime)
    occurrence_count = Column(Integer, default=0)
    task_metadata = Column(Text)  # JSON string
    
    # Relationships
    reminders = relationship("ReminderModel", back_populates="task", cascade="all, delete-orphan")
    dependencies_as_predecessor = relationship("DependencyModel", foreign_keys="DependencyModel.predecessor_id", back_populates="predecessor")
    dependencies_as_successor = relationship("DependencyModel", foreign_keys="DependencyModel.successor_id", back_populates="successor")


class ReminderModel(Base):
    """SQLAlchemy model for reminders."""
    __tablename__ = "reminders"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    reminder_type = Column(String(20), nullable=False)
    advance_minutes = Column(Integer)
    status = Column(String(20), nullable=False)
    sent_at = Column(DateTime)
    snoozed_until = Column(DateTime)
    message = Column(String(500))
    title = Column(String(200))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    task = relationship("TaskModel", back_populates="reminders")


class DependencyModel(Base):
    """SQLAlchemy model for dependencies."""
    __tablename__ = "dependencies"
    
    id = Column(String, primary_key=True)
    predecessor_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    successor_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    dependency_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    satisfied_at = Column(DateTime)
    
    # Relationships
    predecessor = relationship("TaskModel", foreign_keys=[predecessor_id], back_populates="dependencies_as_predecessor")
    successor = relationship("TaskModel", foreign_keys=[successor_id], back_populates="dependencies_as_successor")


class ProjectModel(Base):
    """SQLAlchemy model for projects."""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    status = Column(String(20), nullable=False)
    color = Column(String(7))
    icon = Column(String(10))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    archived_at = Column(DateTime)
    completed_at = Column(DateTime)
    task_metadata = Column(Text)  # JSON string


class TagModel(Base):
    """SQLAlchemy model for tags."""
    __tablename__ = "tags"
    
    id = Column(String, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(200))
    color = Column(String(7))
    icon = Column(String(10))
    parent_tag = Column(String(50))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime)
    task_metadata = Column(Text)  # JSON string


class DatabaseManager:
    """Database manager for all CRUD operations."""
    
    def __init__(self, database_path: Path):
        """Initialize database manager."""
        self.database_path = database_path
        self.engine = create_engine(f"sqlite:///{database_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        logger.info(f"Database initialized at {database_path}")
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    # Task operations
    def create_task(self, task: Task) -> Task:
        """Create a new task."""
        with self.get_session() as session:
            task_model = self._task_to_model(task)
            session.add(task_model)
            session.commit()
            session.refresh(task_model)
            return self._model_to_task(task_model)
    
    def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get a task by ID."""
        with self.get_session() as session:
            try:
                task_model = session.query(TaskModel).filter(TaskModel.id == str(task_id)).one()
                return self._model_to_task(task_model)
            except NoResultFound:
                return None
    
    def update_task(self, task: Task) -> Task:
        """Update an existing task."""
        with self.get_session() as session:
            task_model = session.query(TaskModel).filter(TaskModel.id == str(task.id)).one()
            self._update_task_model(task_model, task)
            session.commit()
            session.refresh(task_model)
            return self._model_to_task(task_model)
    
    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task by ID."""
        with self.get_session() as session:
            task_model = session.query(TaskModel).filter(TaskModel.id == str(task_id)).first()
            if task_model:
                session.delete(task_model)
                session.commit()
                return True
            return False
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        project: Optional[str] = None,
        tag: Optional[str] = None,
        due_today: bool = False,
        due_this_week: bool = False,
        overdue: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[Task]:
        """List tasks with optional filtering."""
        with self.get_session() as session:
            query = session.query(TaskModel)
            
            # Apply filters
            if status:
                query = query.filter(TaskModel.status == status.value)
            
            if priority:
                query = query.filter(TaskModel.priority == priority.value)
            
            if project:
                query = query.filter(TaskModel.project == project)
            
            if tag:
                # This would need a join with a task_tags table in a real implementation
                # For now, we'll search in the tags field (assuming it's stored as JSON)
                query = query.filter(TaskModel.metadata.contains(tag))
            
            if due_today:
                today = datetime.utcnow().date()
                query = query.filter(
                    func.date(TaskModel.due_date) == today
                )
            
            if due_this_week:
                now = datetime.utcnow()
                week_start = now - timedelta(days=now.weekday())
                week_end = week_start + timedelta(days=6)
                query = query.filter(
                    TaskModel.due_date >= week_start,
                    TaskModel.due_date <= week_end
                )
            
            if overdue:
                query = query.filter(
                    TaskModel.due_date < datetime.utcnow(),
                    TaskModel.status != TaskStatus.COMPLETED.value
                )
            
            # Apply ordering
            order_column = getattr(TaskModel, order_by, TaskModel.created_at)
            if order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
            
            # Apply pagination
            if limit:
                query = query.limit(limit)
            query = query.offset(offset)
            
            task_models = query.all()
            return [self._model_to_task(model) for model in task_models]
    
    def search_tasks(self, query_text: str, limit: Optional[int] = None) -> List[Task]:
        """Search tasks by title and description."""
        with self.get_session() as session:
            query = session.query(TaskModel).filter(
                or_(
                    TaskModel.title.contains(query_text),
                    TaskModel.description.contains(query_text)
                )
            )
            
            if limit:
                query = query.limit(limit)
            
            task_models = query.all()
            return [self._model_to_task(model) for model in task_models]
    
    def get_task_count(self, status: Optional[TaskStatus] = None) -> int:
        """Get total number of tasks."""
        with self.get_session() as session:
            query = session.query(TaskModel)
            if status:
                query = query.filter(TaskModel.status == status.value)
            return query.count()
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks."""
        with self.get_session() as session:
            task_models = session.query(TaskModel).filter(
                TaskModel.due_date < datetime.utcnow(),
                TaskModel.status != TaskStatus.COMPLETED.value
            ).all()
            return [self._model_to_task(model) for model in task_models]
    
    def get_tasks_due_today(self) -> List[Task]:
        """Get tasks due today."""
        with self.get_session() as session:
            today = datetime.utcnow().date()
            task_models = session.query(TaskModel).filter(
                func.date(TaskModel.due_date) == today
            ).all()
            return [self._model_to_task(model) for model in task_models]
    
    # Reminder operations
    def create_reminder(self, reminder: Reminder) -> Reminder:
        """Create a new reminder."""
        with self.get_session() as session:
            reminder_model = self._reminder_to_model(reminder)
            session.add(reminder_model)
            session.commit()
            session.refresh(reminder_model)
            return self._model_to_reminder(reminder_model)
    
    def get_reminders_for_task(self, task_id: UUID) -> List[Reminder]:
        """Get all reminders for a task."""
        with self.get_session() as session:
            reminder_models = session.query(ReminderModel).filter(
                ReminderModel.task_id == str(task_id)
            ).all()
            return [self._model_to_reminder(model) for model in reminder_models]
    
    def get_due_reminders(self) -> List[Reminder]:
        """Get all due reminders."""
        with self.get_session() as session:
            now = datetime.utcnow()
            reminder_models = session.query(ReminderModel).filter(
                ReminderModel.reminder_time <= now,
                ReminderModel.status == ReminderStatus.PENDING.value
            ).all()
            return [self._model_to_reminder(model) for model in reminder_models]
    
    def update_reminder(self, reminder: Reminder) -> Reminder:
        """Update an existing reminder."""
        with self.get_session() as session:
            reminder_model = session.query(ReminderModel).filter(
                ReminderModel.id == str(reminder.id)
            ).one()
            self._update_reminder_model(reminder_model, reminder)
            session.commit()
            session.refresh(reminder_model)
            return self._model_to_reminder(reminder_model)
    
    def delete_reminder(self, reminder_id: UUID) -> bool:
        """Delete a reminder by ID."""
        with self.get_session() as session:
            reminder_model = session.query(ReminderModel).filter(
                ReminderModel.id == str(reminder_id)
            ).first()
            if reminder_model:
                session.delete(reminder_model)
                session.commit()
                return True
            return False
    
    # Project operations
    def create_project(self, project: Project) -> Project:
        """Create a new project."""
        with self.get_session() as session:
            project_model = self._project_to_model(project)
            session.add(project_model)
            session.commit()
            session.refresh(project_model)
            return self._model_to_project(project_model)
    
    def get_project(self, project_name: str) -> Optional[Project]:
        """Get a project by name."""
        with self.get_session() as session:
            try:
                project_model = session.query(ProjectModel).filter(
                    ProjectModel.name == project_name
                ).one()
                return self._model_to_project(project_model)
            except NoResultFound:
                return None
    
    def list_projects(self, status: Optional[ProjectStatus] = None) -> List[Project]:
        """List all projects."""
        with self.get_session() as session:
            query = session.query(ProjectModel)
            if status:
                query = query.filter(ProjectModel.status == status.value)
            project_models = query.all()
            return [self._model_to_project(model) for model in project_models]
    
    def update_project(self, project: Project) -> Project:
        """Update an existing project."""
        with self.get_session() as session:
            project_model = session.query(ProjectModel).filter(
                ProjectModel.id == str(project.id)
            ).one()
            self._update_project_model(project_model, project)
            session.commit()
            session.refresh(project_model)
            return self._model_to_project(project_model)
    
    def delete_project(self, project_name: str) -> bool:
        """Delete a project by name."""
        with self.get_session() as session:
            project_model = session.query(ProjectModel).filter(
                ProjectModel.name == project_name
            ).first()
            if project_model:
                session.delete(project_model)
                session.commit()
                return True
            return False
    
    # Tag operations
    def create_tag(self, tag: Tag) -> Tag:
        """Create a new tag."""
        with self.get_session() as session:
            tag_model = self._tag_to_model(tag)
            session.add(tag_model)
            session.commit()
            session.refresh(tag_model)
            return self._model_to_tag(tag_model)
    
    def get_tag(self, tag_name: str) -> Optional[Tag]:
        """Get a tag by name."""
        with self.get_session() as session:
            try:
                tag_model = session.query(TagModel).filter(
                    TagModel.name == tag_name
                ).one()
                return self._model_to_tag(tag_model)
            except NoResultFound:
                return None
    
    def list_tags(self) -> List[Tag]:
        """List all tags."""
        with self.get_session() as session:
            tag_models = session.query(TagModel).all()
            return [self._model_to_tag(model) for model in tag_models]
    
    def update_tag(self, tag: Tag) -> Tag:
        """Update an existing tag."""
        with self.get_session() as session:
            tag_model = session.query(TagModel).filter(
                TagModel.id == str(tag.id)
            ).one()
            self._update_tag_model(tag_model, tag)
            session.commit()
            session.refresh(tag_model)
            return self._model_to_tag(tag_model)
    
    def delete_tag(self, tag_name: str) -> bool:
        """Delete a tag by name."""
        with self.get_session() as session:
            tag_model = session.query(TagModel).filter(
                TagModel.name == tag_name
            ).first()
            if tag_model:
                session.delete(tag_model)
                session.commit()
                return True
            return False
    
    # Dependency operations
    def create_dependency(self, dependency: Dependency) -> Dependency:
        """Create a new dependency."""
        with self.get_session() as session:
            dependency_model = self._dependency_to_model(dependency)
            session.add(dependency_model)
            session.commit()
            session.refresh(dependency_model)
            return self._model_to_dependency(dependency_model)
    
    def get_dependencies_for_task(self, task_id: UUID) -> List[Dependency]:
        """Get all dependencies for a task."""
        with self.get_session() as session:
            dependency_models = session.query(DependencyModel).filter(
                or_(
                    DependencyModel.predecessor_id == str(task_id),
                    DependencyModel.successor_id == str(task_id)
                )
            ).all()
            return [self._model_to_dependency(model) for model in dependency_models]
    
    def delete_dependency(self, dependency_id: UUID) -> bool:
        """Delete a dependency by ID."""
        with self.get_session() as session:
            dependency_model = session.query(DependencyModel).filter(
                DependencyModel.id == str(dependency_id)
            ).first()
            if dependency_model:
                session.delete(dependency_model)
                session.commit()
                return True
            return False
    
    # Statistics
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_session() as session:
            stats = {}
            
            # Task statistics
            stats['total_tasks'] = session.query(TaskModel).count()
            stats['completed_tasks'] = session.query(TaskModel).filter(
                TaskModel.status == TaskStatus.COMPLETED.value
            ).count()
            stats['pending_tasks'] = session.query(TaskModel).filter(
                TaskModel.status == TaskStatus.PENDING.value
            ).count()
            stats['overdue_tasks'] = session.query(TaskModel).filter(
                TaskModel.due_date < datetime.utcnow(),
                TaskModel.status != TaskStatus.COMPLETED.value
            ).count()
            
            # Project statistics
            stats['total_projects'] = session.query(ProjectModel).count()
            stats['active_projects'] = session.query(ProjectModel).filter(
                ProjectModel.status == ProjectStatus.ACTIVE.value
            ).count()
            
            # Tag statistics
            stats['total_tags'] = session.query(TagModel).count()
            
            return stats
    
    # Helper methods for model conversion
    def _task_to_model(self, task: Task) -> TaskModel:
        """Convert Task to TaskModel."""
        import json
        
        return TaskModel(
            id=str(task.id),
            title=task.title,
            description=task.description,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            due_date=task.due_date,
            priority=task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
            status=task.status.value if hasattr(task.status, 'value') else str(task.status),
            project=task.project,
            category=task.category,
            is_recurring=task.is_recurring,
            parent_task_id=str(task.parent_task_id) if task.parent_task_id else None,
            next_occurrence=task.next_occurrence,
            occurrence_count=task.occurrence_count,
            task_metadata=json.dumps(task.metadata) if task.metadata else None
        )
    
    def _model_to_task(self, model: TaskModel) -> Task:
        """Convert TaskModel to Task."""
        import json
        
        return Task(
            id=UUID(model.id),
            title=model.title,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
            due_date=model.due_date,
            priority=TaskPriority(model.priority),
            status=TaskStatus(model.status),
            project=model.project,
            category=model.category,
            is_recurring=model.is_recurring,
            parent_task_id=UUID(model.parent_task_id) if model.parent_task_id else None,
            next_occurrence=model.next_occurrence,
            occurrence_count=model.occurrence_count,
            metadata=json.loads(model.task_metadata) if model.task_metadata else {}
        )
    
    def _update_task_model(self, model: TaskModel, task: Task) -> None:
        """Update TaskModel with Task data."""
        import json
        
        model.title = task.title
        model.description = task.description
        model.updated_at = task.updated_at
        model.completed_at = task.completed_at
        model.due_date = task.due_date
        model.priority = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
        model.status = task.status.value if hasattr(task.status, 'value') else str(task.status)
        model.project = task.project
        model.category = task.category
        model.is_recurring = task.is_recurring
        model.parent_task_id = str(task.parent_task_id) if task.parent_task_id else None
        model.next_occurrence = task.next_occurrence
        model.occurrence_count = task.occurrence_count
        model.task_metadata = json.dumps(task.metadata) if task.metadata else None
    
    def _reminder_to_model(self, reminder: Reminder) -> ReminderModel:
        """Convert Reminder to ReminderModel."""
        return ReminderModel(
            id=str(reminder.id),
            task_id=str(reminder.task_id),
            reminder_time=reminder.reminder_time,
            reminder_type=reminder.reminder_type.value,
            advance_minutes=reminder.advance_minutes,
            status=reminder.status.value,
            sent_at=reminder.sent_at,
            snoozed_until=reminder.snoozed_until,
            message=reminder.message,
            title=reminder.title,
            created_at=reminder.created_at,
            updated_at=reminder.updated_at
        )
    
    def _model_to_reminder(self, model: ReminderModel) -> Reminder:
        """Convert ReminderModel to Reminder."""
        return Reminder(
            id=UUID(model.id),
            task_id=UUID(model.task_id),
            reminder_time=model.reminder_time,
            reminder_type=ReminderType(model.reminder_type),
            advance_minutes=model.advance_minutes,
            status=ReminderStatus(model.status),
            sent_at=model.sent_at,
            snoozed_until=model.snoozed_until,
            message=model.message,
            title=model.title,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _update_reminder_model(self, model: ReminderModel, reminder: Reminder) -> None:
        """Update ReminderModel with Reminder data."""
        model.reminder_time = reminder.reminder_time
        model.reminder_type = reminder.reminder_type.value
        model.advance_minutes = reminder.advance_minutes
        model.status = reminder.status.value
        model.sent_at = reminder.sent_at
        model.snoozed_until = reminder.snoozed_until
        model.message = reminder.message
        model.title = reminder.title
        model.updated_at = reminder.updated_at
    
    def _project_to_model(self, project: Project) -> ProjectModel:
        """Convert Project to ProjectModel."""
        import json
        
        return ProjectModel(
            id=str(project.id),
            name=project.name,
            description=project.description,
            status=project.status.value,
            color=project.color,
            icon=project.icon,
            created_at=project.created_at,
            updated_at=project.updated_at,
            archived_at=project.archived_at,
            completed_at=project.completed_at,
            metadata=json.dumps(project.metadata) if project.metadata else None
        )
    
    def _model_to_project(self, model: ProjectModel) -> Project:
        """Convert ProjectModel to Project."""
        import json
        
        return Project(
            id=UUID(model.id),
            name=model.name,
            description=model.description,
            status=ProjectStatus(model.status),
            color=model.color,
            icon=model.icon,
            created_at=model.created_at,
            updated_at=model.updated_at,
            archived_at=model.archived_at,
            completed_at=model.completed_at,
            metadata=json.loads(model.task_metadata) if model.task_metadata else {}
        )
    
    def _update_project_model(self, model: ProjectModel, project: Project) -> None:
        """Update ProjectModel with Project data."""
        import json
        
        model.name = project.name
        model.description = project.description
        model.status = project.status.value
        model.color = project.color
        model.icon = project.icon
        model.updated_at = project.updated_at
        model.archived_at = project.archived_at
        model.completed_at = project.completed_at
        model.metadata = json.dumps(project.metadata) if project.metadata else None
    
    def _tag_to_model(self, tag: Tag) -> TagModel:
        """Convert Tag to TagModel."""
        import json
        
        return TagModel(
            id=str(tag.id),
            name=tag.name,
            description=tag.description,
            color=tag.color,
            icon=tag.icon,
            parent_tag=tag.parent_tag,
            usage_count=tag.usage_count,
            created_at=tag.created_at,
            updated_at=tag.updated_at,
            last_used_at=tag.last_used_at,
            metadata=json.dumps(tag.metadata) if tag.metadata else None
        )
    
    def _model_to_tag(self, model: TagModel) -> Tag:
        """Convert TagModel to Tag."""
        import json
        
        return Tag(
            id=UUID(model.id),
            name=model.name,
            description=model.description,
            color=model.color,
            icon=model.icon,
            parent_tag=model.parent_tag,
            usage_count=model.usage_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_used_at=model.last_used_at,
            metadata=json.loads(model.task_metadata) if model.task_metadata else {}
        )
    
    def _update_tag_model(self, model: TagModel, tag: Tag) -> None:
        """Update TagModel with Tag data."""
        import json
        
        model.name = tag.name
        model.description = tag.description
        model.color = tag.color
        model.icon = tag.icon
        model.parent_tag = tag.parent_tag
        model.usage_count = tag.usage_count
        model.updated_at = tag.updated_at
        model.last_used_at = tag.last_used_at
        model.metadata = json.dumps(tag.metadata) if tag.metadata else None
    
    def _dependency_to_model(self, dependency: Dependency) -> DependencyModel:
        """Convert Dependency to DependencyModel."""
        return DependencyModel(
            id=str(dependency.id),
            predecessor_id=str(dependency.predecessor_id),
            successor_id=str(dependency.successor_id),
            dependency_type=dependency.dependency_type.value,
            status=dependency.status.value,
            created_at=dependency.created_at,
            updated_at=dependency.updated_at,
            satisfied_at=dependency.satisfied_at
        )
    
    def _model_to_dependency(self, model: DependencyModel) -> Dependency:
        """Convert DependencyModel to Dependency."""
        return Dependency(
            id=UUID(model.id),
            predecessor_id=UUID(model.predecessor_id),
            successor_id=UUID(model.successor_id),
            dependency_type=DependencyType(model.dependency_type),
            status=DependencyStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            satisfied_at=model.satisfied_at
        )
