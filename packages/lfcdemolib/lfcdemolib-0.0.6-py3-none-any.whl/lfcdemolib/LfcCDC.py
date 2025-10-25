"""
LfcCDC - LFC Change Data Capture operations

This module provides CDC (Change Data Capture) and CT (Change Tracking) operations
for SQL Server and PostgreSQL databases. Automatically enables/disables CDC/CT
based on table structure and database type.

This is a thin wrapper that delegates to database-specific providers for easier
maintenance and extensibility.

Key Features:
- SQL Server: CDC for tables without primary keys, CT for tables with primary keys
- PostgreSQL: Logical replication setup for CDC functionality
- Automatic enable/disable when tables are created/dropped
- Primary key detection for appropriate CDC/CT selection
- Database-specific implementation handling via provider pattern
"""

import sqlalchemy as sa
from typing import Dict, List, Optional, Literal


class LfcCDC:
    """LfcCDC - LFC Change Data Capture operations
    
    Thin wrapper that delegates to database-specific providers.
    Maintains backward compatibility while using the provider pattern internally.
    
    SQL Server:
    - CDC (Change Data Capture): For tables without primary keys
    - CT (Change Tracking): For tables with primary keys (CT requires a primary key)
    
    PostgreSQL:
    - Logical Replication: For CDC functionality
    - WAL (Write-Ahead Logging): Configuration for change capture
    """
    
    def __init__(self, engine, schema: str = None, replication_filter: Literal['both', 'pk_only', 'no_pk_only'] = 'both', dba_engine=None, secrets_json=None, shared_state=None, bulk_mode: bool = False):
        """Initialize LfcCDC with database engine and optional schema
        
        Args:
            engine: SQLAlchemy engine for database connection
            schema: Optional schema name for table operations
            replication_filter: Control which tables to enable replication for:
                - 'both': Enable for all tables (default)
                - 'pk_only': Enable only for tables with primary keys
                - 'no_pk_only': Enable only for tables without primary keys
            dba_engine: Optional DBA engine for administrative operations (CDC/CT setup)
                       If not provided, uses the main engine
            secrets_json: Optional secrets dictionary for database connection details
            shared_state: Optional shared state dictionary for coordinating between modules
            bulk_mode: If True, use bulk operations for CDC/CT enable/disable (faster but less reliable)
                      If False (default), use table-by-table operations (slower but more reliable)
        """
        self.engine = engine
        self.dba_engine = dba_engine or engine
        self.shared_state = shared_state or {}
        self.bulk_mode = bulk_mode
        
        # Schema should always be passed explicitly
        if schema is None:
            print(f"⚠️  WARNING: LfcCDC initialized without schema parameter!")
            print(f"   Schema will be set by provider's default (lfcddemo)")
            print(f"   This should be passed explicitly from SimpleTest or calling code.")
            print(f"   Example: LfcCDC(engine, schema='lfcddemo')")
        
        self.schema = schema
        self.dialect = engine.dialect.name
        self.replication_filter = replication_filter
        self.secrets_json = secrets_json
        
        # Log enablement mode
        if bulk_mode:
            print(f"⚠️  CDC/CT Bulk Mode: ENABLED (faster, may miss some tables)")
        else:
            print(f"✅ CDC/CT Table-by-Table Mode: ENABLED (slower, more reliable)")
        
        # Create appropriate provider based on database type (lazy import to avoid circular dependencies)
        if self.dialect == 'mssql':
            from .LfcCDCSqlServer import SqlServerCDCProvider
            self.provider = SqlServerCDCProvider(
                engine=engine,
                dba_engine=self.dba_engine,
                db_type='sqlserver',
                schema=schema,
                secrets_json=secrets_json
            )
        elif self.dialect == 'postgresql':
            from .LfcCDCPostgreSQL import PostgreSQLCDCProvider
            self.provider = PostgreSQLCDCProvider(
                engine=engine,
                dba_engine=self.dba_engine,
                db_type='postgresql',
                schema=schema,
                secrets_json=secrets_json
            )
        else:
            print(f"⚠️ CDC operations not supported for {self.dialect}. Supported: SQL Server, PostgreSQL")
            self.provider = None
        
        # Expose provider attributes for backward compatibility
        if self.provider:
            self.cdc_supported = self.provider.cdc_supported
            self.cdc_failure_reason = self.provider.cdc_failure_reason
            self.db_cdc_enabled = self.provider.db_cdc_enabled
            self.db_ct_enabled = self.provider.db_ct_enabled
            # Update schema to match provider's resolved schema
            self.schema = self.provider.schema
    
    @classmethod
    def create_dba_engine(cls, secrets_json):
        """Create a DBA engine for administrative operations
        
        Args:
            secrets_json: Dictionary containing connection credentials including DBA credentials
            
        Returns:
            sqlalchemy.Engine: DBA engine connected to master database
        """
        import urllib.parse
        
        # Use DBA credentials from v2 format (dba.user, dba.password)
        # Fall back to regular credentials if DBA not available
        dba_obj = secrets_json.get("dba", {})
        dba_user = dba_obj.get("user") or secrets_json.get("user")
        dba_password = dba_obj.get("password") or secrets_json.get("password")
        
        # Get db_type from v2 format
        db_type = secrets_json.get("db_type", "sqlserver")
        if db_type is None or db_type == "": 
            db_type = 'sqlserver'
        else: 
            db_type = db_type.casefold()

        # Driver mapping
        DRIVERS = {
            "mysql": "mysql+pymysql",
            "postgresql": "postgresql+psycopg2", 
            "sqlserver": "mssql+pymssql",
            "oracle": "oracle+oracledb",
            "sqlite": "sqlite"
        }
        
        driver = DRIVERS.get(db_type)
        encoded_username = urllib.parse.quote_plus(dba_user)
        encoded_password = urllib.parse.quote_plus(dba_password)
        
        # For SQL Server, connect to master database for administrative operations
        if db_type == 'sqlserver':
            catalog = 'master'
        else:
            catalog = secrets_json["catalog"]
                
        connection_string = f"{driver}://{encoded_username}:{encoded_password}@{secrets_json['host_fqdn']}:{secrets_json['port']}/{catalog}"
        dba_engine = sa.create_engine(connection_string, echo=False, isolation_level="AUTOCOMMIT")
        
        print(f"🔗 Created DBA engine for {db_type} (connected to {catalog} database)")
        return dba_engine
    
    # Delegate all operations to the provider
    
    def is_cdc_supported(self) -> bool:
        """Check if non-PK replication (CDC) is supported on this database instance"""
        if not self.provider:
            return False
        return self.provider.is_cdc_supported()
    
    def get_cdc_failure_reason(self) -> str:
        """Get the reason why non-PK replication (CDC) is not supported"""
        if not self.provider:
            return "Database type not supported"
        return self.provider.get_cdc_failure_reason()
    
    def _test_cdc_support(self) -> bool:
        """Test if CDC is supported on this database instance
        
        This method is called by SimpleTest and SimpleDDL to determine
        if CDC is available on the database tier.
        
        Returns:
            bool: True if CDC is supported, False otherwise
        """
        if not self.provider:
            return False
        
        # If already tested, return cached result
        if self.provider.cdc_supported is not None:
            return self.provider.cdc_supported
        
        # For SQL Server, test CDC support
        if self.dialect == 'mssql':
            try:
                # Get the target database name
                import sqlalchemy as sa
                target_db_query = sa.text("SELECT DB_NAME()")
                with self.engine.connect() as conn:
                    target_db = conn.execute(target_db_query).scalar()
                
                # Create a target database engine with DBA credentials
                # Azure SQL Database doesn't support USE statement, so we must connect directly
                if hasattr(self.provider, '_create_target_database_engine'):
                    target_engine = self.provider._create_target_database_engine(target_db)
                else:
                    # Fallback: use dba_engine if provider doesn't have this method
                    target_engine = self.dba_engine
                
                try:
                    # Try to enable CDC at database level (this will fail on unsupported tiers)
                    with target_engine.connect() as target_conn:
                        enable_db_cdc = sa.text("EXEC sys.sp_cdc_enable_db")
                        target_conn.execute(enable_db_cdc)
                        target_conn.commit()
                    
                    # CRITICAL: Verify CDC is actually enabled
                    # The sp_cdc_enable_db command can succeed but CDC might not be enabled
                    # (e.g., on Azure SQL Database without SQL Agent)
                    with self.engine.connect() as conn:
                        check_cdc = sa.text("SELECT is_cdc_enabled FROM sys.databases WHERE name = DB_NAME()")
                        is_enabled = conn.execute(check_cdc).scalar()
                        
                        if is_enabled:
                            # CDC is actually enabled
                            self.provider.cdc_supported = True
                            if hasattr(self, 'shared_state'):
                                self.shared_state['non_pk_replication_supported'] = True
                            return True
                        else:
                            # Command succeeded but CDC not enabled (Azure SQL Database limitation)
                            self.provider.cdc_supported = False
                            self.provider.cdc_failure_reason = "CDC not supported on Azure SQL Database (requires SQL Agent)"
                            if hasattr(self, 'shared_state'):
                                self.shared_state['non_pk_replication_supported'] = False
                                self.shared_state['non_pk_replication_failure_reason'] = self.provider.cdc_failure_reason
                            return False
                finally:
                    if hasattr(self.provider, '_create_target_database_engine'):
                        # Only dispose if we created a new engine
                        target_engine.dispose()
                    
            except Exception as e:
                error_msg = str(e)
                if "22871" in error_msg or "not supported" in error_msg.lower():
                    # CDC not supported on this tier
                    self.provider.cdc_supported = False
                    self.provider.cdc_failure_reason = "CDC not supported on this database tier (Basic/Standard)"
                    if hasattr(self, 'shared_state'):
                        self.shared_state['non_pk_replication_supported'] = False
                        self.shared_state['non_pk_replication_failure_reason'] = self.provider.cdc_failure_reason
                    return False
                else:
                    # Other error - check if CDC is enabled despite error
                    try:
                        with self.engine.connect() as conn:
                            check_cdc = sa.text("SELECT is_cdc_enabled FROM sys.databases WHERE name = DB_NAME()")
                            is_enabled = conn.execute(check_cdc).scalar()
                            self.provider.cdc_supported = bool(is_enabled)
                            return bool(is_enabled)
                    except:
                        # Can't determine, assume not supported
                        self.provider.cdc_supported = False
                        return False
        else:
            # For non-SQL Server, assume CDC is supported
            self.provider.cdc_supported = True
            return True
    
    def enable_cdc_for_table(self, table_name: str, has_primary_key: bool = None) -> Dict[str, any]:
        """Enable CDC or CT for a table based on its structure and database type
        
        Args:
            table_name: Name of the table to enable CDC/CT for
            has_primary_key: Optional primary key status. If None, will query database to determine
            
        Returns:
            dict: Result of the CDC/CT enable operation
        """
        if not self.provider:
            return {
                'table_name': table_name,
                'status': 'unsupported',
                'message': f'CDC not supported for {self.dialect}'
            }
        
        # Check replication filter
        if has_primary_key is None:
            # Let provider determine PK status
            pass
        elif self.replication_filter == 'pk_only' and not has_primary_key:
            return {
                'table_name': table_name,
                'status': 'skipped',
                'message': f'Skipped: Table has no primary key and replication_filter is "pk_only"',
                'has_primary_key': has_primary_key,
                'replication_filter': self.replication_filter
            }
        elif self.replication_filter == 'no_pk_only' and has_primary_key:
            return {
                'table_name': table_name,
                'status': 'skipped',
                'message': f'Skipped: Table has primary key and replication_filter is "no_pk_only"',
                'has_primary_key': has_primary_key,
                'replication_filter': self.replication_filter
            }
        
        return self.provider.enable_cdc_for_table(table_name, has_primary_key)
    
    def disable_cdc_for_table(self, table_name: str) -> Dict[str, any]:
        """Disable CDC or CT for a table before dropping
        
        Args:
            table_name: Name of the table to disable CDC/CT for
            
        Returns:
            dict: Result of the CDC/CT disable operation
        """
        if not self.provider:
            return {
                'table_name': table_name,
                'status': 'unsupported',
                'message': f'CDC not supported for {self.dialect}'
            }
        
        return self.provider.disable_cdc_for_table(table_name)
    
    def enable_cdc_for_tables(self, table_names: List[str], primary_key_status: Dict[str, bool] = None) -> Dict[str, Dict[str, any]]:
        """Enable CDC/CT for multiple tables
        
        Args:
            table_names: List of table names to enable CDC/CT for
            primary_key_status: Optional dict mapping table names to their primary key status
            
        Returns:
            dict: Results for each table (includes skipped tables based on replication_filter)
        """
        results = {}
        skipped_count = 0
        enabled_count = 0
        
        for table_name in table_names:
            has_pk = None
            if primary_key_status and table_name in primary_key_status:
                has_pk = primary_key_status[table_name]
            
            result = self.enable_cdc_for_table(table_name, has_pk)
            results[table_name] = result
            
            if result['status'] == 'skipped':
                skipped_count += 1
            elif result['status'] in ['enabled', 'warning']:
                enabled_count += 1
        
        # Add summary information
        results['_summary'] = {
            'total_tables': len(table_names),
            'enabled_count': enabled_count,
            'skipped_count': skipped_count,
            'replication_filter': self.replication_filter
        }
        
        return results
    
    def disable_cdc_for_tables(self, table_names: List[str]) -> Dict[str, Dict[str, any]]:
        """Disable CDC/CT for multiple tables
        
        Args:
            table_names: List of table names to disable CDC/CT for
            
        Returns:
            dict: Results for each table
        """
        results = {}
        for table_name in table_names:
            results[table_name] = self.disable_cdc_for_table(table_name)
        return results
    
    def get_cdc_status(self, table_name: str) -> Dict[str, any]:
        """Get CDC/CT status for a table
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            dict: CDC/CT status information
        """
        if not self.provider:
            return {
                'table_name': table_name,
                'status': 'unsupported',
                'message': f'CDC status check not supported for {self.dialect}'
            }
        
        return self.provider.get_cdc_status(table_name)
    
    def cleanup_orphaned_cdc_instances(self) -> Dict[str, any]:
        """Clean up orphaned CDC capture instances for non-existent tables
        
        Returns:
            dict: Summary of cleanup operations
        """
        if not self.provider:
            return {
                'status': 'unsupported',
                'message': f'CDC cleanup not supported for {self.dialect}'
            }
        
        return self.provider.cleanup_orphaned_cdc_instances()
    
    def enable_cdc_ct_for_tables(self, table_names: List[str], schema_name: str = None, mode: str = 'BOTH') -> Dict[str, any]:
        """Enable CDC/CT for multiple tables using bulk or table-by-table mode
        
        This method respects the bulk_mode setting:
        - If bulk_mode=False (default): Uses reliable table-by-table operations
        - If bulk_mode=True: Uses faster bulk operations (may miss some tables)
        
        Args:
            table_names: List of table names to enable CDC/CT for
            schema_name: Schema name (defaults to self.schema)
            mode: 'CDC' (only CDC), 'CT' (only CT), or 'BOTH' (default)
            
        Returns:
            dict: Results including counts and per-table status
        """
        schema_name = schema_name or self.schema
        
        if self.bulk_mode:
            # Use bulk operation (faster but less reliable)
            print(f"📦 Using BULK mode for {len(table_names)} tables in schema '{schema_name}'")
            return self.bulk_enable_cdc_ct_for_schema(
                schema_name=schema_name,
                table_filter=table_names,
                mode=mode,
                dry_run=False
            )
        else:
            # Use table-by-table operation (slower but more reliable)
            print(f"🔧 Using TABLE-BY-TABLE mode for {len(table_names)} tables in schema '{schema_name}'")
            
            results = {
                'status': 'completed',
                'mode': 'table_by_table',
                'total_tables': len(table_names),
                'cdc_enabled_count': 0,
                'ct_enabled_count': 0,
                'cdc_enabled_already_count': 0,
                'ct_enabled_already_count': 0,
                'errors': [],
                'tables': []
            }
            
            for table_name in table_names:
                print(f"   Processing table: {table_name}")
                try:
                    result = self.enable_cdc_for_table(table_name)
                    
                    if result.get('status') == 'enabled':
                        method = result.get('method', 'unknown')
                        if 'CDC' in method:
                            results['cdc_enabled_count'] += 1
                        elif 'CT' in method or 'Change Tracking' in method:
                            results['ct_enabled_count'] += 1
                        print(f"      ✅ Enabled: {method}")
                    elif result.get('status') == 'already_enabled':
                        method = result.get('method', 'unknown')
                        if 'CDC' in method:
                            results['cdc_enabled_already_count'] += 1
                        elif 'CT' in method or 'Change Tracking' in method:
                            results['ct_enabled_already_count'] += 1
                        print(f"      ℹ️  Already enabled: {method}")
                    else:
                        error_msg = f"Failed to enable for {table_name}: {result.get('message')}"
                        results['errors'].append(error_msg)
                        print(f"      ❌ {error_msg}")
                    
                    results['tables'].append({
                        'table': table_name,
                        'status': result.get('status'),
                        'method': result.get('method'),
                        'has_pk': result.get('has_primary_key')
                    })
                    
                except Exception as e:
                    error_msg = f"Error processing {table_name}: {str(e)}"
                    results['errors'].append(error_msg)
                    print(f"      ❌ {error_msg}")
            
            print(f"\n📊 Table-by-Table Results:")
            print(f"   CDC enabled: {results['cdc_enabled_count']} (already: {results['cdc_enabled_already_count']})")
            print(f"   CT enabled: {results['ct_enabled_count']} (already: {results['ct_enabled_already_count']})")
            if results['errors']:
                print(f"   ⚠️  Errors: {len(results['errors'])}")
            
            return results
    
    def bulk_enable_cdc_ct_for_schema(self, schema_name: str = None, table_filter: List[str] = None, 
                                       mode: str = 'BOTH', dry_run: bool = True) -> Dict[str, any]:
        """Bulk enable/disable CDC and CT for all tables in a schema
        
        This method uses an efficient stored procedure approach to enable/disable CDC and CT
        for multiple tables in one operation, which is much faster than table-by-table operations.
        
        NOTE: This bulk method may not detect all primary keys correctly. Consider using
        enable_cdc_ct_for_tables() with bulk_mode=False for more reliable results.
        
        Args:
            schema_name: Schema name to process (defaults to self.schema)
            table_filter: Optional list of specific table names to include (None = all tables in schema)
            mode: 'CDC' (only CDC), 'CT' (only CT), or 'BOTH' (default)
            dry_run: If True, only shows what would be changed without making changes (default: True)
            
        Returns:
            dict: Results including counts of enabled/disabled tables
        """
        if not self.provider:
            return {
                'status': 'unsupported',
                'message': f'Bulk CDC/CT operations not supported for {self.dialect}'
            }
        
        return self.provider.bulk_enable_cdc_ct_for_schema(schema_name, table_filter, mode, dry_run)
