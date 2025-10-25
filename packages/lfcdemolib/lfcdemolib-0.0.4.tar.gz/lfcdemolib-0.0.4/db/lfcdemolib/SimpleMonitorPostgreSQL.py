#!/usr/bin/env python3
"""
SimpleMonitorPostgreSQL.py - PostgreSQL specific monitoring implementation

This module provides PostgreSQL specific performance and schema monitoring capabilities.
"""

import datetime
import sqlalchemy as sa
from sqlalchemy import text
from typing import Dict, Any, List
from .SimpleMonitorBase import MonitorProviderBase, PerformanceMetrics, SchemaMetrics

class PostgreSQLMonitorProvider(MonitorProviderBase):
    """PostgreSQL specific monitoring implementation"""
    
    def get_default_schema_name(self) -> str:
        """Get the default schema name for PostgreSQL"""
        return 'public'
    
    def capture_performance_metrics(self, timestamp: datetime.datetime) -> PerformanceMetrics:
        """Capture PostgreSQL specific performance metrics"""
        with self.engine.connect() as conn:
            # Initialize default values
            cpu_percent = 0.0
            memory_gb = 0.0
            io_reads_per_sec = 0.0
            io_writes_per_sec = 0.0
            io_read_bytes_per_sec = 0.0
            io_write_bytes_per_sec = 0.0
            network_kb_per_sec = 0.0
            buffer_cache_hit_ratio = 0.0
            active_connections = 0
            blocking_sessions = 0
            wal_size_mb = 0.0
            
            # Get current database name
            try:
                db_query = text("SELECT current_database()")
                db_result = conn.execute(db_query).fetchone()
                current_db = db_result[0] if db_result else 'postgres'
            except Exception:
                current_db = 'postgres'
            
            # CPU utilization and system info (PostgreSQL doesn't have direct CPU metrics, use connection activity)
            try:
                cpu_query = text("""
                    SELECT 
                        COALESCE(
                            (SELECT COUNT(*) * 5.0  -- Rough approximation
                             FROM pg_stat_activity 
                             WHERE state = 'active' AND datname = :db_name), 
                            0.0
                        ) AS cpu_percent,
                        -- Get max connections as proxy for system capacity
                        COALESCE(
                            (SELECT setting::int 
                             FROM pg_settings 
                             WHERE name = 'max_connections'), 
                            100
                        ) AS max_connections,
                        -- Get shared buffers as proxy for available memory
                        COALESCE(
                            (SELECT setting::bigint * 8192 / 1024 / 1024 / 1024  -- Convert 8KB blocks to GB
                             FROM pg_settings 
                             WHERE name = 'shared_buffers'), 
                            0.0
                        ) AS shared_buffers_gb
                """)
                cpu_result = conn.execute(cpu_query, {'db_name': current_db}).fetchone()
                if cpu_result:
                    raw_cpu = float(cpu_result[0]) if cpu_result[0] else 0.0
                    max_connections = int(cpu_result[1]) if cpu_result[1] else 100
                    shared_buffers_gb = float(cpu_result[2]) if cpu_result[2] else 0.0
                    
                    # Ensure CPU percentage is reasonable (0-100%)
                    cpu_percent = min(max(raw_cpu, 0.0), 100.0)
                    
                    # Estimate CPU count from max_connections (rough approximation)
                    cpu_count = max(1, min(max_connections // 25, 16))  # Rough estimate
                    max_memory_gb = max(shared_buffers_gb * 4, 1.0)  # Shared buffers is typically 25% of RAM
                    
                    print(f"🔍 System Info: ~{cpu_count} CPUs (est), Max Memory: ~{max_memory_gb:.1f} GB (est), CPU: {cpu_percent:.1f}%")
                else:
                    cpu_percent = 0.0
                    cpu_count = 1
                    max_memory_gb = 1.0
            except Exception as e:
                print(f"⚠️ Could not capture CPU metrics: {e}")
                cpu_count = 1
                max_memory_gb = 1.0
            
            # Memory usage - from pg_stat_bgwriter and system settings
            try:
                memory_query = text("""
                    SELECT 
                        COALESCE(
                            (SELECT setting::bigint * 8 / 1024.0 / 1024.0  -- Convert 8KB pages to GB
                             FROM pg_settings 
                             WHERE name = 'shared_buffers'), 
                            0.0
                        ) AS shared_buffers_gb,
                        COALESCE(
                            (SELECT buffers_alloc * 8 / 1024.0 / 1024.0  -- Convert 8KB pages to GB
                             FROM pg_stat_bgwriter), 
                            0.0
                        ) AS allocated_buffers_gb
                """)
                memory_result = conn.execute(memory_query).fetchone()
                if memory_result:
                    memory_gb = float(memory_result[0]) if memory_result[0] else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture memory metrics: {e}")
            
            # I/O metrics from pg_stat_database
            try:
                io_query = text("""
                    SELECT 
                        COALESCE(blks_read, 0) AS blocks_read,
                        COALESCE(blks_hit, 0) AS blocks_hit,
                        COALESCE(tup_returned + tup_fetched, 0) AS tuples_read,
                        COALESCE(tup_inserted + tup_updated + tup_deleted, 0) AS tuples_written
                    FROM pg_stat_database 
                    WHERE datname = :db_name
                """)
                io_result = conn.execute(io_query, {'db_name': current_db}).fetchone()
                if io_result:
                    # Convert to per-second approximations (these are cumulative)
                    io_reads_per_sec = float(io_result[0]) / 3600 if io_result[0] else 0.0  # Rough hourly average
                    io_writes_per_sec = float(io_result[3]) / 3600 if io_result[3] else 0.0
                    # Estimate bytes (8KB per block)
                    io_read_bytes_per_sec = io_reads_per_sec * 8192
                    io_write_bytes_per_sec = io_writes_per_sec * 8192
            except Exception as e:
                print(f"⚠️ Could not capture I/O metrics: {e}")
            
            # Buffer cache hit ratio
            try:
                buffer_query = text("""
                    SELECT 
                        COALESCE(
                            CASE 
                                WHEN (blks_read + blks_hit) > 0 
                                THEN (blks_hit::float / (blks_read + blks_hit)) * 100 
                                ELSE 0 
                            END, 
                            0
                        ) AS buffer_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = :db_name
                """)
                buffer_result = conn.execute(buffer_query, {'db_name': current_db}).fetchone()
                buffer_cache_hit_ratio = float(buffer_result[0]) if buffer_result and buffer_result[0] else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture buffer cache metrics: {e}")
            
            # Connection metrics
            try:
                conn_query = text("""
                    SELECT 
                        COUNT(*) AS active_connections,
                        COALESCE(
                            (SELECT COUNT(*) 
                             FROM pg_stat_activity 
                             WHERE wait_event_type = 'Lock' AND datname = :db_name), 
                            0
                        ) AS blocking_sessions
                    FROM pg_stat_activity 
                    WHERE datname = :db_name AND state IS NOT NULL
                """)
                conn_result = conn.execute(conn_query, {'db_name': current_db}).fetchone()
                if conn_result:
                    active_connections = int(conn_result[0]) if conn_result[0] else 0
                    blocking_sessions = int(conn_result[1]) if conn_result[1] else 0
            except Exception as e:
                print(f"⚠️ Could not capture connection metrics: {e}")
            
            # Capture WAL size for PostgreSQL
            try:
                wal_query = text("""
                    SELECT 
                        COALESCE(
                            pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') / 1024.0 / 1024.0,
                            0.0
                        ) AS wal_size_mb
                """)
                wal_result = conn.execute(wal_query).fetchone()
                wal_size_mb = float(wal_result[0]) if wal_result and wal_result[0] else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture WAL size: {e}")
            
            # Network metrics (PostgreSQL doesn't have direct network metrics)
            network_kb_per_sec = 0.0
            
            return PerformanceMetrics(
                timestamp=timestamp,
                cpu_percent=cpu_percent,
                memory_gb=memory_gb,
                io_reads_per_sec=io_reads_per_sec,
                io_writes_per_sec=io_writes_per_sec,
                io_read_bytes_per_sec=io_read_bytes_per_sec,
                io_write_bytes_per_sec=io_write_bytes_per_sec,
                network_kb_per_sec=network_kb_per_sec,
                buffer_cache_hit_ratio=buffer_cache_hit_ratio,
                active_connections=active_connections,
                blocking_sessions=blocking_sessions,
                wal_size_mb=wal_size_mb,
                cpu_count=cpu_count,
                max_memory_gb=max_memory_gb,
                dml_metrics=self.dml_operation_tracker
            )
    
    def capture_schema_metrics(self, timestamp: datetime.datetime, schema_name: str) -> SchemaMetrics:
        """Capture PostgreSQL specific schema metrics"""
        with self.engine.connect() as conn:
            table_metrics = []
            index_metrics = []
            total_size_bytes = 0
            
            try:
                # Table metrics query
                table_query = text("""
                    SELECT 
                        schemaname,
                        relname as tablename,
                        n_tup_ins + n_tup_upd + n_tup_del as total_changes,
                        n_live_tup as estimated_rows,
                        pg_total_relation_size(schemaname||'.'||relname) as total_size_bytes,
                        pg_relation_size(schemaname||'.'||relname) as table_size_bytes
                    FROM pg_stat_user_tables 
                    WHERE schemaname = :schema_name
                    ORDER BY total_size_bytes DESC
                """)
                
                table_result = conn.execute(table_query, {'schema_name': schema_name}).fetchall()
                
                for row in table_result:
                    schema_name_result = row[0]
                    table_name = row[1]
                    total_changes = int(row[2]) if row[2] else 0
                    estimated_rows = int(row[3]) if row[3] else 0
                    size_bytes = int(row[4]) if row[4] else 0
                    
                    table_metrics.append({
                        'table_name': table_name,
                        'schema_name': schema_name_result,
                        'row_count': estimated_rows,
                        'size_bytes': size_bytes,
                        'total_changes': total_changes
                    })
                    
                    total_size_bytes += size_bytes
            
            except Exception as e:
                print(f"⚠️ Could not capture table metrics: {e}")
            
            # Index metrics
            try:
                index_query = text("""
                    SELECT 
                        i.schemaname,
                        i.relname as tablename,
                        i.indexrelname as indexname,
                        pg_relation_size(i.schemaname||'.'||i.indexrelname) as size_bytes,
                        idx_scan as scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes i
                    WHERE i.schemaname = :schema_name
                    ORDER BY size_bytes DESC
                """)
                
                index_result = conn.execute(index_query, {'schema_name': schema_name}).fetchall()
                
                for row in index_result:
                    index_metrics.append({
                        'schema_name': row[0],
                        'table_name': row[1],
                        'index_name': row[2],
                        'size_bytes': int(row[3]) if row[3] else 0,
                        'scans': int(row[4]) if row[4] else 0,
                        'tuples_read': int(row[5]) if row[5] else 0,
                        'tuples_fetched': int(row[6]) if row[6] else 0
                    })
            
            except Exception as e:
                print(f"⚠️ Could not capture index metrics: {e}")
            
            return SchemaMetrics(
                timestamp=timestamp,
                schema_name=schema_name,
                total_size_bytes=total_size_bytes,
                table_metrics=table_metrics,
                index_metrics=index_metrics
            )
