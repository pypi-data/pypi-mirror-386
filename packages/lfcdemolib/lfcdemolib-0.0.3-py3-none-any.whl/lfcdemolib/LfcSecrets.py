"""
LfcSecrets.py - Lakeflow Connect Databricks Secrets Management

This module manages Databricks secret scopes and secrets for database credentials.
It works in conjunction with LfcConn.py to provide complete Databricks integration.

Key Features:
- Automatic secret scope creation (robert_lee)
- Database credential storage with structured format
- Secret key naming based on database FQDN
- Integration with LfcConn for connection metadata
- Support for all database types and cloud providers
- Uses Databricks Python SDK for API interactions
"""

import json
from typing import Dict, Any, Optional, List

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.workspace import CreateScope, ScopeBackendType
except ImportError:
    WorkspaceClient = None
    CreateScope = None
    ScopeBackendType = None

from .LfcEnv import LfcEnv


class LfcSecrets:
    """Manages Databricks secret scopes and secrets for LFC demo databases"""
    
    def __init__(self, workspace_client: Optional[WorkspaceClient] = None, lfc_env: Optional[LfcEnv] = None, scope_name: Optional[str] = None):
        """Initialize LfcSecrets with optional Databricks WorkspaceClient
        
        Args:
            workspace_client: Optional WorkspaceClient instance. If None, secrets won't be created.
            lfc_env: Optional LfcEnv instance for user information. If None, creates new instance.
            scope_name: Optional custom scope name. If None, uses firstname_lastname from lfc_env.
        """
        self.workspace_client = workspace_client
        self.lfc_env = lfc_env or LfcEnv(workspace_client)
        self.scope_name = scope_name if scope_name is not None else self.lfc_env.get_scope_name()
        
    def _create_secret_scope(self) -> Dict[str, Any]:
        """Create the secret scope if it doesn't exist
        
        Returns:
            dict: Result of scope creation
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available.'
            }
        
        try:
            # Check if scope already exists
            existing_scopes = list(self.workspace_client.secrets.list_scopes())
            existing_scope_names = [scope.name for scope in existing_scopes]
            
            if self.scope_name in existing_scope_names:
                print(f"✅ Secret scope '{self.scope_name}' already exists")
                return {
                    'status': 'exists',
                    'message': f"Secret scope '{self.scope_name}' already exists",
                    'scope_name': self.scope_name
                }
            
            # Create the scope using Databricks SDK
            print(f"🔐 Creating secret scope: {self.scope_name}")
            
            if CreateScope and ScopeBackendType:
                create_scope_request = CreateScope(
                    scope=self.scope_name,
                    backend_type=ScopeBackendType.DATABRICKS
                )
                self.workspace_client.secrets.create_scope(create_scope_request)
            else:
                # Fallback method
                self.workspace_client.secrets.create_scope(scope=self.scope_name)
            
            print(f"✅ Secret scope created successfully: {self.scope_name}")
            return {
                'status': 'success',
                'message': f'Secret scope created: {self.scope_name}',
                'scope_name': self.scope_name
            }
                
        except Exception as e:
            error_msg = str(e)
            if 'max limit' in error_msg.lower():
                # Handle scope limit by trying to use an existing scope
                print(f"⚠️ Scope limit reached, checking for existing compatible scope...")
                try:
                    # Look for any scope that starts with our username
                    username_scopes = [scope.name for scope in existing_scopes 
                                     if scope.name.startswith(self.lfc_env.get_firstname_lastname())]
                    
                    if username_scopes:
                        # Use the first compatible scope
                        compatible_scope = username_scopes[0]
                        print(f"✅ Using existing compatible scope: {compatible_scope}")
                        # Update our scope name to use the existing one
                        self.scope_name = compatible_scope
                        return {
                            'status': 'exists',
                            'message': f'Using existing compatible scope: {compatible_scope}',
                            'scope_name': compatible_scope
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'Scope limit reached and no compatible existing scope found: {error_msg}',
                            'scope_name': None
                        }
                except Exception as fallback_error:
                    return {
                        'status': 'error',
                        'message': f'Scope limit reached and could not find fallback: {fallback_error}',
                        'scope_name': None
                    }
            else:
                error_msg = f"Error creating secret scope: {error_msg}"
                print(f"❌ {error_msg}")
                return {
                    'status': 'error',
                    'message': error_msg,
                    'scope_name': self.scope_name
                }
    
    def _get_database_region(self, db_config: Dict[str, Any]) -> str:
        """Get the actual region where the database is located
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            str: Database region
        """
        # First check if region is explicitly provided
        region = db_config.get('region') or db_config.get('location')
        if region:
            return region
            
        # Try to get region from resource group using Azure CLI
        resource_group = db_config.get('resource_group')
        if resource_group:
            try:
                import subprocess
                result = subprocess.run(
                    ['az', 'group', 'show', '--name', resource_group, '--query', 'location', '-o', 'tsv'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    azure_region = result.stdout.strip()
                    # Convert Azure region format to readable format
                    region_mapping = {
                        'centralus': 'Central US',
                        'eastus': 'East US',
                        'eastus2': 'East US 2',
                        'westus': 'West US',
                        'westus2': 'West US 2',
                        'westus3': 'West US 3',
                        'northcentralus': 'North Central US',
                        'southcentralus': 'South Central US',
                        'westcentralus': 'West Central US',
                        'canadacentral': 'Canada Central',
                        'canadaeast': 'Canada East',
                        'brazilsouth': 'Brazil South',
                        'northeurope': 'North Europe',
                        'westeurope': 'West Europe',
                        'uksouth': 'UK South',
                        'ukwest': 'UK West',
                        'francecentral': 'France Central',
                        'germanywestcentral': 'Germany West Central',
                        'norwayeast': 'Norway East',
                        'switzerlandnorth': 'Switzerland North',
                        'southeastasia': 'Southeast Asia',
                        'eastasia': 'East Asia',
                        'australiaeast': 'Australia East',
                        'australiasoutheast': 'Australia Southeast',
                        'japaneast': 'Japan East',
                        'japanwest': 'Japan West',
                        'koreacentral': 'Korea Central',
                        'koreasouth': 'Korea South',
                        'southindia': 'South India',
                        'centralindia': 'Central India',
                        'westindia': 'West India'
                    }
                    return region_mapping.get(azure_region.lower(), azure_region.title())
            except Exception:
                pass  # Fall through to default
        
        # Default fallback - use Central US as it's commonly used
        return 'Central US'
    
    def _create_secret_value(self, db_config: Dict[str, Any]) -> str:
        """Create structured secret value for database credentials in v2 format
        
        Args:
            db_config: Database configuration dictionary in v2 format
            
        Returns:
            str: JSON formatted secret value (v2 format without 'deployed' field)
        """
        # Create a copy of db_config to avoid modifying the original
        secret_data = db_config.copy()
        
        # Remove fields that shouldn't be in the secret value
        # - 'deployed' is deployment tracking metadata (not in secret)
        # - 'scope_name' is for LfcSecrets processing only (not stored in secret)
        # - 'connection_name' is for LfcConn processing only (not stored in secret)
        secret_data.pop('deployed', None)
        secret_data.pop('scope_name', None)
        secret_data.pop('connection_name', None)
        
        # Ensure version is set to v2
        secret_data['version'] = 'v2'
        
        # Convert to JSON format with consistent formatting
        return json.dumps(secret_data, indent=2, sort_keys=False)
    
    def create_secret(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Databricks secret for database credentials
        
        Args:
            db_config: Database configuration dictionary in v2 format containing:
                - version: Format version (v2)
                - name: Original cloud name/identifier
                - host_fqdn: Fully qualified domain name or IP
                - catalog: Database/catalog name
                - user: Database user
                - password: User password
                - dba: DBA credentials object
                - db_type: Database type (sqlserver, mysql, postgresql)
                - port: Database port
                - schema: Schema name
                - replication_mode: Replication mode
                - cloud: Cloud information object
                
        Returns:
            dict: Result of secret creation
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available. Secret not created.',
                'secret_key': None
            }
        
        try:
            # Ensure scope exists
            scope_result = self._create_secret_scope()
            if scope_result['status'] == 'error':
                return scope_result
            
            # Extract secret key (database FQDN with _json suffix)
            host_fqdn = db_config.get('host_fqdn', '')
            secret_key = f"{host_fqdn}_json"
            
            if not secret_key or not host_fqdn:
                return {
                    'status': 'error',
                    'message': 'No host_fqdn found in database configuration',
                    'secret_key': None
                }
            
            # Create secret value (v2 format without 'deployed' field)
            secret_value = self._create_secret_value(db_config)
            
            print(f"🔐 Creating secret: {self.scope_name}/{secret_key}")
            print(f"   Database: {db_config.get('db_type', 'unknown')} - {db_config.get('catalog', 'unknown')}")
            
            # Create the secret using Databricks SDK
            self.workspace_client.secrets.put_secret(
                scope=self.scope_name,
                key=secret_key,
                string_value=secret_value
            )
            
            print(f"✅ Secret created successfully: {self.scope_name}/{secret_key}")
            return {
                'status': 'success',
                'message': f'Secret created: {self.scope_name}/{secret_key}',
                'scope_name': self.scope_name,
                'secret_key': secret_key,
                'secret_preview': secret_value[:200] + '...' if len(secret_value) > 200 else secret_value
            }
                
        except Exception as e:
            error_msg = f"Error creating secret: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'secret_key': None
            }
    
    def delete_secret(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Delete Databricks secret for database credentials
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            dict: Result of secret deletion
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available. Secret not deleted.',
                'secret_key': None
            }
        
        try:
            # Extract secret key (database FQDN with _json suffix)
            host_fqdn = db_config.get('host_fqdn', db_config.get('host', ''))
            secret_key = f"{host_fqdn}_json"
            
            if not secret_key:
                return {
                    'status': 'error',
                    'message': 'No host_fqdn found in database configuration',
                    'secret_key': None
                }
            
            print(f"🗑️  Deleting secret: {self.scope_name}/{secret_key}")
            
            # Delete the secret using Databricks SDK
            self.workspace_client.secrets.delete_secret(
                scope=self.scope_name,
                key=secret_key
            )
            
            print(f"✅ Secret deleted successfully: {self.scope_name}/{secret_key}")
            return {
                'status': 'success',
                'message': f'Secret deleted: {self.scope_name}/{secret_key}',
                'scope_name': self.scope_name,
                'secret_key': secret_key
            }
                
        except Exception as e:
            error_msg = f"Error deleting secret: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'secret_key': None
            }
    
    def list_secrets(self) -> Dict[str, Any]:
        """List secrets in the robert_lee scope
        
        Returns:
            dict: List of secrets
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available.',
                'secrets': []
            }
        
        try:
            print(f"📋 Listing secrets in scope: {self.scope_name}")
            
            # List secrets in scope using Databricks SDK
            secret_list = list(self.workspace_client.secrets.list_secrets(scope=self.scope_name))
            
            # Convert to dict format for compatibility
            secrets = []
            for secret in secret_list:
                secret_dict = {
                    'key': secret.key,
                    'last_updated_timestamp': secret.last_updated_timestamp
                }
                secrets.append(secret_dict)
            
            print(f"✅ Found {len(secrets)} secrets in scope '{self.scope_name}'")
            return {
                'status': 'success',
                'message': f'Found {len(secrets)} secrets',
                'scope_name': self.scope_name,
                'secrets': secrets
            }
                
        except Exception as e:
            error_msg = f"Error listing secrets: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'scope_name': self.scope_name,
                'secrets': []
            }
    
    def get_secret_value(self, secret_key: str) -> Dict[str, Any]:
        """Get secret value for verification
        
        Args:
            secret_key: Secret key (database FQDN, _json suffix will be added automatically)
            
        Returns:
            dict: Secret value and metadata
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available.',
                'secret_value': None
            }
        
        try:
            # Add _json suffix if not already present
            if not secret_key.endswith('_json'):
                secret_key_with_suffix = f"{secret_key}_json"
            else:
                secret_key_with_suffix = secret_key
            
            print(f"🔍 Getting secret value: {self.scope_name}/{secret_key_with_suffix}")
            
            # Get secret value using Databricks SDK
            secret_value = self.workspace_client.secrets.get_secret(
                scope=self.scope_name,
                key=secret_key_with_suffix
            ).value
            
            print(f"✅ Retrieved secret value ({len(secret_value)} characters)")
            
            # Decode base64 secret value (Databricks automatically base64 encodes secrets)
            import base64
            try:
                decoded_value = base64.b64decode(secret_value).decode('utf-8')
                print(f"   🔓 Base64 decoded secret")
            except Exception:
                # If base64 decoding fails, use raw value
                decoded_value = secret_value
                print(f"   ⚠️ Using raw secret value (no base64 decoding)")
            
            # Try to parse as JSON
            try:
                parsed_value = json.loads(decoded_value)
                return {
                    'status': 'success',
                    'message': f'Secret retrieved: {self.scope_name}/{secret_key_with_suffix}',
                    'scope_name': self.scope_name,
                    'secret_key': secret_key_with_suffix,
                    'secret_value': decoded_value,
                    'parsed_value': parsed_value
                }
            except json.JSONDecodeError:
                return {
                    'status': 'success',
                    'message': f'Secret retrieved (not JSON): {self.scope_name}/{secret_key_with_suffix}',
                    'scope_name': self.scope_name,
                    'secret_key': secret_key_with_suffix,
                    'secret_value': decoded_value,
                    'parsed_value': None
                }
                
        except Exception as e:
            error_msg = f"Error getting secret: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'scope_name': self.scope_name,
                'secret_key': secret_key_with_suffix if 'secret_key_with_suffix' in locals() else secret_key,
                'secret_value': None
            }
    
    def create_secrets_for_existing_databases(self, database_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create Databricks secrets for existing databases
        
        Args:
            database_configs: List of database configuration dictionaries
            
        Returns:
            dict: Summary of secret creation results
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available.',
                'results': []
            }
        
        print(f"🔐 Creating Databricks secrets for {len(database_configs)} existing databases...")
        
        results = []
        success_count = 0
        error_count = 0
        
        for i, db_config in enumerate(database_configs, 1):
            print(f"\n📊 Processing database {i}/{len(database_configs)}")
            
            result = self.create_secret(db_config)
            results.append(result)
            
            if result.get('status') == 'success':
                success_count += 1
            else:
                error_count += 1
        
        print(f"\n📊 SECRET CREATION SUMMARY:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {error_count}")
        print(f"   📊 Total: {len(database_configs)}")
        
        return {
            'status': 'completed',
            'message': f'Created secrets for {success_count}/{len(database_configs)} databases',
            'success_count': success_count,
            'error_count': error_count,
            'total_count': len(database_configs),
            'results': results
        }
    
    def verify_secret_connection_integration(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that secret and connection are properly integrated
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            dict: Verification results
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available for verification.'
            }
        
        try:
            host_fqdn = db_config.get('host_fqdn', db_config.get('host', ''))
            secret_key = f"{host_fqdn}_json"
            
            print(f"🔍 VERIFYING SECRET-CONNECTION INTEGRATION")
            print(f"   Database: {db_config.get('type', 'unknown')} - {db_config.get('database', 'unknown')}")
            print(f"   Host FQDN: {host_fqdn}")
            
            # 1. Verify secret exists and get value
            secret_result = self.get_secret_value(secret_key)
            if secret_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f"Secret verification failed: {secret_result['message']}",
                    'secret_key': secret_key
                }
            
            # 2. Verify connection exists (using LfcConn naming convention)
            from .LfcConn import LfcConn
            lfc_conn = LfcConn(self.workspace_client, lfc_env=self.lfc_env)
            connection_name = lfc_conn.get_connection_name(db_config)
            
            connections_result = lfc_conn.list_connections(filter_prefix=True)
            if connections_result['status'] == 'success':
                connection_names = [conn.get('name') for conn in connections_result['connections']]
                connection_exists = connection_name in connection_names
            else:
                connection_exists = False
            
            # 3. Parse secret value
            parsed_secret = secret_result.get('parsed_value', {})
            
            # 4. Verification summary
            verification_results = {
                'secret_exists': secret_result['status'] == 'success',
                'connection_exists': connection_exists,
                'secret_key': secret_key,
                'connection_name': connection_name,
                'secret_scope': self.scope_name,
                'secret_content': parsed_secret,
                'integration_valid': secret_result['status'] == 'success' and connection_exists
            }
            
            print(f"\n📊 VERIFICATION RESULTS:")
            print(f"   🔐 Secret exists: {'✅' if verification_results['secret_exists'] else '❌'}")
            print(f"   🔗 Connection exists: {'✅' if verification_results['connection_exists'] else '❌'}")
            print(f"   🔗 Integration valid: {'✅' if verification_results['integration_valid'] else '❌'}")
            
            if parsed_secret:
                print(f"\n📋 SECRET CONTENT VERIFICATION:")
                print(f"   Connection Type: {parsed_secret.get('connection_type', 'N/A')}")
                print(f"   Catalog: {parsed_secret.get('catalog', 'N/A')}")
                print(f"   Schema: {parsed_secret.get('schema', 'N/A')}")
                print(f"   Host FQDN: {parsed_secret.get('host_fqdn', 'N/A')}")
                print(f"   Port: {parsed_secret.get('port', 'N/A')}")
                print(f"   User: {parsed_secret.get('user', 'N/A')}")
                cloud_info = parsed_secret.get('cloud', {})
                print(f"   Cloud Provider: {cloud_info.get('provider', 'N/A')}")
                print(f"   Cloud Region: {cloud_info.get('region', 'N/A')}")
            
            return {
                'status': 'success',
                'message': 'Verification completed',
                'verification': verification_results
            }
            
        except Exception as e:
            error_msg = f"Error during verification: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def migrate_secrets_to_json_suffix(self) -> Dict[str, Any]:
        """Migrate existing secrets to use _json suffix
        
        This method:
        1. Lists all secrets in the scope
        2. For secrets without _json suffix, creates new secret with _json suffix
        3. Optionally deletes old secrets (with confirmation)
        
        Returns:
            dict: Migration results
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available for migration.'
            }
        
        try:
            print(f"🔄 MIGRATING SECRETS TO _JSON SUFFIX")
            print(f"   Scope: {self.scope_name}")
            print("=" * 60)
            
            # List all secrets in scope
            secrets_list = self.workspace_client.secrets.list_secrets(self.scope_name)
            
            migration_results = {
                'total_secrets': 0,
                'migrated_secrets': 0,
                'skipped_secrets': 0,
                'errors': [],
                'migrated_keys': [],
                'skipped_keys': []
            }
            
            for secret in secrets_list:
                secret_key = secret.key
                migration_results['total_secrets'] += 1
                
                print(f"\n🔍 Processing secret: {secret_key}")
                
                # Skip if already has _json suffix
                if secret_key.endswith('_json'):
                    print(f"   ✅ Already has _json suffix - skipping")
                    migration_results['skipped_secrets'] += 1
                    migration_results['skipped_keys'].append(secret_key)
                    continue
                
                # Check if this looks like a database FQDN
                if not ('.' in secret_key and any(suffix in secret_key for suffix in ['.database.windows.net', '.mysql.database.azure.com', '.postgres.database.azure.com'])):
                    print(f"   ⚠️ Doesn't look like database FQDN - skipping")
                    migration_results['skipped_secrets'] += 1
                    migration_results['skipped_keys'].append(secret_key)
                    continue
                
                try:
                    # Get existing secret value
                    print(f"   📥 Reading existing secret value...")
                    existing_secret = self.workspace_client.secrets.get_secret(
                        scope=self.scope_name,
                        key=secret_key
                    )
                    
                    # Create new secret with _json suffix
                    new_secret_key = f"{secret_key}_json"
                    print(f"   📤 Creating new secret: {new_secret_key}")
                    
                    # Check if new secret already exists
                    try:
                        self.workspace_client.secrets.get_secret(
                            scope=self.scope_name,
                            key=new_secret_key
                        )
                        print(f"   ⚠️ New secret already exists - skipping migration")
                        migration_results['skipped_secrets'] += 1
                        migration_results['skipped_keys'].append(secret_key)
                        continue
                    except Exception:
                        # New secret doesn't exist, proceed with creation
                        pass
                    
                    # Create new secret with same value
                    self.workspace_client.secrets.put_secret(
                        scope=self.scope_name,
                        key=new_secret_key,
                        string_value=existing_secret.value
                    )
                    
                    print(f"   ✅ Successfully migrated to: {new_secret_key}")
                    migration_results['migrated_secrets'] += 1
                    migration_results['migrated_keys'].append({
                        'old_key': secret_key,
                        'new_key': new_secret_key
                    })
                    
                except Exception as e:
                    error_msg = f"Failed to migrate {secret_key}: {str(e)}"
                    print(f"   ❌ {error_msg}")
                    migration_results['errors'].append(error_msg)
            
            print(f"\n📊 MIGRATION SUMMARY")
            print("=" * 40)
            print(f"   Total secrets processed: {migration_results['total_secrets']}")
            print(f"   Successfully migrated: {migration_results['migrated_secrets']}")
            print(f"   Skipped: {migration_results['skipped_secrets']}")
            print(f"   Errors: {len(migration_results['errors'])}")
            
            if migration_results['migrated_keys']:
                print(f"\n✅ MIGRATED SECRETS:")
                for migration in migration_results['migrated_keys']:
                    print(f"   {migration['old_key']} → {migration['new_key']}")
            
            if migration_results['errors']:
                print(f"\n❌ ERRORS:")
                for error in migration_results['errors']:
                    print(f"   {error}")
            
            return {
                'status': 'success',
                'message': f'Migration completed: {migration_results["migrated_secrets"]} secrets migrated',
                'results': migration_results
            }
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'results': None
            }
    
    def cleanup_old_secrets(self, confirm_deletion: bool = False) -> Dict[str, Any]:
        """Clean up old secrets (without _json suffix) after successful migration
        
        Args:
            confirm_deletion: If True, actually delete the old secrets
            
        Returns:
            dict: Cleanup results
        """
        if not self.workspace_client:
            return {
                'status': 'skipped',
                'message': 'No Databricks WorkspaceClient available for cleanup.'
            }
        
        try:
            print(f"🧹 CLEANING UP OLD SECRETS")
            print(f"   Scope: {self.scope_name}")
            print(f"   Confirm deletion: {confirm_deletion}")
            print("=" * 60)
            
            # List all secrets in scope
            secrets_list = self.workspace_client.secrets.list_secrets(self.scope_name)
            
            cleanup_results = {
                'total_secrets': 0,
                'candidates_for_deletion': 0,
                'deleted_secrets': 0,
                'errors': [],
                'deleted_keys': [],
                'candidate_keys': []
            }
            
            for secret in secrets_list:
                secret_key = secret.key
                cleanup_results['total_secrets'] += 1
                
                # Skip if already has _json suffix
                if secret_key.endswith('_json'):
                    continue
                
                # Check if this looks like a database FQDN and has corresponding _json version
                if '.' in secret_key and any(suffix in secret_key for suffix in ['.database.windows.net', '.mysql.database.azure.com', '.postgres.database.azure.com']):
                    json_key = f"{secret_key}_json"
                    
                    try:
                        # Check if _json version exists
                        self.workspace_client.secrets.get_secret(
                            scope=self.scope_name,
                            key=json_key
                        )
                        
                        # _json version exists, this is a candidate for deletion
                        cleanup_results['candidates_for_deletion'] += 1
                        cleanup_results['candidate_keys'].append(secret_key)
                        
                        print(f"🗑️  Candidate for deletion: {secret_key} (has {json_key})")
                        
                        if confirm_deletion:
                            try:
                                self.workspace_client.secrets.delete_secret(
                                    scope=self.scope_name,
                                    key=secret_key
                                )
                                print(f"   ✅ Deleted: {secret_key}")
                                cleanup_results['deleted_secrets'] += 1
                                cleanup_results['deleted_keys'].append(secret_key)
                            except Exception as e:
                                error_msg = f"Failed to delete {secret_key}: {str(e)}"
                                print(f"   ❌ {error_msg}")
                                cleanup_results['errors'].append(error_msg)
                        else:
                            print(f"   ℹ️ Would delete (dry run): {secret_key}")
                    
                    except Exception:
                        # _json version doesn't exist, keep the old one
                        print(f"ℹ️  Keeping: {secret_key} (no _json version found)")
            
            print(f"\n📊 CLEANUP SUMMARY")
            print("=" * 40)
            print(f"   Total secrets: {cleanup_results['total_secrets']}")
            print(f"   Candidates for deletion: {cleanup_results['candidates_for_deletion']}")
            if confirm_deletion:
                print(f"   Actually deleted: {cleanup_results['deleted_secrets']}")
                print(f"   Errors: {len(cleanup_results['errors'])}")
            else:
                print(f"   DRY RUN - No secrets were deleted")
            
            return {
                'status': 'success',
                'message': f'Cleanup completed: {cleanup_results["deleted_secrets"]} secrets deleted' if confirm_deletion else 'Dry run completed',
                'results': cleanup_results
            }
            
        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'results': None
            }
