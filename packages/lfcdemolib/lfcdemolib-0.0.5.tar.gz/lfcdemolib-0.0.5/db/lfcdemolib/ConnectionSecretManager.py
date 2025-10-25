"""
Connection and Secret Manager

Handles Databricks connection and secret creation.
"""

from typing import Dict, Any

class ConnectionSecretManager:
    """Manages Databricks connection and secret creation"""
    
    def __init__(self, simple_test):
        self.simple_test = simple_test
    def test_connection_secret_creation(self, db_type: str = None, creds_file: str = None) -> Dict[str, Any]:
        """Test connection and secret creation for a database
        
        This is a reusable test that verifies:
        1. Loading credentials from local file
        2. Creating Databricks secret
        3. Creating Databricks connection
        4. Verifying the setup
        
        Args:
            db_type: Database type ('mysql', 'postgresql', 'sqlserver'). If None, auto-detect
            creds_file: Path to credentials file. If None, auto-find
            
        Returns:
            dict: Test results with status, connection info, and any errors
        """
        from .LfcConn import LfcConn
        from .LfcSecrets import LfcSecrets
        from .SimpleLocalCred import SimpleLocalCred
        
        results = {
            'status': 'running',
            'database_type': db_type or 'auto-detect',
            'steps': {},
            'connection_name': None,
            'secret_scope': None,
            'secret_key': None,
            'errors': [],
            'warnings': []
        }
        
        print("=" * 80)
        print(f"🧪 TEST: {'MySQL/PostgreSQL' if not db_type else db_type.upper()} Connection and Secret Creation")
        print("=" * 80)
        print()
        
        # Step 1: Load credentials
        print("📂 Step 1: Loading database credentials...")
        try:
            if creds_file:
                import json
                with open(creds_file, 'r') as f:
                    creds = json.load(f)
                print(f"✅ Loaded credentials from: {creds_file}")
            else:
                cred_manager = SimpleLocalCred()
                
                # Auto-find credentials by type
                if db_type:
                    creds_list = cred_manager.find_credentials(db_type=db_type, cloud='azure')
                else:
                    # Try MySQL first, then PostgreSQL
                    creds_list = cred_manager.find_credentials(db_type='mysql', cloud='azure')
                    if not creds_list:
                        creds_list = cred_manager.find_credentials(db_type='postgresql', cloud='azure')
                        db_type = 'postgresql'
                    else:
                        db_type = 'mysql'
                
                if not creds_list:
                    error_msg = f"No {db_type} credentials found in ~/.lfcddemo"
                    print(f"❌ {error_msg}")
                    results['status'] = 'error'
                    results['errors'].append(error_msg)
                    results['steps']['load_credentials'] = {'status': 'error', 'message': error_msg}
                    return results
                
                creds = creds_list[0]
                print(f"✅ Found credentials: {creds.get('_filename', 'unknown')}")
            
            # Try to use Pydantic model for cleaner credential handling
            from .LfcCredentialModel import LfcCredential
            from pydantic import ValidationError
            
            try:
                cred = LfcCredential.from_dict(creds)
                host_fqdn = cred.host_fqdn
                database = cred.catalog
                username = cred.user
                detected_db_type = cred.db_type
                cloud_provider = cred.cloud.provider
            except (ValidationError, Exception):
                # Fall back to manual extraction for backward compatibility
                host_fqdn = creds.get('host_fqdn', creds.get('host', 'unknown'))
                database = creds.get('catalog', creds.get('database', 'unknown'))
                username = creds.get('user', creds.get('username', 'unknown'))
                detected_db_type = creds.get('db_type', db_type)
                
                # Extract cloud provider from either format
                cloud_provider = creds.get('cloud_provider')
                if not cloud_provider:
                    cloud_obj = creds.get('cloud', {})
                    cloud_provider = cloud_obj.get('provider', 'unknown')
            
            print(f"\n📊 Database Info:")
            print(f"   Type: {detected_db_type}")
            print(f"   Cloud: {cloud_provider}")
            print(f"   Host: {host_fqdn}")
            print(f"   Database: {database}")
            print(f"   Schema: {creds.get('schema', 'lfcddemo')}")
            print(f"   User: {username}")
            print(f"   Replication Mode: {creds.get('replication_mode', 'auto')}")
            print(f"   Connection Name: {creds.get('connection_name', creds.get('name', 'unknown'))}")
            
            results['database_type'] = detected_db_type
            results['connection_name'] = creds.get('connection_name')
            results['steps']['load_credentials'] = {'status': 'success', 'filename': creds.get('_filename')}
            print()
            
        except Exception as e:
            error_msg = f"Failed to load credentials: {e}"
            print(f"❌ {error_msg}")
            results['status'] = 'error'
            results['errors'].append(error_msg)
            results['steps']['load_credentials'] = {'status': 'error', 'message': error_msg}
            return results
        
        # Step 2: Create Databricks Secret
        print("🔐 Step 2: Creating/Updating Databricks secret...")
        try:
            lfc_secrets = LfcSecrets(workspace_client=self.simple_test.workspace_client)
            
            # Determine default port based on database type
            default_port = 3306 if detected_db_type == 'mysql' else 5432
            default_replication = 'binlog' if detected_db_type == 'mysql' else 'logical'
            
            # Extract DBA credentials from v2 format
            dba_obj = creds.get('dba', {})
            dba_user = dba_obj.get('user', '')
            dba_password = dba_obj.get('password', '')
            
            # Extract cloud object from v2 format
            cloud_obj = creds.get('cloud', {})
            
            # Create secret config in v2 format
            secret_config = {
                'version': 'v2',
                'name': creds.get('name', ''),
                'host_fqdn': host_fqdn,
                'catalog': database,
                'user': username,
                'password': creds['password'],
                'dba': {
                    'user': dba_user,
                    'password': dba_password
                },
                'db_type': detected_db_type,
                'port': int(creds.get('port', default_port)),
                'schema': creds.get('schema', 'lfcddemo'),
                'replication_mode': creds.get('replication_mode', default_replication),
                'cloud': cloud_obj
            }
            
            print(f"   Creating secret for: {host_fqdn}")
            secret_result = lfc_secrets.create_secret(secret_config)
            
            if secret_result['status'] == 'success':
                print(f"✅ Secret created/updated successfully")
                print(f"   Scope: {secret_result.get('scope_name')}")
                print(f"   Key: {secret_result.get('secret_key')}")
                
                results['secret_scope'] = secret_result.get('scope_name')
                results['secret_key'] = secret_result.get('secret_key')
                results['steps']['create_secret'] = {
                    'status': 'success',
                    'scope': secret_result.get('scope_name'),
                    'key': secret_result.get('secret_key')
                }
            else:
                error_msg = f"Failed to create secret: {secret_result.get('message')}"
                print(f"❌ {error_msg}")
                results['status'] = 'error'
                results['errors'].append(error_msg)
                results['steps']['create_secret'] = {'status': 'error', 'message': error_msg}
                return results
            
            print()
            
        except Exception as e:
            error_msg = f"Error creating secret: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            results['status'] = 'error'
            results['errors'].append(error_msg)
            results['steps']['create_secret'] = {'status': 'error', 'message': error_msg}
            return results
        
        # Step 3: Create Databricks Connection
        print("🔗 Step 3: Creating/Updating Databricks connection...")
        try:
            lfc_conn = LfcConn(workspace_client=self.simple_test.workspace_client)
            
            # Determine default port based on database type
            default_port = 3306 if detected_db_type == 'mysql' else 5432
            default_replication = 'binlog' if detected_db_type == 'mysql' else 'logical'
            
            # Extract DBA credentials from v2 format
            dba_obj = creds.get('dba', {})
            dba_user = dba_obj.get('user', '')
            dba_password = dba_obj.get('password', '')
            
            # Extract cloud object from v2 format
            cloud_obj = creds.get('cloud', {})
            
            # Get connection_name from deployed array (not in secrets)
            connection_name = None
            deployed = creds.get('deployed', [])
            if deployed and len(deployed) > 0:
                connection_name = deployed[0].get('connection_name')
            
            # Create connection config in v2 format
            connection_config = {
                'version': 'v2',
                'name': creds.get('name', ''),
                'host_fqdn': host_fqdn,
                'catalog': database,
                'user': username,
                'password': creds['password'],
                'dba': {
                    'user': dba_user,
                    'password': dba_password
                },
                'db_type': detected_db_type,
                'port': int(creds.get('port', default_port)),
                'schema': creds.get('schema', 'lfcddemo'),
                'replication_mode': creds.get('replication_mode', default_replication),
                'cloud': cloud_obj,
                'connection_name': connection_name
            }
            
            print(f"   Creating connection: {creds.get('connection_name')}")
            connection_result = lfc_conn.create_connection(connection_config)
            
            if connection_result['status'] == 'success':
                print(f"✅ Connection created/updated successfully")
                print(f"   Connection Name: {connection_result.get('connection_name')}")
                
                results['steps']['create_connection'] = {
                    'status': 'success',
                    'connection_name': connection_result.get('connection_name')
                }
            else:
                error_msg = f"Failed to create connection: {connection_result.get('message')}"
                print(f"❌ {error_msg}")
                results['status'] = 'error'
                results['errors'].append(error_msg)
                results['steps']['create_connection'] = {'status': 'error', 'message': error_msg}
                return results
            
            print()
            
        except Exception as e:
            error_msg = f"Error creating connection: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            results['status'] = 'error'
            results['errors'].append(error_msg)
            results['steps']['create_connection'] = {'status': 'error', 'message': error_msg}
            return results
        
        # Step 4: Verify Setup
        print("✅ Step 4: Verifying setup...")
        verification_results = {'connection': False, 'secret': False}
        
        # Verify connection exists
        try:
            connection_name = creds.get('connection_name')
            conn_obj = self.simple_test.workspace_client.connections.get(connection_name)
            print(f"✅ Connection verified: {connection_name}")
            print(f"   Type: {conn_obj.connection_type}")
            print(f"   Host: {conn_obj.options.get('host', 'N/A')}")
            print(f"   Port: {conn_obj.options.get('port', 'N/A')}")
            verification_results['connection'] = True
        except Exception as e:
            warning_msg = f"Connection verification failed: {e}"
            print(f"⚠️  {warning_msg}")
            results['warnings'].append(warning_msg)
        
        # Verify secret exists
        try:
            secret_value = self.simple_test.workspace_client.secrets.get_secret(
                scope=results['secret_scope'],
                key=results['secret_key']
            )
            print(f"✅ Secret verified: {results['secret_scope']}/{results['secret_key']}")
            print(f"   Value length: {len(secret_value.value)} bytes")
            verification_results['secret'] = True
        except Exception as e:
            warning_msg = f"Secret verification failed: {e}"
            print(f"⚠️  {warning_msg}")
            results['warnings'].append(warning_msg)
        
        results['steps']['verification'] = {
            'status': 'success' if all(verification_results.values()) else 'partial',
            'connection_verified': verification_results['connection'],
            'secret_verified': verification_results['secret']
        }
        print()
        
        # Final Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        if results['errors']:
            results['status'] = 'error'
            print("❌ TEST FAILED")
            for error in results['errors']:
                print(f"   ERROR: {error}")
        elif results['warnings']:
            results['status'] = 'success_with_warnings'
            print("⚠️  TEST PASSED WITH WARNINGS")
            for warning in results['warnings']:
                print(f"   WARNING: {warning}")
        else:
            results['status'] = 'success'
            print("✅ TEST PASSED")
        
        print(f"\n📋 Results:")
        print(f"   Database Type: {results['database_type']}")
        print(f"   Connection Name: {results['connection_name']}")
        print(f"   Secret Scope: {results['secret_scope']}")
        print(f"   Secret Key: {results['secret_key']}")
        print(f"   Status: {results['status']}")
        print("=" * 80)
        
        return results




