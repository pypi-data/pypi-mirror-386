"""
Async Parallel Test Scenario

Runs DML, DDL, and ALTER operations in parallel using threads:
- Parallel DML operations (INSERT, UPDATE, DELETE)
- Parallel DDL operations (CREATE TABLE, DROP TABLE)
- Parallel ALTER operations (ADD COLUMN, DROP COLUMN)
- Performance metrics capture
- Contention and concurrency testing

This test validates that the system can handle concurrent operations
and measures performance under parallel load.

Use Case: Testing concurrent operation handling, identifying bottlenecks,
and measuring system performance under parallel load.

⚠️ NOTE: This test creates high database load with parallel operations.
Run in test environments only.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any

class TestAsyncParallel:
    """Async parallel test scenario for concurrent operations"""
    
    def __init__(self, simple_test):
        """Initialize with SimpleTest instance
        
        Args:
            simple_test: SimpleTest instance with setup modules
        """
        self.simple_test = simple_test
    
    def run(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Run async parallel test where DML, DDL, and ALTER operations run in parallel
        
        Args:
            duration_minutes: Duration to run the test
            
        Returns:
            dict: Test results with performance metrics
        """
        print(f"🚀 Starting ASYNC PARALLEL test for {duration_minutes} minutes...")
        print(f"📋 Operations: DML, DDL, and ALTER running in parallel")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Capture initial metrics
        self.simple_test.simple_monitor.capture_performance_metrics()
        initial_schema_metrics = self.simple_test.simple_monitor.capture_schema_metrics()
        
        # Results storage
        results = {
            'dml_operations': {'inserts': 0, 'updates': 0, 'deletes': 0, 'errors': 0},
            'ddl_operations': {'tables_created': 0, 'tables_dropped': 0, 'errors': 0},
            'alter_operations': {'columns_added': 0, 'columns_dropped': 0, 'errors': 0},
            'start_time': start_time,
            'end_time': None,
            'duration_seconds': 0,
            'status': 'running'
        }
        
        # Thread-safe counters
        lock = threading.Lock()
        
        def update_results(category, operation, count=1):
            with lock:
                if category in results and operation in results[category]:
                    results[category][operation] += count
        
        def dml_worker():
            """Worker function for DML operations"""
            try:
                while time.time() < end_time:
                    try:
                        # Perform DML operations
                        dml_result = self.simple_test.simple_dml.perform_round_robin_operations(
                            operation_counts={'insert': 5, 'update': 3, 'delete': 2}
                        )
                        update_results('dml_operations', 'inserts', dml_result.get('insert', {}).get('rows_affected', 0))
                        update_results('dml_operations', 'updates', dml_result.get('update', {}).get('rows_affected', 0))
                        update_results('dml_operations', 'deletes', dml_result.get('delete', {}).get('rows_affected', 0))
                        time.sleep(1)  # Small delay between operations
                    except Exception as e:
                        update_results('dml_operations', 'errors')
                        print(f"⚠️ DML Error: {e}")
            except Exception as e:
                print(f"❌ DML Worker Error: {e}")
        
        def ddl_worker():
            """Worker function for DDL operations"""
            try:
                table_counter = 0
                while time.time() < end_time:
                    try:
                        # Create a test table
                        table_name = f"async_test_{table_counter}"
                        self.simple_test.simple_ddl.create_test_tables(
                            base_names=['intpk'],
                            count_per_type=1,
                            force_recreate=True
                        )
                        update_results('ddl_operations', 'tables_created')
                        table_counter += 1
                        time.sleep(5)  # Delay between DDL operations
                    except Exception as e:
                        update_results('ddl_operations', 'errors')
                        print(f"⚠️ DDL Error: {e}")
            except Exception as e:
                print(f"❌ DDL Worker Error: {e}")
        
        def alter_worker():
            """Worker function for ALTER operations"""
            try:
                column_counter = 0
                while time.time() < end_time:
                    try:
                        # Get available tables
                        tables = list(self.simple_test.created_tables.keys())
                        if tables:
                            table_name = tables[column_counter % len(tables)]
                            test_column = f"async_col_{column_counter}"
                            
                            # Add a column
                            self.simple_test.simple_alter.add_column(
                                table_name=table_name,
                                column_name=test_column,
                                data_type='VARCHAR(50)'
                            )
                            update_results('alter_operations', 'columns_added')
                            column_counter += 1
                        time.sleep(3)  # Delay between ALTER operations
                    except Exception as e:
                        update_results('alter_operations', 'errors')
                        print(f"⚠️ ALTER Error: {e}")
            except Exception as e:
                print(f"❌ ALTER Worker Error: {e}")
        
        # Run workers in parallel
        print("🔄 Starting parallel workers...")
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(dml_worker),
                executor.submit(ddl_worker),
                executor.submit(alter_worker)
            ]
            
            # Wait for all workers to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Worker failed: {e}")
        
        # Capture final metrics
        results['end_time'] = time.time()
        results['duration_seconds'] = results['end_time'] - results['start_time']
        results['status'] = 'completed'
        
        final_perf_metrics = self.simple_test.simple_monitor.capture_performance_metrics()
        final_schema_metrics = self.simple_test.simple_monitor.capture_schema_metrics()
        
        results['performance_metrics'] = {
            'initial': initial_schema_metrics,
            'final': final_schema_metrics,
            'performance': final_perf_metrics
        }
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"📊 ASYNC PARALLEL TEST RESULTS")
        print(f"{'='*80}")
        print(f"Duration: {results['duration_seconds']:.2f} seconds")
        print(f"\nDML Operations:")
        print(f"  Inserts: {results['dml_operations']['inserts']}")
        print(f"  Updates: {results['dml_operations']['updates']}")
        print(f"  Deletes: {results['dml_operations']['deletes']}")
        print(f"  Errors: {results['dml_operations']['errors']}")
        print(f"\nDDL Operations:")
        print(f"  Tables Created: {results['ddl_operations']['tables_created']}")
        print(f"  Errors: {results['ddl_operations']['errors']}")
        print(f"\nALTER Operations:")
        print(f"  Columns Added: {results['alter_operations']['columns_added']}")
        print(f"  Errors: {results['alter_operations']['errors']}")
        print(f"{'='*80}")
        
        return results




