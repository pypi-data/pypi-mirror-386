#!/usr/bin/env python3
"""
SimpleMonitorMySQL.py - MySQL specific monitoring implementation

This module provides MySQL specific performance and schema monitoring capabilities.
"""

import datetime
import sqlalchemy as sa
from sqlalchemy import text
from typing import Dict, Any, List
from .SimpleMonitorBase import MonitorProviderBase, PerformanceMetrics, SchemaMetrics

class MySQLMonitorProvider(MonitorProviderBase):
    """MySQL specific monitoring implementation"""
    
    def get_default_schema_name(self) -> str:
        """Get the default schema name for MySQL"""
        return 'default'
    
    def capture_performance_metrics(self, timestamp: datetime.datetime) -> PerformanceMetrics:
        """Capture MySQL specific performance metrics"""
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
            
            # CPU utilization and system info (MySQL doesn't have direct CPU metrics, use approximation)
            try:
                # Use thread activity as CPU approximation and get system info
                # Use SHOW STATUS and SHOW VARIABLES for Azure MySQL compatibility
                threads_running_query = text("SHOW STATUS LIKE 'Threads_running'")
                max_connections_query = text("SHOW VARIABLES LIKE 'max_connections'")
                buffer_pool_query = text("SHOW VARIABLES LIKE 'innodb_buffer_pool_size'")
                
                threads_result = conn.execute(threads_running_query).fetchone()
                max_conn_result = conn.execute(max_connections_query).fetchone()
                buffer_result = conn.execute(buffer_pool_query).fetchone()
                
                threads_running = int(threads_result[1]) if threads_result else 0
                max_connections = int(max_conn_result[1]) if max_conn_result else 100
                buffer_pool_bytes = int(buffer_result[1]) if buffer_result else 0
                
                # Calculate derived values
                raw_cpu = threads_running * 10.0  # Rough approximation
                buffer_pool_gb = buffer_pool_bytes / 1024 / 1024 / 1024
                    
                # Ensure CPU percentage is reasonable (0-100%)
                cpu_percent = min(max(raw_cpu, 0.0), 100.0)
                
                # Estimate CPU count from max_connections (rough approximation)
                cpu_count = max(1, min(max_connections // 50, 16))  # Rough estimate
                max_memory_gb = max(buffer_pool_gb * 1.5, 1.0)  # Buffer pool is typically 70-80% of RAM
                
                print(f"🔍 System Info: ~{cpu_count} CPUs (est), Max Memory: ~{max_memory_gb:.1f} GB (est), CPU: {cpu_percent:.1f}%")
            except Exception as e:
                print(f"⚠️ Could not capture CPU metrics: {e}")
                cpu_count = 1
                max_memory_gb = 1.0
            
            # Memory usage - from performance_schema
            try:
                memory_query = text("""
                    SELECT 
                        COALESCE(
                            (SELECT SUM(CURRENT_NUMBER_OF_BYTES_USED) / 1024.0 / 1024.0 / 1024.0
                             FROM performance_schema.memory_summary_global_by_event_name 
                             WHERE EVENT_NAME LIKE 'memory/%'), 
                            0.0
                        ) AS memory_gb
                """)
                memory_result = conn.execute(memory_query).fetchone()
                memory_gb = float(memory_result[0]) if memory_result and memory_result[0] else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture memory metrics: {e}")
            
            # I/O metrics from SHOW GLOBAL STATUS
            try:
                # Use SHOW STATUS for Azure MySQL compatibility
                pages_read_query = text("SHOW STATUS LIKE 'Innodb_pages_read'")
                pages_written_query = text("SHOW STATUS LIKE 'Innodb_pages_written'")
                data_read_query = text("SHOW STATUS LIKE 'Innodb_data_read'")
                data_written_query = text("SHOW STATUS LIKE 'Innodb_data_written'")
                
                pages_read_result = conn.execute(pages_read_query).fetchone()
                pages_written_result = conn.execute(pages_written_query).fetchone()
                data_read_result = conn.execute(data_read_query).fetchone()
                data_written_result = conn.execute(data_written_query).fetchone()
                
                pages_read = int(pages_read_result[1]) if pages_read_result else 0
                pages_written = int(pages_written_result[1]) if pages_written_result else 0
                data_read = int(data_read_result[1]) if data_read_result else 0
                data_written = int(data_written_result[1]) if data_written_result else 0
                
                # Convert to per-second approximations (these are cumulative)
                io_reads_per_sec = float(pages_read) / 3600 if pages_read else 0.0  # Rough hourly average
                io_writes_per_sec = float(pages_written) / 3600 if pages_written else 0.0
                io_read_bytes_per_sec = float(data_read) / 3600 if data_read else 0.0
                io_write_bytes_per_sec = float(data_written) / 3600 if data_written else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture I/O metrics: {e}")
            
            # Buffer pool hit ratio
            try:
                # Use SHOW STATUS for buffer pool metrics
                reads_query = text("SHOW STATUS LIKE 'Innodb_buffer_pool_reads'")
                requests_query = text("SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests'")
                
                reads_result = conn.execute(reads_query).fetchone()
                requests_result = conn.execute(requests_query).fetchone()
                
                reads = int(reads_result[1]) if reads_result else 0
                requests = int(requests_result[1]) if requests_result else 0
                
                if requests > 0:
                    buffer_cache_hit_ratio = (1 - (reads / requests)) * 100
                else:
                    buffer_cache_hit_ratio = 0.0
            except Exception as e:
                print(f"⚠️ Could not capture buffer pool metrics: {e}")
            
            # Connection metrics
            try:
                # Use SHOW STATUS for connection metrics
                threads_query = text("SHOW STATUS LIKE 'Threads_connected'")
                processlist_query = text("SELECT COUNT(*) FROM information_schema.PROCESSLIST WHERE STATE LIKE '%lock%'")
                
                threads_result = conn.execute(threads_query).fetchone()
                processlist_result = conn.execute(processlist_query).fetchone()
                
                active_connections = int(threads_result[1]) if threads_result else 0
                blocking_sessions = int(processlist_result[0]) if processlist_result else 0
            except Exception as e:
                print(f"⚠️ Could not capture connection metrics: {e}")
            
            # Capture InnoDB log file size (WAL equivalent for MySQL)
            try:
                # Use SHOW STATUS for InnoDB log metrics
                log_query = text("SHOW STATUS LIKE 'Innodb_os_log_written'")
                log_result = conn.execute(log_query).fetchone()
                
                log_written_bytes = int(log_result[1]) if log_result else 0
                wal_size_mb = log_written_bytes / 1024.0 / 1024.0
            except Exception as e:
                print(f"⚠️ Could not capture InnoDB log size: {e}")
            
            # Network metrics
            try:
                # Use SHOW STATUS for network metrics
                sent_query = text("SHOW STATUS LIKE 'Bytes_sent'")
                received_query = text("SHOW STATUS LIKE 'Bytes_received'")
                
                sent_result = conn.execute(sent_query).fetchone()
                received_result = conn.execute(received_query).fetchone()
                
                bytes_sent = int(sent_result[1]) if sent_result else 0
                bytes_received = int(received_result[1]) if received_result else 0
                
                network_kb_per_sec = (bytes_sent + bytes_received) / 1024.0 / 3600.0
            except Exception as e:
                print(f"⚠️ Could not capture network metrics: {e}")
            
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
        """Capture MySQL specific schema metrics"""
        with self.engine.connect() as conn:
            table_metrics = []
            index_metrics = []
            total_size_bytes = 0
            
            try:
                # Get current database name if schema_name is 'default'
                if schema_name == 'default':
                    db_query = text("SELECT DATABASE()")
                    db_result = conn.execute(db_query).fetchone()
                    schema_name = db_result[0] if db_result and db_result[0] else 'information_schema'
                
                # Table metrics query
                table_query = text("""
                    SELECT 
                        TABLE_NAME,
                        COALESCE(TABLE_ROWS, 0) AS row_count,
                        COALESCE(DATA_LENGTH + INDEX_LENGTH, 0) AS size_bytes
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = :schema_name
                    AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY size_bytes DESC
                """)
                
                table_result = conn.execute(table_query, {'schema_name': schema_name}).fetchall()
                
                for row in table_result:
                    table_name = row[0]
                    row_count = int(row[1]) if row[1] else 0
                    size_bytes = int(row[2]) if row[2] else 0
                    
                    table_metrics.append({
                        'table_name': table_name,
                        'schema_name': schema_name,
                        'row_count': row_count,
                        'size_bytes': size_bytes
                    })
                    
                    total_size_bytes += size_bytes
            
            except Exception as e:
                print(f"⚠️ Could not capture table metrics: {e}")
            
            # Index metrics
            try:
                index_query = text("""
                    SELECT 
                        INDEX_NAME,
                        TABLE_NAME,
                        INDEX_TYPE,
                        COALESCE(
                            (SELECT SUM(STAT_VALUE * @@innodb_page_size) 
                             FROM mysql.innodb_index_stats 
                             WHERE database_name = :schema_name 
                             AND table_name = CONCAT(:schema_name, '/', s.TABLE_NAME)
                             AND index_name = s.INDEX_NAME 
                             AND stat_name = 'size'), 
                            0
                        ) AS size_bytes
                    FROM information_schema.STATISTICS s
                    WHERE s.TABLE_SCHEMA = :schema_name
                    GROUP BY INDEX_NAME, TABLE_NAME, INDEX_TYPE
                    ORDER BY size_bytes DESC
                """)
                
                index_result = conn.execute(index_query, {'schema_name': schema_name}).fetchall()
                
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
