#!/usr/bin/env python3
"""
LfcCDCBase.py - Base class for LFC CDC/CT operations

This module provides the base class and common functionality for database replication,
following the same pattern as CloudBase to eliminate code duplication.
"""

import sqlalchemy as sa
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LfcCDCProviderBase(ABC):
    """Base class for database-specific CDC/CT implementations"""
    
    def __init__(self, engine: sa.Engine, dba_engine: sa.Engine, db_type: str, 
                 schema: str = None, secrets_json: Dict[str, Any] = None):
        """Initialize the replication provider
        
        Args:
            engine: SQLAlchemy engine for regular database connection
            dba_engine: SQLAlchemy engine with DBA privileges
            db_type: Database type identifier
            schema: Target schema name
            secrets_json: Database connection secrets
        """
        self.engine = engine
        self.dba_engine = dba_engine
        self.db_type = db_type
        self.schema = schema or self.get_default_schema()
        self.secrets_json = secrets_json
        
        # Common attributes for tracking support and status
        self.cdc_supported = None  # Will be determined by database-specific logic
        self.cdc_failure_reason = None
        self.db_cdc_enabled = None  # Cache for database-level CDC status
        self.db_ct_enabled = None   # Cache for database-level CT status
    
    @abstractmethod
    def get_default_schema(self) -> str:
        """Get the default schema name for this database type
        
        Returns:
            Default schema name
        """
        pass
    
    @abstractmethod
    def enable_cdc_for_table(self, table_name: str, has_primary_key: bool = None) -> Dict[str, Any]:
        """Enable CDC/CT for a specific table
        
        Args:
            table_name: Name of the table
            has_primary_key: Whether the table has a primary key
            
        Returns:
            Dictionary with operation results
        """
        pass
    
    @abstractmethod
    def disable_cdc_for_table(self, table_name: str) -> Dict[str, Any]:
        """Disable CDC/CT for a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with operation results
        """
        pass
    
    @abstractmethod
    def get_cdc_status(self, table_name: str, has_primary_key: bool = None) -> Dict[str, Any]:
        """Get CDC/CT status for a specific table
        
        Args:
            table_name: Name of the table
            has_primary_key: Whether the table has a primary key
            
        Returns:
            Dictionary with status information
        """
        pass
    
    @abstractmethod
    def cleanup_orphaned_cdc_instances(self) -> Dict[str, Any]:
        """Clean up orphaned CDC instances
        
        Returns:
            Dictionary with cleanup results
        """
        pass
    
    def bulk_enable_cdc_ct_for_schema(self, schema_name: str = None, table_filter: list = None,
                                       mode: str = 'BOTH', dry_run: bool = True) -> Dict[str, Any]:
        """Bulk enable/disable CDC and CT for all tables in a schema
        
        Default implementation returns unsupported. Database-specific providers
        should override this method if they support bulk operations.
        
        Args:
            schema_name: Schema name to process (defaults to self.schema)
            table_filter: Optional list of specific table names to include
            mode: 'CDC' (only CDC), 'CT' (only CT), or 'BOTH' (default)
            dry_run: If True, only shows what would be changed without making changes
            
        Returns:
            Dictionary with operation results
        """
        return {
            'status': 'unsupported',
            'message': f'Bulk CDC/CT operations not implemented for {self.db_type}'
        }
    
    def get_database_type(self) -> str:
        """Get the database type
        
        Returns:
            Database type string
        """
        return self.db_type
    
    def is_cdc_supported(self) -> bool:
        """Check if CDC is supported on this database instance
        
        Returns:
            True if CDC is supported, False otherwise (including None/untested)
        """
        return self.cdc_supported is True
    
    def get_cdc_failure_reason(self) -> Optional[str]:
        """Get the reason why CDC is not supported (if applicable)
        
        Returns:
            Failure reason string or None if CDC is supported
        """
        return self.cdc_failure_reason
    
    def get_qualified_table_name(self, table_name: str) -> str:
        """Get the fully qualified table name
        
        Args:
            table_name: Base table name
            
        Returns:
            Qualified table name (schema.table)
        """
        if self.schema:
            return f"{self.schema}.{table_name}"
        return table_name
    
    def log_operation(self, operation: str, table_name: str, status: str, message: str = ""):
        """Log a replication operation
        
        Args:
            operation: Operation type (enable, disable, status, cleanup)
            table_name: Table name
            status: Operation status (success, error, skipped)
            message: Optional message
        """
        status_emoji = {
            'success': '✅',
            'error': '❌',
            'skipped': '⏭️',
            'warning': '⚠️'
        }.get(status, '❓')
        
        if table_name:
            print(f"{status_emoji} {operation.title()} CDC/CT for {table_name}: {status}")
        else:
            print(f"{status_emoji} {operation.title()}: {status}")
        
        if message:
            print(f"   {message}")

# Factory function to get the appropriate CDC/CT provider
def get_cdc_provider(db_type: str, engine: sa.Engine, dba_engine: sa.Engine, 
                     schema: str = None, secrets_json: Dict[str, Any] = None) -> LfcCDCProviderBase:
    """Factory function to get the appropriate CDC/CT provider
    
    Args:
        db_type: Database type ('sqlserver', 'mysql', 'postgresql')
        engine: SQLAlchemy engine for regular connection
        dba_engine: SQLAlchemy engine with DBA privileges
        schema: Target schema name
        secrets_json: Database connection secrets
        
    Returns:
        Appropriate LfcCDCProvider instance
        
    Raises:
        ValueError: If database type is not supported
    """
    db_type = db_type.lower()
    
    if db_type == 'sqlserver':
        from .LfcCDCSqlServer import SqlServerCDCProvider
        return SqlServerCDCProvider(engine, dba_engine, db_type, schema, secrets_json)
    elif db_type == 'mysql':
        from .LfcCDCMySQL import MySQLCDCProvider
        return MySQLCDCProvider(engine, dba_engine, db_type, schema, secrets_json)
    elif db_type == 'postgresql':
        from .LfcCDCPostgreSQL import PostgreSQLCDCProvider
        return PostgreSQLCDCProvider(engine, dba_engine, db_type, schema, secrets_json)
    else:
        raise ValueError(f"Unsupported database type for CDC/CT: {db_type}")

class LfcCDCWithProvider:
    """Unified CDC/CT interface using provider pattern
    
    This is an alternative implementation that uses the provider pattern
    for database-specific CDC/CT operations. The main LfcCDC class in
    LfcCDC.py contains the SQL Server implementation directly.
    """
    
    def __init__(self, engine: sa.Engine, dba_engine: sa.Engine, db_type: str, 
                 schema: str = None, secrets_json: Dict[str, Any] = None):
        """Initialize the CDC/CT manager with database-specific provider
        
        Args:
            engine: SQLAlchemy engine for regular database connection
            dba_engine: SQLAlchemy engine with DBA privileges
            db_type: Database type ('sqlserver', 'mysql', 'postgresql')
            schema: Target schema name
            secrets_json: Database connection secrets
        """
        self.engine = engine
        self.dba_engine = dba_engine
        self.db_type = db_type.lower()
        self.schema = schema
        self.secrets_json = secrets_json
        
        # Get the appropriate CDC/CT provider
        self.provider = get_cdc_provider(
            self.db_type, engine, dba_engine, schema, secrets_json
        )
        
        print(f"🔄 LfcCDC initialized for {self.db_type}")
    
    # Public interface methods - delegate to provider
    def enable_cdc_for_table(self, table_name: str, has_primary_key: bool = None) -> Dict[str, Any]:
        """Enable CDC/CT for a specific table
        
        Args:
            table_name: Name of the table
            has_primary_key: Whether the table has a primary key
            
        Returns:
            Dictionary with operation results
        """
        return self.provider.enable_cdc_for_table(table_name, has_primary_key)
    
    def disable_cdc_for_table(self, table_name: str) -> Dict[str, Any]:
        """Disable CDC/CT for a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with operation results
        """
        return self.provider.disable_cdc_for_table(table_name)
    
    def get_cdc_status(self, table_name: str, has_primary_key: bool = None) -> Dict[str, Any]:
        """Get CDC/CT status for a specific table
        
        Args:
            table_name: Name of the table
            has_primary_key: Whether the table has a primary key
            
        Returns:
            Dictionary with status information
        """
        return self.provider.get_cdc_status(table_name, has_primary_key)
    
    def cleanup_orphaned_cdc_instances(self) -> Dict[str, Any]:
        """Clean up orphaned CDC instances
        
        Returns:
            Dictionary with cleanup results
        """
        return self.provider.cleanup_orphaned_cdc_instances()
    
    def bulk_enable_cdc_ct_for_schema(self, schema_name: str = None, table_filter: list = None,
                                       mode: str = 'BOTH', dry_run: bool = True) -> Dict[str, Any]:
        """Bulk enable/disable CDC and CT for all tables in a schema
        
        Args:
            schema_name: Schema name to process (defaults to self.schema)
            table_filter: Optional list of specific table names to include
            mode: 'CDC' (only CDC), 'CT' (only CT), or 'BOTH' (default)
            dry_run: If True, only shows what would be changed without making changes
            
        Returns:
            Dictionary with operation results
        """
        return self.provider.bulk_enable_cdc_ct_for_schema(schema_name, table_filter, mode, dry_run)
    
    # Convenience properties for backward compatibility
    def is_cdc_supported(self) -> bool:
        """Check if CDC is supported on this database instance
        
        Returns:
            True if CDC is supported, False otherwise
        """
        return self.provider.is_cdc_supported()
    
    def get_cdc_failure_reason(self) -> Optional[str]:
        """Get the reason why CDC is not supported (if applicable)
        
        Returns:
            Failure reason string or None if CDC is supported
        """
        return self.provider.get_cdc_failure_reason()
    
    @property
    def cdc_supported(self) -> Optional[bool]:
        """Get CDC support status"""
        return self.provider.cdc_supported
    
    @cdc_supported.setter
    def cdc_supported(self, value: bool):
        """Set CDC support status"""
        self.provider.cdc_supported = value
    
    @property
    def cdc_failure_reason(self) -> Optional[str]:
        """Get CDC failure reason"""
        return self.provider.cdc_failure_reason
    
    @cdc_failure_reason.setter
    def cdc_failure_reason(self, value: str):
        """Set CDC failure reason"""
        self.provider.cdc_failure_reason = value
    
    def get_database_type(self) -> str:
        """Get the database type
        
        Returns:
            Database type string
        """
        return self.provider.get_database_type()

# Exports
__all__ = [
    'LfcCDCWithProvider',
    'LfcCDCProviderBase',
    'get_cdc_provider'
]

