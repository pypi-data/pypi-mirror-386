#!/usr/bin/env python3
"""
SimpleMonitorBase.py - Base class for database monitoring

This module provides the base class and common functionality for database monitoring,
following the same pattern as CloudBase to eliminate code duplication.
"""

import datetime
import sqlalchemy as sa
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# Import the dataclasses from the original SimpleMonitor
@dataclass
class DMLOperationMetrics:
    """Container for DML operation metrics"""
    insert_count: int = 0
    update_count: int = 0
    delete_count: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_deleted: int = 0
    operation_duration_seconds: float = 0.0
    
    @property
    def total_operations(self) -> int:
        return self.insert_count + self.update_count + self.delete_count
    
    @property
    def total_rows_affected(self) -> int:
        return self.rows_inserted + self.rows_updated + self.rows_deleted
    
    @property
    def operations_per_second(self) -> float:
        if self.operation_duration_seconds > 0:
            return self.total_operations / self.operation_duration_seconds
        return 0.0
    
    @property
    def rows_per_second(self) -> float:
        if self.operation_duration_seconds > 0:
            return self.total_rows_affected / self.operation_duration_seconds
        return 0.0

@dataclass
class PerformanceMetrics:
    """Container for database performance metrics"""
    timestamp: datetime.datetime
    cpu_percent: float
    memory_gb: float
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
    wait_stats: Dict[str, Any] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SchemaMetrics:
    """Container for database schema metrics"""
    timestamp: datetime.datetime
    schema_name: str
    total_size_bytes: int
    table_metrics: List[Dict[str, Any]] = field(default_factory=list)
    index_metrics: List[Dict[str, Any]] = field(default_factory=list)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

class MonitorProviderBase(ABC):
    """Base class for database-specific monitoring implementations"""
    
    def __init__(self, engine: sa.Engine, db_type: str):
        """Initialize the monitor provider
        
        Args:
            engine: SQLAlchemy engine for database connection
            db_type: Database type identifier
        """
        self.engine = engine
        self.db_type = db_type
        self.baseline_metrics: Optional[PerformanceMetrics] = None
        self.dml_operation_tracker = DMLOperationMetrics()
        self._dml_start_time: Optional[datetime.datetime] = None
    
    @abstractmethod
    def capture_performance_metrics(self, timestamp: datetime.datetime) -> PerformanceMetrics:
        """Capture database-specific performance metrics
        
        Args:
            timestamp: Timestamp for the metrics
            
        Returns:
            PerformanceMetrics object with database-specific data
        """
        pass
    
    @abstractmethod
    def capture_schema_metrics(self, timestamp: datetime.datetime, schema_name: str) -> SchemaMetrics:
        """Capture database-specific schema metrics
        
        Args:
            timestamp: Timestamp for the metrics
            schema_name: Name of the schema to analyze
            
        Returns:
            SchemaMetrics object with database-specific data
        """
        pass
    
    @abstractmethod
    def get_default_schema_name(self) -> str:
        """Get the default schema name for this database type
        
        Returns:
            Default schema name
        """
        pass
    
    def get_database_type(self) -> str:
        """Get the database type
        
        Returns:
            Database type string
        """
        return self.db_type
    
    # Common DML tracking methods (no database-specific logic)
    def reset_dml_tracking(self):
        """Reset DML operation tracking"""
        self.dml_operation_tracker = DMLOperationMetrics()
        self._dml_start_time = datetime.datetime.now()
    
    def record_dml_operation(self, operation_type: str, rows_affected: int = 1):
        """Record a DML operation
        
        Args:
            operation_type: Type of operation ('insert', 'update', 'delete')
            rows_affected: Number of rows affected by the operation
        """
        if self._dml_start_time is None:
            self._dml_start_time = datetime.datetime.now()
        
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
    
    def finalize_dml_tracking(self):
        """Finalize DML tracking by calculating duration"""
        if self._dml_start_time:
            end_time = datetime.datetime.now()
            self.dml_operation_tracker.operation_duration_seconds = (
                end_time - self._dml_start_time
            ).total_seconds()
    
    def get_dml_metrics(self) -> DMLOperationMetrics:
        """Get current DML metrics
        
        Returns:
            Current DML operation metrics
        """
        return self.dml_operation_tracker
    
    # Common baseline and comparison methods
    def set_baseline_metrics(self, metrics: PerformanceMetrics = None):
        """Set baseline performance metrics
        
        Args:
            metrics: Optional metrics to use as baseline. If None, captures current metrics.
        """
        if metrics is None:
            metrics = self.capture_performance_metrics(datetime.datetime.now())
        self.baseline_metrics = metrics
    
    def generate_impact_report(self) -> Dict[str, Any]:
        """Generate impact analysis report comparing current metrics to baseline
        
        Returns:
            Dictionary containing impact analysis
        """
        if not self.baseline_metrics:
            return {
                'status': 'no_baseline',
                'message': 'No baseline metrics available for comparison'
            }
        
        current_metrics = self.capture_performance_metrics(datetime.datetime.now())
        
        # Calculate deltas
        deltas = {
            'cpu_percent_change': current_metrics.cpu_percent - self.baseline_metrics.cpu_percent,
            'memory_gb_change': current_metrics.memory_gb - self.baseline_metrics.memory_gb,
            'io_reads_per_sec_change': current_metrics.io_reads_per_sec - self.baseline_metrics.io_reads_per_sec,
            'io_writes_per_sec_change': current_metrics.io_writes_per_sec - self.baseline_metrics.io_writes_per_sec,
            'buffer_cache_hit_ratio_change': current_metrics.buffer_cache_hit_ratio - self.baseline_metrics.buffer_cache_hit_ratio,
            'active_connections_change': current_metrics.active_connections - self.baseline_metrics.active_connections,
            'blocking_sessions_change': current_metrics.blocking_sessions - self.baseline_metrics.blocking_sessions,
            'wal_size_mb_change': current_metrics.wal_size_mb - self.baseline_metrics.wal_size_mb
        }
        
        # Determine impact level
        impact_score = 0
        if abs(deltas['cpu_percent_change']) > 20:
            impact_score += 2
        elif abs(deltas['cpu_percent_change']) > 10:
            impact_score += 1
        
        if abs(deltas['memory_gb_change']) > 0.5:
            impact_score += 2
        elif abs(deltas['memory_gb_change']) > 0.2:
            impact_score += 1
        
        if deltas['active_connections_change'] > 5:
            impact_score += 1
        
        if deltas['buffer_cache_hit_ratio_change'] < -5:
            impact_score += 2
        elif deltas['buffer_cache_hit_ratio_change'] < -2:
            impact_score += 1
        
        # Classify impact level
        if impact_score >= 5:
            impact_level = 'high'
        elif impact_score >= 3:
            impact_level = 'medium'
        elif impact_score >= 1:
            impact_level = 'low'
        else:
            impact_level = 'minimal'
        
        return {
            'status': 'success',
            'impact_level': impact_level,
            'impact_score': impact_score,
            'baseline_metrics': self.baseline_metrics,
            'current_metrics': current_metrics,
            'deltas': deltas,
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def print_summary_report(self, metrics: PerformanceMetrics = None):
        """Print a summary report of current metrics
        
        Args:
            metrics: Optional metrics to print. If None, captures current metrics.
        """
        if metrics is None:
            metrics = self.capture_performance_metrics(datetime.datetime.now())
        
        print(f"\n📊 {self.db_type.upper()} PERFORMANCE SUMMARY")
        print(f"{'='*50}")
        print(f"Timestamp:          {metrics.timestamp}")
        print(f"System Info:        {metrics.cpu_count} CPUs, {metrics.max_memory_gb:.1f} GB Max Memory")
        print(f"CPU Usage:          {metrics.cpu_percent:.1f}%")
        print(f"Memory Usage:       {metrics.memory_gb:.2f} GB")
        print(f"I/O Reads/sec:      {metrics.io_reads_per_sec:.1f}")
        print(f"I/O Writes/sec:     {metrics.io_writes_per_sec:.1f}")
        print(f"I/O Read MB/sec:    {metrics.io_read_bytes_per_sec/1024/1024:.1f}")
        print(f"I/O Write MB/sec:   {metrics.io_write_bytes_per_sec/1024/1024:.1f}")
        print(f"Buffer Hit Ratio:   {metrics.buffer_cache_hit_ratio:.2f}%")
        print(f"Active Connections: {metrics.active_connections}")
        print(f"Blocking Sessions:  {metrics.blocking_sessions}")
        print(f"WAL Size:           {metrics.wal_size_mb:.1f} MB")
        
        # Print DML metrics if available
        if metrics.dml_metrics.total_operations > 0:
            dml = metrics.dml_metrics
            print(f"\n🔄 DML OPERATIONS:")
            print(f"Total Operations:   {dml.total_operations:,}")
            print(f"Total Rows:         {dml.total_rows_affected:,}")
            print(f"Operations/sec:     {dml.operations_per_second:.1f}")
            print(f"Rows/sec:           {dml.rows_per_second:.1f}")

# Factory function to get the appropriate monitor provider
def get_monitor_provider(db_type: str, engine: sa.Engine) -> MonitorProviderBase:
    """Factory function to get the appropriate monitor provider
    
    Args:
        db_type: Database type ('sqlserver', 'mysql', 'postgresql')
        engine: SQLAlchemy engine
        
    Returns:
        Appropriate MonitorProvider instance
        
    Raises:
        ValueError: If database type is not supported
    """
    db_type = db_type.lower()
    
    if db_type == 'sqlserver':
        from .SimpleMonitorSqlServer import SqlServerMonitorProvider
        return SqlServerMonitorProvider(engine, db_type)
    elif db_type == 'mysql':
        from .SimpleMonitorMySQL import MySQLMonitorProvider
        return MySQLMonitorProvider(engine, db_type)
    elif db_type == 'postgresql':
        from .SimpleMonitorPostgreSQL import PostgreSQLMonitorProvider
        return PostgreSQLMonitorProvider(engine, db_type)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
