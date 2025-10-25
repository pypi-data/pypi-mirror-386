"""
SimpleConn - Centralized Database Connection Management

This module provides robust database connection creation with:
- Automatic database recreation on connection failure
- Credential management and caching
- Support for multiple database types and cloud providers
- Integration with SimpleDB for infrastructure provisioning
"""

import json
import os
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import sqlalchemy as sa
from sqlalchemy import text

try:
    from databricks.sdk import WorkspaceClient
except ImportError:
    WorkspaceClient = None

from .SimpleSqlalchemy import SimpleSqlalchemy
from .SimpleLocalCred import SimpleLocalCred


class SimpleConn:
    """Centralized database connection management with auto-recreation"""
    
    def __init__(self, workspace_client: Optional[Any] = None):
        """Initialize SimpleConn
        
        Args:
            workspace_client: Optional Databricks WorkspaceClient for database provisioning
        """
        self.workspace_client = workspace_client
        self._cred_manager = SimpleLocalCred()
    
    def _get_config_value(self, config: Any, key: str, default=None):
        """Safely get config value from dict or Pydantic model
        
        Args:
            config: Configuration dict or Pydantic model
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            Value from config or default
        """
        if hasattr(config, key):
            # Pydantic model or object with attributes
            return getattr(config, key, default)
        elif isinstance(config, dict):
            # Dictionary access
            return config.get(key, default)
        else:
            return default
    
    def create_engine_from_config(self, 
                                  config: Dict[str, Any],
                                  auto_recreate: bool = True) -> Tuple[sa.Engine, Dict[str, Any]]:
        """Create SQLAlchemy engine from config with automatic database recreation
        
        Args:
            config: Configuration dictionary with database settings
            auto_recreate: Whether to automatically recreate database on connection failure
            
        Returns:
            tuple: (engine, secrets_json) where secrets_json contains connection details
        """
        # Get database config (handle both dict and Pydantic model)
        database_config = self._get_config_value(config, 'database', {})
        if hasattr(database_config, 'type'):
            db_type = database_config.type
            cloud = database_config.cloud
        else:
            db_type = database_config.get('type', 'sqlserver') if isinstance(database_config, dict) else 'sqlserver'
            cloud = database_config.get('cloud', 'azure') if isinstance(database_config, dict) else 'azure'
        
        # Try to find existing credentials
        secrets_json = self._find_existing_credentials(db_type, cloud)
        
        if secrets_json:
            # Try to connect with existing credentials
            engine = self._create_engine_from_secrets(secrets_json)
            success, result = SimpleSqlalchemy.test_connection(engine)
            
            if success:
                print(f"✅ Successfully connected to existing database: {result}")
                return engine, secrets_json
            else:
                print(f"⚠️ Connection test failed: {result}")
                print(f"⚠️ Database may have been deleted or is unavailable")
                
                if auto_recreate:
                    print(f"\n⚠️  WARNING: Database is not accessible!")
                    print(f"   Attempting to recreate database...")
                    engine, secrets_json = self._recreate_database(config, secrets_json)
                    return engine, secrets_json
                else:
                    raise ConnectionError(f"Failed to connect to database: {result}")
        
        # No existing credentials - create new database
        print(f"🔨 No existing credentials found, creating new database...")
        engine, secrets_json = self._create_new_database(config)
        return engine, secrets_json
    
    def create_engine_from_secrets(self, 
                                   secrets_json: Dict[str, Any],
                                   auto_recreate: bool = True) -> sa.Engine:
        """Create SQLAlchemy engine from secrets with automatic recreation
        
        Args:
            secrets_json: Dictionary containing connection credentials
            auto_recreate: Whether to automatically recreate database on connection failure
            
        Returns:
            SQLAlchemy engine
        """
        engine = self._create_engine_from_secrets(secrets_json)
        success, result = SimpleSqlalchemy.test_connection(engine)
        
        if success:
            print(f"✅ Successfully connected to database: {result}")
            return engine
        
        if not auto_recreate:
            raise ConnectionError(f"Failed to connect to database: {result}")
        
        print(f"⚠️ Connection test failed: {result}")
        print(f"⚠️ Attempting to recreate database...")
        
        # Extract config from secrets_json (v2 format)
        config = {
            'database': {
                'type': secrets_json.get('db_type', 'sqlserver'),
                'cloud': secrets_json.get('cloud', {}).get('provider', 'azure')
            },
            'source_schema': secrets_json.get('schema', 'lfcddemo')
        }
        
        engine, new_secrets = self._recreate_database(config, secrets_json)
        return engine
    
    def _create_engine_from_secrets(self, secrets_json: Dict[str, Any]) -> sa.Engine:
        """Create SQLAlchemy engine from secrets JSON
        
        Args:
            secrets_json: Dictionary containing connection credentials
            
        Returns:
            SQLAlchemy engine
        """
        return SimpleSqlalchemy.create_engine_from_secrets(
            secrets_json=secrets_json,
            isolation_level="AUTOCOMMIT",
            echo=False
        )
    
    def _find_existing_credentials(self, db_type: str, cloud: str) -> Optional[Dict[str, Any]]:
        """Find existing credentials for database type and cloud
        
        Args:
            db_type: Database type (sqlserver, mysql, postgresql)
            cloud: Cloud provider (azure, aws, gcp)
            
        Returns:
            Dictionary containing credentials or None if not found
        """
        # Use SimpleLocalCred to find the most recent credentials
        creds_list = self._cred_manager.find_credentials(db_type=db_type, cloud=cloud)
        
        if not creds_list:
            return None
        
        # Get the most recent credentials
        creds_data = creds_list[0]  # Already sorted by date, most recent first
        
        # Convert credentials to secrets format
        secrets_json = self._cred_manager.convert_to_secrets_json(creds_data)
        
        # Extract cloud provider from either format
        cloud_provider = creds_data.get('cloud_provider')
        if not cloud_provider:
            cloud_obj = creds_data.get('cloud', {})
            cloud_provider = cloud_obj.get('provider', 'unknown')
        
        print(f"📂 Found matching credentials: {creds_data.get('_filename', 'unknown')}")
        print(f"   Cloud: {cloud_provider}")
        print(f"   DB Type: {creds_data.get('db_type', 'unknown')}")
        print(f"   Host: {creds_data.get('host_fqdn', creds_data.get('host', 'unknown'))}")
        print(f"   Database: {secrets_json.get('catalog', 'unknown')}")
        print(f"   Created: {creds_data.get('created_at', 'unknown')}")
        
        return secrets_json
    
    def _convert_credentials_to_secrets(self, creds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert credentials format to secrets_json format (v2)
        
        Uses Pydantic model for validation and conversion with automatic field handling.
        
        Args:
            creds_data: Credentials data from file (v2 format)
            
        Returns:
            Dictionary in secrets_json v2 format
            
        Raises:
            ValueError: If replication_mode is missing or validation fails
        """
        from .LfcCredentialModel import LfcCredential
        from pydantic import ValidationError
        
        # Check for required replication_mode field (business requirement)
        if 'replication_mode' not in creds_data:
            raise ValueError(
                f"Missing 'replication_mode' in credentials. "
                f"Please run update_existing_replication_mode.py to detect and set the mode."
            )
        
        # Use Pydantic model for validation and conversion
        try:
            cred = LfcCredential.from_dict(creds_data)
            secrets_json = cred.to_secrets_json()
            # Add replication_mode for backward compatibility
            secrets_json['replication_mode'] = creds_data['replication_mode']
            return secrets_json
        except ValidationError as e:
            # Fall back to manual conversion for backward compatibility
            # Handle both 'database' and 'catalog' field names
            catalog = creds_data.get('catalog') or creds_data.get('database', '')
            
            # Convert port to int if it's a string
            port = creds_data.get('port')
            if isinstance(port, str):
                port = int(port) if port.isdigit() else self._get_default_port(creds_data.get('db_type', 'sqlserver'))
            elif port is None:
                port = self._get_default_port(creds_data.get('db_type', 'sqlserver'))
            
            # Extract DBA credentials from v2 format (nested dba object)
            dba_obj = creds_data.get('dba', {})
            dba_user = dba_obj.get('user', '')
            dba_password = dba_obj.get('password', '')
            
            # Extract cloud object from v2 format
            cloud_obj = creds_data.get('cloud', {})
            
            # Return v2 format secrets_json
            return {
                'version': 'v2',
                'name': creds_data.get('name', ''),
                'host_fqdn': creds_data.get('host_fqdn', ''),
                'catalog': catalog,
                'schema': creds_data.get('schema', 'lfcddemo'),
                'user': creds_data.get('user', ''),
                'password': creds_data.get('password', ''),
                'dba': {
                    'user': dba_user,
                    'password': dba_password
                },
                'port': port,
                'db_type': creds_data.get('db_type', 'sqlserver'),
                'replication_mode': creds_data['replication_mode'],  # REQUIRED - no default
                'cloud': {
                    'provider': cloud_obj.get('provider', 'azure'),
                    'location': cloud_obj.get('location', 'Unknown'),
                    'resource_group': cloud_obj.get('resource_group', 'Unknown')
                }
            }
    
    def _get_default_port(self, db_type: str) -> int:
        """Get default port for database type
        
        Args:
            db_type: Database type
            
        Returns:
            Default port number
        """
        ports = {
            'sqlserver': 1433,
            'mysql': 3306,
            'postgresql': 5432
        }
        return ports.get(db_type.lower(), 1433)
    
    def _create_new_database(self, config: Dict[str, Any]) -> Tuple[sa.Engine, Dict[str, Any]]:
        """Create a new database using SimpleDB with complete setup including seeding
        
        Args:
            config: Configuration dictionary
            
        Returns:
            tuple: (engine, secrets_json)
        """
        from .SimpleDB import SimpleDB
        
        # Get database config (handle both dict and Pydantic model)
        database_config = self._get_config_value(config, 'database', {})
        if hasattr(database_config, 'type'):
            db_type = database_config.type
            cloud = database_config.cloud
        else:
            db_type = database_config.get('type', 'sqlserver') if isinstance(database_config, dict) else 'sqlserver'
            cloud = database_config.get('cloud', 'azure') if isinstance(database_config, dict) else 'azure'
        
        schema = self._get_config_value(config, 'source_schema', 'lfcddemo')
        location = self._get_config_value(config, 'location', 'Central US')
        
        print(f"🔨 Creating new {db_type} database on {cloud} with complete setup...")
        
        db_creator = SimpleDB(
            workspace_client=self.workspace_client,
            config=config,
            db_type=db_type,
            cloud_provider=cloud,
            location=location,
            auto_cleanup=False  # Don't auto-cleanup connections/secrets for persistent databases
        )
        
        # Create complete database setup (infrastructure + permissions + LFC integration)
        setup_result = db_creator.create_complete_database_setup()
        
        if setup_result['status'] not in ['success', 'partial']:
            raise RuntimeError(f"Failed to create database: {setup_result.get('message', 'Unknown error')}")
        
        # Extract db_details from setup_result
        db_details = setup_result.get('database', {})
        
        if db_details.get('status') != 'success':
            raise RuntimeError(f"Database infrastructure creation failed: {db_details.get('message', 'Unknown error')}")
        
        print(f"✅ Database infrastructure and LFC integration completed!")
        print(f"   Host: {db_details['db_host_fqdn']}")
        print(f"   Database: {db_details['db_catalog']}")
        print(f"   Schema: {schema}")
        
        # Save credentials
        secrets_json = self._save_database_credentials(db_details, db_type, cloud, schema)
        
        # Create engine
        engine = self._create_engine_from_secrets(secrets_json)
        
        # Create seed tables using shared method from SimpleDB
        seed_result = SimpleDB.create_seed_tables(
            engine=engine,
            schema=schema,
            table_count_per_type=2,
            rows_per_table=5,
            secrets_json=secrets_json
        )
        
        # Log seed result but don't fail if seeding has issues
        if seed_result['status'] != 'success':
            print(f"   ℹ️  Seed status: {seed_result['status']} - {seed_result.get('message', 'Unknown')}")
        
        return engine, secrets_json
    
    def _recreate_database(self, 
                          config: Dict[str, Any],
                          old_secrets: Dict[str, Any]) -> Tuple[sa.Engine, Dict[str, Any]]:
        """Recreate database when connection fails
        
        Args:
            config: Configuration dictionary
            old_secrets: Old secrets that failed to connect
            
        Returns:
            tuple: (engine, secrets_json)
        """
        print(f"\n⚠️  WARNING: Database is not accessible!")
        print(f"   The database may have been deleted or the server is unavailable.")
        print(f"   Attempting to recreate database using existing credentials...")
        
        # Get database config (handle both dict and Pydantic model)
        database_config = self._get_config_value(config, 'database', {})
        if hasattr(database_config, 'type'):
            db_type = database_config.type
            cloud = database_config.cloud
        else:
            db_type = database_config.get('type', 'sqlserver') if isinstance(database_config, dict) else 'sqlserver'
            cloud = database_config.get('cloud', 'azure') if isinstance(database_config, dict) else 'azure'
        
        # Recreate the database
        engine, new_secrets = self._create_new_database(config)
        
        # For SQL Server, verify and update replication_mode if it changed
        if db_type == 'sqlserver':
            old_mode = old_secrets.get('replication_mode', 'unknown')
            new_mode = new_secrets.get('replication_mode', 'unknown')
            
            if old_mode != new_mode:
                print(f"\n⚠️  Replication mode changed during recreation!")
                print(f"   Old mode: {old_mode}")
                print(f"   New mode: {new_mode}")
                print(f"   This may happen if the database tier changed.")
            else:
                print(f"\n✅ Replication mode unchanged: {new_mode}")
        
        return engine, new_secrets
    
    def _save_database_credentials(self, 
                                   db_details: Dict[str, Any],
                                   db_type: str,
                                   cloud: str,
                                   schema: str) -> Dict[str, Any]:
        """Save database credentials to file using SimpleLocalCred
        
        Args:
            db_details: Database details from SimpleDB
            db_type: Database type
            cloud: Cloud provider
            schema: Schema name
            
        Returns:
            Dictionary in secrets_json format
        """
        # Use SimpleLocalCred to save credentials
        filepath, creds_data = self._cred_manager.save_credentials(
            db_details=db_details,
            db_type=db_type,
            cloud=cloud,
            schema=schema
        )
        
        # Convert to secrets_json format for engine creation
        secrets_json = self._cred_manager.convert_to_secrets_json(creds_data)
        
        return secrets_json

