"""
Background daemon for task reminders and notifications.

This module implements the background daemon service that monitors
due dates, sends notifications, and handles automated tasks.
"""

import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import psutil
from plyer import notification

from cli_task_manager.core.config import Config
from cli_task_manager.core.database import DatabaseManager
from cli_task_manager.models.reminder import Reminder, ReminderStatus
from cli_task_manager.models.task import Task, TaskStatus


class TaskDaemon:
    """Background daemon for task management."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the daemon."""
        self.config = Config.load(config_path)
        self.db = DatabaseManager(self.config.get_database_path())
        self.running = False
        self.check_interval = 60  # Check every minute
        
        # Setup logging
        self.setup_logging()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Setup logging for the daemon."""
        log_dir = self.config.get_log_directory()
        log_file = log_dir / "daemon.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Task daemon initialized")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def is_daemon_running(self) -> bool:
        """Check if daemon is already running."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'task-daemon' in ' '.join(proc.info['cmdline']):
                    if proc.info['pid'] != os.getpid():
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def start(self):
        """Start the daemon."""
        if self.is_daemon_running():
            print("Daemon is already running")
            return
        
        self.logger.info("Starting task daemon...")
        self.running = True
        
        try:
            while self.running:
                self.check_reminders()
                self.check_overdue_tasks()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Daemon interrupted by user")
        except Exception as e:
            self.logger.error(f"Daemon error: {e}")
        finally:
            self.logger.info("Task daemon stopped")
    
    def stop(self):
        """Stop the daemon."""
        self.logger.info("Stopping task daemon...")
        self.running = False
    
    def status(self) -> dict:
        """Get daemon status."""
        return {
            "running": self.running,
            "pid": os.getpid(),
            "check_interval": self.check_interval,
            "last_check": datetime.now().isoformat()
        }
    
    def check_reminders(self):
        """Check for due reminders and send notifications."""
        try:
            due_reminders = self.db.get_due_reminders()
            
            for reminder in due_reminders:
                if reminder.can_send():
                    self.send_notification(reminder)
                    reminder.mark_sent()
                    self.db.update_reminder(reminder)
                    
        except Exception as e:
            self.logger.error(f"Error checking reminders: {e}")
    
    def check_overdue_tasks(self):
        """Check for overdue tasks and send notifications."""
        try:
            overdue_tasks = self.db.get_overdue_tasks()
            
            for task in overdue_tasks:
                if self.should_notify_overdue(task):
                    self.send_overdue_notification(task)
                    
        except Exception as e:
            self.logger.error(f"Error checking overdue tasks: {e}")
    
    def should_notify_overdue(self, task: Task) -> bool:
        """Check if we should notify about overdue task."""
        # Only notify once per day for overdue tasks
        last_notified = task.metadata.get('last_overdue_notification')
        if last_notified:
            last_date = datetime.fromisoformat(last_notified)
            if last_date.date() == datetime.now().date():
                return False
        
        return True
    
    def send_notification(self, reminder: Reminder):
        """Send a notification for a reminder."""
        try:
            task = self.db.get_task(reminder.task_id)
            if not task:
                return
            
            title = reminder.get_display_title()
            message = reminder.get_display_message()
            
            if self.config.notifications.desktop_notifications:
                notification.notify(
                    title=title,
                    message=f"{task.title}\n{message}",
                    timeout=10
                )
            
            self.logger.info(f"Sent reminder notification: {task.title}")
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
    
    def send_overdue_notification(self, task: Task):
        """Send notification for overdue task."""
        try:
            if self.config.notifications.desktop_notifications:
                notification.notify(
                    title="Overdue Task",
                    message=f"Task '{task.title}' is overdue",
                    timeout=10
                )
            
            # Update metadata to prevent spam
            task.metadata['last_overdue_notification'] = datetime.now().isoformat()
            self.db.update_task(task)
            
            self.logger.info(f"Sent overdue notification: {task.title}")
            
        except Exception as e:
            self.logger.error(f"Error sending overdue notification: {e}")


def main():
    """Main entry point for the daemon."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="CLI Task Manager Daemon")
    parser.add_argument("command", choices=["start", "stop", "status", "restart"], 
                       help="Daemon command")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--foreground", action="store_true", 
                       help="Run in foreground (don't daemonize)")
    
    args = parser.parse_args()
    
    daemon = TaskDaemon(args.config)
    
    if args.command == "start":
        if daemon.is_daemon_running():
            print("Daemon is already running")
            sys.exit(1)
        
        if args.foreground:
            daemon.start()
        else:
            # TODO: Implement proper daemonization
            print("Background daemonization not yet implemented")
            print("Use --foreground flag for now")
            sys.exit(1)
    
    elif args.command == "stop":
        if not daemon.is_daemon_running():
            print("Daemon is not running")
            sys.exit(1)
        
        # TODO: Implement proper daemon stopping
        print("Daemon stop not yet implemented")
        sys.exit(1)
    
    elif args.command == "status":
        status = daemon.status()
        print(f"Daemon Status: {'Running' if status['running'] else 'Stopped'}")
        print(f"PID: {status['pid']}")
        print(f"Check Interval: {status['check_interval']}s")
        print(f"Last Check: {status['last_check']}")
    
    elif args.command == "restart":
        print("Daemon restart not yet implemented")
        sys.exit(1)


if __name__ == "__main__":
    main()
