"""
Dedicated Schema Test Scenario

Runs DDL + DML + ALTER operations in a dedicated schema:
- Setup validation
- CDC cleanup
- Table creation (DDL)
- Column operations (ALTER TABLE)
- Bulk CDC/CT enable
- DML operations (INSERT, UPDATE, DELETE)
- Metadata refresh
- Optional cleanup

This test creates and modifies tables within a dedicated schema, making it
suitable for test environments where you have your own schema but share the database.

Use Case: Testing schema-level operations when you have a dedicated schema
but don't want to affect other schemas in the same database.
"""

from typing import Dict, Any, List
from .TestComprehensive import TestComprehensive

class TestDedicatedSchema:
    """Dedicated schema test scenario with DDL + DML + ALTER operations"""
    
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
        """Run DML + DDL + ALTER operations in a dedicated schema
        
        Creates tables, modifies columns, and performs DML operations all within
        a dedicated schema. Suitable for environments where you have schema-level
        control but share the database.
        
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
        
        if self.simple_test.test_mode != 'dedicated_schema':
            print(f"⚠️ Warning: Test mode is '{self.simple_test.test_mode}', expected 'dedicated_schema'")
        
        print(f"🔧 Running SCHEMA test (DDL + ALTER + DML) for {duration_minutes} minutes...")
        print(f"📋 Operations: Create tables, add columns, enable CDC/CT, run DML, cleanup")
        
        # Schema-level operations - delegate to TestComprehensive methods
        schema_phases = [
            ('setup_validation', self.test_comprehensive._test_setup_validation),
            ('cdc_cleanup', self.test_comprehensive._test_cdc_cleanup),
            ('table_creation', self.test_comprehensive._test_table_creation, table_count_per_type),
            ('column_operations', self.test_comprehensive._test_column_operations, test_columns),
            ('bulk_cdc_ct_enable', self.test_comprehensive._test_bulk_cdc_ct_enable),
            ('dml_operations', self.test_comprehensive._test_dml_operations, duration_minutes),
            ('metadata_refresh', self.test_comprehensive._test_metadata_refresh),
        ]
        
        if cleanup_after_test:
            schema_phases.append(('cleanup', self.test_comprehensive._test_cleanup, table_count_per_type))
        
        return self.simple_test._run_test_phases(schema_phases, "Dedicated Schema Test")



