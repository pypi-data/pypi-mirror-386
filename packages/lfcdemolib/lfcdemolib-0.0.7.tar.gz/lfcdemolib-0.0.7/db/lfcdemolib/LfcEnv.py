"""
LfcEnv.py - Lakeflow Connect Environment and User Information

This module handles environment setup and user information retrieval for LFC components.
It provides consistent user identification across all LFC modules.

Key Features:
- User information retrieval from multiple sources
- Consistent firstname_lastname formatting
- Environment variable handling
- Databricks workspace integration
- Fallback mechanisms for non-Databricks environments
"""

import os
import re
import getpass
from typing import Optional

try:
    from databricks.sdk import WorkspaceClient
except ImportError:
    WorkspaceClient = None


class LfcEnv:
    """Manages environment and user information for LFC components"""
    
    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        """Initialize LfcEnv with optional WorkspaceClient
        
        Args:
            workspace_client: Optional WorkspaceClient instance for Databricks integration
        """
        self.workspace_client = workspace_client
        self._user_email = None
        self._username = None
        self._firstname_lastname = None
        
    def get_user_email(self) -> Optional[str]:
        """Get user email from Databricks or environment
        
        Returns:
            str: User email address or None if not available
        """
        if self._user_email is not None:
            return self._user_email
            
        # Try to get from Databricks WorkspaceClient
        if self.workspace_client:
            try:
                self._user_email = self.workspace_client.current_user.me().user_name
                return self._user_email
            except Exception:
                pass
        
        # Try environment variables
        env_vars = ['DATABRICKS_USERNAME', 'USER_EMAIL', 'DATABRICKS_USER_EMAIL']
        for var in env_vars:
            if var in os.environ:
                self._user_email = os.environ[var]
                return self._user_email
        
        return None
    
    def get_username(self) -> str:
        """Get username from various sources
        
        Returns:
            str: Username (system user as fallback)
        """
        if self._username is not None:
            return self._username
            
        # Try to get email first and extract username
        email = self.get_user_email()
        if email and '@' in email:
            self._username = email.split('@')[0]
            return self._username
        
        # Try system username
        try:
            self._username = getpass.getuser()
            return self._username
        except Exception:
            pass
        
        # Default fallback
        self._username = "user"
        return self._username
    
    def get_firstname_lastname(self) -> str:
        """Get firstname_lastname format for naming conventions
        
        This method follows the same logic as DbxRest._setup_user_info()
        to ensure consistency across LFC components.
        
        Returns:
            str: Username in firstname_lastname format
        """
        if self._firstname_lastname is not None:
            return self._firstname_lastname
            
        # Get email or username
        email = self.get_user_email()
        if email:
            # Extract the part before @ if it's an email
            if '@' in email:
                email_text_array = email.split("@")
                username_part = email_text_array[0]
            else:
                username_part = email
        else:
            username_part = self.get_username()
        
        # Apply the same transformation as DbxRest
        # Replace dots, dashes, and @ symbols with underscores
        self._firstname_lastname = re.sub("[-.@]", "_", username_part).lower()
        
        return self._firstname_lastname
    
    def get_scope_name(self) -> str:
        """Get secret scope name for Databricks secrets
        
        Returns:
            str: Scope name in firstname_lastname format
        """
        return self.get_firstname_lastname()
    
    def get_connection_prefix(self) -> str:
        """Get connection name prefix for Databricks connections
        
        Returns:
            str: Connection prefix in firstname_lastname format
        """
        return self.get_firstname_lastname()
    
    def refresh_user_info(self) -> None:
        """Refresh cached user information
        
        Call this method to force re-retrieval of user information
        from Databricks or environment sources.
        """
        self._user_email = None
        self._username = None
        self._firstname_lastname = None
    
    def get_env_info(self) -> dict:
        """Get comprehensive environment information
        
        Returns:
            dict: Dictionary containing all environment information
        """
        return {
            'user_email': self.get_user_email(),
            'username': self.get_username(),
            'firstname_lastname': self.get_firstname_lastname(),
            'scope_name': self.get_scope_name(),
            'connection_prefix': self.get_connection_prefix(),
            'has_workspace_client': self.workspace_client is not None,
            'databricks_sdk_available': WorkspaceClient is not None
        }
    
    @classmethod
    def create_from_workspace_client(cls, workspace_client: Optional[WorkspaceClient] = None) -> 'LfcEnv':
        """Create LfcEnv instance from WorkspaceClient
        
        Args:
            workspace_client: Optional WorkspaceClient instance
            
        Returns:
            LfcEnv: Configured LfcEnv instance
        """
        return cls(workspace_client=workspace_client)
    
    @classmethod
    def create_default(cls) -> 'LfcEnv':
        """Create LfcEnv instance with default configuration
        
        Returns:
            LfcEnv: LfcEnv instance with no WorkspaceClient
        """
        return cls(workspace_client=None)


# Global instance for convenience
_default_lfc_env = None


def get_default_lfc_env() -> LfcEnv:
    """Get the default LfcEnv instance
    
    Returns:
        LfcEnv: Default LfcEnv instance
    """
    global _default_lfc_env
    if _default_lfc_env is None:
        _default_lfc_env = LfcEnv.create_default()
    return _default_lfc_env


def set_default_workspace_client(workspace_client: WorkspaceClient) -> None:
    """Set the WorkspaceClient for the default LfcEnv instance
    
    Args:
        workspace_client: WorkspaceClient instance to use
    """
    global _default_lfc_env
    _default_lfc_env = LfcEnv.create_from_workspace_client(workspace_client)


def get_firstname_lastname() -> str:
    """Convenience function to get firstname_lastname
    
    Returns:
        str: Username in firstname_lastname format
    """
    return get_default_lfc_env().get_firstname_lastname()


def get_scope_name() -> str:
    """Convenience function to get scope name
    
    Returns:
        str: Secret scope name
    """
    return get_default_lfc_env().get_scope_name()


def get_connection_prefix() -> str:
    """Convenience function to get connection prefix
    
    Returns:
        str: Connection name prefix
    """
    return get_default_lfc_env().get_connection_prefix()





