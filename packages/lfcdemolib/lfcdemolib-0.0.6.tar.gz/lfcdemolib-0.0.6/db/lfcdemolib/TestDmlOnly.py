"""
DML-Only Test Scenario (Safe for Shared Environments)

Runs only DML operations without any DDL changes:
- Setup validation
- Metadata refresh
- DML operations (INSERT, UPDATE, DELETE) on existing tables

This is the safest test mode and can be run in shared/production environments
as it doesn't create, modify, or drop any tables.

Use Case: Testing DML performance and data operations in environments where
schema changes are not allowed.
"""

from typing import Dict, Any
from .TestComprehensive import TestComprehensive

class TestDmlOnly:
    """DML-only test scenario for shared environments"""
    
    def __init__(self, simple_test):
        """Initialize with SimpleTest instance
        
        Args:
            simple_test: SimpleTest instance with setup modules
        """
        self.simple_test = simple_test
        self.test_comprehensive = TestComprehensive(simple_test)
    
    def run(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Run safe DML-only operations for shared environments
        
        This mode only performs DML operations on existing tables and is safe
        for shared/production environments.
        
        Args:
            duration_minutes: How long to run DML operations
            
        Returns:
            dict: Test results
        """
        if self.simple_test.test_mode not in ['shared_environment', 'dedicated_schema', 'new_database']:
            print(f"⚠️ Warning: Test mode '{self.simple_test.test_mode}' may not be safe for this operation")
        
        print(f"🛡️ Running SAFE test (DML only) for {duration_minutes} minutes...")
        print("📋 Operations: DML on existing tables, metadata refresh, validation")
        
        # Only run safe operations - delegate to TestComprehensive methods
        safe_phases = [
            ('setup_validation', self.test_comprehensive._test_setup_validation),
            ('metadata_refresh', self.test_comprehensive._test_metadata_refresh),
            ('dml_operations', self.test_comprehensive._test_dml_operations, duration_minutes),
        ]
        
        return self.simple_test._run_test_phases(safe_phases, "Safe DML Test")



