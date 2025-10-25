#!/usr/bin/env python3
"""
SimpleMonitor.py - Refactored Database Performance and Schema Monitoring

This module provides a unified interface for database monitoring using the base class pattern
to eliminate code duplication while supporting multiple database types.
"""

import datetime
import sqlalchemy as sa
from typing import Dict, Any, List, Optional
from .SimpleMonitorBase import (
    MonitorProviderBase, 
    PerformanceMetrics, 
    SchemaMetrics, 
    DMLOperationMetrics,
    get_monitor_provider
)

class SimpleMonitor:
    """Unified database monitoring interface using provider pattern"""
    
    def __init__(self, engine: sa.Engine, db_type: str):
        """Initialize the monitor with database-specific provider
        
        Args:
            engine: SQLAlchemy engine for database connection
            db_type: Database type ('sqlserver', 'mysql', 'postgresql')
        """
        self.engine = engine
        self.db_type = db_type.lower()
        
        # Get the appropriate monitor provider
        self.provider = get_monitor_provider(self.db_type, engine)
        
        print(f"🔍 SimpleMonitor initialized for {self.db_type}")
    
    # Public interface methods - delegate to provider
    def _capture_performance_metrics(self) -> PerformanceMetrics:
        """Capture current performance metrics
        
        Returns:
            PerformanceMetrics object with current database performance data
        """
        return self.provider.capture_performance_metrics(datetime.datetime.now())
    
    def capture_schema_metrics(self, schema_name: str = None) -> SchemaMetrics:
        """Capture current schema metrics
        
        Args:
            schema_name: Optional schema name. If None, uses database default.
            
        Returns:
            SchemaMetrics object with current schema information
        """
        if schema_name is None:
            schema_name = self.provider.get_default_schema_name()
        
        print(f"📏 Capturing schema metrics for: {schema_name}")
        return self.provider.capture_schema_metrics(datetime.datetime.now(), schema_name)
    
    # DML tracking methods - delegate to provider
    def reset_dml_tracking(self):
        """Reset DML operation tracking"""
        self.provider.reset_dml_tracking()
    
    def record_dml_operation(self, operation_type: str, rows_affected: int = 1):
        """Record a DML operation
        
        Args:
            operation_type: Type of operation ('insert', 'update', 'delete')
            rows_affected: Number of rows affected by the operation
        """
        self.provider.record_dml_operation(operation_type, rows_affected)
    
    def finalize_dml_tracking(self):
        """Finalize DML tracking by calculating duration"""
        self.provider.finalize_dml_tracking()
    
    def get_dml_metrics(self) -> DMLOperationMetrics:
        """Get current DML metrics
        
        Returns:
            Current DML operation metrics
        """
        return self.provider.get_dml_metrics()
    
    # Baseline and comparison methods - delegate to provider
    def set_baseline_metrics(self, metrics: PerformanceMetrics = None):
        """Set baseline performance metrics
        
        Args:
            metrics: Optional metrics to use as baseline. If None, captures current metrics.
        """
        self.provider.set_baseline_metrics(metrics)
    
    def generate_impact_report(self) -> Dict[str, Any]:
        """Generate impact analysis report comparing current metrics to baseline
        
        Returns:
            Dictionary containing impact analysis
        """
        return self.provider.generate_impact_report()
    
    def print_summary_report(self, metrics: PerformanceMetrics = None):
        """Print a summary report of current metrics
        
        Args:
            metrics: Optional metrics to print. If None, captures current metrics.
        """
        self.provider.print_summary_report(metrics)
    
    # Convenience properties for backward compatibility
    @property
    def baseline_metrics(self) -> Optional[PerformanceMetrics]:
        """Get baseline metrics"""
        return self.provider.baseline_metrics
    
    @baseline_metrics.setter
    def baseline_metrics(self, value: PerformanceMetrics):
        """Set baseline metrics"""
        self.provider.baseline_metrics = value
    
    @property
    def dml_operation_tracker(self) -> DMLOperationMetrics:
        """Get DML operation tracker"""
        return self.provider.dml_operation_tracker
    
    # Additional utility methods
    def get_database_type(self) -> str:
        """Get the database type
        
        Returns:
            Database type string
        """
        return self.provider.get_database_type()
    
    def get_default_schema_name(self) -> str:
        """Get the default schema name for this database type
        
        Returns:
            Default schema name
        """
        return self.provider.get_default_schema_name()
    
    def capture_full_report(self, schema_name: str = None) -> Dict[str, Any]:
        """Capture a comprehensive report including performance and schema metrics
        
        Args:
            schema_name: Optional schema name for schema metrics
            
        Returns:
            Dictionary containing full monitoring report
        """
        timestamp = datetime.datetime.now()
        
        # Capture performance metrics
        performance_metrics = self.provider.capture_performance_metrics(timestamp)
        
        # Capture schema metrics
        if schema_name is None:
            schema_name = self.provider.get_default_schema_name()
        schema_metrics = self.provider.capture_schema_metrics(timestamp, schema_name)
        
        # Generate impact report if baseline exists
        impact_report = None
        if self.provider.baseline_metrics:
            impact_report = self.provider.generate_impact_report()
        
        return {
            'timestamp': timestamp.isoformat(),
            'database_type': self.db_type,
            'performance_metrics': performance_metrics,
            'schema_metrics': schema_metrics,
            'dml_metrics': self.provider.get_dml_metrics(),
            'impact_report': impact_report
        }
    
    def print_comprehensive_report(self, schema_name: str = None):
        """Print a comprehensive monitoring report
        
        Args:
            schema_name: Optional schema name for schema metrics
        """
        print(f"\n{'='*80}")
        print(f"🔍 COMPREHENSIVE DATABASE MONITORING REPORT")
        print(f"{'='*80}")
        print(f"Database Type: {self.db_type.upper()}")
        print(f"Timestamp: {datetime.datetime.now()}")
        
        # Performance metrics
        self.provider.print_summary_report()
        
        # Schema metrics
        if schema_name is None:
            schema_name = self.provider.get_default_schema_name()
        
        schema_metrics = self.capture_schema_metrics(schema_name)
        
        print(f"\n📈 SCHEMA METRICS ({schema_name}):")
        print(f"Total Size:         {schema_metrics.total_size_bytes / (1024*1024):.1f} MB")
        print(f"Tables Found:       {len(schema_metrics.table_metrics)}")
        print(f"Indexes Found:      {len(schema_metrics.index_metrics)}")
        
        # Top tables by size
        if schema_metrics.table_metrics:
            print(f"\n📊 TOP TABLES BY SIZE:")
            sorted_tables = sorted(schema_metrics.table_metrics, key=lambda x: x.get('size_bytes', 0), reverse=True)[:5]
            for i, table in enumerate(sorted_tables, 1):
                size_mb = table.get('size_bytes', 0) / (1024*1024)
                row_count = table.get('row_count', 0)
                table_name = table.get('table_name', 'Unknown')
                print(f"   {i}. {table_name}: {size_mb:.1f} MB, {row_count:,} rows")
        
        # DML metrics if available
        dml_metrics = self.get_dml_metrics()
        if dml_metrics.total_operations > 0:
            print(f"\n🔄 DML OPERATIONS:")
            print(f"Total Operations:   {dml_metrics.total_operations:,}")
            print(f"Total Rows:         {dml_metrics.total_rows_affected:,}")
            print(f"Operations/sec:     {dml_metrics.operations_per_second:.1f}")
            print(f"Rows/sec:           {dml_metrics.rows_per_second:.1f}")
        
        # Impact analysis if baseline exists
        if self.provider.baseline_metrics:
            impact_report = self.generate_impact_report()
            if impact_report.get('status') == 'success':
                print(f"\n📊 IMPACT ANALYSIS:")
                print(f"Impact Level:       {impact_report['impact_level']}")
                
                deltas = impact_report['deltas']
                print(f"CPU Change:         {deltas['cpu_percent_change']:+.1f}%")
                print(f"Memory Change:      {deltas['memory_gb_change']:+.2f} GB")
                print(f"Buffer Hit Change:  {deltas['buffer_cache_hit_ratio_change']:+.2f}%")
                print(f"Connection Change:  {deltas['active_connections_change']:+d}")
        
        print(f"\n{'='*80}")

# Backward compatibility - export the dataclasses
__all__ = [
    'SimpleMonitor',
    'PerformanceMetrics', 
    'SchemaMetrics', 
    'DMLOperationMetrics'
]





