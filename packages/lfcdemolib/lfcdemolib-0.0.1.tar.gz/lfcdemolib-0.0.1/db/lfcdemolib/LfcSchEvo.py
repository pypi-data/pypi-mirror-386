"""
LfcSchEvo.py - Lakeflow Connect Schema Evolution Management

This module manages DDL support objects for Change Data Capture (CDC) and Change Tracking (CT)
based on the Databricks DDL support script. It handles the creation and cleanup of triggers,
procedures, and tables required for DDL change capture and schema evolution.

Reference: https://docs.databricks.com/aws/en/assets/files/ddl_support_objects-06ebad393ea6bc7d853d5504dc6542de.sql
"""

import sqlalchemy as sa
from typing import Dict, List, Optional, Literal
import time
import warnings
import requests
import tempfile
import os


class LfcSchEvo:
    """Manages Lakeflow Connect Schema Evolution DDL support objects for CDC and CT operations"""
    
    def __init__(self, engine, schema: str = None, replication_filter: Literal['both', 'pk_only', 'no_pk_only'] = 'both', secrets_json: dict = None):
        """Initialize LfcSchEvo with database engine and optional schema
        
        Args:
            engine: SQLAlchemy engine for database connection
            schema: Optional schema name (defaults to 'dbo' for SQL Server)
            replication_filter: Control which tables to enable replication for:
                - 'both': Enable for all tables (default) - uses 'BOTH' mode in DDL script
                - 'pk_only': Enable only for tables with primary keys - uses 'CDC' mode
                - 'no_pk_only': Enable only for tables without primary keys - uses 'CT' mode
            secrets_json: Optional database credentials dictionary (used when dbxrest is None)
        """
        self.engine = engine
        
        # Schema should always be passed explicitly
        if schema is None:
            self.schema = 'lfcddemo'
            print(f"⚠️  WARNING: LfcSchEvo initialized without schema parameter!")
            print(f"   Using default fallback schema: '{self.schema}'")
            print(f"   This should be passed explicitly from SimpleTest or calling code.")
            print(f"   Example: LfcSchEvo(engine, schema='lfcddemo')")
        else:
            self.schema = schema
            
        self.dialect = engine.dialect.name.lower()
        self.replication_filter = replication_filter
        self.secrets_json = secrets_json
        
        # Extract username from engine URL for DDL script
        self.connection_user = self._extract_username_from_engine()
        
        # Map replication filter to DDL script mode
        self.ddl_script_mode = {
            'both': 'BOTH',
            'pk_only': 'CDC', 
            'no_pk_only': 'CT'
        }.get(replication_filter, 'BOTH')
        
        # Only SQL Server is supported for DDL support objects
        # Note: Non-SQL Server databases are handled gracefully in setup_ddl_support_objects()
        
        # DDL script URL
        self.ddl_script_url = "https://docs.databricks.com/aws/en/assets/files/ddl_support_objects-06ebad393ea6bc7d853d5504dc6542de.sql"
    
    def _extract_username_from_engine(self) -> str:
        """Extract username from SQLAlchemy engine URL
        
        Returns:
            str: Username from connection string, or 'unknown' if not found
        """
        try:
            # Get the connection URL
            url = self.engine.url
            if hasattr(url, 'username') and url.username:
                return url.username
            else:
                # Try to get from secrets_json if available (when dbxrest is None)
                # Use regular user, not DBA user, as the engine is typically connected as regular user
                if hasattr(self, 'secrets_json') and self.secrets_json:
                    return self.secrets_json.get('user', self.secrets_json.get('username', 'unknown'))
                return 'unknown'
        except Exception:
            # Fallback to secrets_json if available
            # Use regular user, not DBA user
            if hasattr(self, 'secrets_json') and self.secrets_json:
                return self.secrets_json.get('user', self.secrets_json.get('username', 'unknown'))
            return 'unknown'
    
    def _download_ddl_script(self) -> str:
        """Download the official Databricks DDL support objects script
        
        Returns:
            str: The DDL script content
        """
        try:
            print(f"📥 Downloading DDL support script from Databricks...")
            response = requests.get(self.ddl_script_url, timeout=30)
            response.raise_for_status()
            
            script_content = response.text
            print(f"✅ Downloaded DDL script ({len(script_content)} characters)")
            return script_content
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download DDL script from {self.ddl_script_url}: {str(e)}")
    
    def _modify_script_parameters(self, script_content: str, mode: str = None, replication_user: str = None) -> str:
        """Modify the DDL script parameters
        
        Args:
            script_content: Original script content
            mode: DDL script mode (BOTH, CDC, CT, NONE)
            replication_user: Optional replication user
            
        Returns:
            str: Modified script content
        """
        # Use provided mode or fall back to instance mode
        effective_mode = mode or self.ddl_script_mode
        
        # Replace the mode parameter
        modified_script = script_content.replace(
            "SET @mode = 'BOTH';", 
            f"SET @mode = '{effective_mode}';"
        )
        
        # Replace the replication user parameter
        if replication_user:
            modified_script = modified_script.replace(
                "SET @replicationUser = '';",
                f"SET @replicationUser = '{replication_user}';"
            )
            user_display = replication_user
        else:
            user_display = 'none'
        
        print(f"🔧 Modified script parameters: mode='{effective_mode}', user='{user_display}'")
        return modified_script
    
    def _test_database_connectivity(self) -> bool:
        """Test database connectivity before attempting DDL operations
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sa.text("SELECT 1 as test_connection"))
                return result.scalar() == 1
        except Exception as e:
            print(f"🔍 Database connectivity test failed: {e}")
            return False
    
    def setup_ddl_support_objects(self, mode: Literal['BOTH', 'CT', 'CDC', 'NONE'] = None, 
                                 replication_user: str = None, test_instance=None) -> Dict[str, any]:
        """Setup DDL support objects using the official Databricks script
        
        Args:
            mode: Setup mode - 'BOTH' (CDC+CT), 'CT', 'CDC', or 'NONE' (cleanup only)
                 If None, uses the mode determined by replication_filter
            replication_user: Optional user to grant privileges to. If None, uses connection user
            
        Returns:
            dict: Result of the setup operation
        """
        if self.dialect != 'mssql':
            return {
                'status': 'unsupported',
                'message': f'DDL support objects not supported for {self.dialect}'
            }
        
        try:
            # Test database connectivity first
            print(f"🔍 Testing database connectivity...")
            if not self._test_database_connectivity():
                return {
                    'status': 'connection_failed',
                    'message': 'Database connectivity test failed. Cannot proceed with DDL support objects setup.',
                    'suggestion': 'Check your database connection, firewall rules, and network connectivity.'
                }
            print(f"✅ Database connectivity test passed")
            
            # Use provided mode or fall back to instance mode based on replication_filter
            effective_mode = mode or self.ddl_script_mode
            
            # Use provided replication_user or fall back to connection user
            effective_user = replication_user or self.connection_user
            
            # If still no user, try to get from secrets_json or use a default
            if not effective_user or effective_user == 'unknown':
                if self.secrets_json and ('user' in self.secrets_json or 'username' in self.secrets_json):
                    effective_user = self.secrets_json.get('user', self.secrets_json.get('username'))
                    print(f"🔧 Using username from secrets: {effective_user}")
                else:
                    effective_user = 'db_owner'  # Use a reasonable default for SQL Server
                    print(f"🔧 Using default username: {effective_user}")
            
            # Download the official DDL script
            script_content = self._download_ddl_script()
            
            # Modify script parameters
            modified_script = self._modify_script_parameters(script_content, effective_mode, effective_user)
            
            # Execute the script
            print(f"🚀 Executing DDL support objects script (mode: {effective_mode})...")
            
            # Add connection retry logic for Azure SQL Database
            max_retries = 3
            retry_delay = 2
            
            retry_count = 0
            for attempt in range(max_retries):
                try:
                    with self.engine.connect() as conn:
                        # Test connection first
                        conn.execute(sa.text("SELECT 1"))
                        
                        # Execute the entire script as a single batch
                        conn.execute(sa.text(modified_script))
                        conn.commit()
                        
                        print(f"✅ DDL support objects script executed successfully")
                        break
                        
                except Exception as conn_error:
                    if attempt < max_retries - 1:
                        retry_count += 1
                        print(f"⚠️ Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # Record final retry count in test instance if available
                        if test_instance and hasattr(test_instance, 'record_retry'):
                            test_instance.record_retry('lfc_ddl_setup', retry_count)
                        
                        # If all retries failed, check if it's a known limitation
                        error_msg = str(conn_error)
                        if "connection failed" in error_msg.lower():
                            return {
                                'status': 'connection_failed',
                                'message': f'Connection to database failed after {max_retries} attempts. This may be due to network issues, firewall rules, or database tier limitations.',
                                'original_error': error_msg,
                                'suggestion': 'Try again later or check your database connection settings and firewall rules.',
                                'retry_count': retry_count
                            }
                        elif "Cannot find the user" in error_msg or "does not exist" in error_msg:
                            # User doesn't exist - this is an error that should be fixed
                            print(f"❌ DDL support objects setup failed: User {effective_user} does not exist in database")
                            return {
                                'status': 'error',
                                'mode': effective_mode,
                                'message': f'User {effective_user} does not exist in the database. Please ensure the user is created before setting up DDL support objects.',
                                'user': effective_user,
                                'retry_count': retry_count,
                                'suggestion': 'Ensure LfcDbPerm.setup_database_permissions() is called to create the user before setting up DDL objects.'
                            }
                        else:
                            raise conn_error
            
            # Record successful retry count if any retries occurred
            if retry_count > 0 and test_instance and hasattr(test_instance, 'record_retry'):
                test_instance.record_retry('lfc_ddl_setup', retry_count)
                
                return {
                    'status': 'success',
                    'mode': effective_mode,
                    'replication_filter': self.replication_filter,
                    'message': f'DDL support objects setup completed using official Databricks script (mode: {effective_mode})',
                    'replication_user': replication_user,
                    'script_url': self.ddl_script_url
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to setup DDL support objects: {str(e)}',
                'script_url': self.ddl_script_url
            }
    
    def cleanup_ddl_support_objects(self) -> Dict[str, any]:
        """Remove all DDL support objects"""
        return self.setup_ddl_support_objects(mode='NONE')
    
    
    def get_ddl_support_status(self) -> Dict[str, any]:
        """Get status of DDL support objects created by the official Databricks script"""
        if self.dialect != 'mssql':
            return {
                'status': 'unsupported',
                'message': f'DDL support objects not supported for {self.dialect}'
            }
        
        try:
            with self.engine.connect() as conn:
                # Check for triggers created by the official Databricks script
                trigger_sql = sa.text("""
                    SELECT name, type_desc, create_date 
                    FROM sys.triggers 
                    WHERE [type] = 'TR' AND parent_class = 0
                    AND (name LIKE 'lakeflowAlterTableTrigger_%' OR name LIKE 'lakeflowDdlAuditTrigger_%')
                """)
                triggers = conn.execute(trigger_sql).fetchall()
                
                # Check for procedures created by the official Databricks script
                proc_sql = sa.text("""
                    SELECT name, create_date 
                    FROM sys.procedures 
                    WHERE name LIKE 'lakeflowDisableOldCaptureInstance_%' 
                       OR name LIKE 'lakeflowMergeCaptureInstances_%'
                       OR name LIKE 'lakeflowRefreshCaptureInstance_%'
                """)
                procedures = conn.execute(proc_sql).fetchall()
                
                # Check for tables created by the official Databricks script
                table_sql = sa.text("""
                    SELECT name, create_date 
                    FROM sys.tables 
                    WHERE name LIKE 'lakeflowCaptureInstanceInfo_%' OR name LIKE 'lakeflowDdlAudit_%'
                """)
                tables = conn.execute(table_sql).fetchall()
                
                return {
                    'status': 'success',
                    'triggers': [dict(row._mapping) for row in triggers],
                    'procedures': [dict(row._mapping) for row in procedures],
                    'tables': [dict(row._mapping) for row in tables],
                    'total_objects': len(triggers) + len(procedures) + len(tables),
                    'replication_filter': self.replication_filter,
                    'ddl_script_mode': self.ddl_script_mode,
                    'script_url': self.ddl_script_url
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to get DDL support status: {str(e)}'
            }
