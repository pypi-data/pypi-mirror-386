"""
Comprehensive Test Scenario

Runs a complete test suite covering:
- Setup validation
- CDC/CT cleanup and management
- Bulk CDC/CT operations  
- Data type discovery
- Table creation
- Column operations (ALTER TABLE)
- DML operations (INSERT, UPDATE, DELETE)
- Metadata refresh
- LFC integration
- Optional cleanup

This is the most thorough test and should be run in a dedicated test environment.
"""

import datetime
import time
import traceback
from typing import Dict, Any, List

class TestComprehensive:
    """Comprehensive test scenario for all Simple* modules"""
    
    def __init__(self, simple_test):
        """Initialize with SimpleTest instance
        
        Args:
            simple_test: SimpleTest instance with setup modules
        """
        self.simple_test = simple_test
    
    def run(self, 
            table_count_per_type: int = 2,
            test_columns: List[str] = None,
            cleanup_after_test: bool = True,
            duration_minutes: int = 5) -> Dict[str, Any]:
        """Run comprehensive test suite across all Simple modules
        
        Args:
            table_count_per_type: Number of tables to create for each type (intpk, dtix)
            test_columns: List of test column names to add (default: ['field_test_field_1', 'field_test_field_2'])
            cleanup_after_test: Whether to cleanup tables after testing
            duration_minutes: How long to run DML operations
            
        Returns:
            dict: Comprehensive test results
        """
        if test_columns is None:
            test_columns = ['field_test_field_1', 'field_test_field_2']
        
        test_start_time = datetime.datetime.now()
        print(f"🚀 Starting Comprehensive Test at {test_start_time}")
        
        # Test phases
        test_phases = [
            ('setup_validation', self._test_setup_validation),
            ('cdc_cleanup', self._test_cdc_cleanup),
            ('bulk_cdc_ct_status', self._test_bulk_cdc_ct_status),
            ('data_type_discovery', self._test_data_type_discovery),
            ('table_creation', self._test_table_creation, table_count_per_type),
            ('bulk_cdc_ct_enable', self._test_bulk_cdc_ct_enable),
            ('column_operations', self._test_column_operations, test_columns),
            ('dml_operations', self._test_dml_operations, duration_minutes),
            ('metadata_refresh', self._test_metadata_refresh),
            ('lfc_integration', self._test_lfc_integration),
        ]
        
        if cleanup_after_test:
            test_phases.append(('cleanup', self._test_cleanup, table_count_per_type))
        
        # Execute test phases using SimpleTest's helper
        return self.simple_test._run_test_phases(test_phases, "Comprehensive Test")
    
    # ==================== TEST IMPLEMENTATION METHODS ====================
    
    def _test_setup_validation(self) -> Dict[str, Any]:
        """Validate that all modules are properly setup"""
        validations = {}
        
        # Check SimpleDML
        if self.simple_test.simple_dml is None:
            validations['SimpleDML'] = {'status': 'error', 'message': 'SimpleDML not initialized'}
        else:
            table_info = self.simple_test.simple_dml.get_table_info()
            validations['SimpleDML'] = {
                'status': 'success', 
                'message': f"SimpleDML ready with {table_info['table_count']} tables",
                'table_count': table_info['table_count']
            }
        
        # Check LfcSchEvo
        if self.simple_test.simple_lfc is None:
            validations['LfcSchEvo'] = {'status': 'error', 'message': 'LfcSchEvo not initialized'}
        else:
            lfc_status = self.simple_test.simple_lfc.get_ddl_support_status()
            validations['LfcSchEvo'] = {
                'status': 'success',
                'message': f"LfcSchEvo ready, {lfc_status.get('total_objects', 0)} DDL objects found",
                'ddl_objects': lfc_status.get('total_objects', 0)
            }
        
        # Check SimpleAlter
        if self.simple_test.simple_alter is None:
            validations['SimpleAlter'] = {'status': 'error', 'message': 'SimpleAlter not initialized'}
        else:
            supported_types = self.simple_test.simple_alter.get_supported_types()
            validations['SimpleAlter'] = {
                'status': 'success',
                'message': f"SimpleAlter ready with {len(supported_types)} supported data types",
                'supported_types_count': len(supported_types)
            }
        
        # Determine overall status based on individual validations
        has_errors = any(v.get('status') == 'error' for v in validations.values())
        overall_status = 'error' if has_errors else 'success'
        
        # Return with top-level status for proper test counting
        return {
            'status': overall_status,
            'message': f"Setup validation {'failed' if has_errors else 'completed'} - {len(validations)} modules checked",
            **validations  # Include individual validations as direct keys
        }
    
    def _test_cdc_cleanup(self) -> Dict[str, Any]:
        """Test CDC cleanup operations"""
        if not hasattr(self.simple_test.simple_ddl, 'cdc') or self.simple_test.simple_ddl.cdc is None:
            return {'status': 'skipped', 'message': 'CDC not enabled'}
        
        cleanup_result = self.simple_test.simple_ddl.cdc.cleanup_orphaned_cdc_instances()
        return {
            'status': 'success',
            'message': 'CDC cleanup completed',
            'cleanup_result': cleanup_result
        }
    
    def _test_bulk_cdc_ct_status(self) -> Dict[str, Any]:
        """Test bulk CDC/CT status check (dry run)"""
        if not hasattr(self.simple_test.simple_ddl, 'cdc') or self.simple_test.simple_ddl.cdc is None:
            return {'status': 'skipped', 'message': 'CDC not enabled'}
        
        # Check if this is SQL Server
        if self.simple_test.engine.dialect.name.lower() != 'mssql':
            return {'status': 'skipped', 'message': 'Bulk CDC/CT only supported for SQL Server'}
        
        try:
            schema = self.simple_test._get_config_value('source_schema') or 'lfcddemo'
            
            print(f"🔍 Checking bulk CDC/CT status for schema '{schema}'...")
            dry_run_result = self.simple_test.simple_ddl.cdc.bulk_enable_cdc_ct_for_schema(
                schema_name=schema,
                mode='BOTH',
                dry_run=True
            )
            
            if dry_run_result.get('status') == 'dry_run':
                summary = dry_run_result.get('summary', {})
                print(f"📊 Bulk CDC/CT Status:")
                print(f"   Total tables: {summary.get('total_tables', 0)}")
                print(f"   Tables with PK: {summary.get('tables_with_pk', 0)}")
                print(f"   Tables without PK: {summary.get('tables_without_pk', 0)}")
                print(f"   CDC enabled: {summary.get('cdc_enabled', 0)}")
                print(f"   CT enabled: {summary.get('ct_enabled', 0)}")
            
            return {
                'status': 'success',
                'message': 'Bulk CDC/CT status check completed',
                'dry_run_result': dry_run_result
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Bulk CDC/CT status check failed: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def _test_bulk_cdc_ct_enable(self) -> Dict[str, Any]:
        """Test bulk CDC/CT enable operation"""
        if not hasattr(self.simple_test.simple_ddl, 'cdc') or self.simple_test.simple_ddl.cdc is None:
            return {'status': 'skipped', 'message': 'CDC not enabled'}
        
        # Check if this is SQL Server
        if self.simple_test.engine.dialect.name.lower() != 'mssql':
            return {'status': 'skipped', 'message': 'Bulk CDC/CT only supported for SQL Server'}
        
        # Only run if we have created tables
        if not self.simple_test.created_tables:
            return {'status': 'skipped', 'message': 'No tables created yet'}
        
        try:
            schema = self.simple_test._get_config_value('source_schema') or 'lfcddemo'
            # Process ALL tables in schema, not just created ones
            # This ensures existing tables also get CT/CDC enabled
            table_names = list(self.simple_test.created_tables.keys()) if self.simple_test.created_tables else []
            
            print(f"🚀 Bulk enabling CDC/CT for ALL tables in schema '{schema}'...")
            bulk_result = self.simple_test.simple_ddl.cdc.bulk_enable_cdc_ct_for_schema(
                schema_name=schema,
                table_filter=None,  # Process all tables in schema, not just created ones
                mode='BOTH',
                dry_run=False
            )
            
            if bulk_result.get('status') == 'completed':
                print(f"✅ Bulk CDC/CT operation completed for schema '{schema}':")
                print(f"   CDC enabled: {bulk_result.get('cdc_enabled_count', 0)} (already enabled: {bulk_result.get('cdc_enabled_already_count', 0)})")
                print(f"   CDC disabled: {bulk_result.get('cdc_disabled_count', 0)} (already disabled: {bulk_result.get('cdc_disabled_already_count', 0)})")
                print(f"   CT enabled: {bulk_result.get('ct_enabled_count', 0)} (already enabled: {bulk_result.get('ct_enabled_already_count', 0)})")
                print(f"   CT disabled: {bulk_result.get('ct_disabled_count', 0)} (already disabled: {bulk_result.get('ct_disabled_already_count', 0)})")
            
            return {
                'status': 'success',
                'message': 'Bulk CDC/CT enable completed',
                'bulk_result': bulk_result,
                'tables_processed': table_names
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Bulk CDC/CT enable failed: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def _test_data_type_discovery(self) -> Dict[str, Any]:
        """Test data type discovery functionality"""
        # Test supported types
        supported_types = self.simple_test.simple_alter.get_supported_types()
        
        # Test data type suggestions
        sample_data = [
            ('test_string', 'varchar'),
            (123, 'int'),
            (123.45, 'decimal'),
            (True, 'bit')
        ]
        
        suggestions = {}
        for value, expected_type in sample_data:
            suggestion = self.simple_test.simple_alter.suggest_data_type([value])
            suggestions[str(value)] = suggestion
        
        return {
            'status': 'success',
            'message': f'Data type discovery completed with {len(supported_types)} supported types',
            'supported_types': supported_types,
            'sample_suggestions': suggestions
        }
    
    def _test_table_creation(self, table_count_per_type: int = 2) -> Dict[str, Any]:
        """Test table creation with CDC and LFC integration"""
        created_tables = self.simple_test.create_test_tables(
            base_names=['intpk', 'dtix'],
            count_per_type=table_count_per_type,
            force_recreate=True,
            refresh_metadata=True
        )
        
        self.simple_test.created_tables.update(created_tables)
        
        # Collect errors and warnings from created tables
        errors = []
        warnings = []
        
        for table_name, table_info in created_tables.items():
            if table_info.get('has_error'):
                errors.append({
                    'table': table_name,
                    'error': table_info.get('error_message') or table_info.get('lfc_error'),
                    'cdc_result': table_info.get('cdc_result'),
                    'lfc_result': table_info.get('lfc_result')
                })
            if table_info.get('has_warning'):
                warnings.append({
                    'table': table_name,
                    'warning': table_info.get('warning_message') or table_info.get('lfc_warning'),
                    'cdc_result': table_info.get('cdc_result'),
                    'lfc_result': table_info.get('lfc_result')
                })
        
        result = {
            'status': 'success' if len(errors) == 0 else 'warning',
            'message': f'Created {len(created_tables)} tables successfully',
            'created_tables': list(created_tables.keys()),
            'table_details': created_tables,
            'errors': errors,
            'warnings': warnings,
            'error_count': len(errors),
            'warning_count': len(warnings)
        }
        
        # Update message if there are errors or warnings
        if len(errors) > 0:
            result['message'] = f'Created {len(created_tables)} tables with {len(errors)} error(s)'
        elif len(warnings) > 0:
            result['message'] = f'Created {len(created_tables)} tables with {len(warnings)} warning(s)'
        
        return result
    
    def _test_column_operations(self, test_columns: List[str]) -> Dict[str, Any]:
        """Test column addition and removal operations"""
        if not self.simple_test.created_tables:
            return {'status': 'error', 'message': 'No tables available for column operations'}
        
        # Get first created table for testing
        test_table_name = list(self.simple_test.created_tables.keys())[0]
        
        column_results = {}
        
        # Add columns
        for col_name in test_columns:
            try:
                add_result = self.simple_test.simple_alter.add_field_column(
                    test_table_name, 
                    col_name, 
                    'string', 
                    length=50
                )
                column_results[f'add_{col_name}'] = add_result
            except Exception as e:
                column_results[f'add_{col_name}'] = {'status': 'error', 'message': str(e)}
        
        # List field columns
        try:
            field_columns = self.simple_test.simple_alter.list_field_columns(test_table_name)
            column_results['list_columns'] = {
                'status': 'success',
                'columns': field_columns
            }
        except Exception as e:
            column_results['list_columns'] = {'status': 'error', 'message': str(e)}
        
        # Drop one column (test removal) - only if field columns exist
        try:
            field_columns = self.simple_test.simple_alter.list_field_columns(test_table_name)
            if field_columns.get('count', 0) > 0:
                # Get the first field column to drop
                first_field_column = field_columns['field_columns'][0]['column_name']
                # Extract the field name (remove 'field_' prefix)
                field_name = first_field_column.replace('field_', '', 1)
                drop_result = self.simple_test.simple_alter.drop_field_column(test_table_name, field_name)
                column_results[f'drop_{field_name}'] = drop_result
            else:
                column_results['drop_field_column'] = {
                    'status': 'skipped', 
                    'message': 'No field columns found to drop'
                }
        except Exception as e:
            column_results['drop_field_column'] = {'status': 'error', 'message': str(e)}
        
        return {
            'status': 'success',
            'message': f'Column operations completed on table {test_table_name}',
            'test_table': test_table_name,
            'operations': column_results
        }
    
    def _test_dml_operations(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Test DML operations across created tables for specified duration"""
        if not self.simple_test.created_tables:
            return {'status': 'error', 'message': 'No tables available for DML operations'}
        
        print(f"🔄 Running DML operations for {duration_minutes} minutes...")
        
        dml_results = {}
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Run DML operations for the specified duration
        operations_count = 0
        while time.time() < end_time:
            # Test each created table
            for table_name in self.simple_test.created_tables.keys():
                if time.time() >= end_time:
                    break
                    
                try:
                    # Execute DELETE, UPDATE, INSERT operations
                    operation_result = self.simple_test.simple_dml.execute_delete_update_insert(
                        max_rows=10, 
                        time_window_seconds=60, 
                        table_name=table_name
                    )
                    operations_count += 1
                    
                    # Update results for this table
                    dml_results[table_name] = {
                        'status': 'success',
                        'operations': operation_result
                    }
                    
                    # Verify row counts
                    recent_data = self.simple_test.simple_dml.get_recent_data(
                        seconds_back=60, 
                        table_name=table_name
                    )
                    
                    dml_results[table_name]['verification'] = {
                        'recent_rows': len(recent_data),
                        'expected_max': operation_result['max_rows_target']
                    }
                    
                    # Brief pause between operations
                    time.sleep(1)
                    
                except Exception as e:
                    dml_results[table_name] = {
                    'status': 'error',
                    'message': str(e)
                }
        
        return {
            'status': 'success',
            'message': f'DML operations completed on {len(dml_results)} tables',
            'table_results': dml_results
        }
    
    def _test_metadata_refresh(self) -> Dict[str, Any]:
        """Test metadata refresh functionality"""
        initial_count = self.simple_test.simple_dml.get_table_info()['table_count']
        
        # Force metadata refresh
        new_count = self.simple_test.simple_dml.refresh_metadata()
        
        return {
            'status': 'success',
            'message': 'Metadata refresh completed',
            'initial_count': initial_count,
            'refreshed_count': new_count,
            'tables_changed': new_count != initial_count
        }
    
    def _test_lfc_integration(self) -> Dict[str, Any]:
        """Test LFC DDL support objects integration"""
        if not hasattr(self.simple_test.simple_lfc, 'get_ddl_support_status'):
            return {'status': 'skipped', 'message': 'LFC not available'}
        
        # Get current LFC status
        lfc_status = self.simple_test.simple_lfc.get_ddl_support_status()
        
        return {
            'status': 'success',
            'message': 'LFC integration test completed',
            'lfc_status': lfc_status
        }
    
    def _test_cleanup(self, table_count_per_type: int = 2) -> Dict[str, Any]:
        """Test cleanup operations"""
        cleanup_results = {}
        
        # Drop field columns first
        if self.simple_test.created_tables:
            test_table_name = list(self.simple_test.created_tables.keys())[0]
            try:
                drop_all_result = self.simple_test.simple_alter.drop_all_field_columns(test_table_name)
                cleanup_results['drop_field_columns'] = drop_all_result
            except Exception as e:
                cleanup_results['drop_field_columns'] = {'status': 'error', 'message': str(e)}
        
        # Drop test tables
        try:
            dropped_tables = self.simple_test.drop_test_tables(
                base_names=['intpk', 'dtix'],
                count_per_type=table_count_per_type,
                refresh_metadata=True
            )
            cleanup_results['drop_tables'] = {
                'status': 'success',
                'dropped_tables': list(dropped_tables.keys()),
                'details': dropped_tables
            }
        except Exception as e:
            cleanup_results['drop_tables'] = {'status': 'error', 'message': str(e)}
        
        return {
            'status': 'success',
            'message': 'Cleanup operations completed',
            'operations': cleanup_results
        }
