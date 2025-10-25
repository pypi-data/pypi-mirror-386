"""
SimpleTest - Comprehensive Testing Module for Simple* Components

This module provides comprehensive testing functionality for all Simple* modules:
- SimpleDML: Data manipulation language operations
- SimpleDDL: Data definition language operations  
- LfcCDC: Change data capture management
- LfcSchEvo: Lakeflow Connect Schema Evolution DDL support objects
- SimpleAlter: Column addition and removal operations

Key Features:
- Integrated test suite for all Simple modules
- Automated table creation, DML operations, and cleanup
- CDC/CT and LFC integration testing
- Column alteration testing
- Comprehensive error handling and reporting
- Configurable test parameters
"""

import datetime
import time
import traceback
import sqlalchemy as sa
import urllib.parse
from typing import Dict, List, Any, Optional, Literal
try:
    from databricks.sdk import WorkspaceClient
except ImportError:
    # Databricks SDK may not be available in non-Databricks environments
    WorkspaceClient = None
from .SimpleDML import SimpleDML
from .SimpleDDL import SimpleDDL
from .LfcSchEvo import LfcSchEvo
from .LfcConn import LfcConn
from .LfcSecrets import LfcSecrets
from .SimpleAlter import SimpleAlter
from .SimpleMonitor import SimpleMonitor

# Import test scenarios
from .TestComprehensive import TestComprehensive
from .TestDmlOnly import TestDmlOnly
from .TestDedicatedSchema import TestDedicatedSchema
from .TestFullDatabase import TestFullDatabase
from .TestAsyncParallel import TestAsyncParallel

# Import Phase 2 extracted classes
from .DatabaseSetupValidator import DatabaseSetupValidator
from .ConnectionSecretManager import ConnectionSecretManager
from .TestScenarioRunner import TestScenarioRunner
from .PerformanceReporter import PerformanceReporter
from .ImpactAssessment import ImpactAssessment


class SimpleTest:
    """Comprehensive test suite for all Simple* modules
    
    Provides integrated testing functionality across SimpleDML, SimpleDDL, LfcCDC,
    LfcSchEvo, and SimpleAlter modules with automated setup, execution, and cleanup.
    """
    
    def __init__(self, workspace_client=None, config: Dict[str, Any] = None, auto_setup: bool = True, auto_cleanup: bool = True):
        """Initialize SimpleTest with WorkspaceClient and configuration
        
        Args:
            workspace_client: Databricks WorkspaceClient instance (optional)
            config: Configuration dictionary with connection and schema settings
            auto_setup: Whether to automatically setup modules (default: True)
            auto_cleanup: Whether to automatically cleanup databases on exit (default: True)
        """
        self.workspace_client = workspace_client or self._initialize_workspace_client()
        self.config = config or {}
        self.auto_cleanup = auto_cleanup
        self.test_results = {}
        self.created_tables = {}
        self.test_start_time = None
        self.retry_counts = {}  # Track retry counts per operation
        
        # Initialize LfcEnv with WorkspaceClient
        from .LfcEnv import LfcEnv
        self.lfc_env = LfcEnv(self.workspace_client)
        
        # Initialize Simple modules
        self.simple_dml = None
        self.simple_ddl = None
        self.simple_lfc = None
        self.simple_alter = None
        self.simple_monitor = None
        self.engine = None  # Will be created in setup_modules
        
        # Initialize database creation tracking
        self._created_database_info = None
        self._db_creator = None
        self._secrets_json = None
        
        # Shared state dictionary to coordinate between modules (database-agnostic)
        self.shared_state = {
            'pk_replication_checked': False,        # Change Tracking (SQL Server), equivalent for other DBs
            'non_pk_replication_checked': False,    # Change Data Capture (SQL Server), equivalent for other DBs
            'pk_replication_enabled': False,        # Whether PK-based replication is enabled at DB level
            'non_pk_replication_enabled': False,    # Whether non-PK replication is enabled at DB level
            'non_pk_replication_supported': None,   # None = unknown, True/False = determined
            'non_pk_replication_failure_reason': None
        }
        
        print(f"🧪 SimpleTest initialized with config: {config}")
        
        # Auto-detect test mode based on config contents
        self.test_mode = self._detect_test_mode()
        
        # Show config resolution for key parameters
        schema = self._get_config_value('source_schema')
        cloud = self._get_config_value('cloud')
        source_type = self._get_config_value('type')
        print(f"🔧 Config resolved: schema='{schema}', cloud='{cloud}', type='{source_type}'")
        print(f"🎯 Test mode detected: {self.test_mode}")
        
        # Auto-setup modules by default for convenience
        if auto_setup:
            print("🔧 Auto-setting up modules...")
            self.setup_modules()
    
    def _initialize_workspace_client(self) -> Optional[WorkspaceClient]:
        """Initialize WorkspaceClient for LfcConn and LfcSecrets
        
        Returns:
            WorkspaceClient: Initialized client or None if not available
        """
        if WorkspaceClient is None:
            return None
            
        try:
            # Try to initialize WorkspaceClient
            # It will use environment variables or default authentication
            return WorkspaceClient()
        except Exception as e:
            print(f"⚠️ Could not initialize WorkspaceClient: {e}")
            return None
    
    def _get_config_value(self, key: str, default=None):
        """Get config value with priority: passed config > dbxrest config > default
        
        Database-specific keys (type, cloud) are looked up under config['database']
        Other keys are looked up at the top level
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # Database-specific keys should be under 'database' section
        database_keys = ['type', 'cloud']
        
        # Priority 1: Use passed config parameter
        if key in database_keys:
            # Look for database-specific keys under 'database' section
            if 'database' in self.config and key in self.config['database']:
                return self.config['database'][key]
            # Fallback to top-level for backward compatibility
            elif key in self.config:
                return self.config[key]
        else:
            # Non-database keys at top level
            if key in self.config:
                return self.config[key]
        
        # Priority 2: Use secrets_json for schema-related keys
        if key == 'source_schema' and self._secrets_json:
            return self._secrets_json.get('schema')
        
        # Priority 4: Default value
        return default
    
    def _get_schema_with_warning(self):
        """Get schema from config with warning if using default
        
        Returns:
            str: Schema name (defaults to 'lfcddemo' with warning if not configured)
        """
        schema = self._get_config_value('source_schema')
        
        if schema is None:
            schema = 'lfcddemo'
            print(f"⚠️  WARNING: No schema configured in SimpleTest!")
            print(f"   Using default schema: '{schema}'")
            print(f"   Consider adding 'source_schema' to config:")
            print(f"   config = {{'source_schema': 'lfcddemo', ...}}")
        
        return schema
    
    def _detect_test_mode(self):
        """Detect test mode based on config contents
        
        Returns:
            str: One of 'shared_environment', 'dedicated_schema', 'new_database'
        """
        connection_name = self.config.get('connection_name')
        schema = self.config.get('schema') or self.config.get('source_schema')
        has_database_config = 'database' in self.config
        
        if connection_name is None and has_database_config:
            return 'new_database'  # Mode 3: Create new database
        elif connection_name is not None and schema is not None:
            return 'dedicated_schema'  # Mode 2: Existing connection + dedicated schema
        elif connection_name is not None:
            return 'shared_environment'  # Mode 1: Existing connection, shared environment
        else:
            # Fallback: if workspace_client is provided, assume shared environment
            if self.workspace_client is not None:
                return 'shared_environment'
            else:
                raise ValueError("Config must contain either 'connection_name' or 'database' section")
    
    @classmethod
    def load_database_credentials(cls, connection_name: str) -> Dict[str, Any]:
        """Load database credentials from saved file
        
        Args:
            connection_name: Name of the connection to load (or partial filename match)
            
        Returns:
            dict: Database credentials or None if not found
        """
        import json
        import os
        
        creds_dir = os.path.expanduser("~/.lfcddemo")
        
        # Try to find credential file by connection name or partial match
        creds_file = None
        
        # First try exact match with old format
        old_format_file = os.path.join(creds_dir, f"{connection_name}_credentials.json")
        if os.path.exists(old_format_file):
            creds_file = old_format_file
        else:
            # Search for files containing the connection name
            if os.path.exists(creds_dir):
                for filename in os.listdir(creds_dir):
                    if filename.endswith('_credentials.json') and connection_name in filename:
                        creds_file = os.path.join(creds_dir, filename)
                        break
        
        if not creds_file:
            print(f"⚠️ No saved credentials found for connection: {connection_name}")
            return None
        
        try:
            with open(creds_file, 'r') as f:
                creds_data = json.load(f)
            
            print(f"📂 Loaded credentials for: {connection_name}")
            print(f"   Server: {creds_data['host']}")
            print(f"   Database: {creds_data['database']}")
            print(f"   File: {os.path.basename(creds_file)}")
            print(f"   Saved: {creds_data['saved_at']}")
            
            return creds_data
        except Exception as e:
            print(f"❌ Failed to load credentials for {connection_name}: {e}")
            return None
    
    @classmethod
    def list_saved_credentials(cls) -> List[str]:
        """List all saved database credentials
        
        Returns:
            list: List of connection names with saved credentials
        """
        import os
        import json
        
        creds_dir = os.path.expanduser("~/.lfcddemo")
        if not os.path.exists(creds_dir):
            return []
        
        connection_names = []
        for filename in os.listdir(creds_dir):
            if filename.endswith('_credentials.json'):
                try:
                    # Try to read the file to get the actual connection name
                    filepath = os.path.join(creds_dir, filename)
                    with open(filepath, 'r') as f:
                        creds_data = json.load(f)
                    connection_name = creds_data.get('connection_name', filename.replace('_credentials.json', ''))
                    connection_names.append(connection_name)
                except:
                    # Fallback to filename parsing for old format
                    connection_name = filename.replace('_credentials.json', '')
                    connection_names.append(connection_name)
        
        return connection_names
    
    def _create_engine(self):
        """Create SQLAlchemy engine using SimpleConn for centralized connection management
        
        Returns:
            sqlalchemy.Engine: Configured database engine
        """
        # Use SimpleConn for all engine creation - handles finding credentials,
        # creating engine, testing connection, and auto-recreating if needed
        from .SimpleConn import SimpleConn
        
        conn = SimpleConn(workspace_client=self.workspace_client)
        engine, secrets_json = conn.create_engine_from_config(
            config=self.config,
            auto_recreate=True
        )
        
        # Store secrets_json for module initialization
        self._secrets_json = secrets_json
        
        return engine
    
    def setup_modules(self, 
                     metadata_refresh_interval: int = 60,
                     enable_cdc: bool = True, 
                     enable_lfc: bool = True,
                     replication_filter: Literal['both', 'pk_only', 'no_pk_only'] = 'both') -> Dict[str, Any]:
        """Setup all Simple modules with specified configuration
        
        Args:
            metadata_refresh_interval: Seconds between metadata refreshes
            enable_cdc: Whether to enable CDC/CT for tables
            enable_lfc: Whether to setup LFC DDL support objects
            replication_filter: Control which tables to enable replication for
            
        Returns:
            dict: Setup results for each module
        """
        setup_results = {}
        
        try:
            # Create shared engine first
            print(f"🔧 Creating database engine...")
            self.engine = self._create_engine()
            setup_results['Engine'] = {'status': 'success', 'message': 'Database engine created successfully'}
            
            # Run database permission test for SQL Server (validates master access for Lakeflow Connect)
            print(f"🔧 Validating database permissions...")
            perm_test_result = self.test_database_permissions()
            setup_results['Database_Permissions'] = perm_test_result
            
            # Warn if master access is not available for SQL Server
            if (perm_test_result.get('status') not in ['success', 'skipped'] and 
                self._get_config_value('type') == 'sqlserver'):
                print(f"⚠️  WARNING: Database permission test reported issues!")
                if not perm_test_result.get('correct_setup'):
                    print(f"⚠️  Lakeflow Connect may not work properly without master database access")
            
            # Enable database-level CDC/CT immediately after connection (if CDC is enabled)
            if enable_cdc:
                print(f"🔧 Setting up database-level CDC/CT...")
                db_cdc_ct_result = self._setup_database_level_cdc_ct()
                setup_results['Database_CDC_CT'] = db_cdc_ct_result
            
            # Setup SimpleDML with pre-created engine
            print(f"🔧 Setting up SimpleDML...")
            
            # Use secrets_json from created database
            secrets_json = self._secrets_json
            
            if secrets_json:
                self.simple_dml = SimpleDML.from_secrets(
                    secrets_json, 
                    scheduler=None,  # No scheduler needed
                    config=self.config,  # Pass the full config instead of just schema
                    metadata_refresh_interval=metadata_refresh_interval,
                    engine=self.engine  # Pass the pre-created engine
                )
            else:
                # Fallback: create SimpleDML directly with engine
                self.simple_dml = SimpleDML(
                    self.engine,
                    config=self.config,  # Pass the full config instead of just schema
                    scheduler=None,  # No scheduler needed
                    metadata_refresh_interval=metadata_refresh_interval
                )
            setup_results['SimpleDML'] = {'status': 'success', 'message': 'SimpleDML initialized with shared engine'}
            
            # Setup SimpleDDL with the same engine
            print(f"🔧 Setting up SimpleDDL...")
            self.simple_ddl = SimpleDDL(
                self.engine,  # Use the shared engine directly
                self._get_schema_with_warning(),  # Get schema with warning if not configured
                enable_cdc=enable_cdc,
                enable_lfc=enable_lfc,
                replication_filter=replication_filter,
                secrets_json=secrets_json,  # Use the same secrets_json as SimpleDML
                test_instance=self,  # Pass self for retry tracking
                shared_state=self.shared_state  # Pass shared state for coordination
            )
            setup_results['SimpleDDL'] = {'status': 'success', 'message': 'SimpleDDL initialized with shared engine and DBA support'}
            
            # Setup LfcSchEvo
            print(f"🔧 Setting up LfcSchEvo...")
            self.simple_lfc = LfcSchEvo(
                self.engine,  # Use the shared engine 
                self._get_schema_with_warning(),  # Get schema with warning if not configured
                replication_filter=replication_filter
            )
            setup_results['LfcSchEvo'] = {'status': 'success', 'message': 'LfcSchEvo initialized successfully'}
            
            # Setup SimpleAlter
            print(f"🔧 Setting up SimpleAlter...")
            self.simple_alter = SimpleAlter(
                self.engine,  # Use the shared engine
                self._get_config_value('source_schema')
            )
            setup_results['SimpleAlter'] = {'status': 'success', 'message': 'SimpleAlter initialized with shared engine'}
            
            # Initialize SimpleMonitor for performance monitoring
            print(f"🔧 Setting up SimpleMonitor...")
            self.simple_monitor = SimpleMonitor(
                self.engine,  # Use the shared engine
                self._get_config_value('source_schema')
            )
            setup_results['SimpleMonitor'] = {'status': 'success', 'message': 'SimpleMonitor initialized with shared engine'}
            
            print(f"✅ All Simple modules setup completed")
            
        except Exception as e:
            error_msg = f"Failed to setup modules: {str(e)}"
            print(f"❌ {error_msg}")
            setup_results['error'] = {'status': 'error', 'message': error_msg, 'traceback': traceback.format_exc()}
        
        return setup_results
    
    def _setup_database_level_cdc_ct(self) -> Dict[str, Any]:
        """Setup database-level CDC and Change Tracking
        
        Returns:
            dict: Setup results for database-level CDC/CT
        """
        try:
            # Get database type from engine
            dialect = self.engine.dialect.name.lower()
            
            if dialect != 'mssql':
                return {
                    'status': 'skipped',
                    'message': f'Database-level CDC/CT setup not needed for {dialect}'
                }
            
            # Use secrets_json from created database
            secrets_json = self._secrets_json
            
            # Create a temporary LfcCDC instance for database-level operations
            from .LfcCDC import LfcCDC
            
            # Create DBA engine if secrets are provided
            dba_engine = None
            if secrets_json:
                try:
                    dba_engine = LfcCDC.create_dba_engine(secrets_json)
                    print(f"🔗 Created DBA engine for database-level CDC/CT setup")
                except Exception as e:
                    print(f"⚠️ Could not create DBA engine: {e}. Using regular engine for CDC/CT operations.")
            
            temp_cdc = LfcCDC(
                self.engine, 
                self._get_schema_with_warning(),  # Get schema with warning if not configured
                'both',  # Use 'both' for database-level setup
                dba_engine, 
                secrets_json
            )
            
            # Test CDC support and enable database-level CDC/CT
            cdc_supported = temp_cdc._test_cdc_support()
            
            # Enable Change Tracking at database level (always try this as it's more commonly supported)
            ct_result = self._enable_database_level_ct(temp_cdc)
            
            return {
                'status': 'success',
                'message': 'Database-level CDC/CT setup completed',
                'cdc_supported': cdc_supported,
                'cdc_failure_reason': temp_cdc.get_cdc_failure_reason(),
                'ct_result': ct_result
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to setup database-level CDC/CT: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def _enable_database_level_ct(self, cdc_instance) -> Dict[str, Any]:
        """Enable Change Tracking at database level
        
        Args:
            cdc_instance: LfcCDC instance to use for CT operations
            
        Returns:
            dict: Result of CT database-level enablement
        """
        try:
            with cdc_instance.dba_engine.connect() as dba_conn:
                # Get the target database name
                target_db_query = sa.text("SELECT DB_NAME()")
                with self.engine.connect() as conn:
                    target_db = conn.execute(target_db_query).scalar()
                
                # Check if Change Tracking is already enabled at database level (Azure SQL Database compatible)
                ct_check_query = sa.text(f"""
                    SELECT COUNT(*) 
                    FROM sys.change_tracking_databases 
                    WHERE database_id = DB_ID('{target_db}')
                """)
                
                ct_enabled = dba_conn.execute(ct_check_query).scalar() > 0
                
                if ct_enabled:
                    print(f"✅ Change Tracking already enabled at database level for {target_db}")
                    return {
                        'status': 'already_enabled',
                        'message': f'Change Tracking already enabled for database {target_db}'
                    }
                else:
                    # Enable Change Tracking at database level
                    print(f"🔄 Enabling Change Tracking at database level for {target_db}...")
                    enable_ct_query = sa.text(f"""
                        ALTER DATABASE [{target_db}] 
                        SET CHANGE_TRACKING = ON 
                        (CHANGE_RETENTION = 2 DAYS, AUTO_CLEANUP = ON)
                    """)
                    
                    dba_conn.execute(enable_ct_query)
                    dba_conn.commit()
                    print(f"✅ Change Tracking enabled at database level for {target_db}")
                    
                    return {
                        'status': 'enabled',
                        'message': f'Change Tracking enabled for database {target_db}'
                    }
                    
        except Exception as e:
            error_msg = str(e)
            if "change tracking is already enabled" in error_msg.lower():
                print(f"✅ Change Tracking already enabled at database level")
                return {
                    'status': 'already_enabled',
                    'message': 'Change Tracking already enabled at database level'
                }
            else:
                print(f"⚠️ Failed to enable Change Tracking at database level: {e}")
                return {
                    'status': 'error',
                    'message': f'Failed to enable database-level Change Tracking: {error_msg}'
                }
    
    def run_comprehensive_test(self, 
                             table_count_per_type: int = 2,
                             test_columns: List[str] = None,
                             cleanup_after_test: bool = True,
                             duration_minutes: int = 5) -> Dict[str, Any]:
        """Run comprehensive test suite across all Simple modules
        
        Delegates to TestComprehensive class for execution.
        
        Args:
            table_count_per_type: Number of tables to create for each type (intpk, dtix)
            test_columns: List of test column names to add (default: ['field_test1', 'field_test2'])
            cleanup_after_test: Whether to cleanup tables after testing
            duration_minutes: How long to run DML operations
            
        Returns:
            dict: Comprehensive test results
        """
        test_scenario = TestComprehensive(self)
        return test_scenario.run(
            table_count_per_type=table_count_per_type,
            test_columns=test_columns,
            cleanup_after_test=cleanup_after_test,
            duration_minutes=duration_minutes
        )
    
    def _generate_test_summary(self, test_duration: datetime.timedelta) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        # Exclude 'summary' from test count to avoid circular reference
        test_results_without_summary = {k: v for k, v in self.test_results.items() if k != 'summary'}
        
        total_tests = len(test_results_without_summary)
        passed_tests = sum(1 for result in test_results_without_summary.values() 
                          if isinstance(result, dict) and result.get('status') == 'success')
        failed_tests = total_tests - passed_tests
        
        # Calculate total retry count
        total_retries = sum(self.retry_counts.values())
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'duration': str(test_duration),
            'start_time': self.test_start_time.isoformat() if self.test_start_time else None,
            'modules_tested': ['SimpleDML', 'SimpleDDL', 'LfcCDC', 'LfcSchEvo', 'SimpleAlter'],
            'created_tables_count': len(self.created_tables),
            'total_retries': total_retries,
            'retry_breakdown': self.retry_counts.copy()
        }
    
    def get_test_report(self) -> str:
        """Generate a formatted test report"""
        if not self.test_results:
            return "No test results available. Run run_comprehensive_test() first."
        
        report_lines = [
            "=" * 60,
            "SIMPLE MODULES COMPREHENSIVE TEST REPORT",
            "=" * 60,
        ]
        
        # Summary section
        if 'summary' in self.test_results:
            summary = self.test_results['summary']
            report_lines.extend([
                f"Test Duration: {summary['duration']}",
                f"Tests Passed: {summary['passed']}/{summary['total']} ({summary['success_rate']:.1f}%)",
                f"Modules Tested: {', '.join(summary['modules_tested'])}",
                f"Tables Created: {summary['created_tables_count']}",
                ""
            ])
        
        # Detailed results
        report_lines.append("DETAILED RESULTS:")
        report_lines.append("-" * 40)
        
        for phase_name, result in self.test_results.items():
            if phase_name == 'summary':
                continue
                
            status = result.get('status', 'unknown')
            message = result.get('message', 'No message')
            
            status_icon = "✅" if status == 'success' else "❌" if status == 'error' else "⚠️"
            report_lines.append(f"{status_icon} {phase_name.upper()}: {message}")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def create_test_tables(self, base_names=None, count_per_type=1, force_recreate=False, refresh_metadata=True):
        """Create intpk and dtix test tables with auto-increment IDs and proper indexing
        
        Args:
            base_names: List of base table names (default: ['intpk', 'dtix'])
            count_per_type: Number of tables to create for each base name (default: 1)
            force_recreate: If True, drop existing tables before creating new ones
            refresh_metadata: If True, refresh metadata after creating tables (default: True)
            
        Returns:
            dict: Created table names and their structures
        """
        if not self.simple_ddl:
            raise RuntimeError("SimpleDDL not initialized. Either call setup_modules() first, or create SimpleTest with auto_setup=True (default).")
        
        # Delegate to SimpleDDL for table creation
        created_tables = self.simple_ddl.create_test_tables(base_names, count_per_type, force_recreate)
        
        # Refresh metadata to include new tables (if requested)
        if refresh_metadata and self.simple_dml:
            self.simple_dml._refresh_metadata()
            print(f"🔄 Metadata refreshed after creating {len(created_tables)} tables")
        
        return created_tables
    
    def drop_test_tables(self, base_names=None, count_per_type=1, refresh_metadata=True):
        """Drop test tables starting from the highest numbered suffix (drop from end)
        
        Args:
            base_names: List of base table names (default: ['intpk', 'dtix'])
            count_per_type: Number of tables to drop for each base name (default: 1)
            refresh_metadata: If True, refresh metadata after dropping tables (default: True)
            
        Returns:
            dict: Dropped table names and their details
        """
        if not self.simple_ddl:
            raise RuntimeError("SimpleDDL not initialized. Either call setup_modules() first, or create SimpleTest with auto_setup=True (default).")
        
        # Delegate to SimpleDDL for table dropping
        dropped_tables = self.simple_ddl.drop_test_tables(base_names, count_per_type)
        
        # Refresh metadata to reflect dropped tables (if requested)
        if refresh_metadata and self.simple_dml:
            self.simple_dml._refresh_metadata()
            print(f"🔄 Metadata refreshed after dropping {len(dropped_tables)} tables")
        
        return dropped_tables
    
    def cleanup_created_database(self, force: bool = False):
        """Clean up any database created during initialization
        
        Args:
            force: Force cleanup even if auto_cleanup is disabled
            
        This method should be called when done with testing to clean up
        Azure resources that were created automatically.
        """
        if not self.auto_cleanup and not force:
            print("⚠️ Auto-cleanup disabled - database will persist")
            print("   Use cleanup_created_database(force=True) to force cleanup")
            return
        
        if self._created_database_info:
            # Check if this is a reused database
            if self._created_database_info.get('reused'):
                print("ℹ️ Database was reused from existing credentials - no cleanup needed")
                self._created_database_info = None
                return
            
            # This is a newly created database
            if self._db_creator:
                db_name = self._created_database_info.get('database', {}).get('db_catalog', 'unknown')
                print(f"🧹 Cleaning up created database: {db_name}")
                try:
                    self._db_creator.cleanup_resources()
                    print("✅ Database cleanup completed")
                except Exception as e:
                    print(f"⚠️ Database cleanup failed: {e}")
                finally:
                    self._created_database_info = None
                    self._db_creator = None
            else:
                print("ℹ️ No database creator found - cleanup skipped")
        else:
            print("ℹ️ No created database to clean up")
    
    def run_safe_test(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Run safe DML-only operations for shared environments
        
        Delegates to TestDmlOnly class for execution.
        
        Args:
            duration_minutes: How long to run DML operations
            
        Returns:
            dict: Test results
        """
        test_scenario = TestDmlOnly(self)
        return test_scenario.run(duration_minutes=duration_minutes)
    
    def run_schema_test(self, table_count_per_type: int = 2, test_columns: List[str] = None, 
                       duration_minutes: int = 5) -> Dict[str, Any]:
        """Run DML + DDL + ALTER operations in a dedicated schema
        
        This mode creates tables, performs DML operations, and tests column alterations
        within a dedicated schema. Requires a dedicated schema to be safe.
        
        Args:
            table_count_per_type: Number of tables to create per type
            test_columns: Columns to test for ALTER operations
            duration_minutes: How long to run DML operations
            
        Returns:
            dict: Test results
        """
        if self.test_mode not in ['dedicated_schema', 'new_database']:
            raise ValueError(f"Schema test requires 'dedicated_schema' or 'new_database' mode, got '{self.test_mode}'. "
                           "Please provide a schema in config or use run_safe_test() for shared environments.")
        
        print(f"🔧 Running SCHEMA test (DML + DDL + ALTER) for {duration_minutes} minutes...")
        print("📋 Operations: Table creation, DML, column operations, cleanup")
        
        if test_columns is None:
            test_columns = ['test_field_1', 'test_field_2']
        
        # Delegate to TestDedicatedSchema
        test_scenario = TestDedicatedSchema(self)
        return test_scenario.run(
            table_count_per_type=table_count_per_type,
            test_columns=test_columns,
            duration_minutes=duration_minutes,
            cleanup_after_test=True
        )
    
    def run_full_test(self, table_count_per_type: int = 2, test_columns: List[str] = None,
                     duration_minutes: int = 5) -> Dict[str, Any]:
        """Run all operations including database-level changes
        
        This mode runs all available tests including CDC/CT and LFC integration.
        Only safe for new databases or dedicated test environments.
        
        Args:
            table_count_per_type: Number of tables to create per type
            test_columns: Columns to test for ALTER operations  
            duration_minutes: How long to run DML operations
            
        Returns:
            dict: Test results
        """
        if self.test_mode != 'new_database':
            print(f"⚠️ Warning: Full test in '{self.test_mode}' mode may perform database-level changes")
        
        print(f"🚀 Running FULL test (all operations) for {duration_minutes} minutes...")
        print("📋 Operations: Database-level CDC/CT, LFC, table creation, DML, column operations")
        
        if test_columns is None:
            test_columns = ['test_field_1', 'test_field_2']
        
        # Run all operations (existing comprehensive test)
        return self.run_comprehensive_test(
            table_count_per_type=table_count_per_type,
            test_columns=test_columns,
            cleanup_after_test=True,
            duration_minutes=duration_minutes
        )
    
    def run_async_parallel_test(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Run async parallel test where DML, DDL, and ALTER operations run in parallel
        
        Delegates to TestAsyncParallel class for execution.
        
        Args:
            duration_minutes: Duration to run the test
            
        Returns:
            dict: Test results with performance metrics
        """
        test_scenario = TestAsyncParallel(self)
        return test_scenario.run(duration_minutes=duration_minutes)


    def _run_test_phases(self, test_phases: List, test_name: str) -> Dict[str, Any]:
        """Execute a list of test phases and return results
        
        Args:
            test_phases: List of (phase_name, phase_func, *args) tuples
            test_name: Name of the test for logging
            
        Returns:
            dict: Test results
        """
        self.test_start_time = datetime.datetime.now()
        self.test_results = {}
        
        print(f"🚀 Starting {test_name} at {self.test_start_time}")
        
        # Execute test phases
        for phase_info in test_phases:
            phase_name = phase_info[0]
            phase_func = phase_info[1]
            phase_args = phase_info[2:] if len(phase_info) > 2 else []
            
            print(f"\n📋 TEST PHASE: {phase_name.upper()}")
            try:
                result = phase_func(*phase_args)
                self.test_results[phase_name] = result
                print(f"✅ {phase_name} completed successfully")
            except Exception as e:
                error_result = {
                    'status': 'error',
                    'message': str(e),
                    'traceback': traceback.format_exc()
                }
                self.test_results[phase_name] = error_result
                print(f"❌ {phase_name} failed: {str(e)}")
        
        # Generate final summary
        test_end_time = datetime.datetime.now()
        test_duration = test_end_time - self.test_start_time
        
        summary = self._generate_test_summary(test_duration)
        self.test_results['summary'] = summary
        
        print(f"\n🏁 {test_name} completed in {test_duration}")
        print(f"📊 Summary: {summary['passed']}/{summary['total']} tests passed")
        
        return self.test_results
    
    def record_retry(self, operation_name: str, retry_count: int = 1):
        """Record retry attempts for an operation
        
        Args:
            operation_name: Name of the operation that was retried
            retry_count: Number of retry attempts (default: 1)
        """
        if operation_name not in self.retry_counts:
            self.retry_counts[operation_name] = 0
        self.retry_counts[operation_name] += retry_count
    
    # ==================== DELEGATION METHODS (Phase 2 Refactoring) ====================
    
    def test_database_permissions(self) -> Dict[str, Any]:
        """Comprehensive database setup verification test
        
        Delegates to DatabaseSetupValidator for execution.
        
        Returns:
            dict: Comprehensive test results with detailed validation
        """
        validator = DatabaseSetupValidator(self)
        return validator.test_database_permissions()
    
    def test_connection_secret_creation(self, db_type: str = None, creds_file: str = None) -> Dict[str, Any]:
        """Test connection and secret creation for a database
        
        Delegates to ConnectionSecretManager for execution.
        
        Args:
            db_type: Database type ('mysql', 'postgresql', 'sqlserver')
            creds_file: Path to credentials file
            
        Returns:
            dict: Test results with status, connection info, and any errors
        """
        manager = ConnectionSecretManager(self)
        return manager.test_connection_secret_creation(db_type, creds_file)
    
    def run_all_scenarios(self, 
                         duration_per_scenario: int = 2,
                         table_count_per_type: int = 2,
                         test_columns: List[str] = None,
                         cleanup_between_scenarios: bool = True) -> Dict[str, Any]:
        """Run all 3 test scenarios in sequence
        
        Delegates to TestScenarioRunner for execution.
        
        Args:
            duration_per_scenario: Duration in minutes for each scenario
            table_count_per_type: Number of tables to create per type
            test_columns: Columns to test for ALTER operations
            cleanup_between_scenarios: Whether to cleanup between scenarios
            
        Returns:
            dict: Combined results from all 3 scenarios
        """
        runner = TestScenarioRunner(self)
        return runner.run_all_scenarios(
            duration_per_scenario=duration_per_scenario,
            table_count_per_type=table_count_per_type,
            test_columns=test_columns,
            cleanup_between_scenarios=cleanup_between_scenarios
        )
    
    def _display_performance_monitoring(self):
        """Display comprehensive performance monitoring report
        
        Delegates to PerformanceReporter for execution.
        """
        reporter = PerformanceReporter(self)
        return reporter._display_performance_monitoring()
    
    def run_impact_assessment(self, operation_type: str = "baseline", duration_minutes: int = 5) -> Dict[str, Any]:
        """Run comprehensive database impact assessment
        
        Delegates to ImpactAssessment for execution.
        
        Args:
            operation_type: Type of operation to assess
            duration_minutes: How long to run the assessment
            
        Returns:
            dict: Comprehensive impact assessment results
        """
        assessment = ImpactAssessment(self)
        return assessment.run_impact_assessment(operation_type, duration_minutes)
    
def run_quick_test(workspace_client, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run a quick test of all Simple modules
    
    Args:
        workspace_client: Databricks WorkspaceClient instance
        config: Configuration dictionary
        
    Returns:
        dict: Quick test results
    """
    print("🚀 Running quick test of Simple modules...")
    
    # Initialize test suite
    test_suite = SimpleTest(workspace_client, config)
    
    # Setup modules
    setup_results = test_suite.setup_modules(
        metadata_refresh_interval=60,
        enable_cdc=True,
        enable_lfc=True,
        replication_filter='both'
    )
    
    if any(result.get('status') == 'error' for result in setup_results.values()):
        return {
            'status': 'error',
            'message': 'Module setup failed',
            'setup_results': setup_results
        }
    
    # Run comprehensive test
    test_results = test_suite.run_comprehensive_test(
        table_count_per_type=1,
        test_columns=['field_quick_test'],
        cleanup_after_test=True
    )
    
    # Generate report
    report = test_suite.get_test_report()
    print("\n" + report)
    
    return {
        'status': 'success',
        'message': 'Quick test completed',
        'setup_results': setup_results,
        'test_results': test_results,
        'report': report
    }
