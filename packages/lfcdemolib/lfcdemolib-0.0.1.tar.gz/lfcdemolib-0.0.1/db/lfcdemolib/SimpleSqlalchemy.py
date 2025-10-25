"""
SimpleSqlalchemy - Centralized SQLAlchemy Engine Creation (V2 Format Only)

This module provides a unified interface for creating SQLAlchemy engines across
all database types (SQL Server, MySQL, PostgreSQL) with consistent configuration
and proper credential handling.

Key Features:
- Unified engine creation for all database types
- Strict V2 credential format validation (no defaults, no fallbacks)
- Required fields: db_type, host_fqdn, catalog, user, password, port
- Proper URL encoding of credentials
- Database-specific connection string formatting
- SSL/TLS configuration for cloud providers
- Consistent isolation level and echo settings
- Support for both regular and DBA connections

V2 Format Requirements:
- All credentials must be in V2 format (nested objects for dba/cloud)
- Missing required fields will raise ValueError with clear error messages
- No silent defaults or fallbacks to v1 format
"""

import urllib.parse
import sqlalchemy as sa
from sqlalchemy import create_engine
from typing import Dict, Any, Optional, Literal
from .LfcCredentialModel import LfcCredential
from pydantic import ValidationError


class SimpleSqlalchemy:
    """Centralized SQLAlchemy engine creation and management"""
    
    # Driver mapping for all supported database types
    DRIVERS = {
        "mysql": "mysql+pymysql",
        "postgresql": "postgresql+psycopg2",
        "sqlserver": "mssql+pymssql",
        "oracle": "oracle+oracledb",
        "sqlite": "sqlite"
    }
    
    @classmethod
    def create_engine(
        cls,
        db_type: str,
        host: str,
        database: str,
        username: str,
        password: str,
        port: Optional[int] = None,
        cloud: Optional[str] = None,
        echo: bool = False,
        isolation_level: str = "AUTOCOMMIT",
        **kwargs
    ) -> sa.Engine:
        """Create a SQLAlchemy engine with proper configuration
        
        Args:
            db_type: Database type (sqlserver, mysql, postgresql, oracle, sqlite)
            host: Database host (FQDN or hostname)
            database: Database/catalog name
            username: Database username
            password: Database password
            port: Database port (uses default if not provided)
            cloud: Cloud provider (azure, aws, gcp) - affects SSL settings
            echo: Whether to echo SQL statements (default: False)
            isolation_level: Transaction isolation level (default: AUTOCOMMIT)
            **kwargs: Additional SQLAlchemy engine options
            
        Returns:
            sqlalchemy.Engine: Configured database engine
            
        Raises:
            ValueError: If database type is not supported
        """
        # Get driver for database type
        driver = cls.DRIVERS.get(db_type.lower())
        if not driver:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        # Get default port if not provided
        if port is None:
            port = cls._get_default_port(db_type)
        
        # URL encode credentials
        encoded_username = urllib.parse.quote_plus(username)
        encoded_password = urllib.parse.quote_plus(password)
        
        # Build connection string based on database type
        connection_string = cls._build_connection_string(
            driver=driver,
            username=encoded_username,
            password=encoded_password,
            host=host,
            port=port,
            database=database,
            db_type=db_type,
            cloud=cloud
        )
        
        # Create and return engine
        return sa.create_engine(
            connection_string,
            echo=echo,
            isolation_level=isolation_level,
            **kwargs
        )
    
    @classmethod
    def create_engine_from_secrets(
        cls,
        secrets_json: Dict[str, Any],
        use_dba: bool = False,
        target_database: Optional[str] = None,
        echo: bool = False,
        isolation_level: str = "AUTOCOMMIT",
        **kwargs
    ) -> sa.Engine:
        """Create engine from secrets JSON dictionary (V2 format only)
        
        Uses Pydantic model for automatic validation of all required fields.
        
        Args:
            secrets_json: Dictionary containing V2 connection credentials (required fields):
                - db_type: Database type ('postgresql', 'mysql', 'sqlserver') [REQUIRED]
                - host_fqdn: Fully qualified domain name [REQUIRED]
                - catalog: Database name [REQUIRED]
                - user: Username [REQUIRED]
                - password: Password [REQUIRED]
                - port: Port number [REQUIRED]
                - dba.user: DBA username (if use_dba=True) [REQUIRED if use_dba=True]
                - dba.password: DBA password (if use_dba=True) [REQUIRED if use_dba=True]
                - cloud.provider: Cloud provider (optional)
            use_dba: Whether to use DBA credentials instead of regular user
            target_database: Override database name (useful for master/admin connections)
            echo: Whether to echo SQL statements
            isolation_level: Transaction isolation level
            **kwargs: Additional SQLAlchemy engine options
            
        Returns:
            sqlalchemy.Engine: Configured database engine
            
        Raises:
            ValidationError: If any required field is missing or invalid (from Pydantic)
        """
        # Validate credentials using Pydantic model (automatic validation!)
        try:
            cred = LfcCredential.from_dict(secrets_json)
        except ValidationError as e:
            # Re-raise with more context for backward compatibility
            error_details = []
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                msg = error['msg']
                error_details.append(f"{field}: {msg}")
            raise ValueError(
                f"Invalid credential format: {'; '.join(error_details)}. "
                f"Provided fields: {list(secrets_json.keys())}"
            ) from e
        
        # Get SQLAlchemy parameters from validated credential
        engine_params = cred.to_sqlalchemy_params(
            use_dba=use_dba,
            target_database=target_database
        )
        
        # Create engine with validated parameters
        return cls.create_engine(
            **engine_params,
            echo=echo,
            isolation_level=isolation_level,
            **kwargs
        )
    
    @classmethod
    def create_engine_from_credentials(
        cls,
        creds_data: Dict[str, Any],
        use_dba: bool = False,
        echo: bool = False,
        isolation_level: str = "AUTOCOMMIT",
        **kwargs
    ) -> sa.Engine:
        """Create engine from credentials file data (V2 format only)
        
        Uses Pydantic model for automatic validation of all required fields.
        
        Args:
            creds_data: Credentials dictionary from ~/.lfcddemo/*.json (V2 format required):
                - db_type: Database type [REQUIRED]
                - host_fqdn: Hostname [REQUIRED]
                - catalog: Database name [REQUIRED]
                - user: Username [REQUIRED]
                - password: Password [REQUIRED]
                - port: Port number [REQUIRED]
                - dba.user: DBA username (if use_dba=True) [REQUIRED if use_dba=True]
                - dba.password: DBA password (if use_dba=True) [REQUIRED if use_dba=True]
                - cloud.provider: Cloud provider (optional)
            use_dba: Whether to use DBA credentials
            echo: Whether to echo SQL statements
            isolation_level: Transaction isolation level
            **kwargs: Additional SQLAlchemy engine options
            
        Returns:
            sqlalchemy.Engine: Configured database engine
            
        Raises:
            ValidationError: If any required field is missing or invalid (from Pydantic)
        """
        # Validate credentials using Pydantic model (automatic validation!)
        try:
            cred = LfcCredential.from_dict(creds_data)
        except ValidationError as e:
            # Re-raise with more context for backward compatibility
            error_details = []
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                msg = error['msg']
                error_details.append(f"{field}: {msg}")
            raise ValueError(
                f"Invalid credential format: {'; '.join(error_details)}. "
                f"Provided fields: {list(creds_data.keys())}"
            ) from e
        
        # Get SQLAlchemy parameters from validated credential
        engine_params = cred.to_sqlalchemy_params(use_dba=use_dba)
        
        # Create engine with validated parameters
        return cls.create_engine(
            **engine_params,
            echo=echo,
            isolation_level=isolation_level,
            **kwargs
        )
    
    @classmethod
    def create_dba_engine(
        cls,
        secrets_json: Dict[str, Any],
        target_database: Optional[str] = None,
        echo: bool = False,
        **kwargs
    ) -> sa.Engine:
        """Create a DBA engine for administrative operations (V2 format only)
        
        For SQL Server, connects to 'master' database by default.
        For other databases, connects to the target database.
        
        Uses Pydantic model for automatic validation of all required fields.
        
        Args:
            secrets_json: Dictionary containing V2 connection credentials
            target_database: Override database name (None = use default for db type)
            echo: Whether to echo SQL statements
            **kwargs: Additional SQLAlchemy engine options
            
        Returns:
            sqlalchemy.Engine: DBA engine for administrative operations
            
        Raises:
            ValidationError: If required fields are missing or invalid (from Pydantic)
        """
        # Validate credentials using Pydantic model
        try:
            cred = LfcCredential.from_dict(secrets_json)
        except ValidationError as e:
            # Re-raise with more context for backward compatibility
            error_details = []
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                msg = error['msg']
                error_details.append(f"{field}: {msg}")
            raise ValueError(
                f"Invalid credential format: {'; '.join(error_details)}. "
                f"Provided fields: {list(secrets_json.keys())}"
            ) from e
        
        # Determine target database
        if target_database is None:
            if cred.db_type == "sqlserver":
                target_database = "master"
            else:
                target_database = cred.catalog
        
        # Use the validated credentials with DBA flag
        return cls.create_engine_from_secrets(
            secrets_json=secrets_json,
            use_dba=True,
            target_database=target_database,
            echo=echo,
            isolation_level="AUTOCOMMIT",
            **kwargs
        )
    
    @classmethod
    def _get_default_port(cls, db_type: str) -> int:
        """Get default port for database type
        
        Args:
            db_type: Database type
            
        Returns:
            int: Default port number
        """
        ports = {
            "sqlserver": 1433,
            "mysql": 3306,
            "postgresql": 5432,
            "oracle": 1521
        }
        return ports.get(db_type.lower(), 1433)
    
    @classmethod
    def _build_connection_string(
        cls,
        driver: str,
        username: str,
        password: str,
        host: str,
        port: int,
        database: str,
        db_type: str,
        cloud: Optional[str] = None
    ) -> str:
        """Build database connection string with proper formatting
        
        Args:
            driver: SQLAlchemy driver string
            username: URL-encoded username
            password: URL-encoded password
            host: Database host
            port: Database port
            database: Database name
            db_type: Database type
            cloud: Cloud provider (affects SSL settings)
            
        Returns:
            str: Formatted connection string
        """
        # MySQL: use empty string for catalog/database in connection string
        # MySQL will connect without a default database selection
        if db_type.lower() == "mysql":
            database = ""
        
        # Base connection string
        base_url = f"{driver}://{username}:{password}@{host}:{port}/{database}"
        
        # Add database-specific options
        if db_type == "sqlserver":
            # SQL Server specific options
            return base_url
            
        elif db_type == "postgresql":
            # PostgreSQL SSL for Azure
            if cloud and cloud.lower() == "azure":
                return f"{base_url}?sslmode=require"
            return base_url
            
        elif db_type == "mysql":
            # MySQL SSL for Azure
            if cloud and cloud.lower() == "azure":
                return f"{base_url}?ssl=true&ssl_verify_cert=false"
            return base_url
            
        else:
            # Default (no special options)
            return base_url
    
    @classmethod
    def test_connection(
        cls,
        engine: sa.Engine,
        db_type: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """Test database connection with database-specific query
        
        Args:
            engine: SQLAlchemy engine to test
            db_type: Database type (auto-detected if None)
            
        Returns:
            tuple: (success: bool, database_name: Optional[str])
        """
        if db_type is None:
            db_type = engine.dialect.name
        
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                
                if db_type == "postgresql":
                    result = conn.execute(text("SELECT current_database()"))
                elif db_type == "mysql":
                    result = conn.execute(text("SELECT database()"))
                elif db_type in ["sqlserver", "mssql"]:
                    result = conn.execute(text("SELECT DB_NAME()"))
                else:
                    result = conn.execute(text("SELECT 1"))
                
                current_db = result.scalar()
                return True, current_db
                
        except Exception as e:
            return False, str(e)


# Convenience functions for backward compatibility
def create_engine_from_secrets(secrets_json: Dict[str, Any], use_dba: bool = False, **kwargs) -> sa.Engine:
    """Convenience function for creating engine from secrets
    
    Args:
        secrets_json: Secrets dictionary
        use_dba: Whether to use DBA credentials
        **kwargs: Additional engine options
        
    Returns:
        sqlalchemy.Engine: Configured engine
    """
    return SimpleSqlalchemy.create_engine_from_secrets(secrets_json, use_dba=use_dba, **kwargs)


def create_dba_engine(secrets_json: Dict[str, Any], target_database: Optional[str] = None, **kwargs) -> sa.Engine:
    """Convenience function for creating DBA engine
    
    Args:
        secrets_json: Secrets dictionary
        target_database: Optional target database
        **kwargs: Additional engine options
        
    Returns:
        sqlalchemy.Engine: DBA engine
    """
    return SimpleSqlalchemy.create_dba_engine(secrets_json, target_database=target_database, **kwargs)

