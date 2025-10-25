#!/usr/bin/env python3
"""
LfcCDCPostgreSQL.py - PostgreSQL CDC Provider

This module provides PostgreSQL-specific logical replication operations.

PostgreSQL Strategy:
- Logical Replication with REPLICA IDENTITY
- DEFAULT for tables with primary keys
- FULL for tables without primary keys
"""

import sqlalchemy as sa
from typing import Dict, Any
from .LfcCDCBase import LfcCDCProviderBase


class PostgreSQLCDCProvider(LfcCDCProviderBase):
    """PostgreSQL-specific logical replication implementation"""
    
    def get_default_schema(self) -> str:
        """Get default schema for PostgreSQL"""
        return 'lfcddemo'
    
    def _has_primary_key(self, table_name: str) -> bool:
        """Check if table has a primary key"""
        try:
            with self.engine.connect() as conn:
                query = sa.text("""
                    SELECT COUNT(*)
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'PRIMARY KEY'
                    AND table_name = :table_name
                    AND table_schema = :schema
                """)
                result = conn.execute(query, {
                    'table_name': table_name,
                    'schema': self.schema or 'public'
                }).scalar()
                
                return result > 0
        except Exception as e:
            print(f"⚠️ Error checking primary key for {table_name}: {e}")
            return False
    
    def enable_cdc_for_table(self, table_name: str, has_primary_key: bool = None) -> Dict[str, Any]:
        """Enable logical replication for PostgreSQL table"""
        qualified_name = self.get_qualified_table_name(table_name)
        
        # Use provided primary key status or query database
        if has_primary_key is not None:
            has_pk = has_primary_key
        else:
            has_pk = self._has_primary_key(table_name)
        
        try:
            with self.engine.connect() as conn:
                # Set replica identity based on primary key existence
                if has_pk:
                    # Use primary key for replica identity
                    replica_identity_sql = sa.text(f"""
                        ALTER TABLE {qualified_name} REPLICA IDENTITY DEFAULT
                    """)
                else:
                    # Use full row for replica identity (no primary key)
                    replica_identity_sql = sa.text(f"""
                        ALTER TABLE {qualified_name} REPLICA IDENTITY FULL
                    """)
                
                conn.execute(replica_identity_sql)
                conn.commit()
                
                method = 'Logical Replication (PK)' if has_pk else 'Logical Replication (Full)'
                print(f"✅ {method} enabled for table: {qualified_name}")
                
                return {
                    'table_name': table_name,
                    'qualified_name': qualified_name,
                    'has_primary_key': has_pk,
                    'method': method,
                    'status': 'enabled',
                    'message': f'Replica identity set to {"DEFAULT" if has_pk else "FULL"}'
                }
        except Exception as e:
            print(f"⚠️ Failed to enable logical replication for {qualified_name}: {e}")
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'has_primary_key': has_pk,
                'method': 'Logical Replication',
                'status': 'error',
                'message': str(e)
            }
    
    def disable_cdc_for_table(self, table_name: str) -> Dict[str, Any]:
        """Disable logical replication for PostgreSQL table"""
        qualified_name = self.get_qualified_table_name(table_name)
        
        try:
            with self.engine.connect() as conn:
                # Reset replica identity to default (which effectively disables it)
                disable_replica = sa.text(f"""
                    ALTER TABLE {qualified_name} REPLICA IDENTITY DEFAULT
                """)
                
                conn.execute(disable_replica)
                conn.commit()
                
                print(f"✅ Logical replication disabled for table: {qualified_name}")
                return {
                    'table_name': table_name,
                    'qualified_name': qualified_name,
                    'method': 'Logical Replication',
                    'status': 'disabled',
                    'message': 'Replica identity reset to DEFAULT'
                }
        except Exception as e:
            print(f"⚠️ Failed to disable logical replication for {qualified_name}: {e}")
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'method': 'Logical Replication',
                'status': 'error',
                'message': str(e)
            }
    
    def get_cdc_status(self, table_name: str, has_primary_key: bool = None) -> Dict[str, Any]:
        """Get logical replication status for PostgreSQL table"""
        qualified_name = self.get_qualified_table_name(table_name)
        has_pk = has_primary_key if has_primary_key is not None else self._has_primary_key(table_name)
        
        try:
            with self.engine.connect() as conn:
                replica_query = sa.text("""
                    SELECT relreplident FROM pg_class c
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE c.relname = :table_name AND n.nspname = :schema
                """)
                
                result = conn.execute(replica_query, {
                    'table_name': table_name,
                    'schema': self.schema or 'public'
                }).fetchone()
                
                if result:
                    replica_identity = result[0]
                    replica_status = {
                        'd': 'DEFAULT (Primary Key)',
                        'f': 'FULL (All Columns)',
                        'i': 'INDEX',
                        'n': 'NOTHING'
                    }.get(replica_identity, 'UNKNOWN')
                    
                    enabled = replica_identity in ['d', 'f', 'i']
                else:
                    replica_status = 'TABLE_NOT_FOUND'
                    enabled = False
                
                return {
                    'table_name': table_name,
                    'qualified_name': qualified_name,
                    'has_primary_key': has_pk,
                    'replica_identity': replica_status,
                    'logical_replication_enabled': enabled,
                    'cdc_enabled': enabled and not has_pk,  # For consistency with SQL Server
                    'ct_enabled': enabled and has_pk,       # For consistency with SQL Server
                    'recommended_method': 'Logical Replication (PK)' if has_pk else 'Logical Replication (Full)',
                    'status': 'enabled' if enabled else 'disabled'
                }
        except Exception as e:
            return {
                'table_name': table_name,
                'qualified_name': qualified_name,
                'status': 'error',
                'message': str(e)
            }
    
    def cleanup_orphaned_cdc_instances(self) -> Dict[str, Any]:
        """PostgreSQL doesn't have orphaned CDC instances like SQL Server"""
        return {
            'status': 'not_applicable',
            'message': 'PostgreSQL logical replication does not create orphaned instances',
            'cleaned_instances': 0
        }

