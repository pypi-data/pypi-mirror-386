#!/usr/bin/env python3
"""
SimpleMonitorSqlServer.py - SQL Server specific monitoring implementation

This module provides SQL Server specific performance and schema monitoring capabilities.
"""

import datetime
import sqlalchemy as sa
from sqlalchemy import text
from typing import Dict, Any, List
from .SimpleMonitorBase import MonitorProviderBase, PerformanceMetrics, SchemaMetrics

class SqlServerMonitorProvider(MonitorProviderBase):
    """SQL Server specific monitoring implementation"""
    
    def get_default_schema_name(self) -> str:
        """Get the default schema name for SQL Server"""
        return 'dbo'
    
    def capture_performance_metrics(self, timestamp: datetime.datetime) -> PerformanceMetrics:
        """Capture SQL Server specific performance metrics"""
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
            
            # CPU utilization and system info - enhanced for Azure SQL Database compatibility
            try:
                cpu_query = text("""
                    SELECT 
                        -- CPU usage percentage (should be 0-100)
                        COALESCE(
                            (SELECT TOP 1 CAST(cntr_value AS FLOAT) 
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name = 'CPU usage %' 
                             AND instance_name = 'default'), 
                            COALESCE(
                                (SELECT TOP 1 CAST(cntr_value AS FLOAT) 
                                 FROM sys.dm_os_performance_counters 
                                 WHERE counter_name LIKE '%CPU usage%' 
                                 AND instance_name = '_Total'), 
                                0.0
                            )
                        ) AS cpu_percent,
                        -- CPU count
                        COALESCE(
                            (SELECT TOP 1 CAST(cpu_count AS FLOAT)
                             FROM sys.dm_os_sys_info), 
                            1.0
                        ) AS cpu_count,
                        -- Max server memory in GB (limit to reasonable values for Azure SQL)
                        COALESCE(
                            (SELECT TOP 1 
                                CASE 
                                    WHEN CAST(value_in_use AS FLOAT) > 100000 THEN 32.0  -- Cap at 32GB for Azure SQL Basic/Standard
                                    ELSE CAST(value_in_use AS FLOAT) / 1024.0  -- Convert MB to GB
                                END
                             FROM sys.configurations 
                             WHERE name = 'max server memory (MB)'), 
                            2.0  -- Default to 2GB for Azure SQL Basic
                        ) AS max_memory_gb
                """)
                cpu_result = conn.execute(cpu_query).fetchone()
                if cpu_result:
                    raw_cpu = float(cpu_result[0]) if cpu_result[0] else 0.0
                    cpu_count = int(cpu_result[1]) if cpu_result[1] else 1
                    max_memory_gb = float(cpu_result[2]) if cpu_result[2] else 0.0
                    
                    # Ensure CPU percentage is reasonable (0-100%)
                    cpu_percent = min(max(raw_cpu, 0.0), 100.0)
                    
                    print(f"🔍 System Info: {cpu_count} CPUs, Max Memory: {max_memory_gb:.1f} GB, CPU: {cpu_percent:.1f}%")
                else:
                    cpu_percent = 0.0
                    cpu_count = 1
                    max_memory_gb = 0.0
            except Exception as e:
                print(f"⚠️ Could not capture CPU metrics: {e}")
                cpu_count = 1
                max_memory_gb = 0.0
            
            # Memory usage - enhanced for Azure SQL Database
            try:
                memory_query = text("""
                    SELECT 
                        COALESCE(
                            (SELECT CAST(cntr_value AS FLOAT) / 1024.0 / 1024.0  -- Convert KB to GB
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name = 'Total Server Memory (KB)'), 
                            COALESCE(
                                (SELECT CAST(value_in_use AS FLOAT) * 8 / 1024.0 / 1024.0  -- Convert MB to GB
                                 FROM sys.configurations 
                                 WHERE name = 'max server memory (MB)'), 
                                0.0
                            )
                        ) AS total_memory_gb,
                        COALESCE(
                            (SELECT CAST(cntr_value AS FLOAT) / 1024.0 / 1024.0  -- Convert KB to GB
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name = 'Target Server Memory (KB)'), 
                            0.0
                        ) AS target_memory_gb
                """)
                memory_result = conn.execute(memory_query).fetchone()
                memory_gb = float(memory_result[0]) if memory_result and memory_result[0] else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture memory metrics: {e}")
            
            # I/O metrics - improved to get consistent reads/writes and bytes
            try:
                io_query = text("""
                    SELECT 
                        -- Physical I/O operations per second
                        COALESCE(
                            (SELECT TOP 1 cntr_value 
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name = 'Page reads/sec'), 
                            0
                        ) AS reads_per_sec,
                        COALESCE(
                            (SELECT TOP 1 cntr_value 
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name = 'Page writes/sec'), 
                            0
                        ) AS writes_per_sec,
                        -- Logical I/O operations per second (alternative)
                        COALESCE(
                            (SELECT TOP 1 cntr_value 
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name = 'Batch Requests/sec'), 
                            0
                        ) AS batch_requests_per_sec,
                        -- Bytes per second metrics
                        COALESCE(
                            (SELECT TOP 1 cntr_value 
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name = 'Log Bytes Flushed/sec'), 
                            0
                        ) AS log_bytes_per_sec,
                        COALESCE(
                            (SELECT TOP 1 cntr_value 
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name LIKE '%Bytes/sec%' 
                             AND counter_name LIKE '%Read%'), 
                            0
                        ) AS read_bytes_per_sec_alt,
                        -- Calculate approximate write bytes from pages (8KB per page)
                        COALESCE(
                            (SELECT TOP 1 cntr_value * 8192  -- 8KB per page
                             FROM sys.dm_os_performance_counters 
                             WHERE counter_name = 'Page writes/sec'), 
                            0
                        ) AS write_bytes_calculated
                """)
                io_result = conn.execute(io_query).fetchone()
                if io_result:
                    io_reads_per_sec = float(io_result[0]) if io_result[0] else 0.0
                    io_writes_per_sec = float(io_result[1]) if io_result[1] else 0.0
                    batch_requests_per_sec = float(io_result[2]) if io_result[2] else 0.0
                    log_bytes_per_sec = float(io_result[3]) if io_result[3] else 0.0
                    read_bytes_alt = float(io_result[4]) if io_result[4] else 0.0
                    write_bytes_calculated = float(io_result[5]) if io_result[5] else 0.0
                    
                    # Use the best available metrics
                    io_read_bytes_per_sec = read_bytes_alt if read_bytes_alt > 0 else (io_reads_per_sec * 8192)
                    io_write_bytes_per_sec = log_bytes_per_sec if log_bytes_per_sec > 0 else write_bytes_calculated
                    
                    # If we still don't have writes/sec but have batch requests, use that as approximation
                    if io_writes_per_sec == 0.0 and batch_requests_per_sec > 0:
                        io_writes_per_sec = batch_requests_per_sec * 0.1  # Rough approximation
                    
                    print(f"🔍 I/O Metrics: {io_reads_per_sec:.1f} reads/sec, {io_writes_per_sec:.1f} writes/sec")
                    print(f"   Read: {io_read_bytes_per_sec/1024/1024:.1f} MB/sec, Write: {io_write_bytes_per_sec/1024/1024:.1f} MB/sec")
            except Exception as e:
                print(f"⚠️ Could not capture I/O metrics: {e}")
                # Use fallback approach for I/O metrics
                try:
                    fallback_io_query = text("""
                        SELECT 
                            COALESCE(SUM(num_of_reads), 0) AS total_reads,
                            COALESCE(SUM(num_of_writes), 0) AS total_writes,
                            0 AS reads_per_sec,  -- Will be 0 for fallback
                            0 AS writes_per_sec,
                            0 AS read_bytes_per_sec,
                            0 AS write_bytes_per_sec
                        FROM sys.dm_io_virtual_file_stats(NULL, NULL)
                    """)
                    fallback_result = conn.execute(fallback_io_query).fetchone()
                    if fallback_result:
                        io_reads_per_sec = float(fallback_result[2])
                        io_writes_per_sec = float(fallback_result[3])
                        io_read_bytes_per_sec = float(fallback_result[4])
                        io_write_bytes_per_sec = float(fallback_result[5])
                except Exception as fallback_e:
                    print(f"⚠️ Fallback I/O metrics also failed: {fallback_e}")
            
            # Buffer cache metrics
            try:
                buffer_cache_query = text("""
                    SELECT 
                        CAST((a.cntr_value * 1.0 / b.cntr_value) * 100.0 AS DECIMAL(5,2)) AS buffer_cache_hit_ratio
                    FROM sys.dm_os_performance_counters a
                    JOIN sys.dm_os_performance_counters b ON a.object_name = b.object_name
                    WHERE a.counter_name = 'Buffer cache hit ratio'
                    AND b.counter_name = 'Buffer cache hit ratio base'
                    AND a.object_name LIKE '%Buffer Manager%'
                """)
                buffer_result = conn.execute(buffer_cache_query).fetchone()
                buffer_cache_hit_ratio = float(buffer_result[0]) if buffer_result else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture buffer cache metrics: {e}")
            
            # Connection metrics
            try:
                connections_query = text("""
                    SELECT 
                        COUNT(*) AS active_connections,
                        COALESCE(
                            (SELECT COUNT(*) 
                             FROM sys.dm_exec_requests r
                             WHERE r.blocking_session_id > 0), 
                            0
                        ) AS blocking_sessions
                    FROM sys.dm_exec_sessions 
                    WHERE is_user_process = 1
                """)
                conn_result = conn.execute(connections_query).fetchone()
                if conn_result:
                    active_connections = int(conn_result[0]) if conn_result[0] else 0
                    blocking_sessions = int(conn_result[1]) if conn_result[1] else 0
            except Exception as e:
                print(f"⚠️ Could not capture connection metrics: {e}")
            
            # Capture transaction log size (WAL equivalent for SQL Server)
            try:
                wal_query = text("""
                    SELECT 
                        COALESCE(SUM(CAST(size AS FLOAT) * 8 / 1024.0), 0.0) AS log_size_mb
                    FROM sys.database_files 
                    WHERE type = 1  -- Log files only
                """)
                wal_result = conn.execute(wal_query).fetchone()
                wal_size_mb = float(wal_result[0]) if wal_result and wal_result[0] else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture transaction log size: {e}")
            
            # Network metrics (placeholder - SQL Server doesn't have easy network metrics)
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
        """Capture SQL Server specific schema metrics"""
        with self.engine.connect() as conn:
            table_metrics = []
            index_metrics = []
            total_size_bytes = 0
            
            # Check if Change Tracking is enabled to analyze both schemas
            is_ct_enabled = self._is_change_tracking_enabled()
            schemas_to_analyze = [schema_name]
            
            if is_ct_enabled and schema_name == 'dbo':
                schemas_to_analyze = ['dbo', 'cdc']
                schema_name = 'dbo+cdc'  # Update display name
            
            for current_schema in schemas_to_analyze:
                try:
                    # Enhanced query for Azure SQL Database compatibility
                    schema_query = text("""
                        SELECT 
                            t.name AS table_name,
                            COALESCE(p.row_count, 0) AS row_count,
                            COALESCE(
                                (SELECT SUM(a.total_pages) * 8 * 1024 
                                 FROM sys.allocation_units a 
                                 WHERE a.container_id IN (
                                     SELECT container_id FROM sys.partitions WHERE object_id = t.object_id
                                 )), 
                                0
                            ) AS size_bytes,
                            :schema_name AS schema_name
                        FROM sys.tables t
                        LEFT JOIN sys.dm_db_partition_stats p ON t.object_id = p.object_id AND p.index_id IN (0,1)
                        WHERE t.schema_id = SCHEMA_ID(:schema_name)
                        ORDER BY size_bytes DESC
                    """)
                    
                    schema_result = conn.execute(schema_query, {'schema_name': current_schema}).fetchall()
                    
                    for row in schema_result:
                        table_name = row[0]
                        row_count = int(row[1]) if row[1] else 0
                        size_bytes = int(row[2]) if row[2] else 0
                        table_schema = row[3]
                        
                        table_metrics.append({
                            'table_name': table_name,
                            'schema_name': table_schema,
                            'row_count': row_count,
                            'size_bytes': size_bytes
                        })
                        
                        total_size_bytes += size_bytes
                
                except Exception as e:
                    print(f"⚠️ Could not capture schema metrics for {current_schema}: {e}")
                    # Fallback: at least try to get table names
                    try:
                        fallback_query = text("""
                            SELECT name AS table_name
                            FROM sys.tables 
                            WHERE schema_id = SCHEMA_ID(:schema_name)
                        """)
                        fallback_result = conn.execute(fallback_query, {'schema_name': current_schema}).fetchall()
                        
                        for row in fallback_result:
                            table_metrics.append({
                                'table_name': row[0],
                                'schema_name': current_schema,
                                'row_count': 0,
                                'size_bytes': 0
                            })
                    except Exception as fallback_e:
                        print(f"⚠️ Fallback schema query also failed for {current_schema}: {fallback_e}")
            
            # Get index metrics (simplified for Azure SQL Database)
            try:
                index_query = text("""
                    SELECT 
                        i.name AS index_name,
                        t.name AS table_name,
                        i.type_desc AS index_type,
                        COALESCE(
                            (SELECT SUM(a.total_pages) * 8 * 1024 
                             FROM sys.allocation_units a 
                             WHERE a.container_id IN (
                                 SELECT container_id FROM sys.partitions WHERE object_id = i.object_id AND index_id = i.index_id
                             )), 
                            0
                        ) AS size_bytes
                    FROM sys.indexes i
                    JOIN sys.tables t ON i.object_id = t.object_id
                    WHERE t.schema_id = SCHEMA_ID(:schema_name)
                    AND i.index_id > 0  -- Exclude heap
                    ORDER BY size_bytes DESC
                """)
                
                index_result = conn.execute(index_query, {'schema_name': schemas_to_analyze[0]}).fetchall()
                
                for row in index_result:
                    index_metrics.append({
                        'index_name': row[0],
                        'table_name': row[1],
                        'index_type': row[2],
                        'size_bytes': int(row[3]) if row[3] else 0
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
    
    def _is_change_tracking_enabled(self) -> bool:
        """Check if Change Tracking is enabled on the current database for SQL Server."""
        try:
            with self.engine.connect() as conn:
                # For Azure SQL Database, sys.databases.is_change_tracking_on might not be directly accessible
                # Use sys.change_tracking_databases instead
                query = text("""
                    SELECT COUNT(*) 
                    FROM sys.change_tracking_databases 
                    WHERE database_id = DB_ID()
                """)
                result = conn.execute(query).scalar()
                return result > 0
        except Exception as e:
            print(f"⚠️ Could not check Change Tracking status: {e}")
            return False
