"""
Full Database Test Scenario

Runs complete test suite including database-level changes:
- Setup validation
- CDC cleanup
- Bulk CDC/CT status check
- Data type discovery
- Table creation (DDL)
- Bulk CDC/CT enable
- Column operations (ALTER TABLE)
- DML operations (INSERT, UPDATE, DELETE)
- Metadata refresh
- LFC integration (database-level DDL support)
- Optional cleanup

This is the most comprehensive test and requires full database control.
It tests database-level operations including CDC/CT enablement at the database level.

Use Case: Testing in a dedicated test database where you have full control
and want to validate all operations including database-level changes.

⚠️ WARNING: This test makes database-level changes. Only run in dedicated test databases!
"""

from typing import Dict, Any, List
from .TestComprehensive import TestComprehensive

class TestFullDatabase:
    """Full database test scenario with database-level operations"""
    
    def __init__(self, simple_test):
        """Initialize with SimpleTest instance
        
        Args:
            simple_test: SimpleTest instance with setup modules
        """
        self.simple_test = simple_test
        self.test_comprehensive = TestComprehensive(simple_test)
    
    def run(self, 
            table_count_per_type: int = 2,
            test_columns: List[str] = None,
            duration_minutes: int = 5,
            cleanup_after_test: bool = True) -> Dict[str, Any]:
        """Run complete test with database-level operations
        
        Performs all operations including database-level CDC/CT enablement,
        LFC integration, and full DDL/DML testing.
        
        ⚠️ WARNING: This makes database-level changes!
        
        Args:
            table_count_per_type: Number of tables to create for each type
            test_columns: List of test column names to add
            duration_minutes: How long to run DML operations
            cleanup_after_test: Whether to cleanup tables after testing
            
        Returns:
            dict: Test results
        """
        if test_columns is None:
            test_columns = ['field_test1', 'field_test2']
        
        if self.simple_test.test_mode != 'new_database':
            print(f"⚠️ WARNING: Test mode is '{self.simple_test.test_mode}', expected 'new_database'")
            print(f"⚠️ This test makes database-level changes!")
        
        print(f"🗄️ Running FULL DATABASE test for {duration_minutes} minutes...")
        print(f"⚠️  WARNING: Database-level operations will be performed!")
        print(f"📋 Operations: DB-level CDC/CT, DDL, ALTER, DML, LFC integration")
        
        # Full database operations - delegate to TestComprehensive methods
        full_phases = [
            ('setup_validation', self.test_comprehensive._test_setup_validation),
            ('cdc_cleanup', self.test_comprehensive._test_cdc_cleanup),
            ('bulk_cdc_ct_status', self.test_comprehensive._test_bulk_cdc_ct_status),
            ('data_type_discovery', self.test_comprehensive._test_data_type_discovery),
            ('table_creation', self.test_comprehensive._test_table_creation, table_count_per_type),
            ('bulk_cdc_ct_enable', self.test_comprehensive._test_bulk_cdc_ct_enable),
            ('column_operations', self.test_comprehensive._test_column_operations, test_columns),
            ('dml_operations', self.test_comprehensive._test_dml_operations, duration_minutes),
            ('metadata_refresh', self.test_comprehensive._test_metadata_refresh),
            ('lfc_integration', self.test_comprehensive._test_lfc_integration),
        ]
        
        if cleanup_after_test:
            full_phases.append(('cleanup', self.test_comprehensive._test_cleanup, table_count_per_type))
        
        return self.simple_test._run_test_phases(full_phases, "Full Database Test")



