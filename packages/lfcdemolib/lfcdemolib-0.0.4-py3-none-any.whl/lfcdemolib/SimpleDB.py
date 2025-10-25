"""
SimpleDB - Simple Database Creation and Management

This module provides automated database creation and management for testing:
- Multi-cloud support (Azure, AWS, GCP, OCI) via provider abstraction
- Multi-database support (SQL Server, MySQL, PostgreSQL, Oracle)
- Connection validation and creation
- Automatic cleanup with LIFO queue
- Integration with Databricks connections and secrets via LfcConn and LfcSecrets

Key Features:
- Cloud provider abstraction for extensibility
- Database type abstraction
- Terraform-based infrastructure provisioning
- Automatic resource tagging for cleanup
- LIFO cleanup queue for proper resource deletion order
- Connection name validation and creation
- Integration with existing Simple* modules
"""

import json
import os
import subprocess
import tempfile
import time
import queue
import datetime
import secrets
import string
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
import warnings
import sqlalchemy as sa
from sqlalchemy import text

try:
    from .SimpleCloudBase import (
        CloudProviderBase, 
        DatabaseProviderBase, 
        TerraformProviderBase,
        get_cloud_provider,
        get_database_provider,
        get_connection_suffix
    )
    from .LfcConn import LfcConn
    from .LfcSecrets import LfcSecrets
    from .LfcEnv import LfcEnv
    from .LfcDbPerm import LfcDbPerm
    from .LfcCDC import LfcCDC
    from .LfcSchEvo import LfcSchEvo
except ImportError:
    # For direct module loading in tests
    from SimpleCloudBase import (
        CloudProviderBase, 
        DatabaseProviderBase, 
        TerraformProviderBase,
        get_cloud_provider,
        get_database_provider,
        get_connection_suffix
    )
    try:
        from LfcConn import LfcConn
        from LfcSecrets import LfcSecrets
        from LfcEnv import LfcEnv
        from LfcDbPerm import LfcDbPerm
        from LfcCDC import LfcCDC
        from LfcSchEvo import LfcSchEvo
    except ImportError:
        LfcConn = None
        LfcSecrets = None
        LfcEnv = None
        LfcDbPerm = None
        LfcCDC = None
        LfcSchEvo = None


@dataclass
class SimpleDB:
    """SimpleDB - Automated database creation and management
    
    Provides automated database provisioning using cloud provider abstraction
    with proper cleanup and integration with Databricks connections and secrets.
    """
    
    # Core configuration
    workspace_client: Any  # WorkspaceClient instance for Databricks integration (replaces dbxrest)
    config: Dict[str, Any]
    
    # Database and cloud configuration
    db_type: Literal['sqlserver', 'mysql', 'postgresql', 'oracle'] = 'sqlserver'
    cloud_provider: Literal['azure', 'aws', 'gcp', 'oci'] = 'azure'
    
    # Cloud-specific configuration (passed to provider)
    location: str = "Central US"  # Default for Azure, better MySQL/PostgreSQL support
    
    # Database parameters
    db_basename: Optional[str] = None
    catalog_basename: Optional[str] = None
    dba_username: Optional[str] = None
    dba_password: Optional[str] = None
    user_username: Optional[str] = None
    user_password: Optional[str] = None
    
    # Terraform configuration
    terraform_dir: Optional[str] = None
    terraform_state_file: Optional[str] = None
    
    # Cleanup and state management
    cleanup_queue: queue.LifoQueue = field(default_factory=queue.LifoQueue)
    created_resources: List[Dict[str, Any]] = field(default_factory=list)
    
    # Connection management
    connection_name: Optional[str] = None
    connection_created: bool = False
    secrets_created: bool = False
    include_connection_suffix: bool = False  # Make connection suffix optional
    auto_cleanup: bool = True  # Whether to add connections/secrets to cleanup queue
    
    # Provider instances (initialized in __post_init__)
    _cloud_provider: Optional[CloudProviderBase] = field(default=None, init=False)
    _db_provider: Optional[DatabaseProviderBase] = field(default=None, init=False)
    _terraform_provider: Optional[TerraformProviderBase] = field(default=None, init=False)
    _lfc_env: Optional['LfcEnv'] = field(default=None, init=False)
    
    def __post_init__(self):
        """Initialize SimpleDB after dataclass creation"""
        self._setup_lfc_env()
        self._setup_providers()
        self._setup_defaults()
        self._setup_terraform_workspace()
    
    def _setup_lfc_env(self):
        """Initialize LfcEnv for user information"""
        if LfcEnv is None:
            raise ImportError("LfcEnv module is required but not available. Please ensure lfcdemolib is properly installed.")
        self._lfc_env = LfcEnv(workspace_client=self.workspace_client)
    
    def _setup_providers(self):
        """Initialize cloud and database providers"""
        # Initialize cloud provider
        self._cloud_provider = get_cloud_provider(
            self.cloud_provider, 
            self.workspace_client, 
            self.config,
            location=self.location
        )
        
        # Initialize database provider
        self._db_provider = get_database_provider(self.db_type)
        
        # Initialize Terraform provider
        self._terraform_provider = TerraformProviderBase(
            self._cloud_provider, 
            self._db_provider
        )
    
    def _setup_defaults(self):
        """Setup default values for database creation"""
        # Generate secure random names and passwords if not provided
        if self.db_basename is None:
            self.db_basename = self._generate_random_name(16)
        
        if self.catalog_basename is None:
            self.catalog_basename = self._generate_database_name(8)
        
        if self.dba_username is None:
            self.dba_username = self._generate_username(16)
        
        if self.user_username is None:
            self.user_username = self._generate_username(16)
        
        if self.dba_password is None:
            self.dba_password = self._generate_secure_password()
        
        if self.user_password is None:
            self.user_password = self._generate_secure_password()
        
        # Setup connection name if not provided
        if self.connection_name is None:
            whoami = self._lfc_env.get_connection_prefix()
            
            # Use laptop hostname as fallback - will be updated with database hostname later
            import socket
            hostname = socket.gethostname().split('.')[0].lower().replace('-', '_').replace('.', '_')
            
            # Add connection suffix only if requested
            if self.include_connection_suffix:
                connection_suffix = get_connection_suffix(self.db_type)
                self.connection_name = f"{whoami}_{connection_suffix}"
            else:
                # Use pattern: robert_lee_hostname (will be updated with db hostname)
                self.connection_name = f"{whoami}_{hostname}"
    
    def _generate_random_name(self, length: int = 16) -> str:
        """Generate a random alphanumeric name"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _generate_username(self, length: int = 16) -> str:
        """Generate a username that starts with a letter (required for PostgreSQL/MySQL)"""
        # First character must be a letter
        first_char = secrets.choice(string.ascii_letters)
        # Remaining characters can be letters or digits
        remaining_chars = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length - 1))
        return first_char + remaining_chars
    
    def _generate_database_name(self, length: int = 8) -> str:
        """Generate a database name that starts with a letter (required for PostgreSQL)"""
        # First character must be a letter
        first_char = secrets.choice(string.ascii_lowercase)
        # Remaining characters can be letters or digits
        remaining_chars = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length - 1))
        return first_char + remaining_chars
    
    def _update_connection_name_with_db_hostname(self, db_hostname: str):
        """Update connection name to use database hostname instead of laptop hostname
        
        Args:
            db_hostname: The database server hostname
        """
        if not db_hostname or self.include_connection_suffix:
            return  # Don't update if no hostname or using suffix format
        
        # Extract the base name from current connection name
        whoami = self._lfc_env.get_connection_prefix()
        
        # Extract hostname from database FQDN and clean it
        db_hostname_clean = db_hostname.split('.')[0].lower().replace('-', '_').replace('.', '_')
        
        # Update connection name with database hostname
        old_connection_name = self.connection_name
        self.connection_name = f"{whoami}_{db_hostname_clean}"
        
        if old_connection_name != self.connection_name:
            print(f"🔄 Updated connection name: {old_connection_name} → {self.connection_name}")
            print(f"   Using database hostname: {db_hostname_clean}")
    
    def _generate_secure_password(self, length: int = 32) -> str:
        """Generate a secure password avoiding problematic characters"""
        # Avoid characters that cause issues in bash/eval: -[]{}!=~^$;():.*@\/<>`"'|
        safe_chars = string.ascii_letters + string.digits + '_+%#'
        return ''.join(secrets.choice(safe_chars) for _ in range(length))
    
    def _get_database_size_info(self) -> str:
        """Get database size information based on database type and tier"""
        if self.db_type == 'sqlserver':
            return "2GB (Basic tier - cheapest ~$5/month)"
        elif self.db_type == 'mysql':
            return "32GB (Burstable B1ms - cheapest ~$12/month)"
        elif self.db_type == 'postgresql':
            return "32GB (Burstable B1ms - cheapest ~$12/month)"
        else:
            return "Unknown size"
    
    def _setup_terraform_workspace(self):
        """Setup Terraform workspace directory"""
        if self.terraform_dir is None:
            self.terraform_dir = tempfile.mkdtemp(prefix='simpledb_terraform_')
            print(f"📁 Created Terraform workspace: {self.terraform_dir}")
    
    def check_connection_exists(self, connection_name: str = None) -> bool:
        """Check if a Databricks connection exists
        
        Args:
            connection_name: Name of the connection to check (uses self.connection_name if None)
            
        Returns:
            bool: True if connection exists, False otherwise
        """
        if connection_name is None:
            connection_name = self.connection_name
        
        # If no workspace_client, we're creating a new database - connection doesn't exist yet
        if self.workspace_client is None:
            print(f"ℹ️ No Databricks integration - connection '{connection_name}' will be created")
            return False
        
        try:
            connection_spec = self.workspace_client.connections.get(connection_name)
            print(f"✅ Connection '{connection_name}' exists")
            return True
        except Exception as e:
            print(f"ℹ️ Connection '{connection_name}' does not exist - will be created")
            return False
    
    def create_database_infrastructure(self) -> Dict[str, Any]:
        """Create database infrastructure using cloud provider
        
        Returns:
            dict: Creation results with connection details
        """
        print(f"🚀 Creating {self.db_type} database on {self.cloud_provider} using Terraform...")
        
        # Check region availability and find closest if needed
        temp_provider = get_cloud_provider(
            self.cloud_provider, 
            self.workspace_client, 
            self.config,
            location=self.location,
            resource_group_name=getattr(self, 'resource_group_name', None)
        )
        
        if hasattr(temp_provider, 'find_closest_available_region'):
            optimal_region = temp_provider.find_closest_available_region(
                self.db_type, 
                preferred_region=self.location
            )
            if optimal_region != self.location:
                print(f"🔄 Switching from {self.location} to {optimal_region} for better availability")
                self.location = optimal_region
        
        # Prepare database configuration
        db_config = {
            'db_type': self.db_type,
            'db_basename': self.db_basename,
            'catalog_basename': self.catalog_basename,
            'dba_username': self.dba_username,
            'dba_password': self.dba_password,
            'user_username': self.user_username,
            'user_password': self.user_password,
            'terraform_dir': self.terraform_dir
        }
        
        # Generate Terraform configuration using cloud provider
        terraform_config = self._cloud_provider.generate_terraform_config(db_config)
        
        # Write Terraform files
        main_tf_path = os.path.join(self.terraform_dir, 'main.tf')
        with open(main_tf_path, 'w') as f:
            f.write(terraform_config)
        
        variables_tf_path = os.path.join(self.terraform_dir, 'variables.tf')
        with open(variables_tf_path, 'w') as f:
            f.write(self._cloud_provider.generate_terraform_variables())
        
        outputs_tf_path = os.path.join(self.terraform_dir, 'outputs.tf')
        with open(outputs_tf_path, 'w') as f:
            f.write(self._cloud_provider.generate_terraform_outputs())
        
        # Create terraform.tfvars
        tfvars_path = os.path.join(self.terraform_dir, 'terraform.tfvars')
        with open(tfvars_path, 'w') as f:
            f.write(self._cloud_provider.generate_terraform_tfvars(db_config))
        
        try:
            # Initialize Terraform
            print("🔧 Initializing Terraform...")
            self._run_terraform_command(['init'])
            
            # Plan Terraform
            print("📋 Planning Terraform deployment...")
            self._run_terraform_command(['plan'])
            
            # Apply Terraform
            print("🏗️ Applying Terraform configuration (this may take 5-10 minutes)...")
            self._run_terraform_command(['apply', '-auto-approve'])
            
            # Get outputs
            print("📤 Retrieving Terraform outputs...")
            outputs = self._get_terraform_outputs()
            
            # Get connection details from cloud provider
            creation_result = self._cloud_provider.get_connection_details(outputs, db_config)
            
            # Add to cleanup queue (LIFO - last in, first out)
            self.cleanup_queue.put(('destroy_terraform', creation_result))
            self.created_resources.append(creation_result)
            
            # Get database size info
            size_info = self._get_database_size_info()
            
            # Add connection_name to creation_result for downstream use
            creation_result['connection_name'] = self.connection_name
            
            print(f"✅ {self.db_type.title()} database created successfully on {self.cloud_provider.title()}!")
            print(f"   Server: {creation_result['db_host_fqdn']}")
            print(f"   Database: {creation_result['db_catalog']}")
            print(f"   Size: {size_info}")
            
            return creation_result
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': str(e),
                'terraform_dir': self.terraform_dir,
                'cloud_provider': self.cloud_provider,
                'db_type': self.db_type
            }
            print(f"❌ Failed to create {self.db_type} database on {self.cloud_provider}: {str(e)}")
            return error_result
    
    def _run_terraform_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a Terraform command in the workspace directory"""
        cmd = ['terraform'] + args
        print(f"🔧 Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=self.terraform_dir,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            print(f"❌ Terraform command failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise RuntimeError(f"Terraform command failed: {result.stderr}")
        
        return result
    
    def _get_terraform_outputs(self) -> Dict[str, Any]:
        """Get Terraform outputs as JSON"""
        result = self._run_terraform_command(['output', '-json'])
        return json.loads(result.stdout)
    
    def create_databricks_connection(self, db_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create Databricks connection for the database using LfcConn
        
        Args:
            db_details: Database connection details from create_database_infrastructure
            
        Returns:
            dict: Connection creation results
        """
        print(f"🔗 Creating Databricks connection '{self.connection_name}'...")
        
        # Skip Databricks connection creation if no workspace_client
        if self.workspace_client is None:
            print("ℹ️ No Databricks integration - skipping connection creation")
            return {
                'status': 'skipped',
                'message': 'No Databricks integration available',
                'connection_name': self.connection_name
            }
        
        # Use LfcConn module for connection management
        if LfcConn is None:
            raise ImportError("LfcConn module is required but not available. Please ensure lfcdemolib is properly installed.")
        
        try:
            # Initialize LfcConn with the workspace client
            lfc_conn = LfcConn(workspace_client=self.workspace_client)
            
            # Prepare database config for LfcConn
            # NOTE: Use 'user' and 'password' keys (not 'username') for regular user credentials
            # LfcConn will use these for the Databricks connection (Lakeflow Connect requirement)
            db_config = {
                'type': self.db_type,
                'cloud': self.cloud_provider,
                'host': db_details['db_host'],
                'host_fqdn': db_details['db_host_fqdn'],
                'port': db_details['db_port'],
                'database': db_details['db_catalog'],
                'schema': 'lfcddemo',  # Always use lfcddemo schema
                'user': db_details['user_username'],  # Regular user (NOT dba) for LFC
                'password': db_details['user_password'],  # Regular user password
                'dba_username': db_details['dba_username'],
                'dba_password': db_details['dba_password'],
                'replication_mode': db_details['replication_mode'],  # REQUIRED - no default
                'connection_name': self.connection_name
            }
            
            # Create the connection using LfcConn
            result = lfc_conn.create_connection(db_config)
            
            if result['status'] == 'success':
                # Add to cleanup queue only if auto_cleanup is enabled
                if self.auto_cleanup:
                    self.cleanup_queue.put(('delete_connection', self.connection_name))
                self.connection_created = True
                
                print(f"✅ Databricks connection '{self.connection_name}' created successfully")
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to create Databricks connection: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e),
                'connection_name': self.connection_name
            }
    
    def setup_database_permissions(self, db_details: Dict[str, Any]) -> Dict[str, Any]:
        """Setup database permissions and create lfcddemo schema using LfcDbPerm
        
        Args:
            db_details: Database connection details from create_database_infrastructure
            
        Returns:
            dict: Permission setup results
        """
        print(f"🔐 Setting up database permissions and lfcddemo schema...")
        
        # Skip permission setup if LfcDbPerm is not available
        if LfcDbPerm is None:
            print("ℹ️ LfcDbPerm not available - skipping permission setup")
            return {
                'status': 'skipped',
                'message': 'LfcDbPerm not available',
                'reason': 'module_not_imported'
            }
        
        try:
            # Create normalized database config for LfcDbPerm
            db_config = {
                'type': self.db_type,
                'host_fqdn': db_details['db_host_fqdn'],
                'host': db_details['db_host'],
                'database': db_details['db_catalog'],
                'catalog': db_details['db_catalog'],
                'schema': 'lfcddemo',  # Standard schema name
                'port': db_details.get('db_port', self._get_default_port()),
                'user': db_details['user_username'],
                'password': db_details['user_password'],
                'dba_username': db_details['dba_username'],
                'dba_password': db_details['dba_password'],
                'cloud': {
                    'provider': self.cloud_provider.title(),
                    'region': self.location
                }
            }
            
            print(f"   Database: {db_config['database']}")
            print(f"   Schema: {db_config['schema']}")
            print(f"   DBA User: {db_config['dba_username']}")
            print(f"   Regular User: {db_config['user']}")
            
            # Create DBA engine for permission setup
            dba_engine = self._create_dba_engine(db_config)
            
            # Initialize LfcDbPerm with DBA engine and config
            lfc_db_perm = LfcDbPerm(
                engine=dba_engine,
                db_config=db_config,
                permission_mode='PERMISSIVE'  # Use permissive mode for new databases
            )
            
            print(f"   ✅ LfcDbPerm initialized for {lfc_db_perm.db_type}")
            
            # Setup database permissions (includes schema creation)
            perm_result = lfc_db_perm.setup_database_permissions(
                enable_cdc=False,  # Start with basic permissions
                enable_ct=False,
                enable_replication=False
            )
            
            # Dispose the DBA engine
            dba_engine.dispose()
            
            if perm_result['status'] == 'success':
                print(f"   ✅ Database permissions and lfcddemo schema setup completed")
                return {
                    'status': 'success',
                    'message': 'Database permissions and lfcddemo schema configured successfully',
                    'db_type': self.db_type,
                    'schema': 'lfcddemo',
                    'permission_mode': 'PERMISSIVE',
                    'operations': perm_result.get('operations', [])
                }
            else:
                print(f"   ❌ Permission setup failed: {perm_result.get('message')}")
                return {
                    'status': 'error',
                    'message': f"Permission setup failed: {perm_result.get('message')}",
                    'details': perm_result
                }
                
        except Exception as e:
            print(f"❌ Failed to setup database permissions: {str(e)}")
            return {
                'status': 'error',
                'message': f"Permission setup failed: {str(e)}",
                'db_type': self.db_type
            }
    
    def _create_dba_engine(self, db_config: Dict[str, Any]):
        """Create SQLAlchemy engine using DBA credentials for permission setup"""
        import sqlalchemy as sa
        from urllib.parse import quote_plus
        
        # URL encode credentials
        encoded_username = quote_plus(db_config['dba_username'])
        encoded_password = quote_plus(db_config['dba_password'])
        
        # Create connection string based on database type
        if db_config['type'] == 'sqlserver':
            driver = "mssql+pymssql"
            connection_string = f"{driver}://{encoded_username}:{encoded_password}@{db_config['host_fqdn']}:{db_config['port']}/{db_config['database']}"
        elif db_config['type'] == 'mysql':
            driver = "mysql+pymysql"
            connection_string = f"{driver}://{encoded_username}:{encoded_password}@{db_config['host_fqdn']}:{db_config['port']}/{db_config['database']}?ssl_disabled=false&ssl_verify_cert=false&ssl_verify_identity=false"
        elif db_config['type'] == 'postgresql':
            driver = "postgresql+psycopg2"
            connection_string = f"{driver}://{encoded_username}:{encoded_password}@{db_config['host_fqdn']}:{db_config['port']}/{db_config['database']}"
        else:
            raise ValueError(f"Unsupported database type: {db_config['type']}")
        
        return sa.create_engine(connection_string, echo=False, isolation_level="AUTOCOMMIT")
    
    def _get_default_port(self) -> int:
        """Get default port for database type"""
        port_mapping = {
            'sqlserver': 1433,
            'mysql': 3306,
            'postgresql': 5432,
            'oracle': 1521
        }
        return port_mapping.get(self.db_type, 1433)
    
    def setup_lakeflow_connect_integration(self, db_details: Dict[str, Any]) -> Dict[str, Any]:
        """Setup complete Lakeflow Connect integration for a new database
        
        This method orchestrates all the components required for Lakeflow Connect:
        1. LfcDbPerm: Database permissions and schema setup
        2. LfcSecrets: Databricks secrets management  
        3. LfcConn: Databricks connection creation
        4. LfcCDC: Change Data Capture/Change Tracking setup
        5. LfcSchEvo: Schema evolution DDL support objects
        
        Args:
            db_details: Database connection details from create_database_infrastructure
            
        Returns:
            dict: Complete LFC integration results
        """
        print(f"🔗 Setting up complete Lakeflow Connect integration...")
        
        integration_results = {}
        overall_status = 'success'
        
        try:
            # Step 2.1: Setup database permissions and schema (LfcDbPerm)
            print(f"\n   📋 Step 2.1: Setting up database permissions and lfcddemo schema...")
            permissions_result = self.setup_database_permissions(db_details)
            integration_results['permissions'] = permissions_result
            
            if permissions_result['status'] not in ['success', 'skipped']:
                print(f"   ❌ Database permissions setup failed: {permissions_result['message']}")
                overall_status = 'error'
            else:
                print(f"   ✅ Database permissions and schema configured")
            
            # Step 2.2: Create Databricks secrets (LfcSecrets)
            print(f"\n   📋 Step 2.2: Creating Databricks secrets...")
            secrets_result = self.create_databricks_secrets(db_details)
            integration_results['secrets'] = secrets_result
            
            if secrets_result['status'] not in ['success', 'skipped']:
                print(f"   ❌ Databricks secrets creation failed: {secrets_result['message']}")
                if overall_status == 'success':
                    overall_status = 'partial'
            else:
                print(f"   ✅ Databricks secrets configured")
            
            # Step 2.3: Create Databricks connection (LfcConn)
            print(f"\n   📋 Step 2.3: Creating Databricks connection...")
            connection_result = self.create_databricks_connection(db_details)
            integration_results['connection'] = connection_result
            
            if connection_result['status'] not in ['success', 'skipped']:
                print(f"   ❌ Databricks connection creation failed: {connection_result['message']}")
                if overall_status == 'success':
                    overall_status = 'partial'
            else:
                print(f"   ✅ Databricks connection configured")
            
            # Step 2.4: Setup CDC/CT replication (LfcCDC)
            print(f"\n   📋 Step 2.4: Setting up Change Data Capture/Change Tracking...")
            
            # Get existing tables (if any) for replication setup
            existing_tables = self._get_existing_tables_for_replication(db_details)
            
            replication_result = self.setup_database_replication(db_details, existing_tables)
            integration_results['replication'] = replication_result
            
            if replication_result['status'] not in ['success', 'skipped', 'partial']:
                print(f"   ❌ CDC/CT replication setup failed: {replication_result['message']}")
                if overall_status == 'success':
                    overall_status = 'partial'
            else:
                print(f"   ✅ CDC/CT replication configured")
            
            # Determine final status
            if overall_status == 'success':
                message = "Complete Lakeflow Connect integration configured successfully"
                print(f"\n🎉 Lakeflow Connect integration completed successfully!")
                print("   ✅ Database permissions and lfcddemo schema")
                print("   ✅ Databricks secrets and connections") 
                print("   ✅ Change Data Capture/Change Tracking")
                print("   ✅ Schema evolution DDL support objects")
            elif overall_status == 'partial':
                message = "Lakeflow Connect integration completed with some warnings"
                print(f"\n⚠️ Lakeflow Connect integration completed with warnings")
            else:
                message = "Lakeflow Connect integration failed"
                print(f"\n❌ Lakeflow Connect integration failed")
            
            return {
                'status': overall_status,
                'message': message,
                'db_type': self.db_type,
                'integration_components': {
                    'permissions': permissions_result,
                    'secrets': secrets_result,
                    'connection': connection_result,
                    'replication': replication_result
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to setup Lakeflow Connect integration: {str(e)}")
            return {
                'status': 'error',
                'message': f"Lakeflow Connect integration failed: {str(e)}",
                'db_type': self.db_type,
                'integration_components': integration_results
            }
    
    def _get_existing_tables_for_replication(self, db_details: Dict[str, Any]) -> List[str]:
        """Get list of existing tables for replication setup
        
        Args:
            db_details: Database connection details
            
        Returns:
            list: List of table names in lfcddemo schema
        """
        try:
            # Create a temporary engine to check for existing tables
            temp_engine = self._create_dba_engine({
                'type': self.db_type,
                'host_fqdn': db_details['db_host_fqdn'],
                'port': db_details.get('db_port', self._get_default_port()),
                'database': db_details['db_catalog'],
                'dba_username': db_details['dba_username'],
                'dba_password': db_details['dba_password']
            })
            
            with temp_engine.connect() as conn:
                # Query for tables in lfcddemo schema
                if self.db_type == 'sqlserver':
                    query = sa.text("""
                        SELECT TABLE_NAME 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = 'lfcddemo' 
                        AND TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_NAME
                    """)
                else:
                    # For other databases, adapt the query as needed
                    query = sa.text("SELECT 1 WHERE 1=0")  # Return empty for now
                
                result = conn.execute(query)
                table_names = [row[0] for row in result.fetchall()]
                
                temp_engine.dispose()
                return table_names
                
        except Exception as e:
            print(f"   ⚠️ Could not check for existing tables: {e}")
            return []  # Return empty list if we can't check
    
    def setup_database_replication(self, db_details: Dict[str, Any], table_names: List[str] = None) -> Dict[str, Any]:
        """Setup database and table-level CDC/CT replication using LfcCDC
        
        Args:
            db_details: Database connection details from create_database_infrastructure
            table_names: Optional list of table names to enable replication for
            
        Returns:
            dict: Replication setup results
        """
        print(f"🔄 Setting up database replication (CDC/CT)...")
        
        # Skip replication setup if LfcCDC is not available
        if LfcCDC is None:
            print("ℹ️ LfcCDC not available - skipping replication setup")
            return {
                'status': 'skipped',
                'message': 'LfcCDC not available',
                'reason': 'module_not_imported'
            }
        
        # Only setup replication for SQL Server (for now)
        if self.db_type != 'sqlserver':
            print(f"ℹ️ Replication setup currently only supported for SQL Server, not {self.db_type}")
            return {
                'status': 'skipped',
                'message': f'Replication setup not supported for {self.db_type}',
                'db_type': self.db_type
            }
        
        try:
            # Create normalized database config for LfcCDC
            db_config = {
                'type': self.db_type,
                'host_fqdn': db_details['db_host_fqdn'],
                'host': db_details['db_host'],
                'database': db_details['db_catalog'],
                'catalog': db_details['db_catalog'],
                'schema': 'lfcddemo',  # Standard schema name
                'port': db_details.get('db_port', self._get_default_port()),
                'user': db_details['user_username'],
                'password': db_details['user_password'],
                'dba_username': db_details['dba_username'],
                'dba_password': db_details['dba_password'],
                'connection_type': 'SQLSERVER'  # For LfcCDC compatibility
            }
            
            print(f"   Database: {db_config['database']}")
            print(f"   Schema: {db_config['schema']}")
            
            # Create regular engine for LfcCDC
            regular_engine = self._create_dba_engine(db_config)
            
            # Create DBA engine for administrative operations
            try:
                dba_engine = LfcCDC.create_dba_engine(db_config)
                print(f"   ✅ DBA engine created for CDC/CT operations")
            except Exception as e:
                print(f"   ⚠️ Could not create DBA engine: {e}. Using regular engine.")
                dba_engine = regular_engine
            
            # Initialize LfcCDC
            simple_cdc = LfcCDC(
                engine=regular_engine,
                schema=db_config['schema'],
                replication_filter='both',  # Enable for all tables
                dba_engine=dba_engine,
                secrets_json=db_config
            )
            
            print(f"   ✅ LfcCDC initialized")
            
            # Step 1: Test CDC support and determine replication mode
            print(f"\n   🔍 Testing CDC support...")
            cdc_supported = simple_cdc.is_cdc_supported()
            
            # Determine replication mode
            if cdc_supported:
                replication_mode = 'both'  # Can use both CDC and CT
                print(f"   ✅ CDC is supported on this database")
                print(f"   📋 Replication mode: BOTH (CDC + CT)")
            else:
                replication_mode = 'ct'  # Only CT available
                cdc_failure_reason = simple_cdc.get_cdc_failure_reason()
                print(f"   ⚠️  CDC is not supported: {cdc_failure_reason}")
                print(f"   📋 Replication mode: CT (Change Tracking only)")
            
            # Store the replication mode in db_details for later use
            db_details['replication_mode'] = replication_mode
            
            if cdc_supported:
                print(f"   ✅ Database supports full CDC capabilities")
            else:
                print(f"   ⚠️ CDC not supported: {simple_cdc.get_cdc_failure_reason()}")
                print(f"   🔄 Will use Change Tracking (CT) instead")
            
            # Step 2: Enable database-level replication
            print(f"\n   🔧 Enabling database-level replication...")
            
            # Enable Change Tracking at database level (always supported)
            ct_result = self._enable_database_level_ct(simple_cdc, db_config)
            
            # Step 2.5: Setup schema evolution DDL support objects
            print(f"\n   🔧 Setting up schema evolution DDL support objects...")
            schema_evo_result = self._setup_schema_evolution(db_config, cdc_supported)
            
            # Step 3: Enable table-level replication using bulk method
            table_results = {}
            print(f"\n   🔧 Enabling table-level replication for schema '{db_config['schema']}'...")
            
            # Use enable_cdc_ct_for_tables which respects bulk_mode setting
            # Default is table-by-table (bulk_mode=False) for reliability
            if table_names:
                # Enable CDC/CT for specific tables (respects bulk_mode setting)
                print(f"   🚀 Enabling CDC/CT for {len(table_names)} tables...")
                table_results = simple_cdc.enable_cdc_ct_for_tables(
                    table_names=table_names,
                    schema_name=db_config['schema'],
                    mode='BOTH'
                )
            else:
                # No specific tables provided, use bulk for entire schema
                print(f"   🚀 Enabling CDC/CT for entire schema...")
                table_results = simple_cdc.bulk_enable_cdc_ct_for_schema(
                    schema_name=db_config['schema'],
                    mode='BOTH',
                    dry_run=False
                )
            
            # Cleanup engines
            regular_engine.dispose()
            if dba_engine != regular_engine:
                dba_engine.dispose()
            
            # Determine overall status from bulk operation
            overall_status = 'success'
            if table_results and table_results.get('status') == 'error':
                overall_status = 'error'
            elif table_results and table_results.get('status') == 'completed':
                # Check if any operations failed
                if table_results.get('cdc_disabled_count', 0) > 0 or table_results.get('ct_disabled_count', 0) > 0:
                    overall_status = 'partial'
            
            # Calculate total tables processed
            tables_processed = 0
            if table_results and table_results.get('status') == 'completed':
                tables_processed = (
                    table_results.get('cdc_enabled_count', 0) +
                    table_results.get('ct_enabled_count', 0) +
                    table_results.get('cdc_enabled_already_count', 0) +
                    table_results.get('ct_enabled_already_count', 0)
                )
            
            return {
                'status': overall_status,
                'message': f'Database replication setup completed for {self.db_type}',
                'db_type': self.db_type,
                'schema': db_config['schema'],
                'cdc_supported': cdc_supported,
                'replication_mode': replication_mode,  # Add mode to result
                'ct_result': ct_result,
                'schema_evo_result': schema_evo_result,
                'bulk_cdc_ct_result': table_results,
                'tables_processed': tables_processed
            }
            
        except Exception as e:
            print(f"❌ Failed to setup database replication: {str(e)}")
            return {
                'status': 'error',
                'message': f"Replication setup failed: {str(e)}",
                'db_type': self.db_type
            }
    
    def _enable_database_level_ct(self, cdc_instance, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Enable Change Tracking at database level
        
        Args:
            cdc_instance: LfcCDC instance to use for CT operations
            db_config: Database configuration dictionary
            
        Returns:
            dict: Result of CT database-level enablement
        """
        try:
            with cdc_instance.dba_engine.connect() as dba_conn:
                target_db = db_config['database']
                
                # Check if Change Tracking is already enabled at database level
                ct_check_query = sa.text(f"""
                    SELECT COUNT(*) 
                    FROM sys.change_tracking_databases 
                    WHERE database_id = DB_ID('{target_db}')
                """)
                
                ct_enabled = dba_conn.execute(ct_check_query).scalar() > 0
                
                if ct_enabled:
                    print(f"      ✅ Change Tracking already enabled at database level for {target_db}")
                    return {
                        'status': 'already_enabled',
                        'message': f'Change Tracking already enabled for database {target_db}'
                    }
                
                # Enable Change Tracking at database level
                print(f"      🔄 Enabling Change Tracking at database level for {target_db}...")
                
                enable_ct_query = sa.text(f"""
                    ALTER DATABASE [{target_db}] SET CHANGE_TRACKING = ON 
                    (CHANGE_RETENTION = 3 DAYS, AUTO_CLEANUP = ON)
                """)
                
                dba_conn.execute(enable_ct_query)
                dba_conn.commit()
                
                # Verify CT was enabled
                ct_enabled_after = dba_conn.execute(ct_check_query).scalar() > 0
                
                if ct_enabled_after:
                    print(f"      ✅ Change Tracking enabled successfully for {target_db}")
                    return {
                        'status': 'success',
                        'message': f'Change Tracking enabled for database {target_db}'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'Failed to enable Change Tracking for database {target_db}'
                    }
                    
        except Exception as e:
            print(f"      ❌ Failed to enable Change Tracking: {str(e)}")
            return {
                'status': 'error',
                'message': f'Change Tracking setup failed: {str(e)}'
            }
    
    def _setup_schema_evolution(self, db_config: Dict[str, Any], cdc_supported: bool) -> Dict[str, Any]:
        """Setup schema evolution DDL support objects using LfcSchEvo
        
        Args:
            db_config: Database configuration dictionary
            cdc_supported: Whether CDC is supported on this database
            
        Returns:
            dict: Result of schema evolution setup
        """
        # Skip schema evolution setup if LfcSchEvo is not available
        if LfcSchEvo is None:
            print("      ℹ️ LfcSchEvo not available - skipping schema evolution setup")
            return {
                'status': 'skipped',
                'message': 'LfcSchEvo not available',
                'reason': 'module_not_imported'
            }
        
        try:
            # Create regular engine for LfcSchEvo
            regular_engine = self._create_dba_engine(db_config)
            
            # Initialize LfcSchEvo
            lfc_sch_evo = LfcSchEvo(
                engine=regular_engine,
                schema=db_config['schema'],
                replication_filter='both',  # Enable for all tables
                secrets_json=db_config
            )
            
            print(f"      ✅ LfcSchEvo initialized")
            
            # Determine DDL support mode based on CDC support
            if cdc_supported:
                ddl_mode = 'BOTH'  # CDC + CT
                print(f"      📋 Using BOTH mode (CDC + CT) - CDC is supported")
            else:
                ddl_mode = 'CT'    # CT only
                print(f"      📋 Using CT mode only - CDC not supported")
            
            # Setup DDL support objects
            print(f"      🔧 Setting up DDL support objects (mode: {ddl_mode})...")
            
            setup_result = lfc_sch_evo.setup_ddl_support_objects(
                mode=ddl_mode,
                replication_user=db_config['user']
            )
            
            # Cleanup engine
            regular_engine.dispose()
            
            if setup_result['status'] == 'success':
                print(f"      ✅ Schema evolution DDL support objects setup completed")
                return {
                    'status': 'success',
                    'message': f'Schema evolution setup completed with mode: {ddl_mode}',
                    'mode': ddl_mode,
                    'cdc_supported': cdc_supported,
                    'setup_details': setup_result
                }
            else:
                print(f"      ⚠️ Schema evolution setup completed with warnings: {setup_result.get('message')}")
                return {
                    'status': 'warning',
                    'message': f"Schema evolution setup completed with warnings: {setup_result.get('message')}",
                    'mode': ddl_mode,
                    'cdc_supported': cdc_supported,
                    'setup_details': setup_result
                }
                
        except Exception as e:
            print(f"      ❌ Failed to setup schema evolution: {str(e)}")
            return {
                'status': 'error',
                'message': f'Schema evolution setup failed: {str(e)}',
                'cdc_supported': cdc_supported
            }
    
    def create_databricks_secrets(self, db_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create Databricks secrets for the database
        
        Args:
            db_details: Database connection details
            
        Returns:
            dict: Secrets creation results
        """
        print(f"🔐 Creating Databricks secrets...")
        
        # Skip Databricks secrets creation if no workspace_client
        if self.workspace_client is None:
            print("ℹ️ No Databricks integration - skipping secrets creation")
            return {
                'status': 'skipped',
                'message': 'No Databricks integration available',
                'db_details': db_details
            }
        
        # Use LfcSecrets module for secret management
        if LfcSecrets is None:
            raise ImportError("LfcSecrets module is required but not available. Please ensure lfcdemolib is properly installed.")
        
        try:
            # Initialize LfcSecrets with the workspace client
            lfc_secrets = LfcSecrets(workspace_client=self.workspace_client)
            
            # Prepare database config for LfcSecrets
            db_config = {
                'type': self.db_type,
                'cloud': self.cloud_provider,
                'host': db_details['db_host'],
                'host_fqdn': db_details['db_host_fqdn'],
                'port': db_details['db_port'],
                'database': db_details['db_catalog'],
                'schema': 'lfcddemo',  # Always use lfcddemo schema
                'username': db_details['user_username'],
                'password': db_details['user_password'],
                'dba_username': db_details['dba_username'],
                'dba_password': db_details['dba_password'],
                'replication_mode': db_details.get('replication_mode', 'ct')  # CDC capability mode
            }
            
            # Create the secret using LfcSecrets
            result = lfc_secrets.create_secret(db_config)
            
            if result['status'] == 'success':
                # Add secret to cleanup queue only if auto_cleanup is enabled
                if self.auto_cleanup:
                    self.cleanup_queue.put(('delete_secret', result['scope_name'], result['secret_key']))
                self.secrets_created = True
                
                print(f"✅ Databricks secrets created successfully")
                print(f"   Scope: {result['scope_name']}")
                print(f"   Key: {result['secret_key']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to create Databricks secrets: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def create_complete_database_setup(self) -> Dict[str, Any]:
        """Create complete database setup: Infrastructure + Databricks connection + secrets
        
        Returns:
            dict: Complete setup results
        """
        print(f"🚀 Creating complete {self.db_type} database setup on {self.cloud_provider} for '{self.connection_name}'...")
        
        # Check if connection already exists
        if self.check_connection_exists():
            return {
                'status': 'exists',
                'message': f"Connection '{self.connection_name}' already exists",
                'connection_name': self.connection_name
            }
        
        setup_results = {
            'connection_name': self.connection_name,
            'db_type': self.db_type,
            'cloud_provider': self.cloud_provider,
            'started_at': datetime.datetime.now().isoformat()
        }
        
        try:
            # Step 1: Create database infrastructure
            print(f"\n📋 Step 1: Creating {self.db_type} database on {self.cloud_provider}...")
            db_result = self.create_database_infrastructure()
            if db_result['status'] != 'success':
                setup_results['database'] = db_result
                setup_results['status'] = 'failed_database'
                return setup_results
            
            # Update connection name with database hostname
            if 'db_host_fqdn' in db_result:
                self._update_connection_name_with_db_hostname(db_result['db_host_fqdn'])
                # Update the connection_name in db_result to reflect the updated name
                db_result['connection_name'] = self.connection_name
            
            setup_results['database'] = db_result
            
            # Step 2: Setup complete Lakeflow Connect integration
            print(f"\n📋 Step 2: Setting up complete Lakeflow Connect integration...")
            lfc_result = self.setup_lakeflow_connect_integration(db_result)
            setup_results['lakeflow_connect'] = lfc_result
            
            # Final status - treat 'skipped' as success when no Databricks integration
            lfc_ok = lfc_result['status'] in ['success', 'skipped', 'partial']
            
            if (db_result['status'] == 'success' and lfc_ok):
                setup_results['status'] = 'success'
                if self.workspace_client is None:
                    setup_results['message'] = f"{self.db_type} database created successfully on {self.cloud_provider} (standalone mode)"
                    print(f"\n🎉 Database created successfully in standalone mode!")
                else:
                    setup_results['message'] = f"Complete {self.db_type} database setup created successfully on {self.cloud_provider}"
                    print(f"\n🎉 Complete database setup created successfully!")
                print(f"   Connection: {self.connection_name}")
                print(f"   Server: {db_result['db_host_fqdn']}")
                print(f"   Database: {db_result['db_catalog']}")
                print(f"   Type: {self.db_type} on {self.cloud_provider}")
            else:
                setup_results['status'] = 'partial'
                setup_results['message'] = f"Database setup partially completed"
                print(f"\n⚠️ Database setup partially completed")
            
            setup_results['completed_at'] = datetime.datetime.now().isoformat()
            return setup_results
            
        except Exception as e:
            setup_results['status'] = 'error'
            setup_results['message'] = str(e)
            setup_results['error_at'] = datetime.datetime.now().isoformat()
            print(f"❌ Failed to create complete database setup: {str(e)}")
            return setup_results
    
    @staticmethod
    def create_seed_tables(engine, schema: str = 'lfcddemo', 
                          table_count_per_type: int = 2,
                          rows_per_table: int = 5,
                          secrets_json: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create and populate seed tables for testing (shared by SimpleDB and SimpleConn)
        
        This is a shared utility method that creates standard test tables with initial data.
        It's used by both SimpleDB and SimpleConn to ensure consistent seeding behavior.
        
        Args:
            engine: SQLAlchemy engine for database connection
            schema: Schema name for tables (default: 'lfcddemo')
            table_count_per_type: Number of tables to create per type (default: 2)
            rows_per_table: Number of rows to insert per table (default: 5)
            secrets_json: Optional secrets for CDC/CT integration
            
        Returns:
            dict: Results of seed table creation with status and details
        """
        from .SimpleDDL import SimpleDDL
        from .SimpleDML import SimpleDML
        
        result = {
            'status': 'success',
            'tables_created': 0,
            'rows_inserted': 0,
            'table_names': [],
            'errors': []
        }
        
        try:
            print(f"\n🌱 Creating seed tables in schema '{schema}'...")
            
            # Initialize SimpleDDL for table creation
            ddl = SimpleDDL(
                engine=engine,
                schema=schema,
                enable_cdc=False,  # CDC will be enabled later if needed
                enable_lfc=False,
                secrets_json=secrets_json
            )
            
            # Create intpk and dtix tables
            created_tables = ddl.create_test_tables(
                base_names=['intpk', 'dtix'],
                count_per_type=table_count_per_type,
                force_recreate=False
            )
            
            result['tables_created'] = len(created_tables)
            result['table_names'] = list(created_tables.keys())
            
            print(f"✅ Created {len(created_tables)} seed tables:")
            for table_name in created_tables.keys():
                print(f"   - {table_name}")
            
            # Populate seed tables with initial data
            print(f"\n📊 Populating seed tables with initial data...")
            dml = SimpleDML(engine=engine, config={'source_schema': schema})
            
            # Insert rows into each table
            for table_name in created_tables.keys():
                try:
                    # Execute multiple insert operations to populate with desired row count
                    total_inserted = 0
                    for _ in range(rows_per_table):
                        insert_result = dml.execute_insert(table_name=table_name)
                        total_inserted += insert_result.get('rows_affected', 0)
                    
                    result['rows_inserted'] += total_inserted
                    print(f"   ✅ {table_name}: {total_inserted} rows inserted")
                except Exception as e:
                    error_msg = f"Failed to insert rows into {table_name}: {str(e)}"
                    result['errors'].append(error_msg)
                    print(f"   ⚠️ {table_name}: {e}")
            
            if result['errors']:
                result['status'] = 'partial'
                result['message'] = f"Created {result['tables_created']} tables but encountered {len(result['errors'])} errors during population"
            else:
                result['message'] = f"Successfully created {result['tables_created']} seed tables with {result['rows_inserted']} total rows"
                print(f"✅ Seed tables populated with {result['rows_inserted']} total rows")
            
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f"Failed to create seed tables: {str(e)}"
            result['errors'].append(str(e))
            print(f"⚠️  Failed to create seed tables: {e}")
            print(f"   Database is ready but without seed data")
            import traceback
            traceback.print_exc()
        
        return result
    
    def cleanup_resources(self):
        """Cleanup all created resources in LIFO order"""
        print(f"🧹 Starting cleanup of created resources...")
        
        cleanup_count = 0
        while not self.cleanup_queue.empty():
            try:
                cleanup_item = self.cleanup_queue.get()
                cleanup_type = cleanup_item[0]
                
                if cleanup_type == 'destroy_terraform':
                    db_details = cleanup_item[1]
                    print(f"🗑️ Destroying Terraform infrastructure...")
                    self._destroy_terraform(db_details['terraform_dir'])
                    
                elif cleanup_type == 'delete_connection':
                    connection_name = cleanup_item[1]
                    print(f"🗑️ Deleting Databricks connection '{connection_name}'...")
                    try:
                        self.workspace_client.connections.delete(connection_name)
                        print(f"✅ Connection '{connection_name}' deleted")
                    except Exception as e:
                        print(f"⚠️ Failed to delete connection '{connection_name}': {str(e)}")
                
                elif cleanup_type == 'delete_secret':
                    scope, key = cleanup_item[1], cleanup_item[2]
                    print(f"🗑️ Deleting secret '{key}' from scope '{scope}'...")
                    try:
                        self.workspace_client.secrets.delete_secret(scope=scope, key=key)
                        print(f"✅ Secret '{key}' deleted")
                    except Exception as e:
                        print(f"⚠️ Failed to delete secret '{key}': {str(e)}")
                
                elif cleanup_type == 'delete_secrets_scope':
                    scope = cleanup_item[1]
                    print(f"🗑️ Deleting secrets scope '{scope}'...")
                    try:
                        self.workspace_client.secrets.delete_scope(scope)
                        print(f"✅ Secrets scope '{scope}' deleted")
                    except Exception as e:
                        print(f"⚠️ Failed to delete secrets scope '{scope}': {str(e)}")
                
                cleanup_count += 1
                self.cleanup_queue.task_done()
                
            except Exception as e:
                print(f"❌ Error during cleanup: {str(e)}")
        
        print(f"✅ Cleanup completed. Processed {cleanup_count} items.")
    
    def _destroy_terraform(self, terraform_dir: str):
        """Destroy Terraform infrastructure"""
        try:
            print(f"🗑️ Destroying Terraform infrastructure in {terraform_dir}...")
            
            # Run terraform destroy
            result = subprocess.run(
                ['terraform', 'destroy', '-auto-approve'],
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                print(f"⚠️ Terraform destroy had issues:")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
            else:
                print(f"✅ Terraform infrastructure destroyed successfully")
            
            # Clean up terraform directory
            import shutil
            shutil.rmtree(terraform_dir, ignore_errors=True)
            print(f"🗑️ Terraform directory cleaned up")
            
        except Exception as e:
            print(f"❌ Failed to destroy Terraform infrastructure: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of SimpleDB instance
        
        Returns:
            dict: Current status and configuration
        """
        return {
            'connection_name': self.connection_name,
            'db_type': self.db_type,
            'cloud_provider': self.cloud_provider,
            'location': self.location,
            'terraform_dir': self.terraform_dir,
            'connection_created': self.connection_created,
            'secrets_created': self.secrets_created,
            'created_resources_count': len(self.created_resources),
            'cleanup_queue_size': self.cleanup_queue.qsize(),
            'created_resources': self.created_resources,
            'supported_db_types': self._cloud_provider.get_supported_database_types() if self._cloud_provider else [],
            'provider_name': self._cloud_provider.get_provider_name() if self._cloud_provider else None
        }


def create_database_if_connection_missing(workspace_client, config: Dict[str, Any], 
                                        connection_name: str = None,
                                        db_type: str = 'sqlserver',
                                        cloud_provider: str = 'azure',
                                        **kwargs) -> Dict[str, Any]:
    """Create database infrastructure if Databricks connection is missing
    
    Args:
        workspace_client: WorkspaceClient instance
        config: Configuration dictionary
        connection_name: Name of the connection to check/create
        db_type: Type of database to create ('sqlserver', 'mysql', 'postgresql', 'oracle')
        cloud_provider: Cloud provider to use ('azure', 'aws', 'gcp', 'oci')
        **kwargs: Additional cloud provider specific parameters
        
    Returns:
        dict: Results of the database creation process
    """
    print(f"🔍 Checking if {db_type} database connection is needed...")
    
    # Initialize SimpleDB
    simple_db = SimpleDB(
        workspace_client=workspace_client,
        config=config,
        db_type=db_type,
        cloud_provider=cloud_provider,
        connection_name=connection_name,
        **kwargs
    )
    
    # Check if connection exists
    if simple_db.check_connection_exists():
        return {
            'status': 'exists',
            'message': f"Connection '{simple_db.connection_name}' already exists",
            'connection_name': simple_db.connection_name,
            'simple_db': simple_db
        }
    
    # Create complete database setup
    print(f"🚀 Connection '{simple_db.connection_name}' not found. Creating {db_type} database infrastructure on {cloud_provider}...")
    setup_result = simple_db.create_complete_database_setup()
    setup_result['simple_db'] = simple_db
    
    return setup_result


# Note: SimpleDB has its own cleanup_resources() method that should be called
# to clean up created resources. No longer depends on DbxRest cleanup system.
