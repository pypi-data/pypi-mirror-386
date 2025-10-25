"""
Impact Assessment

Database impact assessment and performance testing.
"""

import datetime
import time
import sqlalchemy as sa
from typing import Dict, Any, List

class ImpactAssessment:
    """Handles database impact assessment"""
    
    def __init__(self, simple_test):
        self.simple_test = simple_test
    def run_impact_assessment(self, operation_type: str = "baseline", duration_minutes: int = 5) -> Dict[str, Any]:
        """Run comprehensive database impact assessment
        
        Args:
            operation_type: Type of operation to assess ('baseline', 'dml', 'cdc_ct', 'lfc_setup', 'lfc_running')
            duration_minutes: How long to run the assessment
            
        Returns:
            dict: Comprehensive impact assessment results
        """
        if not self.simple_test.simple_monitor:
            print("❌ SimpleMonitor not initialized - call setup_modules() first")
            return {'status': 'error', 'message': 'Monitor not available'}
        
        print(f"🔍 Starting {operation_type.upper()} impact assessment for {duration_minutes} minutes...")
        
        # Capture baseline if not already done
        if self.simple_test.simple_monitor.baseline_metrics is None:
            print("📊 Capturing baseline metrics...")
            self.simple_test.simple_monitor.capture_baseline()
        
        # Capture schema metrics before operation
        schema_before = self.simple_test.simple_monitor.capture_schema_metrics()
        
        # Run the specified operation
        operation_results = {}
        if operation_type == "baseline":
            operation_results = self._run_baseline_assessment(duration_minutes)
        elif operation_type == "dml":
            operation_results = self._run_dml_impact_assessment(duration_minutes)
        elif operation_type == "cdc_ct":
            operation_results = self._run_cdc_ct_impact_assessment(duration_minutes)
        elif operation_type == "lfc_setup":
            operation_results = self._run_lfc_setup_impact_assessment(duration_minutes)
        elif operation_type == "lfc_running":
            operation_results = self._run_lfc_running_impact_assessment(duration_minutes)
        else:
            return {'status': 'error', 'message': f'Unknown operation type: {operation_type}'}
        
        # Capture metrics after operation
        performance_after = self.simple_test.simple_monitor._capture_performance_metrics()
        schema_after = self.simple_test.simple_monitor.capture_schema_metrics()
        
        # Generate impact report
        impact_report = self.simple_test.simple_monitor.generate_impact_report(performance_after)
        
        # Calculate schema changes
        schema_changes = {
            'total_size_change_bytes': schema_after.total_size_bytes - schema_before.total_size_bytes,
            'table_count_before': len(schema_before.table_metrics),
            'table_count_after': len(schema_after.table_metrics)
        }
        
        comprehensive_report = {
            'operation_type': operation_type,
            'duration_minutes': duration_minutes,
            'timestamp': datetime.datetime.now().isoformat(),
            'performance_impact': impact_report,
            'schema_changes': schema_changes,
            'operation_results': operation_results,
            'recommendations': self._generate_operation_recommendations(operation_type, impact_report)
        }
        
        # Print summary
        self._print_impact_assessment_summary(comprehensive_report)
        
        return comprehensive_report
    

    def _run_baseline_assessment(self, duration_minutes: int) -> Dict[str, Any]:
        """Run baseline assessment with no special operations"""
        print("📋 Running baseline assessment (no operations)...")
        time.sleep(duration_minutes * 60)  # Just wait
        return {'status': 'completed', 'message': 'Baseline assessment completed'}
    

    def _run_dml_impact_assessment(self, duration_minutes: int) -> Dict[str, Any]:
        """Run DML operations impact assessment"""
        print("📋 Running DML operations impact assessment...")
        if not self.simple_test.simple_dml:
            return {'status': 'error', 'message': 'SimpleDML not initialized'}
        
        if not self.simple_test.created_tables:
            return {'status': 'error', 'message': 'No tables available for DML operations'}
        
        # Reset DML tracking
        if self.simple_test.simple_monitor:
            self.simple_test.simple_monitor.reset_dml_tracking()
        
        # Run DML operations for specified duration
        start_time = time.time()
        operations_count = 0
        total_rows_affected = 0
        
        while (time.time() - start_time) < (duration_minutes * 60):
            # Cycle through all created tables
            for table_name in self.simple_test.created_tables.keys():
                if (time.time() - start_time) >= (duration_minutes * 60):
                    break
                    
                try:
                    # Execute DML operations and capture results
                    result = self.simple_test.simple_dml.execute_delete_update_insert(
                        max_rows=10,
                        time_window_seconds=60,
                        table_name=table_name
                    )
                    operations_count += 1
                    
                    # Parse the result to extract row counts
                    if isinstance(result, dict):
                        deletes = result.get('deleted', 0)
                        updates = result.get('updated', 0) 
                        inserts = result.get('inserted', 0)
                        
                        # Record operations in monitor
                        if self.simple_test.simple_monitor:
                            if deletes > 0:
                                self.simple_test.simple_monitor.record_dml_operation('delete', deletes)
                            if updates > 0:
                                self.simple_test.simple_monitor.record_dml_operation('update', updates)
                            if inserts > 0:
                                self.simple_test.simple_monitor.record_dml_operation('insert', inserts)
                        
                        total_rows_affected += deletes + updates + inserts
                    
                    time.sleep(2)  # Brief pause between operations
                except Exception as e:
                    print(f"⚠️ DML operation failed for {table_name}: {e}")
                    continue
        
        actual_duration = time.time() - start_time
        
        # Finalize DML tracking
        if self.simple_test.simple_monitor:
            self.simple_test.simple_monitor.finalize_dml_tracking(actual_duration)
        
        return {
            'status': 'completed',
            'operations_executed': operations_count,
            'total_rows_affected': total_rows_affected,
            'duration_actual_minutes': actual_duration / 60,
            'duration_actual_seconds': actual_duration
        }
    

    def _run_cdc_ct_impact_assessment(self, duration_minutes: int) -> Dict[str, Any]:
        """Run CDC/CT impact assessment"""
        print("📋 Running CDC/CT impact assessment...")
        
        # Enable CDC/CT on tables if not already enabled
        cdc_results = []
        if self.simple_test.created_tables:
            for table_type, tables in self.simple_test.created_tables.items():
                for table_info in tables:
                    try:
                        if hasattr(self.simple_test.simple_dml.ddl, 'cdc') and self.simple_test.simple_dml.ddl.cdc:
                            result = self.simple_test.simple_dml.ddl.cdc._enable_cdc_for_table(table_info['name'])
                            cdc_results.append(result)
                    except Exception as e:
                        print(f"⚠️ CDC setup failed for {table_info['name']}: {e}")
        
        # Run DML operations with CDC enabled (this will track DML operations)
        dml_results = self._run_dml_impact_assessment(duration_minutes)
        
        return {
            'status': 'completed',
            'cdc_setup_results': cdc_results,
            'dml_with_cdc_results': dml_results,
            'message': 'CDC/CT impact assessment with DML operations completed'
        }
    

    def _run_lfc_setup_impact_assessment(self, duration_minutes: int) -> Dict[str, Any]:
        """Run LFC setup impact assessment"""
        print("📋 Running LFC setup impact assessment...")
        
        lfc_results = []
        if hasattr(self.simple_test.simple_dml.ddl, 'lfc') and self.simple_test.simple_dml.ddl.lfc:
            try:
                # Setup LFC DDL support objects
                result = self.simple_test.simple_dml.ddl.lfc.setup_ddl_support_objects()
                lfc_results.append(result)
            except Exception as e:
                print(f"⚠️ LFC setup failed: {e}")
        
        # Brief monitoring period
        time.sleep(duration_minutes * 60)
        
        return {
            'status': 'completed',
            'lfc_setup_results': lfc_results,
            'message': 'LFC setup completed - minimal runtime impact expected'
        }
    

    def _run_lfc_running_impact_assessment(self, duration_minutes: int) -> Dict[str, Any]:
        """Run LFC running (active replication) impact assessment"""
        print("📋 Running LFC active replication impact assessment...")
        print("ℹ️ Note: This simulates the impact of active Lakeflow Connect replication")
        
        # Simulate active replication by running frequent queries
        start_time = time.time()
        query_count = 0
        
        while (time.time() - start_time) < (duration_minutes * 60):
            try:
                # Simulate change detection queries
                with self.simple_test.engine.connect() as conn:
                    # Query change tracking tables (if available)
                    if self.db_type == 'sqlserver':
                        conn.execute(sa.text("SELECT COUNT(*) FROM sys.change_tracking_tables"))
                    
                    # Query table metadata
                    conn.execute(sa.text("SELECT COUNT(*) FROM information_schema.tables"))
                    
                query_count += 1
                time.sleep(2)  # Simulate replication frequency
                
            except Exception as e:
                print(f"⚠️ Replication simulation query failed: {e}")
                break
        
        return {
            'status': 'completed',
            'simulated_queries': query_count,
            'duration_actual_minutes': (time.time() - start_time) / 60,
            'message': 'Simulated active Lakeflow Connect replication impact'
        }
    

    def _generate_operation_recommendations(self, operation_type: str, impact_report: Dict[str, Any]) -> List[str]:
        """Generate operation-specific recommendations"""
        recommendations = []
        impact_level = impact_report.get('impact_level', 'UNKNOWN')
        
        if operation_type == "dml":
            if impact_level == "HIGH":
                recommendations.append("🔧 Consider reducing DML operation frequency")
                recommendations.append("📊 Monitor for lock contention and blocking")
            recommendations.append("💡 DML operations have direct impact on transaction log growth")
            
        elif operation_type == "cdc_ct":
            recommendations.append("📈 CDC/CT adds overhead to all DML operations")
            recommendations.append("🗂️ Monitor change tracking table growth")
            if impact_level in ["HIGH", "MEDIUM"]:
                recommendations.append("⚠️ Consider CDC retention period optimization")
                
        elif operation_type == "lfc_setup":
            recommendations.append("✅ LFC setup has minimal runtime impact")
            recommendations.append("📋 Impact occurs mainly during initial setup phase")
            
        elif operation_type == "lfc_running":
            recommendations.append("🔄 Active replication creates continuous read load")
            recommendations.append("🔒 Monitor for shared lock blocking on source tables")
            recommendations.append("📊 Network bandwidth usage will increase significantly")
            if impact_level == "HIGH":
                recommendations.append("⚡ Consider replication frequency optimization")
        
        return recommendations
    

    def _print_impact_assessment_summary(self, report: Dict[str, Any]):
        """Print formatted impact assessment summary"""
        print(f"\n{'='*70}")
        print(f"🔍 DATABASE IMPACT ASSESSMENT SUMMARY")
        print(f"{'='*70}")
        print(f"Operation Type: {report['operation_type'].upper()}")
        print(f"Duration:       {report['duration_minutes']} minutes")
        print(f"Impact Level:   {report['performance_impact']['impact_level']}")
        
        # Performance deltas
        deltas = report['performance_impact']['deltas']
        print(f"\n📊 PERFORMANCE IMPACT:")
        print(f"CPU Change:           {deltas['cpu_percent_change']:+.1f}%")
        print(f"Memory Change:        {deltas['memory_gb_change']:+.2f}GB")
        print(f"Buffer Cache Change:  {deltas['buffer_cache_hit_ratio_change']:+.2f}%")
        print(f"Connection Change:    {deltas['active_connections_change']:+d}")
        
        # DML Operations Summary
        dml_ops = report['performance_impact']['dml_operations']
        if dml_ops['total_operations'] > 0:
            print(f"\n🔄 DML OPERATIONS:")
            print(f"Total Operations:     {dml_ops['total_operations']:,} ({dml_ops['operations_per_second']:.1f}/sec)")
            print(f"Total Rows:           {dml_ops['total_rows_affected']:,} ({dml_ops['rows_per_second']:.1f}/sec)")
            print(f"INSERT:               {dml_ops['insert_count']:,} ops, {dml_ops['rows_inserted']:,} rows")
            print(f"UPDATE:               {dml_ops['update_count']:,} ops, {dml_ops['rows_updated']:,} rows")
            print(f"DELETE:               {dml_ops['delete_count']:,} ops, {dml_ops['rows_deleted']:,} rows")
            if dml_ops['total_operations'] > 0:
                avg_rows_per_op = dml_ops['total_rows_affected'] / dml_ops['total_operations']
                print(f"Avg Rows/Operation:   {avg_rows_per_op:.1f}")
        
        # Schema changes
        schema_changes = report['schema_changes']
        print(f"\n📏 SCHEMA IMPACT:")
        print(f"Size Change:     {schema_changes['total_size_change_bytes']:+,} bytes")
        print(f"Table Count:     {schema_changes['table_count_before']} → {schema_changes['table_count_after']}")
        
        # Recommendations
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   {rec}")
        
        print(f"{'='*70}\n")
    

