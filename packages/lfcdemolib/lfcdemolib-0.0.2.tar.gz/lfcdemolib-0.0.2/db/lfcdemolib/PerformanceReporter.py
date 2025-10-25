"""
Performance Reporter

Handles performance monitoring display and reporting.
"""

from typing import Dict, Any

class PerformanceReporter:
    """Displays performance monitoring reports"""
    
    def __init__(self, simple_test):
        self.simple_test = simple_test
    def _display_performance_monitoring(self):
        """Display comprehensive performance monitoring report"""
        if not self.simple_test.simple_monitor:
            print("⚠️ Performance monitoring not available (SimpleMonitor not initialized)")
            return
        
        try:
            # Generate and display the impact report
            print(f"\n{'='*80}")
            print(f"🔍 PERFORMANCE MONITORING REPORT")
            print(f"{'='*80}")
            
            # Get current performance metrics
            current_metrics = self.simple_test.simple_monitor._capture_performance_metrics()
            
            print(f"\n📊 CURRENT PERFORMANCE METRICS:")
            print(f"Timestamp:          {current_metrics.timestamp}")
            print(f"System Info:        {current_metrics.cpu_count} CPUs, {current_metrics.max_memory_gb:.1f} GB Max Memory")
            print(f"CPU Usage:          {current_metrics.cpu_percent:.1f}%")
            print(f"Memory Usage:       {current_metrics.memory_gb:.2f} GB")
            print(f"I/O Reads/sec:      {current_metrics.io_reads_per_sec:.1f}")
            print(f"I/O Writes/sec:     {current_metrics.io_writes_per_sec:.1f}")
            print(f"I/O Read MB/sec:    {current_metrics.io_read_bytes_per_sec/1024/1024:.1f}")
            print(f"I/O Write MB/sec:   {current_metrics.io_write_bytes_per_sec/1024/1024:.1f}")
            print(f"Buffer Hit Ratio:   {current_metrics.buffer_cache_hit_ratio:.2f}%")
            print(f"Active Connections: {current_metrics.active_connections}")
            print(f"Blocking Sessions:  {current_metrics.blocking_sessions}")
            print(f"WAL Size:           {current_metrics.wal_size_mb:.1f} MB")
            
            # Get schema metrics
            schema_metrics = self.simple_test.simple_monitor.capture_schema_metrics()
            
            print(f"\n📈 SCHEMA METRICS:")
            print(f"Schema Name:        {schema_metrics.schema_name}")
            print(f"Total Size:         {schema_metrics.total_size_bytes / (1024*1024):.1f} MB")
            print(f"Tables Found:       {len(schema_metrics.table_metrics)}")
            print(f"Indexes Found:      {len(schema_metrics.index_metrics)}")
            
            # Show breakdown by schema if multiple schemas are included
            if '+' in schema_metrics.schema_name and schema_metrics.table_metrics:
                print(f"\n📏 SCHEMA BREAKDOWN:")
                schema_breakdown = {}
                for table in schema_metrics.table_metrics:
                    schema = table.get('schema_name', 'unknown')
                    if schema not in schema_breakdown:
                        schema_breakdown[schema] = {'tables': 0, 'size_bytes': 0, 'rows': 0}
                    schema_breakdown[schema]['tables'] += 1
                    schema_breakdown[schema]['size_bytes'] += table.get('size_bytes', 0)
                    schema_breakdown[schema]['rows'] += table.get('row_count', 0)
                
                for schema, stats in schema_breakdown.items():
                    size_mb = stats['size_bytes'] / (1024*1024)
                    print(f"   {schema}: {stats['tables']} tables, {size_mb:.1f} MB, {stats['rows']:,} rows")
            
            # Show top 3 largest tables if available
            if schema_metrics.table_metrics:
                print(f"\n📊 TOP TABLES BY SIZE:")
                sorted_tables = sorted(schema_metrics.table_metrics, key=lambda x: x.get('size_bytes', 0), reverse=True)[:3]
                for i, table in enumerate(sorted_tables, 1):
                    size_mb = table.get('size_bytes', 0) / (1024*1024)
                    row_count = table.get('row_count', 0)
                    schema_name = table.get('schema_name', '')
                    table_name = table.get('table_name', 'Unknown')
                    display_name = f"{schema_name}.{table_name}" if schema_name and schema_name != 'dbo' else table_name
                    print(f"   {i}. {display_name}: {size_mb:.1f} MB, {row_count:,} rows")
            
            # Display DML operation metrics if available
            dml_metrics = self.simple_test.simple_monitor.get_dml_metrics()
            if dml_metrics and dml_metrics.total_operations > 0:
                print(f"\n🔄 DML OPERATIONS SUMMARY:")
                print(f"Total Operations:   {dml_metrics.total_operations:,}")
                print(f"Total Rows:         {dml_metrics.total_rows_affected:,}")
                print(f"Duration:           {dml_metrics.operation_duration_seconds:.1f} seconds")
                print(f"Operations/Second:  {dml_metrics.operations_per_second:.1f}")
                print(f"Rows/Second:        {dml_metrics.rows_per_second:.1f}")
                
                print(f"\n📋 OPERATION BREAKDOWN:")
                print(f"INSERT:             {dml_metrics.insert_count:,} operations, {dml_metrics.rows_inserted:,} rows")
                print(f"UPDATE:             {dml_metrics.update_count:,} operations, {dml_metrics.rows_updated:,} rows")
                print(f"DELETE:             {dml_metrics.delete_count:,} operations, {dml_metrics.rows_deleted:,} rows")
            
            # Generate full impact report if baseline exists
            if hasattr(self.simple_test.simple_monitor, 'baseline_metrics') and self.simple_test.simple_monitor.baseline_metrics:
                print(f"\n📊 IMPACT ANALYSIS:")
                impact_report = self.simple_test.simple_monitor.generate_impact_report()
                
                print(f"Impact Level:       {impact_report['impact_level']}")
                
                deltas = impact_report['deltas']
                print(f"\n📈 PERFORMANCE CHANGES:")
                print(f"CPU Change:         {deltas['cpu_percent_change']:+.1f}%")
                print(f"Memory Change:      {deltas['memory_gb_change']:+.2f} GB")
                print(f"Buffer Hit Change:  {deltas['buffer_cache_hit_ratio_change']:+.2f}%")
                print(f"Connection Change:  {deltas['active_connections_change']:+d}")
                
                # Display recommendations
                if impact_report['recommendations']:
                    print(f"\n💡 RECOMMENDATIONS:")
                    for rec in impact_report['recommendations']:
                        print(f"   {rec}")
            
            print(f"\n{'='*80}")
            
        except Exception as e:
            print(f"⚠️ Error generating performance monitoring report: {e}")
            import traceback
            traceback.print_exc()
    
    

