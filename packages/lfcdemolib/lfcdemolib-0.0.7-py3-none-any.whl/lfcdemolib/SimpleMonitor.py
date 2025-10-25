"""
SimpleMonitor - Database Performance and Impact Monitoring

This module provides comprehensive monitoring of database performance metrics
to assess the impact of DML operations, CDC/CT, and Lakeflow Connect operations.

Key Features:
- Real-time performance metrics (CPU, Memory, I/O, Network)
- Database and schema size monitoring
- Table row count estimation
- CDC/CT overhead analysis
- Lakeflow Connect impact assessment
- Before/after comparison reports
"""

import time
import datetime
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import sqlalchemy as sa
from sqlalchemy import text

# Import the new provider-based architecture
from .SimpleMonitorBase import MonitorProviderBase, PerformanceMetrics as BasePerformanceMetrics, SchemaMetrics as BaseSchemaMetrics, DMLOperationMetrics as BaseDMLOperationMetrics
from .SimpleMonitorSqlServer import SqlServerMonitorProvider
from .SimpleMonitorMySQL import MySQLMonitorProvider
from .SimpleMonitorPostgreSQL import PostgreSQLMonitorProvider


@dataclass
class DMLOperationMetrics:
    """Container for DML operation statistics"""
    insert_count: int = 0
    update_count: int = 0
    delete_count: int = 0
    total_operations: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_deleted: int = 0
    total_rows_affected: int = 0
    operation_duration_seconds: float = 0.0
    operations_per_second: float = 0.0
    rows_per_second: float = 0.0


@dataclass
class PerformanceMetrics:
    """Container for database performance metrics"""
    timestamp: datetime.datetime
    cpu_percent: float
    memory_gb: float  # Changed from memory_mb to memory_gb
    io_reads_per_sec: float
    io_writes_per_sec: float
    io_read_bytes_per_sec: float
    io_write_bytes_per_sec: float
    network_kb_per_sec: float
    buffer_cache_hit_ratio: float
    active_connections: int
    blocking_sessions: int
    wal_size_mb: float = 0.0  # Write-Ahead Log size in MB
    cpu_count: int = 1  # Number of CPU cores
    max_memory_gb: float = 0.0  # Maximum available memory in GB
    dml_metrics: DMLOperationMetrics = field(default_factory=DMLOperationMetrics)
    wait_stats: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Legacy compatibility property
    @property
    def memory_mb(self) -> float:
        """Legacy compatibility - returns memory in MB"""
        return self.memory_gb * 1024.0


@dataclass
class SchemaMetrics:
    """Container for schema and table size metrics"""
    timestamp: datetime.datetime
    schema_name: str
    total_size_bytes: int
    table_metrics: List[Dict[str, Any]] = field(default_factory=list)
    index_metrics: List[Dict[str, Any]] = field(default_factory=list)


class SimpleMonitor:
    """Database performance and impact monitoring system"""
    
    def __init__(self, engine: sa.Engine, schema: str = None):
        """Initialize monitor with database connection
        
        Args:
            engine: SQLAlchemy engine for database connection
            schema: Optional schema name to focus monitoring on
        """
        self.engine = engine
        self.schema = schema
        self.db_type = self._detect_database_type()
        self.baseline_metrics = None
        self.monitoring_active = False
        self.metrics_history = []
        self.dml_operation_tracker = DMLOperationMetrics()
        self.cdc_ct_status = None  # Store CDC/CT status for baseline
        
        # Initialize the appropriate provider
        self.provider = self._create_provider()
        
        print(f"🔍 SimpleMonitor initialized for {self.db_type}")
        if schema:
            print(f"   Focused on schema: {schema}")
    
    def _create_provider(self) -> MonitorProviderBase:
        """Create the appropriate monitoring provider for this database type"""
        if self.db_type == 'sqlserver':
            return SqlServerMonitorProvider(self.engine, self.db_type)
        elif self.db_type == 'mysql':
            return MySQLMonitorProvider(self.engine, self.db_type)
        elif self.db_type == 'postgresql':
            return PostgreSQLMonitorProvider(self.engine, self.db_type)
        else:
            # Fallback to SQL Server provider for unknown databases
            return SqlServerMonitorProvider(self.engine, self.db_type)
    
    def _detect_database_type(self) -> str:
        """Detect the database type from the engine"""
        dialect_name = self.engine.dialect.name.lower()
        if 'mysql' in dialect_name:
            return 'mysql'
        elif 'postgresql' in dialect_name:
            return 'postgresql'
        elif 'mssql' in dialect_name or 'sqlserver' in dialect_name:
            return 'sqlserver'
        elif 'oracle' in dialect_name:
            return 'oracle'
        else:
            return 'unknown'
    
    def capture_baseline(self) -> PerformanceMetrics:
        """Capture baseline performance metrics before operations
        
        Returns:
            PerformanceMetrics: Baseline performance snapshot
        """
        print("📊 Capturing baseline performance metrics...")
        self.baseline_metrics = self._capture_performance_metrics()
        print(f"✅ Baseline captured: CPU={self.baseline_metrics.cpu_percent:.1f}%, "
              f"Memory={self.baseline_metrics.memory_gb:.2f}GB, "
              f"I/O Reads={self.baseline_metrics.io_reads_per_sec:.1f}/sec, "
              f"I/O Writes={self.baseline_metrics.io_writes_per_sec:.1f}/sec, "
              f"Buffer Cache Hit Ratio={self.baseline_metrics.buffer_cache_hit_ratio:.2f}%")
        return self.baseline_metrics
    
    def _capture_performance_metrics(self) -> PerformanceMetrics:
        """Capture current performance metrics using the provider"""
        timestamp = datetime.datetime.now()
        
        # Use the provider to capture metrics
        base_metrics = self.provider.capture_performance_metrics(timestamp)
        
        # Convert to our local PerformanceMetrics format (they should be compatible)
        return PerformanceMetrics(
            timestamp=base_metrics.timestamp,
            cpu_percent=base_metrics.cpu_percent,
            memory_gb=base_metrics.memory_gb,
            io_reads_per_sec=base_metrics.io_reads_per_sec,
            io_writes_per_sec=base_metrics.io_writes_per_sec,
            io_read_bytes_per_sec=base_metrics.io_read_bytes_per_sec,
            io_write_bytes_per_sec=base_metrics.io_write_bytes_per_sec,
            network_kb_per_sec=base_metrics.network_kb_per_sec,
            buffer_cache_hit_ratio=base_metrics.buffer_cache_hit_ratio,
            active_connections=base_metrics.active_connections,
            blocking_sessions=base_metrics.blocking_sessions,
            wal_size_mb=base_metrics.wal_size_mb,
            cpu_count=base_metrics.cpu_count,
            max_memory_gb=base_metrics.max_memory_gb,
            dml_metrics=self.dml_operation_tracker
        )
    
    def _capture_sqlserver_metrics(self, timestamp: datetime.datetime) -> PerformanceMetrics:
        """Capture SQL Server specific performance metrics"""
        with self.engine.connect() as conn:
            # CPU utilization - use a simple fallback for Azure SQL Database compatibility
            cpu_query = text("""
                SELECT 
                    COALESCE(
                        (SELECT TOP 1 CAST(cntr_value AS FLOAT) 
                         FROM sys.dm_os_performance_counters 
                         WHERE counter_name LIKE '%CPU usage%' 
                         AND instance_name = '_Total'), 
                        0.0
                    ) AS cpu_percent
            """)
            
            # Memory usage - enhanced for Azure SQL Database
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
            
            # I/O statistics - enhanced with rate calculations (fixed subquery issue)
            io_query = text("""
                SELECT 
                    SUM(num_of_reads) AS total_reads,
                    SUM(num_of_writes) AS total_writes,
                    SUM(num_of_bytes_read) AS total_read_bytes,
                    SUM(num_of_bytes_written) AS total_write_bytes,
                    -- Get I/O rates from performance counters (use TOP 1 to avoid multiple values)
                    COALESCE(
                        (SELECT TOP 1 cntr_value 
                         FROM sys.dm_os_performance_counters 
                         WHERE counter_name = 'Page reads/sec' 
                         AND instance_name = '_Total'), 
                        0
                    ) AS reads_per_sec,
                    COALESCE(
                        (SELECT TOP 1 cntr_value 
                         FROM sys.dm_os_performance_counters 
                         WHERE counter_name = 'Page writes/sec' 
                         AND instance_name = '_Total'), 
                        0
                    ) AS writes_per_sec,
                    -- Get bytes per second from performance counters (use more specific matching)
                    COALESCE(
                        (SELECT TOP 1 cntr_value 
                         FROM sys.dm_os_performance_counters 
                         WHERE counter_name = 'Database pages/sec' 
                         AND instance_name = '_Total'), 
                        0
                    ) AS read_bytes_per_sec,
                    COALESCE(
                        (SELECT TOP 1 cntr_value 
                         FROM sys.dm_os_performance_counters 
                         WHERE counter_name = 'Log Bytes Flushed/sec' 
                         AND instance_name = '_Total'), 
                        0
                    ) AS write_bytes_per_sec
                FROM sys.dm_io_virtual_file_stats(NULL, NULL)
            """)
            
            # Buffer cache hit ratio
            buffer_cache_query = text("""
                SELECT 
                    CAST((a.cntr_value * 1.0 / b.cntr_value) * 100.0 AS DECIMAL(5,2)) AS buffer_cache_hit_ratio
                FROM sys.dm_os_performance_counters a
                JOIN sys.dm_os_performance_counters b ON a.object_name = b.object_name
                WHERE a.counter_name = 'Buffer cache hit ratio'
                AND b.counter_name = 'Buffer cache hit ratio base'
                AND a.object_name LIKE '%Buffer Manager%'
            """)
            
            # Active connections (Azure SQL Database compatible)
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
            
            # Wait statistics
            wait_stats_query = text("""
                SELECT TOP 10
                    wait_type,
                    wait_time_ms,
                    waiting_tasks_count,
                    signal_wait_time_ms
                FROM sys.dm_os_wait_stats
                WHERE wait_type NOT IN (
                    'CLR_SEMAPHORE', 'LAZYWRITER_SLEEP', 'RESOURCE_QUEUE', 'SLEEP_TASK',
                    'SLEEP_SYSTEMTASK', 'SQLTRACE_BUFFER_FLUSH', 'WAITFOR', 'LOGMGR_QUEUE',
                    'CHECKPOINT_QUEUE', 'REQUEST_FOR_DEADLOCK_SEARCH', 'XE_TIMER_EVENT',
                    'BROKER_TO_FLUSH', 'BROKER_TASK_STOP', 'CLR_MANUAL_EVENT', 'CLR_AUTO_EVENT'
                )
                AND wait_time_ms > 0
                ORDER BY wait_time_ms DESC
            """)
            
            # Execute queries with individual error handling
            cpu_percent = 0.0
            memory_gb = 0.0
            io_reads_per_sec = 0.0
            io_writes_per_sec = 0.0
            io_read_bytes_per_sec = 0.0
            io_write_bytes_per_sec = 0.0
            buffer_cache_hit_ratio = 0.0
            active_connections = 0
            blocking_sessions = 0
            wait_stats = {}
            
            # CPU metrics
            try:
                cpu_result = conn.execute(cpu_query).fetchone()
                cpu_percent = float(cpu_result[0]) if cpu_result and cpu_result[0] else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture CPU metrics: {e}")
            
            # Memory metrics
            try:
                memory_result = conn.execute(memory_query).fetchone()
                memory_gb = float(memory_result[0]) if memory_result and memory_result[0] else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture memory metrics: {e}")
            
            # I/O metrics
            try:
                io_result = conn.execute(io_query).fetchone()
                if io_result:
                    io_reads_per_sec = float(io_result[4]) if io_result[4] else 0.0
                    io_writes_per_sec = float(io_result[5]) if io_result[5] else 0.0
                    io_read_bytes_per_sec = float(io_result[6]) if io_result[6] else 0.0
                    io_write_bytes_per_sec = float(io_result[7]) if io_result[7] else 0.0
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
                buffer_result = conn.execute(buffer_cache_query).fetchone()
                buffer_cache_hit_ratio = float(buffer_result[0]) if buffer_result else 0.0
            except Exception as e:
                print(f"⚠️ Could not capture buffer cache metrics: {e}")
            
            # Connection metrics
            try:
                conn_result = conn.execute(connections_query).fetchone()
                active_connections = int(conn_result[0]) if conn_result else 0
                blocking_sessions = int(conn_result[1]) if conn_result else 0
            except Exception as e:
                print(f"⚠️ Could not capture connection metrics: {e}")
            
            # Wait statistics (optional)
            try:
                wait_results = conn.execute(wait_stats_query).fetchall()
                for row in wait_results:
                    wait_stats[row[0]] = {
                        'wait_time_ms': row[1],
                        'waiting_tasks': row[2],
                        'signal_wait_ms': row[3]
                    }
            except Exception as e:
                print(f"⚠️ Could not capture wait statistics: {e}")
            
            # Capture transaction log size (WAL equivalent for SQL Server)
            wal_size_mb = 0.0
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
            
            return PerformanceMetrics(
                timestamp=timestamp,
                cpu_percent=cpu_percent,
                memory_gb=memory_gb,
                io_reads_per_sec=io_reads_per_sec,
                io_writes_per_sec=io_writes_per_sec,
                network_kb_per_sec=0.0,  # Not easily available in SQL Server
                buffer_cache_hit_ratio=buffer_cache_hit_ratio,
                active_connections=active_connections,
                blocking_sessions=blocking_sessions,
                io_read_bytes_per_sec=io_read_bytes_per_sec,
                io_write_bytes_per_sec=io_write_bytes_per_sec,
                wal_size_mb=wal_size_mb,
                wait_stats=wait_stats
            )
    
    def _capture_mysql_metrics(self, timestamp: datetime.datetime) -> PerformanceMetrics:
        """Capture MySQL specific performance metrics"""
        with self.engine.connect() as conn:
            # Get various MySQL status variables including I/O metrics
            status_query = text("""
                SHOW STATUS WHERE Variable_name IN (
                    'Threads_connected', 'Threads_running', 'Innodb_buffer_pool_reads',
                    'Innodb_buffer_pool_read_requests', 'Com_select', 'Com_insert',
                    'Com_update', 'Com_delete', 'Bytes_sent', 'Bytes_received',
                    'Innodb_data_reads', 'Innodb_data_writes', 'Innodb_data_read',
                    'Innodb_data_written', 'Innodb_pages_read', 'Innodb_pages_written'
                )
            """)
            
            # Get memory information
            memory_query = text("""
                SELECT 
                    @@innodb_buffer_pool_size / 1024 / 1024 / 1024 AS buffer_pool_gb,
                    @@key_buffer_size / 1024 / 1024 / 1024 AS key_buffer_gb,
                    @@sort_buffer_size / 1024 / 1024 / 1024 AS sort_buffer_gb
            """)
            
            try:
                status_results = conn.execute(status_query).fetchall()
                status_dict = {row[0]: row[1] for row in status_results}
                
                # Calculate buffer pool hit ratio
                buffer_reads = float(status_dict.get('Innodb_buffer_pool_reads', 0))
                buffer_requests = float(status_dict.get('Innodb_buffer_pool_read_requests', 1))
                buffer_hit_ratio = ((buffer_requests - buffer_reads) / buffer_requests) * 100 if buffer_requests > 0 else 0
                
                # Capture InnoDB log file size (WAL equivalent for MySQL)
                wal_size_mb = 0.0
                try:
                    wal_query = text("""
                        SELECT 
                            COALESCE(
                                (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS 
                                 WHERE VARIABLE_NAME = 'Innodb_os_log_written') / 1024.0 / 1024.0,
                                0.0
                            ) AS log_written_mb
                    """)
                    wal_result = conn.execute(wal_query).fetchone()
                    wal_size_mb = float(wal_result[0]) if wal_result and wal_result[0] else 0.0
                except Exception as e:
                    print(f"⚠️ Could not capture InnoDB log size: {e}")
                
                # Get memory information
                memory_gb = 0.0
                try:
                    memory_result = conn.execute(memory_query).fetchone()
                    if memory_result:
                        # Sum up major memory components
                        memory_gb = float(memory_result[0] or 0) + float(memory_result[1] or 0) + float(memory_result[2] or 0)
                except Exception as e:
                    print(f"⚠️ Could not capture MySQL memory metrics: {e}")
                
                # Calculate I/O metrics
                io_reads_per_sec = float(status_dict.get('Innodb_pages_read', 0))
                io_writes_per_sec = float(status_dict.get('Innodb_pages_written', 0))
                io_read_bytes_per_sec = float(status_dict.get('Innodb_data_read', 0))
                io_write_bytes_per_sec = float(status_dict.get('Innodb_data_written', 0))
                
                return PerformanceMetrics(
                    timestamp=timestamp,
                    cpu_percent=0.0,  # Not easily available in MySQL
                    memory_gb=memory_gb,
                    io_reads_per_sec=io_reads_per_sec,
                    io_writes_per_sec=io_writes_per_sec,
                    network_kb_per_sec=(float(status_dict.get('Bytes_sent', 0)) + float(status_dict.get('Bytes_received', 0))) / 1024.0,
                    buffer_cache_hit_ratio=buffer_hit_ratio,
                    active_connections=int(status_dict.get('Threads_connected', 0)),
                    blocking_sessions=0,  # Would need processlist analysis
                    io_read_bytes_per_sec=io_read_bytes_per_sec,
                    io_write_bytes_per_sec=io_write_bytes_per_sec,
                    wal_size_mb=wal_size_mb
                )
                
            except Exception as e:
                print(f"⚠️ Error capturing MySQL metrics: {e}")
                return PerformanceMetrics(
                    timestamp=timestamp,
                    cpu_percent=0.0,
                    memory_gb=0.0,
                    io_reads_per_sec=0.0,
                    io_writes_per_sec=0.0,
                    network_kb_per_sec=0.0,
                    buffer_cache_hit_ratio=0.0,
                    active_connections=0,
                    blocking_sessions=0
                )
    
    def _capture_postgresql_metrics(self, timestamp: datetime.datetime) -> PerformanceMetrics:
        """Capture PostgreSQL specific performance metrics"""
        with self.engine.connect() as conn:
            # Database statistics including I/O metrics
            stats_query = text("""
                SELECT 
                    sum(blks_read) as total_reads,
                    sum(blks_hit) as buffer_hits,
                    sum(tup_returned) as tuples_returned,
                    sum(tup_fetched) as tuples_fetched,
                    sum(blk_read_time) as read_time_ms,
                    sum(blk_write_time) as write_time_ms
                FROM pg_stat_database
            """)
            
            # Memory information
            memory_query = text("""
                SELECT 
                    setting::bigint * 8 / 1024 / 1024 / 1024 AS shared_buffers_gb,
                    (SELECT setting::bigint FROM pg_settings WHERE name = 'work_mem')::bigint / 1024 / 1024 AS work_mem_gb,
                    (SELECT setting::bigint FROM pg_settings WHERE name = 'maintenance_work_mem')::bigint / 1024 / 1024 AS maintenance_work_mem_gb
                FROM pg_settings 
                WHERE name = 'shared_buffers'
            """)
            
            # I/O statistics from pg_stat_bgwriter
            io_query = text("""
                SELECT 
                    checkpoints_timed + checkpoints_req as total_checkpoints,
                    buffers_checkpoint + buffers_clean + buffers_backend as total_buffers_written,
                    buffers_backend_fsync as backend_fsyncs,
                    buffers_alloc as buffers_allocated
                FROM pg_stat_bgwriter
            """)
            
            # Active connections
            connections_query = text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_connections
                FROM pg_stat_activity
            """)
            
            try:
                stats_result = conn.execute(stats_query).fetchone()
                conn_result = conn.execute(connections_query).fetchone()
                
                # Calculate buffer hit ratio
                total_reads = float(stats_result[0]) if stats_result[0] else 0
                buffer_hits = float(stats_result[1]) if stats_result[1] else 0
                total_accesses = total_reads + buffer_hits
                buffer_hit_ratio = (buffer_hits / total_accesses) * 100 if total_accesses > 0 else 0
                
                # Capture WAL size for PostgreSQL
                wal_size_mb = 0.0
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
                
                # Get memory information
                memory_gb = 0.0
                try:
                    memory_result = conn.execute(memory_query).fetchone()
                    if memory_result:
                        # Sum up major memory components
                        memory_gb = float(memory_result[0] or 0) + float(memory_result[1] or 0) + float(memory_result[2] or 0)
                except Exception as e:
                    print(f"⚠️ Could not capture PostgreSQL memory metrics: {e}")
                
                # Get I/O statistics
                io_reads_per_sec = 0.0
                io_writes_per_sec = 0.0
                io_read_bytes_per_sec = 0.0
                io_write_bytes_per_sec = 0.0
                try:
                    io_result = conn.execute(io_query).fetchone()
                    if io_result:
                        # Use buffer statistics as proxy for I/O rates
                        io_reads_per_sec = float(total_reads) if total_reads else 0.0
                        io_writes_per_sec = float(io_result[1]) if io_result[1] else 0.0
                        # Estimate bytes from block counts (8KB per block typically)
                        io_read_bytes_per_sec = io_reads_per_sec * 8192
                        io_write_bytes_per_sec = io_writes_per_sec * 8192
                except Exception as e:
                    print(f"⚠️ Could not capture PostgreSQL I/O metrics: {e}")
                
                return PerformanceMetrics(
                    timestamp=timestamp,
                    cpu_percent=0.0,  # Would need system queries
                    memory_gb=memory_gb,
                    io_reads_per_sec=io_reads_per_sec,
                    io_writes_per_sec=io_writes_per_sec,
                    network_kb_per_sec=0.0,
                    buffer_cache_hit_ratio=buffer_hit_ratio,
                    active_connections=int(conn_result[1]) if conn_result else 0,
                    blocking_sessions=int(conn_result[2]) if conn_result else 0,
                    io_read_bytes_per_sec=io_read_bytes_per_sec,
                    io_write_bytes_per_sec=io_write_bytes_per_sec,
                    wal_size_mb=wal_size_mb
                )
                
            except Exception as e:
                print(f"⚠️ Error capturing PostgreSQL metrics: {e}")
                return PerformanceMetrics(
                    timestamp=timestamp,
                    cpu_percent=0.0,
                    memory_gb=0.0,
                    io_reads_per_sec=0.0,
                    io_writes_per_sec=0.0,
                    network_kb_per_sec=0.0,
                    buffer_cache_hit_ratio=0.0,
                    active_connections=0,
                    blocking_sessions=0
                )
    
    def capture_schema_metrics(self, schema_name: str = None) -> SchemaMetrics:
        """Capture schema and table size metrics using the provider
        
        Args:
            schema_name: Schema to analyze (uses provider default if None)
            
        Returns:
            SchemaMetrics: Schema size and table information
        """
        if schema_name is None:
            # Use provider's default schema
            schema_name = self.provider.get_default_schema_name()
        
        print(f"📏 Capturing schema metrics for: {schema_name}")
        
        timestamp = datetime.datetime.now()
        
        # Use the provider to capture schema metrics
        base_metrics = self.provider.capture_schema_metrics(timestamp, schema_name)
        
        # Convert to our local SchemaMetrics format (they should be compatible)
        return SchemaMetrics(
            timestamp=base_metrics.timestamp,
            schema_name=base_metrics.schema_name,
            total_size_bytes=base_metrics.total_size_bytes,
            table_metrics=base_metrics.table_metrics,
            index_metrics=base_metrics.index_metrics
        )
    
    def _is_change_tracking_enabled(self) -> bool:
        """Check if Change Tracking is enabled on the database"""
        if self.db_type != 'sqlserver':
            return False
            
        try:
            with self.engine.connect() as conn:
                # Try the standard query first
                ct_query = text("""
                    SELECT is_change_tracking_on 
                    FROM sys.databases 
                    WHERE name = DB_NAME()
                """)
                try:
                    result = conn.execute(ct_query).scalar()
                    return bool(result) if result is not None else False
                except Exception:
                    # Fallback for Azure SQL Database - check sys.change_tracking_databases
                    ct_fallback_query = text("""
                        SELECT COUNT(*) 
                        FROM sys.change_tracking_databases 
                        WHERE database_id = DB_ID()
                    """)
                    result = conn.execute(ct_fallback_query).scalar()
                    return bool(result and result > 0)
        except Exception as e:
            print(f"⚠️ Could not check Change Tracking status: {e}")
            return False
    
    def _capture_sqlserver_schema_metrics(self, timestamp: datetime.datetime, schema_name: str) -> SchemaMetrics:
        """Capture SQL Server schema metrics including CDC schema when Change Tracking is enabled"""
        with self.engine.connect() as conn:
            # Check if Change Tracking is enabled
            ct_enabled = self._is_change_tracking_enabled()
            
            # Collect schemas to analyze
            schemas_to_analyze = [schema_name]
            if ct_enabled and schema_name != 'cdc':
                schemas_to_analyze.append('cdc')
                print(f"📊 Change Tracking detected - will also analyze 'cdc' schema")
            
            all_table_metrics = []
            total_size = 0
            
            # Define the table query once
            table_query = text("""
                SELECT 
                    t.name AS table_name,
                    s.name AS schema_name,
                    COALESCE(SUM(p.rows), 0) AS row_count,
                    COALESCE(SUM(a.total_pages) * 8 * 1024, 0) AS total_size_bytes,
                    COALESCE(SUM(a.used_pages) * 8 * 1024, 0) AS used_size_bytes,
                    COALESCE(SUM(a.data_pages) * 8 * 1024, 0) AS data_size_bytes
                FROM sys.tables t
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                LEFT JOIN sys.indexes i ON t.object_id = i.object_id AND i.index_id <= 1  -- Only clustered index or heap
                LEFT JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                LEFT JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE s.name = :schema_name
                GROUP BY t.name, s.name
                ORDER BY total_size_bytes DESC
            """)
            
            for current_schema in schemas_to_analyze:
                print(f"📏 Analyzing schema: {current_schema}")
                
                try:
                    table_results = conn.execute(table_query, {'schema_name': current_schema}).fetchall()
                    
                    for row in table_results:
                        # Use row count from sys.dm_db_partition_stats if available for better accuracy
                        try:
                            row_count_query = text("""
                                SELECT SUM(row_count) 
                                FROM sys.dm_db_partition_stats ps
                                JOIN sys.tables t ON ps.object_id = t.object_id
                                JOIN sys.schemas s ON t.schema_id = s.schema_id
                                WHERE t.name = :table_name AND s.name = :schema_name
                                AND ps.index_id <= 1
                            """)
                            accurate_rows = conn.execute(row_count_query, {
                                'table_name': row[0], 
                                'schema_name': current_schema
                            }).scalar()
                            row_count = int(accurate_rows) if accurate_rows else int(row[2])
                        except:
                            row_count = int(row[2])
                        
                        table_info = {
                            'table_name': row[0],
                            'schema_name': row[1],
                            'row_count': row_count,
                            'size_bytes': int(row[3]),
                            'used_size_bytes': int(row[4]),
                            'data_size_bytes': int(row[5])
                        }
                        all_table_metrics.append(table_info)
                        total_size += int(row[3])
                    
                    # If no tables found in this schema, try a simpler fallback query
                    if not table_results:
                        fallback_query = text("""
                            SELECT t.name AS table_name, s.name AS schema_name
                            FROM sys.tables t
                            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                            WHERE s.name = :schema_name
                        """)
                        fallback_results = conn.execute(fallback_query, {'schema_name': current_schema}).fetchall()
                        
                        for row in fallback_results:
                            table_info = {
                                'table_name': row[0],
                                'schema_name': row[1],
                                'row_count': 0,
                                'size_bytes': 0,
                                'used_size_bytes': 0,
                                'data_size_bytes': 0
                            }
                            all_table_metrics.append(table_info)
                
                except Exception as e:
                    print(f"⚠️ Error capturing schema metrics for {current_schema}: {e}")
            
            # Create a combined schema name if multiple schemas were analyzed
            combined_schema_name = schema_name
            if ct_enabled and len(schemas_to_analyze) > 1:
                combined_schema_name = f"{schema_name}+cdc"
            
            return SchemaMetrics(
                timestamp=timestamp,
                schema_name=combined_schema_name,
                total_size_bytes=total_size,
                table_metrics=all_table_metrics
            )
    
    def _capture_mysql_schema_metrics(self, timestamp: datetime.datetime, schema_name: str) -> SchemaMetrics:
        """Capture MySQL schema metrics"""
        with self.engine.connect() as conn:
            table_query = text("""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length,
                    data_length + index_length AS total_size
                FROM information_schema.tables 
                WHERE table_schema = :schema_name
                ORDER BY total_size DESC
            """)
            
            try:
                table_results = conn.execute(table_query, {'schema_name': schema_name}).fetchall()
                
                table_metrics = []
                total_size = 0
                
                for row in table_results:
                    table_info = {
                        'table_name': row[0],
                        'schema_name': schema_name,
                        'estimated_rows': int(row[1]) if row[1] else 0,
                        'data_size_bytes': int(row[2]) if row[2] else 0,
                        'index_size_bytes': int(row[3]) if row[3] else 0,
                        'total_size_bytes': int(row[4]) if row[4] else 0
                    }
                    table_metrics.append(table_info)
                    total_size += table_info['total_size_bytes']
                
                return SchemaMetrics(
                    timestamp=timestamp,
                    schema_name=schema_name,
                    total_size_bytes=total_size,
                    table_metrics=table_metrics
                )
                
            except Exception as e:
                print(f"⚠️ Error capturing MySQL schema metrics: {e}")
                return SchemaMetrics(
                    timestamp=timestamp,
                    schema_name=schema_name,
                    total_size_bytes=0
                )
    
    def _capture_postgresql_schema_metrics(self, timestamp: datetime.datetime, schema_name: str) -> SchemaMetrics:
        """Capture PostgreSQL schema metrics"""
        with self.engine.connect() as conn:
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
            
            try:
                table_results = conn.execute(table_query, {'schema_name': schema_name}).fetchall()
                
                table_metrics = []
                total_size = 0
                
                for row in table_results:
                    table_info = {
                        'table_name': row[1],
                        'schema_name': row[0],
                        'estimated_rows': int(row[3]) if row[3] else 0,
                        'total_changes': int(row[2]) if row[2] else 0,
                        'total_size_bytes': int(row[4]) if row[4] else 0,
                        'table_size_bytes': int(row[5]) if row[5] else 0
                    }
                    table_metrics.append(table_info)
                    total_size += table_info['total_size_bytes']
                
                return SchemaMetrics(
                    timestamp=timestamp,
                    schema_name=schema_name,
                    total_size_bytes=total_size,
                    table_metrics=table_metrics
                )
                
            except Exception as e:
                print(f"⚠️ Error capturing PostgreSQL schema metrics: {e}")
                return SchemaMetrics(
                    timestamp=timestamp,
                    schema_name=schema_name,
                    total_size_bytes=0
                )
    
    def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous monitoring
        
        Args:
            interval_seconds: How often to capture metrics
        """
        print(f"🔄 Starting continuous monitoring (every {interval_seconds}s)")
        self.monitoring_active = True
        
        # This would typically run in a separate thread
        # For now, just capture one snapshot
        metrics = self._capture_performance_metrics()
        self.metrics_history.append(metrics)
        print(f"📊 Captured metrics at {metrics.timestamp}")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        print("⏹️ Stopping monitoring")
        self.monitoring_active = False
    
    def reset_dml_tracking(self):
        """Reset DML operation tracking counters"""
        self.dml_operation_tracker = DMLOperationMetrics()
        print("🔄 DML operation tracking reset")
    
    def record_dml_operation(self, operation_type: str, rows_affected: int):
        """Record a DML operation and its row count
        
        Args:
            operation_type: 'insert', 'update', or 'delete'
            rows_affected: Number of rows affected by the operation
        """
        operation_type = operation_type.lower()
        
        if operation_type == 'insert':
            self.dml_operation_tracker.insert_count += 1
            self.dml_operation_tracker.rows_inserted += rows_affected
        elif operation_type == 'update':
            self.dml_operation_tracker.update_count += 1
            self.dml_operation_tracker.rows_updated += rows_affected
        elif operation_type == 'delete':
            self.dml_operation_tracker.delete_count += 1
            self.dml_operation_tracker.rows_deleted += rows_affected
        
        # Update totals
        self.dml_operation_tracker.total_operations += 1
        self.dml_operation_tracker.total_rows_affected += rows_affected
    
    def finalize_dml_tracking(self, duration_seconds: float):
        """Finalize DML tracking with duration and calculate rates
        
        Args:
            duration_seconds: Total duration of DML operations
        """
        self.dml_operation_tracker.operation_duration_seconds = duration_seconds
        
        if duration_seconds > 0:
            self.dml_operation_tracker.operations_per_second = (
                self.dml_operation_tracker.total_operations / duration_seconds
            )
            self.dml_operation_tracker.rows_per_second = (
                self.dml_operation_tracker.total_rows_affected / duration_seconds
            )
        
        print(f"📊 DML Tracking Summary:")
        print(f"   Operations: {self.dml_operation_tracker.total_operations} "
              f"({self.dml_operation_tracker.operations_per_second:.1f}/sec)")
        print(f"   Rows: {self.dml_operation_tracker.total_rows_affected} "
              f"({self.dml_operation_tracker.rows_per_second:.1f}/sec)")
        print(f"   Breakdown: INS={self.dml_operation_tracker.insert_count} "
              f"({self.dml_operation_tracker.rows_inserted} rows), "
              f"UPD={self.dml_operation_tracker.update_count} "
              f"({self.dml_operation_tracker.rows_updated} rows), "
              f"DEL={self.dml_operation_tracker.delete_count} "
              f"({self.dml_operation_tracker.rows_deleted} rows)")
    
    def get_dml_metrics(self) -> DMLOperationMetrics:
        """Get current DML operation metrics
        
        Returns:
            DMLOperationMetrics: Current DML statistics
        """
        return self.dml_operation_tracker
    
    def generate_impact_report(self, current_metrics: PerformanceMetrics = None) -> Dict[str, Any]:
        """Generate impact analysis report
        
        Args:
            current_metrics: Current metrics to compare against baseline
            
        Returns:
            dict: Comprehensive impact report
        """
        if current_metrics is None:
            current_metrics = self._capture_performance_metrics()
        
        if self.baseline_metrics is None:
            print("⚠️ No baseline metrics available - capturing baseline now")
            self.capture_baseline()
        
        print("📋 Generating impact analysis report...")
        
        # Calculate deltas
        cpu_delta = current_metrics.cpu_percent - self.baseline_metrics.cpu_percent
        memory_delta = current_metrics.memory_gb - self.baseline_metrics.memory_gb
        buffer_delta = current_metrics.buffer_cache_hit_ratio - self.baseline_metrics.buffer_cache_hit_ratio
        connections_delta = current_metrics.active_connections - self.baseline_metrics.active_connections
        wal_delta = current_metrics.wal_size_mb - self.baseline_metrics.wal_size_mb
        io_reads_delta = current_metrics.io_reads_per_sec - self.baseline_metrics.io_reads_per_sec
        io_writes_delta = current_metrics.io_writes_per_sec - self.baseline_metrics.io_writes_per_sec
        io_read_bytes_delta = current_metrics.io_read_bytes_per_sec - self.baseline_metrics.io_read_bytes_per_sec
        io_write_bytes_delta = current_metrics.io_write_bytes_per_sec - self.baseline_metrics.io_write_bytes_per_sec
        
        # Determine impact level (updated for GB memory units)
        def get_impact_level(cpu_delta: float, memory_delta: float) -> str:
            if cpu_delta > 20 or memory_delta > 0.5:  # 0.5GB = 500MB
                return "HIGH"
            elif cpu_delta > 10 or memory_delta > 0.2:  # 0.2GB = 200MB
                return "MEDIUM"
            elif cpu_delta > 5 or memory_delta > 0.1:  # 0.1GB = 100MB
                return "LOW"
            else:
                return "MINIMAL"
        
        impact_level = get_impact_level(cpu_delta, memory_delta)
        
        report = {
            'timestamp': current_metrics.timestamp.isoformat(),
            'database_type': self.db_type,
            'impact_level': impact_level,
            'baseline': {
                'cpu_percent': self.baseline_metrics.cpu_percent,
                'memory_gb': self.baseline_metrics.memory_gb,
                'io_reads_per_sec': self.baseline_metrics.io_reads_per_sec,
                'io_writes_per_sec': self.baseline_metrics.io_writes_per_sec,
                'io_read_bytes_per_sec': self.baseline_metrics.io_read_bytes_per_sec,
                'io_write_bytes_per_sec': self.baseline_metrics.io_write_bytes_per_sec,
                'buffer_cache_hit_ratio': self.baseline_metrics.buffer_cache_hit_ratio,
                'active_connections': self.baseline_metrics.active_connections,
                'wal_size_mb': self.baseline_metrics.wal_size_mb
            },
            'current': {
                'cpu_percent': current_metrics.cpu_percent,
                'memory_gb': current_metrics.memory_gb,
                'io_reads_per_sec': current_metrics.io_reads_per_sec,
                'io_writes_per_sec': current_metrics.io_writes_per_sec,
                'io_read_bytes_per_sec': current_metrics.io_read_bytes_per_sec,
                'io_write_bytes_per_sec': current_metrics.io_write_bytes_per_sec,
                'buffer_cache_hit_ratio': current_metrics.buffer_cache_hit_ratio,
                'active_connections': current_metrics.active_connections,
                'wal_size_mb': current_metrics.wal_size_mb
            },
            'deltas': {
                'cpu_percent_change': cpu_delta,
                'memory_gb_change': memory_delta,
                'io_reads_per_sec_change': io_reads_delta,
                'io_writes_per_sec_change': io_writes_delta,
                'io_read_bytes_per_sec_change': io_read_bytes_delta,
                'io_write_bytes_per_sec_change': io_write_bytes_delta,
                'buffer_cache_hit_ratio_change': buffer_delta,
                'wal_size_mb_change': wal_delta,
                'active_connections_change': connections_delta
            },
            'dml_operations': {
                'total_operations': self.dml_operation_tracker.total_operations,
                'operations_per_second': self.dml_operation_tracker.operations_per_second,
                'total_rows_affected': self.dml_operation_tracker.total_rows_affected,
                'rows_per_second': self.dml_operation_tracker.rows_per_second,
                'insert_count': self.dml_operation_tracker.insert_count,
                'update_count': self.dml_operation_tracker.update_count,
                'delete_count': self.dml_operation_tracker.delete_count,
                'rows_inserted': self.dml_operation_tracker.rows_inserted,
                'rows_updated': self.dml_operation_tracker.rows_updated,
                'rows_deleted': self.dml_operation_tracker.rows_deleted,
                'duration_seconds': self.dml_operation_tracker.operation_duration_seconds
            },
            'recommendations': self._generate_recommendations(impact_level, cpu_delta, memory_delta)
        }
        
        return report
    
    def _generate_recommendations(self, impact_level: str, cpu_delta: float, memory_delta: float) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []
        
        if impact_level == "HIGH":
            recommendations.append("🚨 High impact detected - consider reducing operation frequency")
            recommendations.append("🔍 Monitor for blocking sessions and long-running queries")
            
        if cpu_delta > 15:
            recommendations.append("⚡ High CPU usage - consider optimizing queries or adding indexes")
            
        if memory_delta > 0.3:  # 0.3GB = 300MB
            recommendations.append("💾 High memory usage - monitor for memory pressure")
            
        if impact_level == "MINIMAL":
            recommendations.append("✅ Minimal impact - operations are well-optimized")
            
        return recommendations
    
    def print_summary_report(self, report: Dict[str, Any] = None):
        """Print a formatted summary report"""
        if report is None:
            report = self.generate_impact_report()
        
        print(f"\n{'='*60}")
        print(f"📊 DATABASE IMPACT ANALYSIS REPORT")
        print(f"{'='*60}")
        print(f"Database Type: {report['database_type'].upper()}")
        print(f"Impact Level:  {report['impact_level']}")
        print(f"Timestamp:     {report['timestamp']}")
        
        print(f"\n📈 PERFORMANCE METRICS COMPARISON:")
        print(f"                    Baseline    Current     Delta")
        print(f"CPU Usage:          {report['baseline']['cpu_percent']:8.1f}%   {report['current']['cpu_percent']:8.1f}%   {report['deltas']['cpu_percent_change']:+8.1f}%")
        print(f"Memory Usage:       {report['baseline']['memory_gb']:8.2f}GB  {report['current']['memory_gb']:8.2f}GB  {report['deltas']['memory_gb_change']:+8.2f}GB")
        print(f"I/O Reads/sec:      {report['baseline']['io_reads_per_sec']:8.1f}    {report['current']['io_reads_per_sec']:8.1f}    {report['deltas']['io_reads_per_sec_change']:+8.1f}")
        print(f"I/O Writes/sec:     {report['baseline']['io_writes_per_sec']:8.1f}    {report['current']['io_writes_per_sec']:8.1f}    {report['deltas']['io_writes_per_sec_change']:+8.1f}")
        print(f"I/O Read MB/sec:    {report['baseline']['io_read_bytes_per_sec']/1024/1024:8.1f}    {report['current']['io_read_bytes_per_sec']/1024/1024:8.1f}    {report['deltas']['io_read_bytes_per_sec_change']/1024/1024:+8.1f}")
        print(f"I/O Write MB/sec:   {report['baseline']['io_write_bytes_per_sec']/1024/1024:8.1f}    {report['current']['io_write_bytes_per_sec']/1024/1024:8.1f}    {report['deltas']['io_write_bytes_per_sec_change']/1024/1024:+8.1f}")
        print(f"Buffer Hit Ratio:   {report['baseline']['buffer_cache_hit_ratio']:8.2f}%   {report['current']['buffer_cache_hit_ratio']:8.2f}%   {report['deltas']['buffer_cache_hit_ratio_change']:+8.2f}%")
        print(f"Active Connections: {report['baseline']['active_connections']:8d}     {report['current']['active_connections']:8d}     {report['deltas']['active_connections_change']:+8d}")
        print(f"WAL Size:           {report['baseline']['wal_size_mb']:8.1f}MB  {report['current']['wal_size_mb']:8.1f}MB  {report['deltas']['wal_size_mb_change']:+8.1f}MB")
        
        # DML Operations Summary
        dml = report['dml_operations']
        if dml['total_operations'] > 0:
            print(f"\n📊 DML OPERATIONS SUMMARY:")
            print(f"Total Operations:   {dml['total_operations']:,} ({dml['operations_per_second']:.1f}/sec)")
            print(f"Total Rows:         {dml['total_rows_affected']:,} ({dml['rows_per_second']:.1f}/sec)")
            print(f"Duration:           {dml['duration_seconds']:.1f} seconds")
            print(f"\n📋 OPERATION BREAKDOWN:")
            print(f"INSERT:             {dml['insert_count']:,} operations, {dml['rows_inserted']:,} rows")
            print(f"UPDATE:             {dml['update_count']:,} operations, {dml['rows_updated']:,} rows") 
            print(f"DELETE:             {dml['delete_count']:,} operations, {dml['rows_deleted']:,} rows")
            
            # Calculate efficiency metrics
            if dml['total_operations'] > 0:
                avg_rows_per_op = dml['total_rows_affected'] / dml['total_operations']
                print(f"\n⚡ EFFICIENCY METRICS:")
                print(f"Avg Rows/Operation: {avg_rows_per_op:.1f}")
                if dml['duration_seconds'] > 0:
                    ops_per_minute = dml['operations_per_second'] * 60
                    rows_per_minute = dml['rows_per_second'] * 60
                    print(f"Operations/Minute:  {ops_per_minute:.0f}")
                    print(f"Rows/Minute:        {rows_per_minute:.0f}")
        
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   {rec}")
        
        print(f"{'='*60}\n")

    def capture_baseline_metrics(self, duration_minutes: int = 1) -> Dict[str, Any]:
        """Capture baseline database metrics before starting tests
        
        Args:
            duration_minutes: How long to monitor baseline (default 1 minute)
            
        Returns:
            Dictionary containing baseline metrics and CDC/CT status
        """
        print(f"📊 CAPTURING BASELINE DATABASE METRICS")
        print(f"⏱️  Monitoring idle database for {duration_minutes} minute(s)...")
        print()
        
        # Check CDC/CT status first
        self.cdc_ct_status = self._check_cdc_ct_status()
        
        # Display CDC/CT status
        print("🔍 DATABASE REPLICATION STATUS:")
        for key, value in self.cdc_ct_status.items():
            status_icon = "✅" if value else "❌"
            print(f"   {status_icon} {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Capture initial metrics
        print("📈 Capturing initial metrics...")
        initial_metrics = self._capture_performance_metrics()
        
        # Monitor for the specified duration
        samples = []
        sample_interval = 10  # seconds
        total_samples = int((duration_minutes * 60) // sample_interval)
        
        for i in range(total_samples):
            time.sleep(sample_interval)
            sample_metrics = self._capture_performance_metrics()
            samples.append(sample_metrics)
            
            # Show progress
            progress = ((i + 1) / total_samples) * 100
            print(f"   📊 Sample {i+1}/{total_samples} ({progress:.0f}%) - "
                  f"CPU: {sample_metrics.cpu_percent:.1f}%, "
                  f"I/O R/W: {sample_metrics.io_reads_per_sec:.0f}/{sample_metrics.io_writes_per_sec:.0f}")
        
        # Calculate baseline averages
        baseline_metrics = self._calculate_baseline_averages(initial_metrics, samples)
        
        # Store baseline for later comparison
        self.baseline_metrics = {
            'metrics': baseline_metrics,
            'cdc_ct_status': self.cdc_ct_status,
            'duration_minutes': duration_minutes,
            'sample_count': len(samples) + 1,
            'timestamp': datetime.datetime.now()
        }
        
        print()
        print("📊 BASELINE METRICS SUMMARY:")
        print(f"   CPU Usage: {baseline_metrics.cpu_percent:.1f}%")
        print(f"   Memory Usage: {getattr(baseline_metrics, 'memory_usage_gb', getattr(baseline_metrics, 'memory_gb', 0)):.2f} GB")
        print(f"   I/O Reads/sec: {baseline_metrics.io_reads_per_sec:.1f}")
        print(f"   I/O Writes/sec: {baseline_metrics.io_writes_per_sec:.1f}")
        print(f"   Buffer Hit Ratio: {baseline_metrics.buffer_cache_hit_ratio:.1f}%")
        print(f"   Active Connections: {getattr(baseline_metrics, 'active_connections', 0)}")
        print()
        
        return self.baseline_metrics

    def _check_cdc_ct_status(self) -> Dict[str, bool]:
        """Check if CDC and Change Tracking are enabled on the database"""
        status = {
            'cdc_enabled': False,
            'change_tracking_enabled': False,
            'has_cdc_tables': False,
            'has_ct_tables': False
        }
        
        try:
            if self.db_type == 'mssql':
                # Check database-level CDC
                cdc_query = text("SELECT is_cdc_enabled FROM sys.databases WHERE name = DB_NAME()")
                result = self.engine.execute(cdc_query).fetchone()
                if result:
                    status['cdc_enabled'] = bool(result[0])
                
                # Check database-level Change Tracking
                ct_query = text("SELECT COUNT(*) FROM sys.change_tracking_databases WHERE database_id = DB_ID()")
                result = self.engine.execute(ct_query).fetchone()
                if result:
                    status['change_tracking_enabled'] = result[0] > 0
                
                # Check for tables with CDC enabled
                cdc_tables_query = text("SELECT COUNT(*) FROM sys.tables t INNER JOIN cdc.change_tables ct ON t.object_id = ct.source_object_id")
                result = self.engine.execute(cdc_tables_query).fetchone()
                if result:
                    status['has_cdc_tables'] = result[0] > 0
                
                # Check for tables with Change Tracking enabled
                ct_tables_query = text("SELECT COUNT(*) FROM sys.change_tracking_tables")
                result = self.engine.execute(ct_tables_query).fetchone()
                if result:
                    status['has_ct_tables'] = result[0] > 0
                    
            elif self.db_type == 'postgresql':
                # Check for logical replication
                try:
                    wal_level_query = text("SELECT setting FROM pg_settings WHERE name = 'wal_level'")
                    result = self.engine.execute(wal_level_query).fetchone()
                    if result and result[0] == 'logical':
                        status['cdc_enabled'] = True
                        
                    # Check for publications (logical replication)
                    pub_query = text("SELECT COUNT(*) FROM pg_publication")
                    result = self.engine.execute(pub_query).fetchone()
                    if result and result[0] > 0:
                        status['has_cdc_tables'] = True
                except:
                    pass  # Ignore if we can't check
                    
            elif self.db_type == 'mysql':
                # Check for binary logging
                try:
                    binlog_query = text("SHOW VARIABLES LIKE 'log_bin'")
                    result = self.engine.execute(binlog_query).fetchone()
                    if result and result[1].lower() == 'on':
                        status['cdc_enabled'] = True
                except:
                    pass  # Ignore if we can't check
                    
        except Exception as e:
            print(f"⚠️  Could not fully determine CDC/CT status: {e}")
        
        return status

    def _calculate_baseline_averages(self, initial_metrics: BasePerformanceMetrics, samples: List[BasePerformanceMetrics]) -> BasePerformanceMetrics:
        """Calculate average baseline metrics from samples"""
        all_metrics = [initial_metrics] + samples
        
        # Calculate averages (handle different attribute names)
        avg_cpu = sum(m.cpu_percent for m in all_metrics) / len(all_metrics)
        avg_memory = sum(getattr(m, 'memory_usage_gb', getattr(m, 'memory_gb', 0)) for m in all_metrics) / len(all_metrics)
        avg_io_reads = sum(m.io_reads_per_sec for m in all_metrics) / len(all_metrics)
        avg_io_writes = sum(m.io_writes_per_sec for m in all_metrics) / len(all_metrics)
        avg_io_read_bytes = sum(m.io_read_bytes_per_sec for m in all_metrics) / len(all_metrics)
        avg_io_write_bytes = sum(m.io_write_bytes_per_sec for m in all_metrics) / len(all_metrics)
        avg_buffer_hit = sum(m.buffer_cache_hit_ratio for m in all_metrics) / len(all_metrics)
        avg_connections = sum(getattr(m, 'active_connections', 0) for m in all_metrics) / len(all_metrics)
        avg_blocking = sum(getattr(m, 'blocking_sessions', 0) for m in all_metrics) / len(all_metrics)
        avg_wal_size = sum(getattr(m, 'wal_size_mb', 0) for m in all_metrics) / len(all_metrics)
        avg_network_in = sum(getattr(m, 'network_io_bytes_in_per_sec', getattr(m, 'network_kb_per_sec', 0) * 1024) for m in all_metrics) / len(all_metrics)
        avg_network_out = sum(getattr(m, 'network_io_bytes_out_per_sec', 0) for m in all_metrics) / len(all_metrics)
        
        # Use the most recent timestamp and system info
        latest = all_metrics[-1]
        
        return BasePerformanceMetrics(
            timestamp=latest.timestamp,
            cpu_percent=avg_cpu,
            memory_gb=avg_memory,
            io_reads_per_sec=avg_io_reads,
            io_writes_per_sec=avg_io_writes,
            io_read_bytes_per_sec=avg_io_read_bytes,
            io_write_bytes_per_sec=avg_io_write_bytes,
            network_kb_per_sec=avg_network_in / 1024,  # Convert to KB
            buffer_cache_hit_ratio=avg_buffer_hit,
            active_connections=int(avg_connections),
            blocking_sessions=int(avg_blocking),
            wal_size_mb=avg_wal_size,
            cpu_count=getattr(latest, 'cpu_count', 2),
            max_memory_gb=getattr(latest, 'max_memory_gb', 32.0)
        )

    def calculate_test_delta_metrics(self, current_metrics: BasePerformanceMetrics) -> Dict[str, Any]:
        """Calculate the delta between current metrics and baseline
        
        Args:
            current_metrics: Current performance metrics
            
        Returns:
            Dictionary with delta calculations and analysis
        """
        if not self.baseline_metrics:
            return {"error": "No baseline metrics available. Call capture_baseline_metrics() first."}
        
        baseline = self.baseline_metrics['metrics']
        
        delta = {
            'cpu_delta': current_metrics.cpu_percent - baseline.cpu_percent,
            'memory_delta_gb': getattr(current_metrics, 'memory_usage_gb', getattr(current_metrics, 'memory_gb', 0)) - getattr(baseline, 'memory_usage_gb', getattr(baseline, 'memory_gb', 0)),
            'io_reads_delta': current_metrics.io_reads_per_sec - baseline.io_reads_per_sec,
            'io_writes_delta': current_metrics.io_writes_per_sec - baseline.io_writes_per_sec,
            'io_read_bytes_delta': current_metrics.io_read_bytes_per_sec - baseline.io_read_bytes_per_sec,
            'io_write_bytes_delta': current_metrics.io_write_bytes_per_sec - baseline.io_write_bytes_per_sec,
            'buffer_hit_delta': current_metrics.buffer_cache_hit_ratio - baseline.buffer_cache_hit_ratio,
            'connections_delta': getattr(current_metrics, 'active_connections', 0) - getattr(baseline, 'active_connections', 0),
            'wal_size_delta_mb': getattr(current_metrics, 'wal_size_mb', 0) - getattr(baseline, 'wal_size_mb', 0),
            'baseline_timestamp': self.baseline_metrics['timestamp'],
            'current_timestamp': current_metrics.timestamp,
            'cdc_ct_status': self.baseline_metrics['cdc_ct_status']
        }
        
        return delta

    def print_baseline_comparison_report(self, current_metrics: BasePerformanceMetrics):
        """Print a detailed comparison between baseline and current metrics"""
        if not self.baseline_metrics:
            print("⚠️  No baseline metrics available for comparison")
            return
        
        delta = self.calculate_test_delta_metrics(current_metrics)
        baseline = self.baseline_metrics['metrics']
        
        print("📊 BASELINE vs CURRENT METRICS COMPARISON")
        print("=" * 60)
        print()
        
        # CDC/CT Status
        print("🔍 DATABASE REPLICATION STATUS (at baseline):")
        for key, value in delta['cdc_ct_status'].items():
            status_icon = "✅" if value else "❌"
            print(f"   {status_icon} {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Performance Deltas
        print("📈 PERFORMANCE IMPACT (Current - Baseline):")
        baseline_memory = getattr(baseline, 'memory_usage_gb', getattr(baseline, 'memory_gb', 0))
        current_memory = getattr(current_metrics, 'memory_usage_gb', getattr(current_metrics, 'memory_gb', 0))
        baseline_connections = getattr(baseline, 'active_connections', 0)
        current_connections = getattr(current_metrics, 'active_connections', 0)
        baseline_wal = getattr(baseline, 'wal_size_mb', 0)
        current_wal = getattr(current_metrics, 'wal_size_mb', 0)
        
        print(f"   CPU Usage:        {baseline.cpu_percent:.1f}% → {current_metrics.cpu_percent:.1f}% (Δ {delta['cpu_delta']:+.1f}%)")
        print(f"   Memory Usage:     {baseline_memory:.2f} GB → {current_memory:.2f} GB (Δ {delta['memory_delta_gb']:+.2f} GB)")
        print(f"   I/O Reads/sec:    {baseline.io_reads_per_sec:.1f} → {current_metrics.io_reads_per_sec:.1f} (Δ {delta['io_reads_delta']:+.1f})")
        print(f"   I/O Writes/sec:   {baseline.io_writes_per_sec:.1f} → {current_metrics.io_writes_per_sec:.1f} (Δ {delta['io_writes_delta']:+.1f})")
        print(f"   Buffer Hit Ratio: {baseline.buffer_cache_hit_ratio:.1f}% → {current_metrics.buffer_cache_hit_ratio:.1f}% (Δ {delta['buffer_hit_delta']:+.1f}%)")
        print(f"   Active Connections: {baseline_connections} → {current_connections} (Δ {delta['connections_delta']:+.0f})")
        print(f"   WAL Size:         {baseline_wal:.1f} MB → {current_wal:.1f} MB (Δ {delta['wal_size_delta_mb']:+.1f} MB)")
        print()
        
        # Analysis
        print("💡 IMPACT ANALYSIS:")
        if abs(delta['cpu_delta']) < 1.0:
            print("   ✅ Minimal CPU impact")
        elif delta['cpu_delta'] > 5.0:
            print(f"   ⚠️  Significant CPU increase: +{delta['cpu_delta']:.1f}%")
        
        if abs(delta['io_reads_delta']) < 10 and abs(delta['io_writes_delta']) < 10:
            print("   ✅ Minimal I/O impact")
        else:
            print(f"   📊 I/O Impact: +{delta['io_reads_delta']:.0f} reads/sec, +{delta['io_writes_delta']:.0f} writes/sec")
        
        if delta['wal_size_delta_mb'] > 100:
            print(f"   📈 Significant WAL growth: +{delta['wal_size_delta_mb']:.1f} MB")
        
        print("=" * 60)
