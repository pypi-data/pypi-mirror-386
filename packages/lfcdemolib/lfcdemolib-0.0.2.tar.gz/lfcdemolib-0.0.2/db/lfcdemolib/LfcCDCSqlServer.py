#!/usr/bin/env python3
"""
LfcCDCSqlServer.py - SQL Server CDC/CT Provider

This module provides SQL Server-specific CDC (Change Data Capture) and 
CT (Change Tracking) operations.

SQL Server Strategy:
- CDC: For tables WITHOUT primary keys (requires higher service tier)
- CT: For tables WITH primary keys (supported on all tiers)
"""

import sqlalchemy as sa
import pandas as pd
from typing import Dict, List, Any, Optional
from .LfcCDCBase import LfcCDCProviderBase


class SqlServerCDCProvider(LfcCDCProviderBase):
    """SQL Server-specific CDC/CT implementation"""
    
    def get_default_schema(self) -> str:
        """Get default schema for SQL Server"""
        return 'lfcddemo'
    
    def _has_primary_key(self, table_name: str) -> bool:
        """Check if table has a primary key
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if table has primary key, False otherwise
        """
        qualified_name = self.get_qualified_table_name(table_name)
        
        try:
            with self.engine.connect() as conn:
                query = sa.text("""
                    SELECT COUNT(*) 
                    FROM sys.key_constraints kc
                    JOIN sys.tables t ON kc.parent_object_id = t.object_id
                    JOIN sys.schemas s ON t.schema_id = s.schema_id
                    WHERE kc.type = 'PK' 
                    AND t.name = :table_name 
                    AND s.name = ISNULL(:schema, 'dbo')
                """)
                result = conn.execute(query, {
                    'table_name': table_name,
                    'schema': self.schema or 'dbo'
                }).scalar()
                
                return result > 0
        except Exception as e:
            print(f"⚠️ Error checking primary key for {qualified_name}: {e}")
            return False
    
    def enable_cdc_for_table(self, table_name: str, has_primary_key: bool = None) -> Dict[str, Any]:
        """Enable CDC or CT for SQL Server table
        
        Args:
            table_name: Name of the table
            has_primary_key: Optional primary key status. If None, will query database
            
        Returns:
            dict: Result of the operation
        """
        qualified_name = self.get_qualified_table_name(table_name)
        
        # Use provided primary key status or query database
        if has_primary_key is not None:
            has_pk = has_primary_key
            print(f"🔍 Using provided primary key status for {qualified_name}: {has_pk}")
        else:
            has_pk = self._has_primary_key(table_name)
            print(f"🔍 Queried primary key status for {qualified_name}: {has_pk}")
        
        try:
            with self.engine.connect() as conn:
                if has_pk:
                    # Tables WITH primary key: Use Change Tracking (CT)
                    result = self._enable_ct(conn, table_name, qualified_name)
                else:
                    # Tables WITHOUT primary key: Use Change Data Capture (CDC)
                    if self.cdc_supported is False:
                        return {
                            'table_name': table_name,
                            'qualified_name': qualified_name,
                            'has_primary_key': has_pk,
                            'method': 'CDC',
                            'status': 'skipped',
                            'message': 'CDC not supported on this database service tier (table has no primary key for CT)'
                        }
                    else:
                        result = self._enable_cdc(conn, table_name, qualified_name)
                
                return result
        except Exception as e:
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'has_primary_key': has_pk,
                'status': 'error',
                'message': str(e)
            }
    
    def _enable_cdc(self, conn, table_name: str, qualified_name: str) -> Dict[str, Any]:
        """Enable CDC for SQL Server table without primary key"""
        # Skip CDC if we already know it's not supported
        if self.cdc_supported is False:
            print(f"🚫 Skipping CDC for {qualified_name} - CDC not supported on this database tier")
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'has_primary_key': False,
                'method': 'CDC',
                'status': 'tier_limited',
                'message': f'CDC skipped: {self.cdc_failure_reason}'
            }
        
        try:
            # Check if CDC is already enabled at database level
            if self.db_cdc_enabled is None:
                with self.dba_engine.connect() as dba_conn:
                    target_db_query = sa.text("SELECT DB_NAME()")
                    target_db = conn.execute(target_db_query).scalar()
                    
                    try:
                        check_db_cdc = sa.text(f"SELECT is_cdc_enabled FROM sys.databases WHERE name = '{target_db}'")
                        cdc_db_enabled = dba_conn.execute(check_db_cdc).scalar()
                        
                        if cdc_db_enabled:
                            print(f"🔍 CDC already enabled for database {target_db}")
                            self.db_cdc_enabled = True
                        else:
                            self.db_cdc_enabled = False
                    except Exception:
                        self.db_cdc_enabled = False
            else:
                cdc_db_enabled = self.db_cdc_enabled
            
            if not cdc_db_enabled:
                print(f"🔄 Enabling CDC at database level...")
                target_db_query = sa.text("SELECT DB_NAME()")
                target_db = conn.execute(target_db_query).scalar()
                
                # Create target database engine
                target_engine = self._create_target_database_engine(target_db)
                
                try:
                    with target_engine.connect() as target_conn:
                        enable_db_cdc = sa.text("EXEC sys.sp_cdc_enable_db")
                        target_conn.execute(enable_db_cdc)
                        target_conn.commit()
                        print(f"✅ CDC enabled at database level for {target_db}")
                        self.cdc_supported = True
                except Exception as db_cdc_error:
                    error_msg = str(db_cdc_error)
                    if "22871" in error_msg and "not supported on Free, Basic or Standard tier" in error_msg:
                        print(f"🚫 CDC not supported on this database service tier")
                        self.cdc_supported = False
                        self.cdc_failure_reason = "Service tier limitation - CDC requires higher tier"
                        return {
                            'table_name': table_name,
                            'qualified_name': qualified_name,
                            'has_primary_key': False,
                            'method': 'CDC',
                            'status': 'tier_limited',
                            'message': 'CDC not supported on this database service tier'
                        }
                    else:
                        raise db_cdc_error
            
            # Check if CDC is already enabled for this table
            try:
                check_existing_cdc = sa.text("""
                SELECT COUNT(*) FROM cdc.change_tables ct
                JOIN sys.tables t ON ct.object_id = t.object_id
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE t.name = :table_name AND s.name = :schema
                """)
                
                existing_cdc = conn.execute(check_existing_cdc, {
                    'table_name': table_name,
                    'schema': self.schema or 'dbo'
                }).scalar() > 0
            except Exception as cdc_check_error:
                # CDC tables don't exist - CDC not enabled at database level
                if "Invalid object name 'cdc.change_tables'" in str(cdc_check_error):
                    existing_cdc = False
                else:
                    raise cdc_check_error
            
            if existing_cdc:
                print(f"✅ CDC already enabled for table: {qualified_name}")
                return {
                    'table_name': table_name,
                    'qualified_name': qualified_name,
                    'has_primary_key': False,
                    'method': 'CDC',
                    'status': 'enabled',
                    'message': 'Change Data Capture already enabled'
                }
            
            # Enable CDC for the specific table
            import time
            unique_suffix = str(int(time.time() * 1000) % 100000)
            capture_instance = f"{self.schema or 'dbo'}_{table_name}_{unique_suffix}"
            
            enable_table_cdc = sa.text("""
                EXEC sys.sp_cdc_enable_table
                @source_schema = :schema,
                @source_name = :table_name,
                @capture_instance = :capture_instance,
                @role_name = NULL,
                @supports_net_changes = 0
            """)
            
            conn.execute(enable_table_cdc, {
                'schema': self.schema or 'dbo',
                'table_name': table_name,
                'capture_instance': capture_instance
            })
            conn.commit()
            
            print(f"✅ CDC enabled for table: {qualified_name}")
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'has_primary_key': False,
                'method': 'CDC',
                'status': 'enabled',
                'message': 'Change Data Capture enabled successfully'
            }
        except Exception as e:
            print(f"⚠️ Failed to enable CDC for {qualified_name}: {e}")
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'has_primary_key': False,
                'method': 'CDC',
                'status': 'warning',
                'message': f'CDC setup failed (may not be supported): {str(e)}'
            }
    
    def _enable_ct(self, conn, table_name: str, qualified_name: str) -> Dict[str, Any]:
        """Enable Change Tracking for SQL Server table with primary key"""
        try:
            # Check if CT is supported
            ct_supported, version_info = self._check_ct_support(conn)
            if not ct_supported:
                return {
                    'table_name': table_name,
                    'qualified_name': qualified_name,
                    'has_primary_key': True,
                    'method': 'CT',
                    'status': 'error',
                    'message': version_info
                }
            
            # Check if CT is enabled at database level
            if self.db_ct_enabled is None:
                target_db_query = sa.text("SELECT DB_NAME()")
                target_db = conn.execute(target_db_query).scalar()
                
                with self.dba_engine.connect() as dba_conn:
                    try:
                        check_db_ct = sa.text(f"""
                            SELECT database_id
                            FROM sys.change_tracking_databases
                            WHERE database_id = DB_ID('{target_db}')
                        """)
                        ct_result = dba_conn.execute(check_db_ct).fetchone()
                        self.db_ct_enabled = ct_result is not None
                    except Exception:
                        self.db_ct_enabled = False
            
            if not self.db_ct_enabled:
                print(f"🔄 Enabling Change Tracking at database level...")
                target_db_query = sa.text("SELECT DB_NAME()")
                target_db = conn.execute(target_db_query).scalar()
                
                with self.dba_engine.connect() as dba_conn:
                    try:
                        enable_db_ct = sa.text(f"""
                            ALTER DATABASE [{target_db}]
                            SET CHANGE_TRACKING = ON 
                            (CHANGE_RETENTION = 2 DAYS, AUTO_CLEANUP = ON)
                        """)
                        dba_conn.execute(enable_db_ct)
                        dba_conn.commit()
                        print(f"✅ Change Tracking enabled at database level for {target_db}")
                        self.db_ct_enabled = True
                    except Exception as enable_e:
                        error_msg = str(enable_e)
                        if "change tracking is already enabled" in error_msg.lower():
                            print(f"✅ Change Tracking already enabled at database level")
                            self.db_ct_enabled = True
                        else:
                            print(f"⚠️ Failed to enable Change Tracking: {enable_e}")
            
            # Check if CT is already enabled for the table
            check_table_ct = sa.text(f"""
                SELECT COUNT(*) as table_ct_count
                FROM sys.change_tracking_tables ct
                JOIN sys.objects o ON ct.object_id = o.object_id
                WHERE o.name = '{table_name}' AND SCHEMA_NAME(o.schema_id) = '{self.schema or "dbo"}'
            """)
            
            table_ct_result = conn.execute(check_table_ct).scalar()
            
            if table_ct_result > 0:
                print(f"✅ Change Tracking already enabled for table: {qualified_name}")
                return {
                    'table_name': table_name,
                    'qualified_name': qualified_name,
                    'has_primary_key': True,
                    'method': 'CT',
                    'status': 'enabled',
                    'message': 'Change Tracking already enabled'
                }
            
            # Enable CT for the table
            print(f"🔄 Enabling Change Tracking for table: {qualified_name}")
            enable_table_ct = sa.text(f"""
                ALTER TABLE {qualified_name} 
                ENABLE CHANGE_TRACKING 
                WITH (TRACK_COLUMNS_UPDATED = ON)
            """)
            
            conn.execute(enable_table_ct)
            conn.commit()
            print(f"✅ Change Tracking enabled for table: {qualified_name}")
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'has_primary_key': True,
                'method': 'CT',
                'status': 'enabled',
                'message': 'Change Tracking enabled successfully'
            }
        except Exception as e:
            print(f"⚠️ Failed to enable Change Tracking for {qualified_name}: {e}")
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'has_primary_key': True,
                'method': 'CT',
                'status': 'warning',
                'message': f'Change Tracking setup failed: {str(e)}'
            }
    
    def _check_ct_support(self, conn) -> tuple:
        """Check if SQL Server supports Change Tracking
        
        Returns:
            tuple: (is_supported, version_info)
        """
        try:
            version_check = sa.text("SELECT SERVERPROPERTY('ProductVersion') as version, SERVERPROPERTY('Edition') as edition")
            result = conn.execute(version_check).fetchone()
            version = result.version if result else "Unknown"
            edition = result.edition if result else "Unknown"
            
            ct_test = sa.text("""
                SELECT COUNT(*) 
                FROM sys.change_tracking_databases 
                WHERE database_id IS NOT NULL
            """)
            conn.execute(ct_test).scalar()
            
            return True, f"SQL Server {version} ({edition})"
        except Exception as e:
            return False, f"Change Tracking not supported: {str(e)}"
    
    def _create_target_database_engine(self, target_db: str):
        """Create an engine connected to the target database"""
        import urllib.parse
        from .LfcCredentialModel import LfcCredential
        from pydantic import ValidationError
        
        # Extract DBA credentials using Pydantic model if possible
        try:
            cred = LfcCredential.from_dict(self.secrets_json)
            dba_user = cred.dba.user
            dba_password = cred.dba.password
            db_type = cred.db_type
        except (ValidationError, Exception):
            # Fall back to manual extraction for backward compatibility
            dba_obj = self.secrets_json.get("dba", {})
            if dba_obj:
                # V2 format: nested dba object
                dba_user = dba_obj.get("user")
                dba_password = dba_obj.get("password")
            else:
                # V1 format: flat fields with fallback
                dba_user = self.secrets_json.get("dba_user") or self.secrets_json.get("user")
                dba_password = self.secrets_json.get("dba_password") or self.secrets_json.get("password")
            
            db_type = self.secrets_json.get("connection_type") or self.secrets_json.get("db_type")
            if db_type is None or db_type == "": 
                db_type = 'sqlserver'
        
        if db_type: 
            db_type = db_type.casefold()
        
        driver = "mssql+pymssql"
        encoded_username = urllib.parse.quote_plus(dba_user)
        encoded_password = urllib.parse.quote_plus(dba_password)
                
        connection_string = f"{driver}://{encoded_username}:{encoded_password}@{self.secrets_json['host_fqdn']}:{self.secrets_json['port']}/{target_db}"
        target_engine = sa.create_engine(connection_string, echo=False, isolation_level="AUTOCOMMIT")
        
        return target_engine
    
    def disable_cdc_for_table(self, table_name: str) -> Dict[str, Any]:
        """Disable CDC or CT for SQL Server table
        
        Args:
            table_name: Name of the table to disable CDC/CT for
            
        Returns:
            dict: Result of the CDC/CT disable operation
        """
        qualified_name = self.get_qualified_table_name(table_name)
        
        try:
            with self.engine.connect() as conn:
                # Try to disable CDC first
                cdc_result = self._disable_cdc(conn, table_name, qualified_name)
                
                # Try to disable CT
                ct_result = self._disable_ct(conn, table_name, qualified_name)
                
                # Return combined result
                disabled_methods = []
                if cdc_result['status'] == 'disabled':
                    disabled_methods.append('CDC')
                if ct_result['status'] == 'disabled':
                    disabled_methods.append('CT')
                
                if disabled_methods:
                    return {
                        'table_name': table_name,
                        'qualified_name': qualified_name,
                        'methods_disabled': disabled_methods,
                        'status': 'disabled',
                        'message': f'Disabled: {", ".join(disabled_methods)}'
                    }
                else:
                    return {
                        'table_name': table_name,
                        'qualified_name': qualified_name,
                        'methods_disabled': [],
                        'status': 'none_found',
                        'message': 'No CDC or CT found to disable'
                    }
        except Exception as e:
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'status': 'error',
                'message': str(e)
            }
    
    def _disable_cdc(self, conn, table_name: str, qualified_name: str) -> Dict[str, Any]:
        """Disable CDC for SQL Server table"""
        try:
            if hasattr(self, 'cdc_supported') and self.cdc_supported is False:
                return {'status': 'skipped', 'message': 'CDC not supported'}
            
            # Check if CDC is enabled for this table
            cdc_enabled = False
            try:
                check_cdc = sa.text("""
                    SELECT COUNT(*) FROM cdc.change_tables ct
                    JOIN sys.tables t ON ct.object_id = t.object_id
                    JOIN sys.schemas s ON t.schema_id = s.schema_id
                    WHERE t.name = :table_name AND s.name = :schema
                """)
                
                cdc_enabled = conn.execute(check_cdc, {
                    'table_name': table_name,
                    'schema': self.schema or 'dbo'
                }).scalar() > 0
            except Exception as cdc_check_error:
                # CDC tables don't exist - CDC not enabled at database level
                if "Invalid object name 'cdc.change_tables'" in str(cdc_check_error):
                    cdc_enabled = False
                else:
                    raise cdc_check_error
            
            if cdc_enabled:
                get_capture_instances = sa.text("""
                    SELECT capture_instance FROM cdc.change_tables ct
                    JOIN sys.tables t ON ct.object_id = t.object_id
                    JOIN sys.schemas s ON t.schema_id = s.schema_id
                    WHERE t.name = :table_name AND s.name = :schema
                """)
                
                capture_instances = conn.execute(get_capture_instances, {
                    'table_name': table_name,
                    'schema': self.schema or 'dbo'
                }).fetchall()
                
                for (capture_instance,) in capture_instances:
                    disable_cdc = sa.text("""
                        EXEC sys.sp_cdc_disable_table
                        @source_schema = :schema,
                        @source_name = :table_name,
                        @capture_instance = :capture_instance
                    """)
                    
                    conn.execute(disable_cdc, {
                        'schema': self.schema or 'dbo',
                        'table_name': table_name,
                        'capture_instance': capture_instance
                    })
                    print(f"🗑️ Disabled CDC capture instance: {capture_instance}")
                conn.commit()
                
                print(f"✅ CDC disabled for table: {qualified_name}")
                return {'status': 'disabled', 'method': 'CDC'}
            else:
                return {'status': 'not_enabled', 'method': 'CDC'}
                
        except Exception as e:
            print(f"⚠️ Error disabling CDC for {qualified_name}: {e}")
            return {'status': 'error', 'method': 'CDC', 'message': str(e)}
    
    def _disable_ct(self, conn, table_name: str, qualified_name: str) -> Dict[str, Any]:
        """Disable Change Tracking for SQL Server table"""
        try:
            check_ct = sa.text("""
                SELECT COUNT(*) FROM sys.change_tracking_tables ctt
                JOIN sys.tables t ON ctt.object_id = t.object_id
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE t.name = :table_name AND s.name = :schema
            """)
            
            ct_enabled = conn.execute(check_ct, {
                'table_name': table_name,
                'schema': self.schema or 'dbo'
            }).scalar() > 0
            
            if ct_enabled:
                disable_ct = sa.text(f"""
                    ALTER TABLE {qualified_name} DISABLE CHANGE_TRACKING
                """)
                
                conn.execute(disable_ct)
                conn.commit()
                
                print(f"✅ Change Tracking disabled for table: {qualified_name}")
                return {'status': 'disabled', 'method': 'CT'}
            else:
                return {'status': 'not_enabled', 'method': 'CT'}
                
        except Exception as e:
            print(f"⚠️ Error disabling Change Tracking for {qualified_name}: {e}")
            return {'status': 'error', 'method': 'CT', 'message': str(e)}
    
    def get_cdc_status(self, table_name: str, has_primary_key: bool = None) -> Dict[str, Any]:
        """Get CDC/CT status for a SQL Server table
        
        Args:
            table_name: Name of the table to check
            has_primary_key: Optional primary key status
            
        Returns:
            dict: CDC/CT status information
        """
        qualified_name = self.get_qualified_table_name(table_name)
        has_pk = has_primary_key if has_primary_key is not None else self._has_primary_key(table_name)
        
        try:
            with self.engine.connect() as conn:
                # Check CDC status
                cdc_enabled = False
                if hasattr(self, 'cdc_supported') and self.cdc_supported is not False:
                    try:
                        cdc_query = sa.text("""
                            SELECT COUNT(*) FROM cdc.change_tables ct
                            JOIN sys.tables t ON ct.object_id = t.object_id
                            JOIN sys.schemas s ON t.schema_id = s.schema_id
                            WHERE t.name = :table_name AND s.name = :schema
                        """)
                        cdc_enabled = conn.execute(cdc_query, {
                            'table_name': table_name,
                            'schema': self.schema or 'dbo'
                        }).scalar() > 0
                    except Exception:
                        cdc_enabled = False
                
                # Check CT status  
                ct_query = sa.text("""
                    SELECT COUNT(*) FROM sys.change_tracking_tables ctt
                    JOIN sys.tables t ON ctt.object_id = t.object_id
                    JOIN sys.schemas s ON t.schema_id = s.schema_id
                    WHERE t.name = :table_name AND s.name = :schema
                """)
                
                ct_enabled = conn.execute(ct_query, {
                    'table_name': table_name,
                    'schema': self.schema or 'dbo'
                }).scalar() > 0
                
                return {
                    'table_name': table_name,
                    'qualified_name': qualified_name,
                    'has_primary_key': has_pk,
                    'cdc_enabled': cdc_enabled,
                    'ct_enabled': ct_enabled,
                    'recommended_method': 'CT' if has_pk else 'CDC',
                    'status': 'enabled' if (cdc_enabled or ct_enabled) else 'disabled'
                }
        except Exception as e:
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'status': 'error',
                'message': str(e)
            }
    
    def cleanup_orphaned_cdc_instances(self) -> Dict[str, Any]:
        """Clean up orphaned CDC capture instances for non-existent tables
        
        Returns:
            dict: Summary of cleanup operations
        """
        if hasattr(self, 'cdc_supported') and self.cdc_supported is False:
            return {
                'status': 'skipped',
                'message': 'CDC not supported on this database tier',
                'cleaned_instances': 0
            }
        
        try:
            with self.engine.connect() as conn:
                try:
                    orphaned_query = sa.text("""
                        SELECT ct.capture_instance, ct.source_object_id
                        FROM cdc.change_tables ct
                        LEFT JOIN sys.tables t ON ct.object_id = t.object_id
                        WHERE t.object_id IS NULL
                    """)
                    
                    orphaned_instances = conn.execute(orphaned_query).fetchall()
                except Exception as query_error:
                    if "Invalid object name 'cdc.change_tables'" in str(query_error):
                        return {
                            'status': 'skipped',
                            'message': 'CDC not supported on this database tier',
                            'cleaned_instances': 0
                        }
                    else:
                        raise query_error
                
                cleaned_up = []
                for capture_instance, source_object_id in orphaned_instances:
                    try:
                        cleanup_sql = sa.text("""
                            EXEC sys.sp_cdc_disable_table
                            @source_schema = NULL,
                            @source_name = NULL,
                            @capture_instance = :capture_instance
                        """)
                        
                        conn.execute(cleanup_sql, {'capture_instance': capture_instance})
                        cleaned_up.append(capture_instance)
                        print(f"🧹 Cleaned up orphaned CDC instance: {capture_instance}")
                        
                    except Exception as e:
                        print(f"⚠️ Could not clean up {capture_instance}: {e}")
                
                conn.commit()
                
                return {
                    'status': 'completed',
                    'cleaned_up_instances': cleaned_up,
                    'message': f'Cleaned up {len(cleaned_up)} orphaned CDC instances'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'CDC cleanup failed: {str(e)}'
            }
    
    def bulk_enable_cdc_ct_for_schema(self, schema_name: str = None, table_filter: list = None,
                                       mode: str = 'BOTH', dry_run: bool = True) -> Dict[str, Any]:
        """Bulk enable/disable CDC and CT for all tables in a schema (SQL Server)
        
        This method uses an efficient stored procedure approach to enable/disable CDC and CT
        for multiple tables in one operation. Shows tabular displays of status before/after.
        
        Args:
            schema_name: Schema name to process (defaults to self.schema)
            table_filter: Optional list of specific table names to include
            mode: 'CDC' (only CDC), 'CT' (only CT), or 'BOTH' (default)
            dry_run: If True, only shows what would be changed without making changes
            
        Returns:
            dict: Results including counts of enabled/disabled tables
        """
        schema_name = schema_name or self.schema or 'dbo'
        
        # Build table filter SQL clause
        s_t_filter_sql = ""
        if table_filter:
            table_list = ",".join(f"'{table_name}'" for table_name in table_filter)
            s_t_filter_sql = f"and (table_schema='{schema_name}' and table_name in ({table_list}))"
        else:
            s_t_filter_sql = f"and table_schema='{schema_name}'"

        print(f"*** {s_t_filter_sql=}")
        
        # T-SQL for enabling/disabling CDC and CT
        cdc_ct_enable_tsql = """
DECLARE @cdc_enabled_count INT = 0;
DECLARE @cdc_disabled_count INT = 0;
DECLARE @ct_enabled_count INT = 0;
DECLARE @ct_disabled_count INT = 0;
DECLARE @cdc_enabled_already_count INT = 0;
DECLARE @cdc_disabled_already_count INT = 0;
DECLARE @ct_enabled_already_count INT = 0;
DECLARE @ct_disabled_already_count INT = 0;

OPEN MyCursor
FETCH NEXT FROM MyCursor INTO @TABLE_CAT, @TABLE_SCHEM, @TABLE_NAME, @PK, @CDC, @CT
WHILE @@FETCH_STATUS = 0
BEGIN
    if (@PK is NULL) 
      if (@mode='CDC' or @mode='BOTH') and (@cdc_enabled_on_cat = 1) 
        -- need to enable CDC if not enabled
        if @CDC is NULL 
        BEGIN
            exec sys.sp_cdc_enable_table @source_schema = @TABLE_SCHEM, @source_name = @TABLE_NAME,  @role_name = NULL, @supports_net_changes = 0;
            set @cdc_enabled_count = @cdc_enabled_count + 1;
        END
        else
        BEGIN
            set @cdc_enabled_already_count = @cdc_enabled_already_count + 1;
        END
      else 
        -- need to disable CDC if enabled
        if @CDC is not NULL
        BEGIN
            exec sys.sp_cdc_disable_table @source_schema = @TABLE_SCHEM, @source_name = @TABLE_NAME,  @capture_instance = 'all';
            set @cdc_disabled_count = @cdc_disabled_count + 1;
        END
        else
        BEGIN
            set @cdc_disabled_already_count = @cdc_disabled_already_count + 1;
        END

    if (@PK is NOT NULL)
      if (@mode='CT' or @mode='BOTH') and (@ct_enabled_on_cat = 1) 
        -- need to enable CT if not enabled
        if @CT is NULL 
        BEGIN
            exec('ALTER TABLE ['+@TABLE_SCHEM+'].['+@TABLE_NAME+'] ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON)');
            set @ct_enabled_count = @ct_enabled_count + 1;
        END
        else
        BEGIN
            set @ct_enabled_already_count = @ct_enabled_already_count + 1;
        END
      else 
        -- need to disable CT if enabled
        if @CT is not NULL
        BEGIN
            exec('ALTER TABLE ['+@TABLE_SCHEM+'].['+@TABLE_NAME+'] DISABLE CHANGE_TRACKING')	
            set @ct_disabled_count = @ct_disabled_count + 1;
        END
        else
        BEGIN
            set @ct_disabled_already_count = @ct_disabled_already_count + 1;
        END
    -- fetch next    
    FETCH NEXT FROM MyCursor INTO @TABLE_CAT, @TABLE_SCHEM, @TABLE_NAME, @PK, @CDC, @CT;
END
CLOSE MyCursor;
DEALLOCATE MyCursor;

SELECT  
    @cdc_enabled_count cdc_enabled_count,
    @cdc_disabled_count cdc_disabled_count,
    @ct_enabled_count ct_enabled_count,
    @ct_disabled_count ct_disabled_count,
    @cdc_enabled_already_count cdc_enabled_already_count,
    @cdc_disabled_already_count cdc_disabled_already_count,
    @ct_enabled_already_count ct_enabled_already_count,
    @ct_disabled_already_count ct_disabled_already_count;
"""
        
        # Function to build the SQL command (status check or alter)
        def get_sql(run_cdc_ct: bool):
            """Generate T-SQL for status check or alter operation"""
            return f"""
BEGIN
DECLARE @mode NVARCHAR(10) = N'{mode}';
DECLARE @schema_name nvarchar(128) = N'{schema_name}';
DECLARE @TABLE_CAT nvarchar(128), @TABLE_SCHEM nvarchar(128), @TABLE_NAME nvarchar(128), @PK nvarchar(128), @CT nvarchar(128), @CDC nvarchar(128);

-- set if cdc or ct is enabled on the catalog
DECLARE @ct_enabled_on_cat INT;
DECLARE @cdc_enabled_on_cat INT;
if exists(select is_cdc_enabled from sys.databases where name=db_name() and is_cdc_enabled=1)
    set @cdc_enabled_on_cat = 1;
else
    set @cdc_enabled_on_cat = 0;

if exists(select database_id from sys.change_tracking_databases where database_id=db_id())
    set @ct_enabled_on_cat = 1;
else
    set @ct_enabled_on_cat = 0;

{'DECLARE MyCursor CURSOR FOR' if run_cdc_ct else ''}
with 
tab as (
	select table_catalog TABLE_CAT, table_schema TABLE_SCHEM, table_name TABLE_NAME 
	from INFORMATION_SCHEMA.TABLES 
	where table_type='BASE TABLE'
	and table_name not in ('MSchange_tracking_history', 'systranschemas')
	{s_t_filter_sql}
	)
, pk as (
	-- PRIMARY KEY TABLES (using sys tables - more reliable for detecting inline PRIMARY KEY declarations)
    SELECT 
        DB_NAME() as TABLE_CAT,
        s.name as TABLE_SCHEM,
        t.name as TABLE_NAME
    FROM sys.key_constraints kc
    JOIN sys.tables t ON kc.parent_object_id = t.object_id
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE kc.type = 'PK'
    AND s.name = @schema_name
    )
, ct as (    
    -- CT enabled tables
    select db_name() TABLE_CAT, schema_name(t.schema_id) TABLE_SCHEM, t.name TABLE_NAME  
    from sys.change_tracking_tables ctt 
    left join sys.tables t on ctt.object_id = t.object_id
    where t.schema_id=schema_id(@schema_name)
)
, cdc as (
    -- CDC enabled table
    select db_name() TABLE_CAT, s.name TABLE_SCHEM, t.name as TABLE_NAME 
    from sys.tables t
    left join sys.schemas s on t.schema_id = s.schema_id
    where t.is_tracked_by_cdc=1 and 
    t.schema_id=schema_id(@schema_name)
)
select tab.TABLE_CAT, tab.TABLE_SCHEM, tab.TABLE_NAME, pk.TABLE_NAME PK, cdc.TABLE_NAME CDC, ct.TABLE_NAME CT 
from tab
left join pk  on pk.TABLE_CAT=tab.TABLE_CAT  and pk.TABLE_SCHEM=tab.TABLE_SCHEM  and pk.TABLE_NAME=tab.TABLE_NAME
left join ct  on ct.TABLE_CAT=tab.TABLE_CAT  and ct.TABLE_SCHEM=tab.TABLE_SCHEM  and ct.TABLE_NAME=tab.TABLE_NAME
left join cdc on cdc.TABLE_CAT=tab.TABLE_CAT and cdc.TABLE_SCHEM=tab.TABLE_SCHEM and cdc.TABLE_NAME=tab.TABLE_NAME
{cdc_ct_enable_tsql if run_cdc_ct else ''}
END
"""
        
        try:
            with self.engine.connect() as conn:
                # Step 1: Show current status (BEFORE)
                print(f"\n{'='*80}")
                print(f"📊 BEFORE: Current CDC/CT Status for Schema '{schema_name}'")
                print(f"{'='*80}")
                sql_cmd_status = sa.text(get_sql(False))
                df_before = pd.read_sql(sql_cmd_status, conn)
                print(df_before.to_string(index=False))
                print()
                
                # Convert to tables_info for backward compatibility
                tables_info = []
                for _, row in df_before.iterrows():
                    tables_info.append({
                        'catalog': row['TABLE_CAT'],
                        'schema': row['TABLE_SCHEM'],
                        'table': row['TABLE_NAME'],
                        'has_pk': row['PK'] is not None,
                        'cdc_enabled': row['CDC'] is not None,
                        'ct_enabled': row['CT'] is not None
                    })
                
                if dry_run:
                    # Dry run mode - just show summary
                    print(f"🔍 Dry run mode - showing what would be changed:")
                    print(f"   Total tables: {len(tables_info)}")
                    print(f"   Tables with PK: {sum(1 for t in tables_info if t['has_pk'])}")
                    print(f"   Tables without PK: {sum(1 for t in tables_info if not t['has_pk'])}")
                    print(f"   CDC enabled: {sum(1 for t in tables_info if t['cdc_enabled'])}")
                    print(f"   CT enabled: {sum(1 for t in tables_info if t['ct_enabled'])}")
                    print(f"{'='*80}\n")
                    
                    return {
                        'status': 'dry_run',
                        'schema': schema_name,
                        'mode': mode,
                        'tables': tables_info,
                        'before_dataframe': df_before,
                        'summary': {
                            'total_tables': len(tables_info),
                            'tables_with_pk': sum(1 for t in tables_info if t['has_pk']),
                            'tables_without_pk': sum(1 for t in tables_info if not t['has_pk']),
                            'cdc_enabled': sum(1 for t in tables_info if t['cdc_enabled']),
                            'ct_enabled': sum(1 for t in tables_info if t['ct_enabled'])
                        }
                    }
                else:
                    # Step 2: Execute alter operations
                    print(f"{'='*80}")
                    print(f"🔄 Executing CDC/CT Changes...")
                    print(f"{'='*80}")
                    sql_cmd_alter = sa.text(get_sql(True))
                    result = conn.execute(sql_cmd_alter)
                    row = result.fetchone()
                    conn.commit()
                    
                    # Display the counts as a DataFrame
                    counts_df = pd.DataFrame([{
                        'cdc_enabled_count': row[0],
                        'cdc_disabled_count': row[1],
                        'ct_enabled_count': row[2],
                        'ct_disabled_count': row[3],
                        'cdc_enabled_already_count': row[4],
                        'cdc_disabled_already_count': row[5],
                        'ct_enabled_already_count': row[6],
                        'ct_disabled_already_count': row[7]
                    }])
                    print("\n📈 Operation Counts:")
                    print(counts_df.to_string(index=False))
                    print()
                    
                    # Step 3: Show status after changes (AFTER)
                    print(f"{'='*80}")
                    print(f"📊 AFTER: Updated CDC/CT Status for Schema '{schema_name}'")
                    print(f"{'='*80}")
                    sql_cmd_status_after = sa.text(get_sql(False))
                    df_after = pd.read_sql(sql_cmd_status_after, conn)
                    print(df_after.to_string(index=False))
                    print(f"{'='*80}\n")
                    
                    result_dict = {
                        'status': 'completed',
                        'schema': schema_name,
                        'mode': mode,
                        'cdc_enabled_count': row[0],
                        'cdc_disabled_count': row[1],
                        'ct_enabled_count': row[2],
                        'ct_disabled_count': row[3],
                        'cdc_enabled_already_count': row[4],
                        'cdc_disabled_already_count': row[5],
                        'ct_enabled_already_count': row[6],
                        'ct_disabled_already_count': row[7],
                        'before_dataframe': df_before,
                        'after_dataframe': df_after,
                        'counts_dataframe': counts_df,
                        'tables': tables_info
                    }
                    
                    print(f"✅ Bulk CDC/CT operation completed for schema '{schema_name}':")
                    print(f"   CDC enabled: {result_dict['cdc_enabled_count']} (already enabled: {result_dict['cdc_enabled_already_count']})")
                    print(f"   CDC disabled: {result_dict['cdc_disabled_count']} (already disabled: {result_dict['cdc_disabled_already_count']})")
                    print(f"   CT enabled: {result_dict['ct_enabled_count']} (already enabled: {result_dict['ct_enabled_already_count']})")
                    print(f"   CT disabled: {result_dict['ct_disabled_count']} (already disabled: {result_dict['ct_disabled_already_count']})")
                    
                    return result_dict
                    
        except Exception as e:
            print(f"❌ Bulk CDC/CT operation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'schema': schema_name,
                'mode': mode,
                'message': str(e)
            }

