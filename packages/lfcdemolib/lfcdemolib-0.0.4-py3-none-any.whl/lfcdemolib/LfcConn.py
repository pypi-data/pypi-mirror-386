"""
LfcConn.py - Lakeflow Connect Databricks Connection Management

This module manages Databricks connection objects for databases created through the LFC demo system.
It handles creating and deleting connections with standardized naming conventions and metadata.

Key Features:
- Automatic connection creation when databases are created
- Standardized naming: robert_lee_{database_hostname}
- JSON metadata in connection comments
- Connection cleanup when databases are deleted
- Support for SQL Server, MySQL, and PostgreSQL
- Uses Databricks Python SDK for API interactions
"""

import json
import socket
from typing import Dict, Any, Optional, Literal

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.catalog import ConnectionInfo, ConnectionType
except ImportError:
    WorkspaceClient = None
    ConnectionInfo = None
    ConnectionType = None

from .LfcEnv import LfcEnv


class LfcConn:
    """Manages Databricks connection objects for LFC demo databases"""
    
    def __init__(self, workspace_client: Optional[WorkspaceClient] = None, lfc_env: Optional[LfcEnv] = None, scope_name: Optional[str] = None):
        """Initialize LfcConn with optional Databricks WorkspaceClient
        
        Args:
            workspace_client: Optional WorkspaceClient instance. If None, connections won't be created.
            lfc_env: Optional LfcEnv instance for user information. If None, creates new instance.
            scope_name: Optional custom scope name. If None, uses firstname_lastname from lfc_env.
        """
        self.workspace_client = workspace_client
        self.lfc_env = lfc_env or LfcEnv(workspace_client)
        self.username_prefix = self.lfc_env.get_connection_prefix()
        self.scope_name = scope_name if scope_name is not None else self.lfc_env.get_scope_name()
        
    def _get_connection_type(self, db_type: str) -> ConnectionType:
        """Map database type to Databricks connection type
        
        Args:
            db_type: Database type (sqlserver, mysql, postgresql)
            
        Returns:
            ConnectionType: Databricks connection type enum
        """
        if not ConnectionType:
            return db_type.upper()  # Fallback for when SDK not available
            
        type_mapping = {
            'sqlserver': ConnectionType.SQLSERVER,
            'mysql': ConnectionType.MYSQL,
            'postgresql': ConnectionType.POSTGRESQL
        }
        return type_mapping.get(db_type.lower(), ConnectionType.SQLSERVER)
    
    def _extract_hostname(self, host_fqdn: str) -> str:
        """Extract hostname from FQDN for connection naming
        
        Args:
            host_fqdn: Fully qualified domain name
            
        Returns:
            str: Hostname portion (before first dot)
        """
        return host_fqdn.split('.')[0] if '.' in host_fqdn else host_fqdn
    
    def _create_connection_comment(self, catalog: str, schema: str, host_fqdn: str) -> str:
        """Create JSON comment for Databricks connection
        
        Args:
            catalog: Database catalog name
            schema: Database schema name  
            host_fqdn: Fully qualified domain name
            
        Returns:
            str: JSON string for connection comment
        """
        comment_data = {
            "secrets": {
                "scope": self.scope_name,  # Use custom or default scope name
                "key": host_fqdn
            }
        }
        return json.dumps(comment_data, separators=(',', ':'))
    
    def _create_connection_options(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create connection options based on database configuration in v2 format
        
        Args:
            db_config: Database configuration dictionary in v2 format containing:
                - host_fqdn: Database host (REQUIRED)
                - port: Database port (REQUIRED)
                - user: Regular user credentials (REQUIRED, NOT DBA)
                - password: User password (REQUIRED)
                - db_type: Database type (for SQL Server specific options)
            
        Returns:
            dict: Connection options for Databricks
            
        Raises:
            ValueError: If required connection parameters are not provided
        """
        # CRITICAL: All connection parameters are REQUIRED - NO FALLBACKS
        # This prevents silent failures and ensures explicit configuration
        
        # Validate host_fqdn (v2 format)
        host = db_config.get('host_fqdn')
        if not host:
            raise ValueError(
                "❌ CRITICAL ERROR: 'host_fqdn' is required for Databricks connection.\n"
                "   Provided keys: " + ', '.join(db_config.keys())
            )
        
        # Validate port (REQUIRED - no default)
        if 'port' not in db_config or not db_config['port']:
            raise ValueError(
                "❌ CRITICAL ERROR: 'port' is required for Databricks connection.\n"
                "   Provided keys: " + ', '.join(db_config.keys())
            )
        
        # Validate USER credentials (CRITICAL: MUST use USER, NOT DBA)
        if 'user' not in db_config or not db_config['user']:
            raise ValueError(
                "❌ CRITICAL ERROR: 'user' credential is required for Lakeflow Connect.\n"
                "   Databricks connections MUST use regular USER credentials (not DBA).\n"
                "   Provided keys: " + ', '.join(db_config.keys())
            )
        
        if 'password' not in db_config or not db_config['password']:
            raise ValueError(
                "❌ CRITICAL ERROR: 'password' is required for Lakeflow Connect.\n"
                "   Databricks connections MUST use regular USER credentials (not DBA).\n"
                "   Provided keys: " + ', '.join(db_config.keys())
            )
        
        # Build options with validated parameters (NO FALLBACKS)
        options = {
            "host": host,
            "port": str(db_config['port']),
            "user": db_config['user'],
            "password": db_config['password']
        }
        
        # Add SQL Server specific options (use v2 field name 'db_type')
        if db_config.get('db_type', '').lower() == 'sqlserver':
            options["trustServerCertificate"] = "true"
            
        return options
    
    def create_connection(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Databricks connection for a database
        
        Args:
            db_config: Database configuration dictionary in v2 format containing:
                - db_type: Database type (sqlserver, mysql, postgresql)
                - host_fqdn: Fully qualified domain name or IP
                - name: Original cloud name/identifier
                - port: Database port
                - catalog: Database/catalog name
                - user: Database user (NOT DBA)
                - password: User password
                - schema: Schema name
                - connection_name: Custom connection name (optional, for LfcConn processing)
                
        Returns:
            dict: Result of connection creation
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available. Connection not created.',
                'connection_name': None
            }
        
        try:
            # Extract connection details (v2 format)
            host_fqdn = db_config.get('host_fqdn', '')
            hostname = self._extract_hostname(host_fqdn)
            db_type = db_config.get('db_type', 'sqlserver')
            catalog = db_config.get('catalog', '')
            schema = db_config.get('schema', 'lfcddemo')
            
            # Create connection name - use custom name if provided, otherwise generate
            if 'connection_name' in db_config and db_config['connection_name']:
                connection_name = db_config['connection_name']
            else:
                connection_name = f"{self.username_prefix}_{hostname}"
            
            # Create connection type
            connection_type = self._get_connection_type(db_type)
            
            # Create comment with metadata (v2 format uses 'catalog')
            comment = self._create_connection_comment(catalog, schema, host_fqdn)
            
            # Create connection options
            options = self._create_connection_options(db_config)
            
            print(f"🔗 Creating Databricks connection: {connection_name}")
            print(f"   Type: {connection_type}")
            print(f"   Host: {host_fqdn}")
            print(f"   Catalog: {catalog}")
            
            # Create the connection via Databricks SDK
            if ConnectionInfo:
                # Try the newer SDK format first
                try:
                    connection_info = ConnectionInfo(
                        name=connection_name,
                        connection_type=connection_type,
                        comment=comment,
                        options=options
                    )
                    created_connection = self.workspace_client.connections.create(connection_info)
                except TypeError:
                    # Fallback to older SDK format
                    created_connection = self.workspace_client.connections.create(
                        name=connection_name,
                        connection_type=connection_type,
                        options=options,
                        comment=comment
                    )
                
                print(f"✅ Databricks connection created successfully: {connection_name}")
                return {
                    'status': 'success',
                    'message': f'Databricks connection created: {connection_name}',
                    'connection_name': connection_name,
                    'connection_type': str(connection_type),
                    'connection_info': created_connection
                }
            else:
                # Fallback when SDK not available
                print(f"⚠️  Databricks SDK not available, simulating connection creation")
                return {
                    'status': 'simulated',
                    'message': f'Connection creation simulated: {connection_name}',
                    'connection_name': connection_name,
                    'connection_type': str(connection_type)
                }
                
        except Exception as e:
            error_msg = str(e)
            
            # Handle connection already exists case
            if 'already exists' in error_msg.lower():
                print(f"✅ Connection already exists: {connection_name}")
                return {
                    'status': 'exists',
                    'message': f'Connection already exists: {connection_name}',
                    'connection_name': connection_name,
                    'connection_type': str(connection_type)
                }
            
            # Handle other errors
            full_error_msg = f"Error creating Databricks connection: {error_msg}"
            print(f"❌ {full_error_msg}")
            return {
                'status': 'error',
                'message': full_error_msg,
                'connection_name': None
            }
    
    def update_connection(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing Databricks connection with new schema information
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            dict: Result of connection update
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available. Connection not updated.',
                'connection_name': None
            }
        
        try:
            # Extract connection details
            host_fqdn = db_config.get('host_fqdn', db_config.get('host', ''))
            database = db_config.get('database', '')
            schema = db_config.get('schema', 'lfcddemo')  # Default to lfcddemo
            
            # Generate connection name
            hostname = self._extract_hostname(host_fqdn)
            connection_name = f"{self.username_prefix}_{hostname}"
            
            print(f"🔄 Updating Databricks connection: {connection_name}")
            print(f"   Schema: {schema}")
            
            # Check if connection exists
            try:
                existing_connection = self.workspace_client.connections.get(connection_name)
                print(f"✅ Found existing connection: {connection_name}")
            except Exception:
                return {
                    'status': 'not_found',
                    'message': f'Connection not found: {connection_name}',
                    'connection_name': connection_name
                }
            
            # Create updated comment with correct schema
            updated_comment = self._create_connection_comment(database, schema, host_fqdn)
            
            # Since Databricks doesn't support updating comments directly,
            # we need to recreate the connection with the updated comment
            
            # Get current connection details for recreation
            current_connection = existing_connection
            current_connection_type = current_connection.connection_type
            
            # Create proper options with credentials from db_config
            updated_options = self._create_connection_options(db_config)
            
            print(f"🔄 Recreating connection with updated comment...")
            print(f"   Options include: {list(updated_options.keys())}")
            
            # Delete existing connection
            self.workspace_client.connections.delete(connection_name)
            print(f"🗑️  Deleted existing connection: {connection_name}")
            
            # Create new connection with updated comment and proper options
            if ConnectionInfo:
                # Try the newer SDK format first
                try:
                    connection_info = ConnectionInfo(
                        name=connection_name,
                        connection_type=current_connection_type,
                        comment=updated_comment,
                        options=updated_options
                    )
                    recreated_connection = self.workspace_client.connections.create(connection_info)
                except TypeError:
                    # Fallback to older SDK format
                    recreated_connection = self.workspace_client.connections.create(
                        name=connection_name,
                        connection_type=current_connection_type,
                        options=updated_options,
                        comment=updated_comment
                    )
            else:
                # Fallback when SDK not available
                raise Exception("Databricks SDK not available for connection recreation")
            
            print(f"✅ Connection updated successfully: {connection_name}")
            print(f"   Updated schema to: {schema}")
            
            return {
                'status': 'success',
                'message': f'Connection updated: {connection_name}',
                'connection_name': connection_name,
                'updated_schema': schema,
                'comment': updated_comment
            }
            
        except Exception as e:
            error_msg = f"Error updating Databricks connection: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'connection_name': None
            }
    
    def get_connection_info(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about existing Databricks connection
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            dict: Connection information including parsed comment
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available.',
                'connection_name': None
            }
        
        try:
            # Extract connection details
            host_fqdn = db_config.get('host_fqdn', db_config.get('host', ''))
            hostname = self._extract_hostname(host_fqdn)
            connection_name = f"{self.username_prefix}_{hostname}"
            
            print(f"🔍 Getting connection info: {connection_name}")
            
            # Get connection details
            connection = self.workspace_client.connections.get(connection_name)
            
            # Parse comment if it exists
            parsed_comment = None
            if connection.comment:
                try:
                    parsed_comment = json.loads(connection.comment)
                except json.JSONDecodeError:
                    parsed_comment = {'raw_comment': connection.comment}
            
            print(f"✅ Connection found: {connection_name}")
            if parsed_comment:
                schema = parsed_comment.get('schema', 'unknown')
                catalog = parsed_comment.get('catalog', 'unknown')
                print(f"   Schema: {schema}")
                print(f"   Catalog: {catalog}")
            
            return {
                'status': 'success',
                'message': f'Connection found: {connection_name}',
                'connection_name': connection_name,
                'connection_type': str(connection.connection_type),
                'comment': connection.comment,
                'parsed_comment': parsed_comment,
                'options': connection.options
            }
            
        except Exception as e:
            error_msg = f"Error getting connection info: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'connection_name': None
            }
    
    def delete_connection(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Delete Databricks connection for a database
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            dict: Result of connection deletion
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available. Connection not deleted.',
                'connection_name': None
            }
        
        try:
            # Extract hostname for connection name
            host_fqdn = db_config.get('host_fqdn', db_config.get('host', ''))
            hostname = self._extract_hostname(host_fqdn)
            connection_name = f"{self.username_prefix}_{hostname}"
            
            print(f"🗑️  Deleting Databricks connection: {connection_name}")
            
            # Delete the connection via Databricks SDK
            self.workspace_client.connections.delete(connection_name)
            
            print(f"✅ Databricks connection deleted successfully: {connection_name}")
            return {
                'status': 'success',
                'message': f'Databricks connection deleted: {connection_name}',
                'connection_name': connection_name
            }
                
        except Exception as e:
            error_msg = f"Error deleting Databricks connection: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'connection_name': None
            }
    
    def list_connections(self, filter_prefix: bool = True) -> Dict[str, Any]:
        """List Databricks connections, optionally filtered by prefix
        
        Args:
            filter_prefix: If True, only return connections with robert_lee_ prefix
            
        Returns:
            dict: List of connections
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available.',
                'connections': []
            }
        
        try:
            print(f"📋 Listing Databricks connections...")
            
            # Get all connections via Databricks SDK
            all_connections = list(self.workspace_client.connections.list())
            
            # Convert to dict format for compatibility
            connections = []
            for conn in all_connections:
                conn_dict = {
                    'name': conn.name,
                    'connection_type': str(conn.connection_type) if conn.connection_type else None,
                    'comment': conn.comment,
                    'options': conn.options or {}
                }
                connections.append(conn_dict)
            
            if filter_prefix:
                # Filter connections with our prefix
                filtered_connections = [
                    conn for conn in connections 
                    if conn.get('name', '').startswith(f"{self.username_prefix}_")
                ]
                connections = filtered_connections
            
            print(f"✅ Found {len(connections)} connections")
            return {
                'status': 'success',
                'message': f'Found {len(connections)} connections',
                'connections': connections
            }
                
        except Exception as e:
            error_msg = f"Error listing Databricks connections: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'connections': []
            }
    
    def create_connections_for_existing_databases(self, database_configs: list) -> Dict[str, Any]:
        """Create Databricks connections for existing databases
        
        Args:
            database_configs: List of database configuration dictionaries
            
        Returns:
            dict: Summary of connection creation results
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available.',
                'results': []
            }
        
        print(f"🔗 Creating Databricks connections for {len(database_configs)} existing databases...")
        
        results = []
        success_count = 0
        error_count = 0
        
        for i, db_config in enumerate(database_configs, 1):
            print(f"\n📊 Processing database {i}/{len(database_configs)}")
            
            result = self.create_connection(db_config)
            results.append(result)
            
            if result.get('status') == 'success':
                success_count += 1
            else:
                error_count += 1
        
        print(f"\n📊 CONNECTION CREATION SUMMARY:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {error_count}")
        print(f"   📊 Total: {len(database_configs)}")
        
        return {
            'status': 'completed',
            'message': f'Created connections for {success_count}/{len(database_configs)} databases',
            'success_count': success_count,
            'error_count': error_count,
            'total_count': len(database_configs),
            'results': results
        }
    
    def get_connection_name(self, db_config: Dict[str, Any]) -> str:
        """Get the connection name that would be used for a database
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            str: Connection name
        """
        host_fqdn = db_config.get('host_fqdn', db_config.get('host', ''))
        hostname = self._extract_hostname(host_fqdn)
        return f"{self.username_prefix}_{hostname}"
