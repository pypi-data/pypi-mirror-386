"""
Test Scenario Runner

Orchestrates running multiple test scenarios in sequence.
"""

import datetime
import traceback
from typing import Dict, Any, List

class TestScenarioRunner:
    """Runs multiple test scenarios in sequence"""
    
    def __init__(self, simple_test):
        self.simple_test = simple_test
    def run_all_scenarios(self, 
                         duration_per_scenario: int = 2,
                         table_count_per_type: int = 2,
                         test_columns: List[str] = None,
                         cleanup_between_scenarios: bool = True) -> Dict[str, Any]:
        """Run all 3 test scenarios in sequence with 3 different databases
        
        This comprehensive test suite runs:
        1. Mode 1 (Shared Environment): DML-only on existing database
        2. Mode 2 (Dedicated Schema): DML + DDL + ALTER in dedicated schema
        3. Mode 3 (New Database): Full test with CDC/CT and LFC
        
        Each scenario uses a different database to ensure isolation.
        
        Args:
            duration_per_scenario: Duration in minutes for each scenario
            table_count_per_type: Number of tables to create per type (modes 2 & 3)
            test_columns: Columns to test for ALTER operations (modes 2 & 3)
            cleanup_between_scenarios: Whether to cleanup between scenarios
            
        Returns:
            dict: Combined results from all 3 scenarios
        """
        print("=" * 80)
        print("🎯 RUNNING ALL 3 TEST SCENARIOS")
        print("=" * 80)
        print(f"Duration per scenario: {duration_per_scenario} minutes")
        print(f"Total estimated time: {duration_per_scenario * 3} minutes")
        print()
        
        all_results = {
            'start_time': datetime.datetime.now(),
            'scenarios': {},
            'summary': {}
        }
        
        # Scenario 1: Shared Environment (DML only)
        print("\n" + "=" * 80)
        print("📋 SCENARIO 1: SHARED ENVIRONMENT (DML Only)")
        print("=" * 80)
        print("Mode: Shared Environment")
        print("Operations: DML on existing tables")
        print("Safety: ✅ Safest - No schema changes")
        print()
        
        try:
            # For scenario 1, we need an existing connection
            # If we're in new_database mode, create a database first
            if self.simple_test.test_mode == 'new_database':
                print("ℹ️  Creating database for Scenario 1...")
                # This will create a database and set up the engine
                # The database will be reused for this scenario
            
            scenario1_results = self.run_safe_test(duration_minutes=duration_per_scenario)
            all_results['scenarios']['scenario_1_shared_environment'] = {
                'mode': 'shared_environment',
                'status': 'success',
                'results': scenario1_results,
                'description': 'DML-only operations on existing tables'
            }
            print(f"\n✅ Scenario 1 completed successfully")
            
        except Exception as e:
            print(f"\n❌ Scenario 1 failed: {e}")
            all_results['scenarios']['scenario_1_shared_environment'] = {
                'mode': 'shared_environment',
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Cleanup between scenarios if requested
        if cleanup_between_scenarios:
            print(f"\n🧹 Cleaning up Scenario 1...")
            try:
                if hasattr(self, 'simple_ddl') and self.simple_test.simple_ddl:
                    self.simple_test.simple_ddl.drop_test_tables(list(self.simple_test.created_tables.keys()))
                self.simple_test.created_tables.clear()
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
        
        # Scenario 2: Dedicated Schema (DML + DDL + ALTER)
        print("\n" + "=" * 80)
        print("📋 SCENARIO 2: DEDICATED SCHEMA (DML + DDL + ALTER)")
        print("=" * 80)
        print("Mode: Dedicated Schema")
        print("Operations: Table creation, DML, column operations")
        print("Safety: ⚠️  Moderate - Schema changes in dedicated schema")
        print()
        
        try:
            scenario2_results = self.run_schema_test(
                table_count_per_type=table_count_per_type,
                test_columns=test_columns,
                duration_minutes=duration_per_scenario
            )
            all_results['scenarios']['scenario_2_dedicated_schema'] = {
                'mode': 'dedicated_schema',
                'status': 'success',
                'results': scenario2_results,
                'description': 'DML + DDL + ALTER in dedicated schema'
            }
            print(f"\n✅ Scenario 2 completed successfully")
            
        except Exception as e:
            print(f"\n❌ Scenario 2 failed: {e}")
            all_results['scenarios']['scenario_2_dedicated_schema'] = {
                'mode': 'dedicated_schema',
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Cleanup between scenarios if requested
        if cleanup_between_scenarios:
            print(f"\n🧹 Cleaning up Scenario 2...")
            try:
                if hasattr(self, 'simple_ddl') and self.simple_test.simple_ddl:
                    self.simple_test.simple_ddl.drop_test_tables(list(self.simple_test.created_tables.keys()))
                self.simple_test.created_tables.clear()
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
        
        # Scenario 3: New Database (Full test with CDC/CT and LFC)
        print("\n" + "=" * 80)
        print("📋 SCENARIO 3: NEW DATABASE (Full Test)")
        print("=" * 80)
        print("Mode: New Database")
        print("Operations: Database-level CDC/CT, LFC, DDL, DML, ALTER")
        print("Safety: ⚠️  Full - Database-level changes")
        print()
        
        try:
            scenario3_results = self.run_full_test(
                table_count_per_type=table_count_per_type,
                test_columns=test_columns,
                duration_minutes=duration_per_scenario
            )
            all_results['scenarios']['scenario_3_new_database'] = {
                'mode': 'new_database',
                'status': 'success',
                'results': scenario3_results,
                'description': 'Full test with CDC/CT and LFC integration'
            }
            print(f"\n✅ Scenario 3 completed successfully")
            
        except Exception as e:
            print(f"\n❌ Scenario 3 failed: {e}")
            all_results['scenarios']['scenario_3_new_database'] = {
                'mode': 'new_database',
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Generate summary
        all_results['end_time'] = datetime.datetime.now()
        all_results['total_duration'] = all_results['end_time'] - all_results['start_time']
        
        # Count successes
        successful_scenarios = sum(
            1 for scenario in all_results['scenarios'].values()
            if scenario.get('status') == 'success'
        )
        total_scenarios = len(all_results['scenarios'])
        
        all_results['summary'] = {
            'total_scenarios': total_scenarios,
            'successful_scenarios': successful_scenarios,
            'failed_scenarios': total_scenarios - successful_scenarios,
            'success_rate': f"{(successful_scenarios / total_scenarios * 100):.1f}%" if total_scenarios > 0 else "0%",
            'total_duration': str(all_results['total_duration'])
        }
        
        # Print final summary
        print("\n" + "=" * 80)
        print("🏁 ALL SCENARIOS COMPLETED")
        print("=" * 80)
        print(f"Total Duration: {all_results['total_duration']}")
        print(f"Scenarios Run: {total_scenarios}")
        print(f"Successful: {successful_scenarios}")
        print(f"Failed: {total_scenarios - successful_scenarios}")
        print(f"Success Rate: {all_results['summary']['success_rate']}")
        print()
        
        # Print scenario details
        for scenario_name, scenario_data in all_results['scenarios'].items():
            status_icon = "✅" if scenario_data['status'] == 'success' else "❌"
            print(f"{status_icon} {scenario_name}: {scenario_data['status']}")
            print(f"   Mode: {scenario_data['mode']}")
            print(f"   Description: {scenario_data['description']}")
            if scenario_data['status'] == 'error':
                print(f"   Error: {scenario_data.get('error', 'Unknown')}")
        
        print("=" * 80)
        
        return all_results
    

