#!/usr/bin/env python3
"""
SimpleReport.py - Reporting and Display Functions for Database Testing

This module contains all reporting, display, and summary generation functions
that were extracted from SimpleTest.py to improve code organization.
"""

import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

class SimpleReport:
    """Handles all reporting and display functionality for database testing"""
    
    def __init__(self, simple_monitor=None):
        """Initialize the reporting module
        
        Args:
            simple_monitor: SimpleMonitor instance for performance metrics
        """
        self.simple_monitor = simple_monitor
    
    def display_performance_monitoring(self):
        """Display comprehensive performance monitoring report"""
        if not self.simple_monitor:
            print("⚠️ Performance monitoring not available (SimpleMonitor not initialized)")
            return
        
        try:
            # Generate and display the impact report
            print(f"\n{'='*80}")
            print(f"🔍 PERFORMANCE MONITORING REPORT")
            print(f"{'='*80}")
            
            # Get current performance metrics
            current_metrics = self.simple_monitor._capture_performance_metrics()
            
            print(f"\n📊 CURRENT PERFORMANCE METRICS:")
            print(f"Timestamp:          {current_metrics.timestamp}")
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
            schema_metrics = self.simple_monitor.capture_schema_metrics()
            
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
            dml_metrics = self.simple_monitor.get_dml_metrics()
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
            if hasattr(self.simple_monitor, 'baseline_metrics') and self.simple_monitor.baseline_metrics:
                print(f"\n📊 IMPACT ANALYSIS:")
                impact_report = self.simple_monitor.generate_impact_report()
                
                print(f"Impact Level:       {impact_report['impact_level']}")
                
                deltas = impact_report['deltas']
                print(f"\n📈 PERFORMANCE CHANGES:")
                print(f"CPU Change:         {deltas['cpu_percent_change']:+.1f}%")
                print(f"Memory Change:      {deltas['memory_gb_change']:+.2f} GB")
                print(f"Buffer Hit Change:  {deltas['buffer_cache_hit_ratio_change']:+.2f}%")
                print(f"Connection Change:  {deltas['active_connections_change']:+d}")
                
                # Show recommendations
                recommendations = impact_report.get('recommendations', [])
                if recommendations:
                    print(f"\n💡 RECOMMENDATIONS:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec}")
            
            print(f"\n{'='*80}")
            
        except Exception as e:
            print(f"⚠️ Error generating performance monitoring report: {e}")
    
    def generate_test_summary(self, test_results: Dict[str, Any], test_duration: datetime.timedelta, retry_counts: Dict[str, int] = None) -> Dict[str, Any]:
        """Generate a comprehensive test summary
        
        Args:
            test_results: Dictionary of test results
            test_duration: Total test duration
            retry_counts: Dictionary of retry counts by operation type
            
        Returns:
            Dictionary containing test summary statistics
        """
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        # Count test results (exclude 'summary' to avoid circular reference)
        for test_name, result in test_results.items():
            if test_name == 'summary':
                continue
                
            total_tests += 1
            
            if isinstance(result, dict):
                status = result.get('status', 'unknown')
                if status == 'success':
                    passed_tests += 1
                elif status == 'error':
                    failed_tests += 1
                elif status == 'skipped':
                    skipped_tests += 1
                else:
                    # Treat unknown status as failed
                    failed_tests += 1
            else:
                # Non-dict results are treated as failed
                failed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate retry statistics
        total_retries = sum(retry_counts.values()) if retry_counts else 0
        retry_breakdown = retry_counts.copy() if retry_counts else {}
        
        summary = {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'skipped': skipped_tests,
            'success_rate': success_rate,
            'duration_seconds': test_duration.total_seconds(),
            'duration_formatted': str(test_duration),
            'total_retries': total_retries,
            'retry_breakdown': retry_breakdown
        }
        
        return summary
    
    def generate_operation_recommendations(self, operation_type: str, impact_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on operation impact
        
        Args:
            operation_type: Type of operation (e.g., 'dml_operations', 'table_creation')
            impact_report: Impact analysis report
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not impact_report or 'deltas' not in impact_report:
            return recommendations
        
        deltas = impact_report['deltas']
        impact_level = impact_report.get('impact_level', 'unknown')
        
        # CPU-based recommendations
        cpu_change = deltas.get('cpu_percent_change', 0)
        if cpu_change > 50:
            recommendations.append(f"High CPU increase (+{cpu_change:.1f}%) during {operation_type} - consider optimizing queries or adding indexes")
        elif cpu_change > 20:
            recommendations.append(f"Moderate CPU increase (+{cpu_change:.1f}%) during {operation_type} - monitor for sustained load")
        
        # Memory-based recommendations
        memory_change = deltas.get('memory_gb_change', 0)
        if memory_change > 1.0:
            recommendations.append(f"Significant memory increase (+{memory_change:.2f} GB) during {operation_type} - check for memory leaks")
        elif memory_change > 0.5:
            recommendations.append(f"Moderate memory increase (+{memory_change:.2f} GB) during {operation_type} - monitor memory usage")
        
        # Connection-based recommendations
        connection_change = deltas.get('active_connections_change', 0)
        if connection_change > 10:
            recommendations.append(f"High connection increase (+{connection_change}) during {operation_type} - review connection pooling")
        elif connection_change > 5:
            recommendations.append(f"Moderate connection increase (+{connection_change}) during {operation_type} - monitor connection usage")
        
        # Buffer cache recommendations
        buffer_change = deltas.get('buffer_cache_hit_ratio_change', 0)
        if buffer_change < -5:
            recommendations.append(f"Buffer cache hit ratio decreased ({buffer_change:.1f}%) during {operation_type} - consider increasing buffer pool size")
        
        # Operation-specific recommendations
        if operation_type == 'dml_operations':
            if cpu_change > 30:
                recommendations.append("Consider batching DML operations or using bulk operations for better performance")
            if memory_change > 0.5:
                recommendations.append("Large DML operations may benefit from smaller batch sizes to reduce memory pressure")
        
        elif operation_type == 'table_creation':
            if cpu_change > 20:
                recommendations.append("Table creation showing high CPU usage - consider creating tables during maintenance windows")
            if memory_change > 0.3:
                recommendations.append("Table creation using significant memory - monitor for large table operations")
        
        elif operation_type == 'column_operations':
            if cpu_change > 25:
                recommendations.append("Column operations showing high CPU usage - consider scheduling during low-activity periods")
        
        # Overall impact recommendations
        if impact_level == 'high':
            recommendations.append(f"Overall impact level is HIGH for {operation_type} - consider performance optimization")
        elif impact_level == 'medium':
            recommendations.append(f"Overall impact level is MEDIUM for {operation_type} - monitor performance trends")
        
        return recommendations
    
    def print_impact_assessment_summary(self, report: Dict[str, Any]):
        """Print a comprehensive impact assessment summary
        
        Args:
            report: Impact assessment report dictionary
        """
        print(f"\n{'='*80}")
        print(f"📊 IMPACT ASSESSMENT SUMMARY")
        print(f"{'='*80}")
        
        # Print overall summary
        overall_summary = report.get('overall_summary', {})
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"Total Phases:       {overall_summary.get('total_phases', 0)}")
        print(f"Successful Phases:  {overall_summary.get('successful_phases', 0)}")
        print(f"Failed Phases:      {overall_summary.get('failed_phases', 0)}")
        print(f"Success Rate:       {overall_summary.get('success_rate', 0):.1f}%")
        print(f"Total Duration:     {overall_summary.get('total_duration_seconds', 0):.1f} seconds")
        
        # Print phase-by-phase results
        phase_results = report.get('phase_results', {})
        if phase_results:
            print(f"\n📋 PHASE-BY-PHASE RESULTS:")
            for phase_name, phase_data in phase_results.items():
                status = phase_data.get('status', 'unknown')
                duration = phase_data.get('duration_seconds', 0)
                
                status_emoji = "✅" if status == 'success' else "❌" if status == 'error' else "⏭️"
                print(f"   {status_emoji} {phase_name.replace('_', ' ').title()}: {status} ({duration:.1f}s)")
                
                # Show impact level if available
                impact_report = phase_data.get('impact_report', {})
                if impact_report:
                    impact_level = impact_report.get('impact_level', 'unknown')
                    print(f"      Impact Level: {impact_level}")
        
        # Print performance summary
        performance_summary = report.get('performance_summary', {})
        if performance_summary:
            print(f"\n📈 PERFORMANCE SUMMARY:")
            baseline = performance_summary.get('baseline_metrics', {})
            final = performance_summary.get('final_metrics', {})
            
            if baseline and final:
                cpu_change = final.get('cpu_percent', 0) - baseline.get('cpu_percent', 0)
                memory_change = final.get('memory_gb', 0) - baseline.get('memory_gb', 0)
                
                print(f"CPU Change:         {cpu_change:+.1f}%")
                print(f"Memory Change:      {memory_change:+.2f} GB")
                print(f"Final Buffer Hit:   {final.get('buffer_cache_hit_ratio', 0):.2f}%")
                print(f"Final Connections:  {final.get('active_connections', 0)}")
        
        # Print recommendations
        all_recommendations = []
        for phase_name, phase_data in phase_results.items():
            phase_recommendations = phase_data.get('recommendations', [])
            all_recommendations.extend(phase_recommendations)
        
        if all_recommendations:
            print(f"\n💡 KEY RECOMMENDATIONS:")
            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in all_recommendations:
                if rec not in seen:
                    seen.add(rec)
                    unique_recommendations.append(rec)
            
            for i, rec in enumerate(unique_recommendations[:10], 1):  # Show top 10
                print(f"   {i}. {rec}")
        
        print(f"\n{'='*80}")
    
    def print_test_phase_summary(self, phase_name: str, result: Dict[str, Any], duration: float = None):
        """Print a summary for a single test phase
        
        Args:
            phase_name: Name of the test phase
            result: Test phase result dictionary
            duration: Optional duration in seconds
        """
        status = result.get('status', 'unknown')
        message = result.get('message', '')
        
        # Choose emoji based on status
        if status == 'success':
            status_emoji = "✅"
        elif status == 'error':
            status_emoji = "❌"
        elif status == 'skipped':
            status_emoji = "⏭️"
        else:
            status_emoji = "❓"
        
        # Format phase name
        formatted_name = phase_name.replace('_', ' ').upper()
        
        # Print phase header
        print(f"\n📋 TEST PHASE: {formatted_name}")
        
        # Print result with duration if available
        if duration is not None:
            print(f"{status_emoji} {phase_name} completed: {status} ({duration:.1f}s)")
        else:
            print(f"{status_emoji} {phase_name} completed: {status}")
        
        # Print message if available
        if message:
            print(f"   Message: {message}")
        
        # Print additional details if available
        details = result.get('details', {})
        if isinstance(details, dict) and details:
            print(f"   Details: {len(details)} items")
            # Show first few details if they're simple
            for key, value in list(details.items())[:3]:
                if isinstance(value, (str, int, float, bool)):
                    print(f"      {key}: {value}")
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable format
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable format
        
        Args:
            bytes_value: Size in bytes
            
        Returns:
            Formatted size string
        """
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024**2:
            return f"{bytes_value/1024:.1f} KB"
        elif bytes_value < 1024**3:
            return f"{bytes_value/(1024**2):.1f} MB"
        else:
            return f"{bytes_value/(1024**3):.2f} GB"
    
    def format_number(self, number: int) -> str:
        """Format large numbers with commas
        
        Args:
            number: Number to format
            
        Returns:
            Formatted number string
        """
        return f"{number:,}"





