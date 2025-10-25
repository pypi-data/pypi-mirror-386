"""
LfcToken.py - Lakeflow Connect Databricks Token Management

This module provides automatic token management with scheduled renewal for Databricks API access.
It ensures tokens are refreshed before expiration and provides thread-safe access to current tokens.

Key Features:
- Automatic token creation and renewal
- APScheduler integration for background renewal
- Thread-safe token access
- Configurable expiration times (default: 1 hour)
- Automatic cleanup on shutdown
- Token renewal 10 minutes before expiration
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

try:
    from databricks.sdk import WorkspaceClient
    databricks_sdk_available = True
except ImportError:
    WorkspaceClient = None
    databricks_sdk_available = False

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.date import DateTrigger
except ImportError:
    BackgroundScheduler = None
    DateTrigger = None

from .LfcEnv import LfcEnv

# Setup logging
logger = logging.getLogger(__name__)


class LfcToken:
    """Manages Databricks API tokens with automatic renewal"""
    
    def __init__(self, 
                 workspace_client: Optional[WorkspaceClient] = None,
                 scheduler: Optional[BackgroundScheduler] = None,
                 lfc_env: Optional[LfcEnv] = None,
                 token_lifetime_hours: int = 1,
                 renewal_minutes_before_expiry: int = 10,
                 token_comment_prefix: str = "lfcddemo"):
        """Initialize LfcToken with automatic renewal
        
        Args:
            workspace_client: Databricks WorkspaceClient instance
            scheduler: APScheduler BackgroundScheduler instance
            lfc_env: LfcEnv instance for user information
            token_lifetime_hours: Token lifetime in hours (default: 1)
            renewal_minutes_before_expiry: Minutes before expiry to renew (default: 10)
            token_comment_prefix: Prefix for token comments (default: "lfcddemo")
        """
        self.workspace_client = workspace_client
        self.scheduler = scheduler
        self.lfc_env = lfc_env or LfcEnv(workspace_client)
        self.token_lifetime_hours = token_lifetime_hours
        self.renewal_minutes_before_expiry = renewal_minutes_before_expiry
        self.token_comment_prefix = token_comment_prefix
        
        # Thread-safe token storage
        self._token_lock = threading.RLock()
        self._current_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_comment: Optional[str] = None
        self._renewal_job_id: Optional[str] = None
        
        # Track if we own the scheduler
        self._owns_scheduler = False
        
        # Initialize scheduler if needed
        if self.scheduler is None and BackgroundScheduler is not None:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            self._owns_scheduler = True
            logger.info("Created and started internal APScheduler")
        
        # Validate dependencies
        if not self._validate_dependencies():
            logger.warning("LfcToken initialized with missing dependencies")
            return
        
        # Create initial token
        self._create_initial_token()
        
        logger.info(f"LfcToken initialized with {token_lifetime_hours}h lifetime, "
                   f"renewal {renewal_minutes_before_expiry}min before expiry")
    
    def _validate_dependencies(self) -> bool:
        """Validate required dependencies are available"""
        if not databricks_sdk_available:
            logger.error("Databricks SDK not available")
            return False
        
        if not self.workspace_client:
            logger.error("No WorkspaceClient provided")
            return False
        
        if BackgroundScheduler is None:
            logger.warning("APScheduler not available - automatic renewal disabled")
            return False
        
        if not self.scheduler:
            logger.warning("No scheduler provided - automatic renewal disabled")
            return False
        
        return True
    
    def _create_initial_token(self):
        """Create the initial token and schedule renewal"""
        try:
            with self._token_lock:
                self._create_new_token()
                self._schedule_renewal()
                logger.info("Initial token created and renewal scheduled")
        except Exception as e:
            logger.error(f"Failed to create initial token: {e}")
    
    def _create_new_token(self):
        """Create a new token (must be called with lock held)"""
        if not self.workspace_client:
            raise ValueError("No WorkspaceClient available")
        
        # Calculate token lifetime in seconds
        lifetime_seconds = self.token_lifetime_hours * 3600
        
        # Create token comment with timestamp and user info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        user_info = self.lfc_env.get_firstname_lastname()
        self._token_comment = f"{self.token_comment_prefix}-{user_info}-{timestamp}"
        
        # Create the token
        logger.info(f"Creating new token with {lifetime_seconds}s lifetime")
        new_token = self.workspace_client.tokens.create(
            comment=self._token_comment,
            lifetime_seconds=lifetime_seconds
        )
        
        # Store token details
        self._current_token = new_token.token_value
        self._token_expires_at = datetime.now() + timedelta(seconds=lifetime_seconds)
        
        logger.info(f"New token created, expires at: {self._token_expires_at}")
    
    def _schedule_renewal(self):
        """Schedule token renewal (must be called with lock held)"""
        if not self.scheduler or not self._token_expires_at:
            return
        
        # Cancel existing renewal job if any
        if self._renewal_job_id:
            try:
                self.scheduler.remove_job(self._renewal_job_id)
                logger.debug(f"Cancelled previous renewal job: {self._renewal_job_id}")
            except Exception as e:
                logger.warning(f"Could not cancel previous renewal job: {e}")
        
        # Calculate renewal time (X minutes before expiry)
        renewal_time = self._token_expires_at - timedelta(minutes=self.renewal_minutes_before_expiry)
        
        # Only schedule if renewal time is in the future
        if renewal_time > datetime.now():
            self._renewal_job_id = f"token_renewal_{id(self)}_{int(time.time())}"
            
            self.scheduler.add_job(
                func=self._renew_token,
                trigger=DateTrigger(run_date=renewal_time),
                id=self._renewal_job_id,
                name=f"LfcToken renewal for {self._token_comment}",
                max_instances=1,
                coalesce=True
            )
            
            logger.info(f"Scheduled token renewal at: {renewal_time} (job: {self._renewal_job_id})")
        else:
            logger.warning("Token expires too soon to schedule renewal")
    
    def _renew_token(self):
        """Renew the token (called by scheduler)"""
        logger.info("Starting automatic token renewal")
        
        try:
            with self._token_lock:
                old_token = self._current_token
                old_expires = self._token_expires_at
                
                # Create new token
                self._create_new_token()
                
                # Schedule next renewal
                self._schedule_renewal()
                
                logger.info(f"Token renewed successfully. Old token expires: {old_expires}, "
                           f"New token expires: {self._token_expires_at}")
                
        except Exception as e:
            logger.error(f"Failed to renew token: {e}")
            # Try to schedule another renewal attempt in 1 minute
            if self.scheduler:
                retry_time = datetime.now() + timedelta(minutes=1)
                retry_job_id = f"token_renewal_retry_{id(self)}_{int(time.time())}"
                
                self.scheduler.add_job(
                    func=self._renew_token,
                    trigger=DateTrigger(run_date=retry_time),
                    id=retry_job_id,
                    name=f"LfcToken renewal retry for {self._token_comment}",
                    max_instances=1,
                    coalesce=True
                )
                
                logger.info(f"Scheduled token renewal retry at: {retry_time}")
    
    def get_access_token(self) -> Optional[str]:
        """Get the current access token (thread-safe)
        
        Returns:
            str: Current valid access token, or None if not available
        """
        with self._token_lock:
            if self._current_token is None:
                logger.warning("No token available")
                return None
            
            # Check if token is still valid (with 1 minute buffer)
            if self._token_expires_at:
                buffer_time = datetime.now() + timedelta(minutes=1)
                if buffer_time >= self._token_expires_at:
                    logger.warning("Token is expired or expiring soon")
                    return None
            
            return self._current_token
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get information about the current token (thread-safe)
        
        Returns:
            dict: Token information including expiry time and validity
        """
        with self._token_lock:
            now = datetime.now()
            
            info = {
                'has_token': self._current_token is not None,
                'token_comment': self._token_comment,
                'expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None,
                'is_valid': False,
                'seconds_until_expiry': None,
                'renewal_job_id': self._renewal_job_id,
                'scheduler_running': self.scheduler.running if self.scheduler else False
            }
            
            if self._current_token and self._token_expires_at:
                seconds_left = (self._token_expires_at - now).total_seconds()
                info['seconds_until_expiry'] = max(0, int(seconds_left))
                info['is_valid'] = seconds_left > 60  # Valid if more than 1 minute left
            
            return info
    
    def force_renewal(self) -> bool:
        """Force immediate token renewal (thread-safe)
        
        Returns:
            bool: True if renewal successful, False otherwise
        """
        logger.info("Forcing immediate token renewal")
        
        try:
            with self._token_lock:
                old_expires = self._token_expires_at
                self._create_new_token()
                self._schedule_renewal()
                
                logger.info(f"Forced renewal successful. Old expires: {old_expires}, "
                           f"New expires: {self._token_expires_at}")
                return True
                
        except Exception as e:
            logger.error(f"Forced renewal failed: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid (thread-safe)
        
        Returns:
            bool: True if token is valid and not expiring soon
        """
        with self._token_lock:
            if not self._current_token or not self._token_expires_at:
                return False
            
            # Consider token invalid if it expires within 1 minute
            buffer_time = datetime.now() + timedelta(minutes=1)
            return buffer_time < self._token_expires_at
    
    def shutdown(self):
        """Shutdown token manager and cleanup resources"""
        logger.info("Shutting down LfcToken")
        
        with self._token_lock:
            # Cancel renewal job
            if self._renewal_job_id and self.scheduler:
                try:
                    self.scheduler.remove_job(self._renewal_job_id)
                    logger.info(f"Cancelled renewal job: {self._renewal_job_id}")
                except Exception as e:
                    logger.warning(f"Could not cancel renewal job: {e}")
            
            # Shutdown scheduler if we own it
            if self._owns_scheduler and self.scheduler:
                try:
                    self.scheduler.shutdown(wait=False)
                    logger.info("Shutdown internal scheduler")
                except Exception as e:
                    logger.warning(f"Could not shutdown scheduler: {e}")
            
            # Clear token (Databricks will auto-delete expired tokens)
            self._current_token = None
            self._token_expires_at = None
            self._token_comment = None
            self._renewal_job_id = None
        
        logger.info("LfcToken shutdown completed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self.shutdown()
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.shutdown()
        except Exception:
            pass  # Ignore errors during destruction


# Convenience functions
def create_token_manager(workspace_client: Optional[WorkspaceClient] = None,
                        scheduler: Optional[BackgroundScheduler] = None,
                        **kwargs) -> LfcToken:
    """Create a new LfcToken manager
    
    Args:
        workspace_client: Databricks WorkspaceClient instance
        scheduler: APScheduler BackgroundScheduler instance
        **kwargs: Additional arguments for LfcToken constructor
        
    Returns:
        LfcToken: Configured token manager
    """
    return LfcToken(workspace_client=workspace_client, scheduler=scheduler, **kwargs)


def get_token_with_auto_renewal(workspace_client: Optional[WorkspaceClient] = None,
                               token_lifetime_hours: int = 1) -> Optional[str]:
    """Get a token with automatic renewal (creates internal scheduler)
    
    Args:
        workspace_client: Databricks WorkspaceClient instance
        token_lifetime_hours: Token lifetime in hours
        
    Returns:
        str: Access token, or None if creation failed
    """
    try:
        token_manager = LfcToken(
            workspace_client=workspace_client,
            token_lifetime_hours=token_lifetime_hours
        )
        return token_manager.get_access_token()
    except Exception as e:
        logger.error(f"Failed to create token with auto-renewal: {e}")
        return None
