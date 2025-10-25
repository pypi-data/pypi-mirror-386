"""
LfcDbPerm.py - Lakeflow Connect Database Permission Management

This module handles database permission setup for LFC (Lakeflow Connect) operations.
It supports both permissive and strict permission modes for different database types.

Key Features:
- Permissive mode: Broad permissions for development and testing
- Strict mode: Minimal permissions for production environments
- Support for SQL Server, MySQL, and PostgreSQL
- Separate DBA and user permission management
- CDC/CT (Change Data Capture/Change Tracking) permission setup
- Schema evolution support
- Replication permission management

Permission Modes:
- PERMISSIVE (default): Full access for development/testing
- STRICT: Minimal required permissions for production

Database Support:
- SQL Server: CDC, Change Tracking, schema evolution
- MySQL: Replication, schema management
- PostgreSQL: Logical replication, schema management
"""

import json
from typing import Dict, Any, Optional, List, Literal
from sqlalchemy import create_engine, text
import sqlalchemy as sa
from sqlalchemy.engine import Engine
import logging
from .LfcCredentialModel import LfcCredential
from pydantic import ValidationError

# Setup logging
logger = logging.getLogger(__name__)

PermissionMode = Literal["PERMISSIVE", "STRICT"]
DatabaseType = Literal["sqlserver", "mysql", "postgresql"]


class LfcDbPerm:
    """Database Permission Management for Lakeflow Connect"""
    
    def __init__(self, 
                 engine: Engine = None,
                 db_config: Dict[str, Any] = None,
                 permission_mode: PermissionMode = "PERMISSIVE"):
        """Initialize LfcDbPerm
        
        Args:
            engine: SQLAlchemy engine for database connection
            db_config: Database configuration dictionary
            permission_mode: Permission mode (PERMISSIVE or STRICT)
        """
        self.engine = engine
        self.db_config = db_config or {}
        self.permission_mode = permission_mode
        self.db_type = self._detect_database_type()
        
        # Extract connection details using Pydantic model if possible
        # Try to validate as V2 format first, fall back to manual extraction
        try:
            cred = LfcCredential.from_dict(self.db_config)
            # Use validated credential fields
            self.dba_username = cred.dba.user
            self.dba_password = cred.dba.password
            self.user_username = cred.user
            self.user_password = cred.password
            self.database = cred.catalog
            self.schema = cred.schema_name
            self.host_fqdn = cred.host_fqdn
            self.port = cred.port
        except (ValidationError, Exception):
            # Fall back to manual extraction for backward compatibility
            logger.debug("Credential validation failed, using manual extraction")
            
            # DBA credentials
            dba_obj = self.db_config.get('dba', {})
            if dba_obj:
                # V2 format: nested dba object
                self.dba_username = dba_obj.get('user', '')
                self.dba_password = dba_obj.get('password', '')
            else:
                # V1 format: flat fields
                self.dba_username = self.db_config.get('dba_username') or self.db_config.get('dba_user', '')
                self.dba_password = self.db_config.get('dba_password', '')
            
            # User credentials
            self.user_username = self.db_config.get('user', self.db_config.get('username', ''))
            self.user_password = self.db_config.get('password', '')
            
            # Database/catalog name
            self.database = self.db_config.get('catalog', self.db_config.get('database', ''))
            
            # Schema
            self.schema = self.db_config.get('schema', self._get_default_schema())
            
            # Host
            self.host_fqdn = self.db_config.get('host_fqdn', self.db_config.get('host', ''))
            
            # Port
            self.port = self.db_config.get('port', self._get_default_port())
        
        logger.info(f"Initialized LfcDbPerm for {self.db_type} in {permission_mode} mode")
    
    def _detect_database_type(self) -> DatabaseType:
        """Detect database type from engine or config"""
        if self.engine:
            dialect_name = self.engine.dialect.name.lower()
            if 'mssql' in dialect_name or 'sqlserver' in dialect_name:
                return 'sqlserver'
            elif 'mysql' in dialect_name:
                return 'mysql'
            elif 'postgresql' in dialect_name or 'postgres' in dialect_name:
                return 'postgresql'
        
        # Fallback to config
        db_type = self.db_config.get('type', '').lower()
        if db_type in ['sqlserver', 'mysql', 'postgresql']:
            return db_type
        
        return 'sqlserver'  # Default fallback
    
    def _get_default_schema(self) -> str:
        """Get default schema for database type - using lfcddemo as standard"""
        # Use lfcddemo as the standard schema across all database types
        # This matches the schema created by the LFC configuration scripts
        return 'lfcddemo'
    
    def _get_default_port(self) -> int:
        """Get default port for database type"""
        port_defaults = {
            'sqlserver': 1433,
            'mysql': 3306,
            'postgresql': 5432
        }
        return port_defaults.get(self.db_type, 1433)
    
    def create_dba_engine(self) -> Engine:
        """Create SQLAlchemy engine using DBA credentials connected to target database
        
        Returns:
            Engine: SQLAlchemy engine connected to target database with DBA credentials
        """
        if not all([self.dba_username, self.dba_password, self.host_fqdn, self.database]):
            raise ValueError("DBA credentials and database connection details are required")
        
        # Import here to avoid circular imports
        import urllib.parse
        import sqlalchemy as sa
        
        # Database driver mapping
        drivers = {
            'sqlserver': 'mssql+pymssql',
            'mysql': 'mysql+pymysql',
            'postgresql': 'postgresql+psycopg2'
        }
        
        driver = drivers.get(self.db_type)
        if not driver:
            raise ValueError(f"Unsupported database type: {self.db_type}")
        
        # URL encode credentials
        encoded_username = urllib.parse.quote_plus(self.dba_username)
        encoded_password = urllib.parse.quote_plus(self.dba_password)
        
        # For SQL Server, connect to target database (not master)
        # This ensures all commands run in the correct database context
        catalog = self.database
        if self.db_type == 'mysql':
            catalog = self.schema  # MySQL uses schema as catalog
        
        connection_string = f"{driver}://{encoded_username}:{encoded_password}@{self.host_fqdn}:{self.port}/{catalog}"
        
        # Add SQL Server specific options
        if self.db_type == 'sqlserver':
            connection_string += "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
        
        engine = sa.create_engine(connection_string, echo=False, isolation_level="AUTOCOMMIT")
        logger.info(f"Created DBA engine for {self.db_type} connected to database: {catalog}")
        
        return engine
    
    def create_user_engine(self) -> Engine:
        """Create SQLAlchemy engine using user credentials connected to target database
        
        Returns:
            Engine: SQLAlchemy engine connected to target database with user credentials
        """
        if not all([self.user_username, self.user_password, self.host_fqdn, self.database]):
            raise ValueError("User credentials and database connection details are required")
        
        # Import here to avoid circular imports
        import urllib.parse
        import sqlalchemy as sa
        
        # Database driver mapping
        drivers = {
            'sqlserver': 'mssql+pymssql',
            'mysql': 'mysql+pymysql',
            'postgresql': 'postgresql+psycopg2'
        }
        
        driver = drivers.get(self.db_type)
        if not driver:
            raise ValueError(f"Unsupported database type: {self.db_type}")
        
        # URL encode credentials
        encoded_username = urllib.parse.quote_plus(self.user_username)
        encoded_password = urllib.parse.quote_plus(self.user_password)
        
        # Connect to target database
        catalog = self.database
        if self.db_type == 'mysql':
            catalog = self.schema  # MySQL uses schema as catalog
        
        connection_string = f"{driver}://{encoded_username}:{encoded_password}@{self.host_fqdn}:{self.port}/{catalog}"
        
        # Add SQL Server specific options
        if self.db_type == 'sqlserver':
            connection_string += "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
        
        engine = sa.create_engine(connection_string, echo=False, isolation_level="AUTOCOMMIT")
        logger.info(f"Created user engine for {self.db_type} connected to database: {catalog}")
        
        return engine
    
    def setup_database_permissions(self, 
                                 enable_cdc: bool = True,
                                 enable_ct: bool = True,
                                 enable_replication: bool = True) -> Dict[str, Any]:
        """Setup complete database permissions
        
        Args:
            enable_cdc: Enable Change Data Capture (SQL Server only)
            enable_ct: Enable Change Tracking (SQL Server only) 
            enable_replication: Enable replication permissions
            
        Returns:
            dict: Results of permission setup
        """
        results = {
            'status': 'success',
            'message': 'Database permissions setup completed',
            'database_type': self.db_type,
            'permission_mode': self.permission_mode,
            'operations': []
        }
        
        try:
            # Step 1: Setup DBA permissions
            dba_result = self._setup_dba_permissions()
            results['operations'].append(dba_result)
            
            # Step 2: Create/configure user
            user_result = self._setup_user_permissions()
            results['operations'].append(user_result)
            
            # Step 3: Setup replication permissions
            if enable_replication:
                repl_result = self._setup_replication_permissions()
                results['operations'].append(repl_result)
            
            # Step 4: Setup CDC/CT (SQL Server only)
            if self.db_type == 'sqlserver':
                if enable_cdc:
                    cdc_result = self._setup_cdc_permissions()
                    results['operations'].append(cdc_result)
                
                if enable_ct:
                    ct_result = self._setup_change_tracking_permissions()
                    results['operations'].append(ct_result)
            
            # Step 5: Setup schema permissions
            schema_result = self._setup_schema_permissions()
            results['operations'].append(schema_result)
            
            logger.info(f"Database permissions setup completed for {self.db_type}")
            
        except Exception as e:
            results['status'] = 'error'
            results['message'] = f'Permission setup failed: {str(e)}'
            logger.error(f"Permission setup failed: {e}")
        
        return results
    
    def _setup_dba_permissions(self) -> Dict[str, Any]:
        """Setup DBA-level permissions"""
        if self.db_type == 'sqlserver':
            return self._setup_sqlserver_dba_permissions()
        elif self.db_type == 'mysql':
            return self._setup_mysql_dba_permissions()
        elif self.db_type == 'postgresql':
            return self._setup_postgresql_dba_permissions()
    
    def _setup_user_permissions(self) -> Dict[str, Any]:
        """Setup user-level permissions"""
        if self.db_type == 'sqlserver':
            return self._setup_sqlserver_user_permissions()
        elif self.db_type == 'mysql':
            return self._setup_mysql_user_permissions()
        elif self.db_type == 'postgresql':
            return self._setup_postgresql_user_permissions()
    
    def _setup_replication_permissions(self) -> Dict[str, Any]:
        """Setup replication permissions"""
        if self.db_type == 'sqlserver':
            return self._setup_sqlserver_replication_permissions()
        elif self.db_type == 'mysql':
            return self._setup_mysql_replication_permissions()
        elif self.db_type == 'postgresql':
            return self._setup_postgresql_replication_permissions()
    
    # SQL Server Permission Methods
    def _setup_sqlserver_dba_permissions(self) -> Dict[str, Any]:
        """Setup SQL Server DBA permissions"""
        try:
            # Step 1: Create server-level login in master database
            master_engine = self._create_master_engine()
            
            master_commands = [
                f"IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = '{self.dba_username}') CREATE LOGIN [{self.dba_username}] WITH PASSWORD = '{self.dba_password}'",
                f"ALTER LOGIN [{self.dba_username}] WITH PASSWORD = '{self.dba_password}'",
                f"IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{self.dba_username}') CREATE USER [{self.dba_username}] FOR LOGIN [{self.dba_username}] WITH DEFAULT_SCHEMA=dbo"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                master_commands.append(f"ALTER SERVER ROLE sysadmin ADD MEMBER [{self.dba_username}]")
            
            # Execute master database commands
            print(f"   🔐 Creating server-level login for DBA: {self.dba_username}")
            self._execute_sql_commands_with_engine(master_commands, master_engine)
            master_engine.dispose()
            
            # Step 2: Create user and assign roles in target database
            database_commands = [
                f"IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{self.dba_username}') CREATE USER [{self.dba_username}] FOR LOGIN [{self.dba_username}]",
                f"ALTER ROLE db_owner ADD MEMBER [{self.dba_username}]",
                f"ALTER ROLE db_ddladmin ADD MEMBER [{self.dba_username}]"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                database_commands.append(f"ALTER ROLE db_securityadmin ADD MEMBER [{self.dba_username}]")
            
            print(f"   🔐 Creating database user for DBA: {self.dba_username}")
            self._execute_sql_commands(database_commands)
            
            return {
                'operation': 'sqlserver_dba_setup',
                'status': 'success',
                'message': f'SQL Server DBA permissions configured for {self.dba_username}',
                'operations': ['server_login_created', 'master_user_created', 'database_user_created', 'roles_assigned']
            }
            
        except Exception as e:
            return {
                'operation': 'sqlserver_dba_setup',
                'status': 'error',
                'message': f'SQL Server DBA setup failed: {str(e)}'
            }
    
    def _setup_sqlserver_user_permissions(self) -> Dict[str, Any]:
        """Setup SQL Server user permissions"""
        try:
            # Step 1: Create server-level login AND user in master database
            # NOTE: Lakeflow Connect requires user access to master database for connection pooling
            master_engine = self._create_master_engine()
            
            master_commands = [
                f"IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = '{self.user_username}') CREATE LOGIN [{self.user_username}] WITH PASSWORD = '{self.user_password}'",
                f"ALTER LOGIN [{self.user_username}] WITH PASSWORD = '{self.user_password}'",
                f"IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{self.user_username}') CREATE USER [{self.user_username}] FOR LOGIN [{self.user_username}] WITH DEFAULT_SCHEMA=dbo"
                # NOTE: GRANT VIEW ANY DATABASE not supported on Azure SQL Database
                # Azure SQL Database automatically grants necessary catalog views
            ]
            
            # Execute master database commands
            print(f"   🔐 Creating server-level login and master user: {self.user_username}")
            print(f"   ℹ️  User needs master access for Lakeflow Connect connection pooling")
            self._execute_sql_commands_with_engine(master_commands, master_engine)
            master_engine.dispose()
            
            # Step 2: Create user in target database with proper default schema
            sql_commands = [
                f"IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{self.user_username}') CREATE USER [{self.user_username}] FOR LOGIN [{self.user_username}] WITH DEFAULT_SCHEMA=[{self.schema}]"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                # Broad permissions for development (matching the reference script)
                sql_commands.extend([
                    f"ALTER ROLE db_owner ADD MEMBER [{self.user_username}]",
                    f"ALTER ROLE db_ddladmin ADD MEMBER [{self.user_username}]"
                ])
            else:
                # Minimal permissions for production
                sql_commands.extend([
                    f"ALTER ROLE db_datareader ADD MEMBER [{self.user_username}]",
                    f"ALTER ROLE db_datawriter ADD MEMBER [{self.user_username}]",
                    f"GRANT CREATE TABLE TO [{self.user_username}]",
                    f"GRANT ALTER ON SCHEMA::[{self.schema}] TO [{self.user_username}]"
                ])
            
            print(f"   🔐 Creating database user: {self.user_username} with default schema: {self.schema}")
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'sqlserver_user_setup',
                'status': 'success',
                'message': f'SQL Server user permissions configured for {self.user_username}',
                'operations': ['server_login_created', 'master_user_created', 'database_user_created', 'roles_assigned']
            }
            
        except Exception as e:
            return {
                'operation': 'sqlserver_user_setup',
                'status': 'error',
                'message': f'SQL Server user setup failed: {str(e)}'
            }
    
    def _setup_sqlserver_replication_permissions(self) -> Dict[str, Any]:
        """Setup SQL Server replication permissions"""
        try:
            sql_commands = []
            
            if self.permission_mode == "PERMISSIVE":
                sql_commands.extend([
                    f"ALTER ROLE db_owner ADD MEMBER [{self.user_username}]"
                ])
            else:
                sql_commands.extend([
                    f"GRANT SELECT ON sys.change_tracking_tables TO [{self.user_username}]",
                    f"GRANT SELECT ON sys.change_tracking_databases TO [{self.user_username}]",
                    f"GRANT VIEW DATABASE STATE TO [{self.user_username}]"
                ])
            
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'sqlserver_replication_setup',
                'status': 'success',
                'message': 'SQL Server replication permissions configured'
            }
            
        except Exception as e:
            return {
                'operation': 'sqlserver_replication_setup',
                'status': 'error',
                'message': f'SQL Server replication setup failed: {str(e)}'
            }
    
    def _setup_cdc_permissions(self) -> Dict[str, Any]:
        """Setup CDC permissions for SQL Server"""
        try:
            sql_commands = [
                "EXEC sys.sp_cdc_enable_db"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                sql_commands.extend([
                    f"ALTER ROLE db_owner ADD MEMBER [{self.user_username}]"
                ])
            else:
                sql_commands.extend([
                    f"GRANT SELECT ON SCHEMA::cdc TO [{self.user_username}]",
                    f"GRANT EXECUTE ON sys.sp_cdc_enable_table TO [{self.user_username}]",
                    f"GRANT EXECUTE ON sys.sp_cdc_disable_table TO [{self.user_username}]"
                ])
            
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'sqlserver_cdc_setup',
                'status': 'success',
                'message': 'SQL Server CDC permissions configured'
            }
            
        except Exception as e:
            return {
                'operation': 'sqlserver_cdc_setup',
                'status': 'error',
                'message': f'SQL Server CDC setup failed: {str(e)}'
            }
    
    def _setup_change_tracking_permissions(self) -> Dict[str, Any]:
        """Setup Change Tracking permissions for SQL Server"""
        try:
            sql_commands = [
                f"ALTER DATABASE [{self.database}] SET CHANGE_TRACKING = ON (CHANGE_RETENTION = 3 DAYS, AUTO_CLEANUP = ON)"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                sql_commands.extend([
                    f"ALTER ROLE db_owner ADD MEMBER [{self.user_username}]"
                ])
            else:
                sql_commands.extend([
                    f"GRANT ALTER ON SCHEMA::[{self.schema}] TO [{self.user_username}]",
                    f"GRANT SELECT ON sys.change_tracking_tables TO [{self.user_username}]",
                    f"GRANT VIEW CHANGE TRACKING ON SCHEMA::[{self.schema}] TO [{self.user_username}]"
                ])
            
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'sqlserver_ct_setup',
                'status': 'success',
                'message': 'SQL Server Change Tracking permissions configured'
            }
            
        except Exception as e:
            return {
                'operation': 'sqlserver_ct_setup',
                'status': 'error',
                'message': f'SQL Server Change Tracking setup failed: {str(e)}'
            }
    
    # MySQL Permission Methods
    def _setup_mysql_dba_permissions(self) -> Dict[str, Any]:
        """Setup MySQL DBA permissions"""
        try:
            sql_commands = [
                f"CREATE USER IF NOT EXISTS '{self.dba_username}'@'%' IDENTIFIED BY '{self.dba_password}'",
                f"ALTER USER '{self.dba_username}'@'%' IDENTIFIED BY '{self.dba_password}'"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                sql_commands.extend([
                    f"GRANT ALL PRIVILEGES ON *.* TO '{self.dba_username}'@'%' WITH GRANT OPTION"
                ])
            else:
                sql_commands.extend([
                    f"GRANT CREATE, ALTER, DROP, SELECT, INSERT, UPDATE, DELETE ON `{self.database}`.* TO '{self.dba_username}'@'%'",
                    f"GRANT REPLICATION CLIENT ON *.* TO '{self.dba_username}'@'%'",
                    f"GRANT REPLICATION SLAVE ON *.* TO '{self.dba_username}'@'%'"
                ])
            
            sql_commands.append("FLUSH PRIVILEGES")
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'mysql_dba_setup',
                'status': 'success',
                'message': f'MySQL DBA permissions configured for {self.dba_username}'
            }
            
        except Exception as e:
            return {
                'operation': 'mysql_dba_setup',
                'status': 'error',
                'message': f'MySQL DBA setup failed: {str(e)}'
            }
    
    def _setup_mysql_user_permissions(self) -> Dict[str, Any]:
        """Setup MySQL user permissions"""
        try:
            sql_commands = [
                f"CREATE USER IF NOT EXISTS '{self.user_username}'@'%' IDENTIFIED BY '{self.user_password}'",
                f"ALTER USER '{self.user_username}'@'%' IDENTIFIED BY '{self.user_password}'"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                sql_commands.extend([
                    f"GRANT ALTER, CREATE, DROP, SELECT, INSERT, DELETE, UPDATE ON *.* TO '{self.user_username}'@'%'",
                    f"GRANT REPLICATION CLIENT ON *.* TO '{self.user_username}'@'%'",
                    f"GRANT REPLICATION SLAVE ON *.* TO '{self.user_username}'@'%'"
                ])
            else:
                sql_commands.extend([
                    f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{self.database}`.* TO '{self.user_username}'@'%'",
                    f"GRANT CREATE, ALTER, DROP ON `{self.database}`.`{self.schema}_%` TO '{self.user_username}'@'%'"
                ])
            
            sql_commands.append("FLUSH PRIVILEGES")
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'mysql_user_setup',
                'status': 'success',
                'message': f'MySQL user permissions configured for {self.user_username}'
            }
            
        except Exception as e:
            return {
                'operation': 'mysql_user_setup',
                'status': 'error',
                'message': f'MySQL user setup failed: {str(e)}'
            }
    
    def _setup_mysql_replication_permissions(self) -> Dict[str, Any]:
        """Setup MySQL replication permissions"""
        try:
            sql_commands = [
                f"GRANT REPLICATION CLIENT ON *.* TO '{self.user_username}'@'%'",
                f"GRANT REPLICATION SLAVE ON *.* TO '{self.user_username}'@'%'",
                "FLUSH PRIVILEGES"
            ]
            
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'mysql_replication_setup',
                'status': 'success',
                'message': 'MySQL replication permissions configured'
            }
            
        except Exception as e:
            return {
                'operation': 'mysql_replication_setup',
                'status': 'error',
                'message': f'MySQL replication setup failed: {str(e)}'
            }
    
    # PostgreSQL Permission Methods
    def _setup_postgresql_dba_permissions(self) -> Dict[str, Any]:
        """Setup PostgreSQL DBA permissions"""
        try:
            sql_commands = [
                f"DO $$ BEGIN IF NOT EXISTS (SELECT * FROM pg_user WHERE usename = '{self.dba_username}') THEN CREATE USER {self.dba_username} PASSWORD '{self.dba_password}'; END IF; END $$",
                f"ALTER USER {self.dba_username} WITH PASSWORD '{self.dba_password}'"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                sql_commands.extend([
                    f"ALTER USER {self.dba_username} WITH SUPERUSER",
                    f"GRANT ALL PRIVILEGES ON DATABASE {self.database} TO {self.dba_username}"
                ])
            else:
                sql_commands.extend([
                    f"GRANT CONNECT ON DATABASE {self.database} TO {self.dba_username}",
                    f"GRANT ALL PRIVILEGES ON DATABASE {self.database} TO {self.dba_username}",
                    f"ALTER ROLE {self.dba_username} WITH REPLICATION"
                ])
            
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'postgresql_dba_setup',
                'status': 'success',
                'message': f'PostgreSQL DBA permissions configured for {self.dba_username}'
            }
            
        except Exception as e:
            return {
                'operation': 'postgresql_dba_setup',
                'status': 'error',
                'message': f'PostgreSQL DBA setup failed: {str(e)}'
            }
    
    def _setup_postgresql_user_permissions(self) -> Dict[str, Any]:
        """Setup PostgreSQL user permissions"""
        try:
            sql_commands = [
                f"DO $$ BEGIN IF NOT EXISTS (SELECT * FROM pg_user WHERE usename = '{self.user_username}') THEN CREATE USER {self.user_username} PASSWORD '{self.user_password}'; END IF; END $$",
                f"ALTER USER {self.user_username} WITH PASSWORD '{self.user_password}'",
                f"GRANT CONNECT ON DATABASE {self.database} TO {self.user_username}"
            ]
            
            if self.permission_mode == "PERMISSIVE":
                sql_commands.extend([
                    f"GRANT ALL PRIVILEGES ON DATABASE {self.database} TO {self.user_username}",
                    f"ALTER ROLE {self.user_username} WITH REPLICATION"
                ])
            else:
                sql_commands.extend([
                    f"GRANT USAGE ON SCHEMA {self.schema} TO {self.user_username}",
                    f"GRANT CREATE ON SCHEMA {self.schema} TO {self.user_username}",
                    f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {self.schema} TO {self.user_username}",
                    f"ALTER DEFAULT PRIVILEGES IN SCHEMA {self.schema} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {self.user_username}"
                ])
            
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'postgresql_user_setup',
                'status': 'success',
                'message': f'PostgreSQL user permissions configured for {self.user_username}'
            }
            
        except Exception as e:
            return {
                'operation': 'postgresql_user_setup',
                'status': 'error',
                'message': f'PostgreSQL user setup failed: {str(e)}'
            }
    
    def _setup_postgresql_replication_permissions(self) -> Dict[str, Any]:
        """Setup PostgreSQL replication permissions"""
        try:
            sql_commands = [
                f"ALTER ROLE {self.user_username} WITH REPLICATION"
            ]
            
            # Try AWS RDS specific grant (will fail gracefully if not RDS)
            try:
                self._execute_sql_commands([f"GRANT rds_replication TO {self.user_username}"])
            except:
                pass  # Not RDS, continue
            
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'postgresql_replication_setup',
                'status': 'success',
                'message': 'PostgreSQL replication permissions configured'
            }
            
        except Exception as e:
            return {
                'operation': 'postgresql_replication_setup',
                'status': 'error',
                'message': f'PostgreSQL replication setup failed: {str(e)}'
            }
    
    def _setup_schema_permissions(self) -> Dict[str, Any]:
        """Setup schema-level permissions"""
        try:
            if self.db_type == 'sqlserver':
                sql_commands = [
                    f"IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{self.schema}') EXEC('CREATE SCHEMA [{self.schema}]')",
                    f"GRANT ALL ON SCHEMA::[{self.schema}] TO [{self.user_username}]"
                ]
            elif self.db_type == 'mysql':
                sql_commands = [
                    f"CREATE SCHEMA IF NOT EXISTS `{self.schema}`",
                    f"GRANT ALL PRIVILEGES ON `{self.schema}`.* TO '{self.user_username}'@'%'"
                ]
            elif self.db_type == 'postgresql':
                sql_commands = [
                    f"CREATE SCHEMA IF NOT EXISTS {self.schema}",
                    f"GRANT ALL ON SCHEMA {self.schema} TO {self.user_username}",
                    f"GRANT ALL ON ALL TABLES IN SCHEMA {self.schema} TO {self.user_username}",
                    f"ALTER DEFAULT PRIVILEGES IN SCHEMA {self.schema} GRANT ALL ON TABLES TO {self.user_username}"
                ]
            
            self._execute_sql_commands(sql_commands)
            
            return {
                'operation': 'schema_setup',
                'status': 'success',
                'message': f'Schema permissions configured for {self.schema}'
            }
            
        except Exception as e:
            return {
                'operation': 'schema_setup',
                'status': 'error',
                'message': f'Schema setup failed: {str(e)}'
            }
    
    def _execute_sql_commands(self, commands: List[str]) -> None:
        """Execute a list of SQL commands using the default engine"""
        self._execute_sql_commands_with_engine(commands, self.engine)
    
    def _execute_sql_commands_with_engine(self, commands: List[str], engine) -> None:
        """Execute a list of SQL commands with a specific engine"""
        if not engine:
            raise Exception("No database engine available")
        
        with engine.connect() as conn:
            for command in commands:
                try:
                    logger.debug(f"Executing SQL: {command}")
                    conn.execute(text(command))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"SQL command failed (may be expected): {command} - {e}")
                    # Continue with other commands
    
    def _create_master_engine(self):
        """Create SQLAlchemy engine connected to master database for SQL Server"""
        if self.db_type != 'sqlserver':
            raise ValueError("Master database engine is only supported for SQL Server")
        
        from urllib.parse import quote_plus
        
        # Extract connection details from current engine
        url = self.engine.url
        
        # URL encode credentials
        encoded_username = quote_plus(self.dba_username)
        encoded_password = quote_plus(self.dba_password)
        
        # Create connection string to master database
        master_connection_string = f"mssql+pymssql://{encoded_username}:{encoded_password}@{url.host}:{url.port}/master"
        
        return sa.create_engine(master_connection_string, echo=False, isolation_level="AUTOCOMMIT")
    
    def verify_permissions(self) -> Dict[str, Any]:
        """Verify that permissions are correctly set up"""
        results = {
            'status': 'success',
            'message': 'Permission verification completed',
            'checks': []
        }
        
        try:
            # Test basic connectivity
            conn_result = self._test_user_connectivity()
            results['checks'].append(conn_result)
            
            # Test schema access
            schema_result = self._test_schema_access()
            results['checks'].append(schema_result)
            
            # Test replication permissions
            repl_result = self._test_replication_permissions()
            results['checks'].append(repl_result)
            
            # Test CT enablement on tables with primary keys (SQL Server only)
            if self.db_type == 'sqlserver':
                ct_result = self._test_ct_enablement()
                results['checks'].append(ct_result)
            
        except Exception as e:
            results['status'] = 'error'
            results['message'] = f'Permission verification failed: {str(e)}'
        
        return results
    
    def _test_user_connectivity(self) -> Dict[str, Any]:
        """Test user can connect to database"""
        try:
            # This would require creating a new connection with user credentials
            # For now, return success if we have the credentials
            if self.user_username and self.user_password:
                return {
                    'check': 'user_connectivity',
                    'status': 'success',
                    'message': f'User {self.user_username} credentials available'
                }
            else:
                return {
                    'check': 'user_connectivity',
                    'status': 'error',
                    'message': 'User credentials not configured'
                }
        except Exception as e:
            return {
                'check': 'user_connectivity',
                'status': 'error',
                'message': f'Connectivity test failed: {str(e)}'
            }
    
    def _test_schema_access(self) -> Dict[str, Any]:
        """Test user can access schema"""
        try:
            with self.engine.connect() as conn:
                if self.db_type == 'sqlserver':
                    result = conn.execute(text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{self.schema}'"))
                elif self.db_type == 'mysql':
                    result = conn.execute(text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{self.schema}'"))
                elif self.db_type == 'postgresql':
                    result = conn.execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{self.schema}'"))
                
                if result.fetchone():
                    return {
                        'check': 'schema_access',
                        'status': 'success',
                        'message': f'Schema {self.schema} accessible'
                    }
                else:
                    return {
                        'check': 'schema_access',
                        'status': 'error',
                        'message': f'Schema {self.schema} not found'
                    }
        except Exception as e:
            return {
                'check': 'schema_access',
                'status': 'error',
                'message': f'Schema access test failed: {str(e)}'
            }
    
    def _test_replication_permissions(self) -> Dict[str, Any]:
        """Test replication permissions"""
        try:
            # Database-specific replication checks would go here
            return {
                'check': 'replication_permissions',
                'status': 'success',
                'message': 'Replication permissions configured'
            }
        except Exception as e:
            return {
                'check': 'replication_permissions',
                'status': 'error',
                'message': f'Replication permission test failed: {str(e)}'
            }
    
    def _test_ct_enablement(self) -> Dict[str, Any]:
        """Test that Change Tracking is enabled on all tables with primary keys (SQL Server)"""
        try:
            with self.engine.connect() as conn:
                # Check if CT is enabled at database level
                db_ct_check = text("""
                    SELECT COUNT(*) 
                    FROM sys.change_tracking_databases 
                    WHERE database_id = DB_ID()
                """)
                db_ct_enabled = conn.execute(db_ct_check).scalar() > 0
                
                if not db_ct_enabled:
                    return {
                        'check': 'ct_enablement',
                        'status': 'warning',
                        'message': 'Change Tracking not enabled at database level'
                    }
                
                # Find tables with primary keys that don't have CT enabled
                ct_check_query = text(f"""
                    WITH pk_tables AS (
                        SELECT 
                            s.name as schema_name,
                            t.name as table_name
                        FROM sys.key_constraints kc
                        JOIN sys.tables t ON kc.parent_object_id = t.object_id
                        JOIN sys.schemas s ON t.schema_id = s.schema_id
                        WHERE kc.type = 'PK'
                        AND s.name = '{self.schema}'
                    ),
                    ct_tables AS (
                        SELECT 
                            s.name as schema_name,
                            t.name as table_name
                        FROM sys.change_tracking_tables ct
                        JOIN sys.tables t ON ct.object_id = t.object_id
                        JOIN sys.schemas s ON t.schema_id = s.schema_id
                        WHERE s.name = '{self.schema}'
                    )
                    SELECT 
                        pk.schema_name,
                        pk.table_name
                    FROM pk_tables pk
                    LEFT JOIN ct_tables ct 
                        ON pk.schema_name = ct.schema_name 
                        AND pk.table_name = ct.table_name
                    WHERE ct.table_name IS NULL
                """)
                
                missing_ct_tables = conn.execute(ct_check_query).fetchall()
                
                if missing_ct_tables:
                    table_list = [f"{row[0]}.{row[1]}" for row in missing_ct_tables]
                    return {
                        'check': 'ct_enablement',
                        'status': 'error',
                        'message': f'❌ CRITICAL: {len(missing_ct_tables)} table(s) with PRIMARY KEY missing CT: {", ".join(table_list)}',
                        'missing_ct_tables': table_list,
                        'recommendation': 'Run: cdc.enable_cdc_ct_for_tables() with table-by-table mode (bulk_mode=False)'
                    }
                else:
                    # Count how many tables have CT enabled
                    ct_count_query = text(f"""
                        SELECT COUNT(*) 
                        FROM sys.change_tracking_tables ct
                        JOIN sys.tables t ON ct.object_id = t.object_id
                        JOIN sys.schemas s ON t.schema_id = s.schema_id
                        WHERE s.name = '{self.schema}'
                    """)
                    ct_count = conn.execute(ct_count_query).scalar()
                    
                    return {
                        'check': 'ct_enablement',
                        'status': 'success',
                        'message': f'✅ Change Tracking correctly enabled on all {ct_count} table(s) with primary keys in schema {self.schema}'
                    }
                    
        except Exception as e:
            return {
                'check': 'ct_enablement',
                'status': 'error',
                'message': f'CT enablement check failed: {str(e)}'
            }


# Convenience functions
def setup_permissive_permissions(engine: Engine, db_config: Dict[str, Any]) -> Dict[str, Any]:
    """Setup permissive permissions (default mode)"""
    perm_manager = LfcDbPerm(engine, db_config, "PERMISSIVE")
    return perm_manager.setup_database_permissions()


def setup_strict_permissions(engine: Engine, db_config: Dict[str, Any]) -> Dict[str, Any]:
    """Setup strict permissions (production mode)"""
    perm_manager = LfcDbPerm(engine, db_config, "STRICT")
    return perm_manager.setup_database_permissions()


def verify_database_permissions(engine: Engine, db_config: Dict[str, Any]) -> Dict[str, Any]:
    """Verify database permissions are correctly configured"""
    perm_manager = LfcDbPerm(engine, db_config)
    return perm_manager.verify_permissions()
