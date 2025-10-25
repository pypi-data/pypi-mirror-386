"""
LfcScheduler - Background Scheduler Manager

This module provides a centralized scheduler for managing
asynchronous tasks in LFC demos.

Key Features:
- Background scheduler using APScheduler
- Automatic scheduler startup and shutdown
- Job management methods

Usage:
    from lfcdemolib import LfcScheduler
    
    # Create scheduler
    scheduler = LfcScheduler()
    
    # Access scheduler for adding jobs
    scheduler.add_job(my_function, 'interval', seconds=60)
"""

import apscheduler.schedulers.background
from typing import Any, Callable


class LfcScheduler:
    """Background scheduler manager for LFC operations
    
    Provides a BackgroundScheduler for managing asynchronous operations.
    
    Attributes:
        scheduler: APScheduler BackgroundScheduler instance
    """
    
    def __init__(self, auto_start: bool = True):
        """Initialize LfcScheduler with background scheduler
        
        Args:
            auto_start: Whether to automatically start the scheduler (default: True)
        """
        print("🔧 Creating LfcScheduler...")
        
        # Create and optionally start scheduler
        self.scheduler: apscheduler.schedulers.background.BackgroundScheduler = (
            apscheduler.schedulers.background.BackgroundScheduler()
        )
        
        if auto_start:
            self.scheduler.start()
            print("  ✅ Created and started scheduler")
        else:
            print("  ✅ Created scheduler (not started)")
    
    def start(self):
        """Start the scheduler if not already running"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("▶️  Scheduler started")
    
    def shutdown(self, wait: bool = True):
        """Shutdown the scheduler
        
        Args:
            wait: Whether to wait for running jobs to finish (default: True)
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            print("⏹️  Scheduler shutdown")
    
    def add_job(self, func: Callable, trigger: str = 'interval', **trigger_args) -> Any:
        """Add a job to the scheduler
        
        Args:
            func: Function to execute
            trigger: Trigger type ('interval', 'cron', 'date')
            **trigger_args: Trigger-specific arguments
            
        Returns:
            Job instance
            
        Example:
            scheduler.add_job(my_func, 'interval', seconds=60, id='my_job')
        """
        return self.scheduler.add_job(func, trigger, **trigger_args)
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler
        
        Args:
            job_id: Job identifier to remove
        """
        self.scheduler.remove_job(job_id)
    
    def get_jobs(self) -> list:
        """Get list of all scheduled jobs
        
        Returns:
            List of Job instances
        """
        return self.scheduler.get_jobs()
    
    def __repr__(self) -> str:
        """String representation of LfcScheduler"""
        running_status = "running" if self.scheduler.running else "stopped"
        job_count = len(self.scheduler.get_jobs())
        
        return (
            f"LfcScheduler(scheduler={running_status}, "
            f"jobs={job_count})"
        )
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
        except:
            pass  # Suppress errors during cleanup

