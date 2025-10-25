"""
Database Setup Validator

Comprehensive validation of database setup for Lakeflow Connect.
"""

import sqlalchemy as sa
from typing import Dict, Any

class DatabaseSetupValidator:
    """Validates complete database setup for Lakeflow Connect"""
    
    def __init__(self, simple_test):
        self.simple_test = simple_test
    def test_database_permissions(self) -> Dict[str, Any]:
        """Comprehensive database setup verification test
        
        Tests after database creation or recreation:
        1. User and DBA access to catalog and master databases
        2. Schema exists and is accessible
        3. Seed tables exist and have data
        4. Database is set up for Lakeflow Connect
        5. Connection, secrets, and local credentials exist and values match
        6. Resources are not automatically deleted (for persistent databases)
        
        Returns:
            dict: Comprehensive test results with detailed validation
        """
        print("\n" + "=" * 80)
        print("🔐 COMPREHENSIVE DATABASE SETUP TEST")
        print("=" * 80)
        print("Verifying complete database setup for Lakeflow Connect")
        print()
        
        results = {
            'status': 'pending',
            'user_access': None,
            'dba_access': None,
            'schema_exists': None,
            'seed_tables': None,
            'lakeflow_connect_setup': None,
            'connection_exists': None,
            'secrets_exist': None,
            'local_credentials': None,
            'values_match': None,
            'auto_cleanup_disabled': None,
            'correct_setup': False
        }
        
        # Only test for SQL Server
        db_type = self.simple_test._get_config_value('type')
        if db_type != 'sqlserver':
            results['status'] = 'skipped'
            results['message'] = f'Comprehensive test only applicable to SQL Server (current: {db_type})'
            print(f"ℹ️  Skipped: Test only applicable to SQL Server")
            return results
        
        if not self.simple_test._secrets_json:
            results['status'] = 'error'
            results['message'] = 'No secrets_json available for testing'
            print(f"❌ Error: No secrets available")
            return results
        
        user = self.simple_test._secrets_json.get('user')
        dba_user = self.simple_test._secrets_json.get('dba', {}).get('user')  # v2 format: dba.user
        catalog = self.simple_test._secrets_json.get('catalog')
        schema = self.simple_test._get_schema_with_warning()
        host_fqdn = self.simple_test._secrets_json.get('host_fqdn')
        
        print(f"Database: {catalog}")
        print(f"Schema: {schema}")
        print(f"User: {user}")
        print(f"DBA User: {dba_user}")
        print(f"Host: {host_fqdn}")
        print()
        
        try:
            from .SimpleSqlalchemy import SimpleSqlalchemy
            from .SimpleLocalCred import SimpleLocalCred
            from .LfcConn import LfcConn
            from .LfcSecrets import LfcSecrets
            from sqlalchemy import text, inspect
            
            # Test 1: User access to catalog and master
            print(f"📊 Test 1: User Access (Catalog & Master)")
            user_access_results = {'catalog': None, 'master': None}
            
            try:
                # Catalog access
                catalog_engine = SimpleSqlalchemy.create_engine_from_secrets(self.simple_test._secrets_json)
                with catalog_engine.connect() as conn:
                    result = conn.execute(text("SELECT DB_NAME(), USER_NAME()"))
                    db, usr = result.fetchone()
                    user_access_results['catalog'] = {'status': 'success', 'database': db, 'user': usr}
                    print(f"   ✅ Catalog: Connected to '{db}' as '{usr}'")
                catalog_engine.dispose()
            except Exception as e:
                user_access_results['catalog'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Catalog: {e}")
            
            try:
                # Master access (required for Lakeflow Connect)
                master_secrets = dict(self.simple_test._secrets_json)
                master_secrets['catalog'] = 'master'
                master_engine = SimpleSqlalchemy.create_engine_from_secrets(master_secrets)
                with master_engine.connect() as conn:
                    result = conn.execute(text("SELECT DB_NAME(), USER_NAME()"))
                    db, usr = result.fetchone()
                    user_access_results['master'] = {'status': 'success', 'database': db, 'user': usr}
                    print(f"   ✅ Master: Connected to '{db}' as '{usr}'")
                master_engine.dispose()
            except Exception as e:
                user_access_results['master'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Master: Login failed - LFC requirement not met")
            
            results['user_access'] = user_access_results
            
            # Test 2: DBA access to catalog and master
            print(f"\n📊 Test 2: DBA Access (Catalog & Master)")
            dba_access_results = {'catalog': None, 'master': None}
            
            try:
                # DBA catalog access
                dba_engine = SimpleSqlalchemy.create_dba_engine(self.simple_test._secrets_json, target_database=catalog)
                with dba_engine.connect() as conn:
                    result = conn.execute(text("SELECT DB_NAME(), USER_NAME()"))
                    db, usr = result.fetchone()
                    dba_access_results['catalog'] = {'status': 'success', 'database': db, 'user': usr}
                    print(f"   ✅ Catalog: Connected to '{db}' as '{usr}'")
                dba_engine.dispose()
            except Exception as e:
                dba_access_results['catalog'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Catalog: {e}")
            
            try:
                # DBA master access
                dba_master_engine = SimpleSqlalchemy.create_dba_engine(self.simple_test._secrets_json, target_database='master')
                with dba_master_engine.connect() as conn:
                    result = conn.execute(text("SELECT DB_NAME(), USER_NAME()"))
                    db, usr = result.fetchone()
                    dba_access_results['master'] = {'status': 'success', 'database': db, 'user': usr}
                    print(f"   ✅ Master: Connected to '{db}' as '{usr}'")
                dba_master_engine.dispose()
            except Exception as e:
                dba_access_results['master'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Master: {e}")
            
            results['dba_access'] = dba_access_results
            
            # Test 3: Schema exists and ownership
            print(f"\n📊 Test 3: Schema Existence and Ownership")
            try:
                with self.simple_test.engine.connect() as conn:
                    # Check if schema exists and get owner
                    check_schema = text(f"""
                        SELECT 
                            s.name as schema_name,
                            USER_NAME(s.principal_id) as owner
                        FROM sys.schemas s
                        WHERE s.name = :schema_name
                    """)
                    result = conn.execute(check_schema, {'schema_name': schema})
                    schema_row = result.fetchone()
                    
                    if schema_row:
                        schema_name, schema_owner = schema_row
                        # Check if user owns the schema
                        owns_schema = (schema_owner == user or schema_owner == 'dbo')
                        ownership_icon = "👤" if schema_owner == user else "🔧" if schema_owner == 'dbo' else "⚠️"
                        
                        results['schema_exists'] = {
                            'status': 'success', 
                            'schema': schema,
                            'owner': schema_owner,
                            'user_owns': owns_schema
                        }
                        print(f"   ✅ Schema '{schema}' exists {ownership_icon} (owner: {schema_owner})")
                    else:
                        results['schema_exists'] = {'status': 'not_found', 'schema': schema}
                        print(f"   ❌ Schema '{schema}' not found")
            except Exception as e:
                results['schema_exists'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Error checking schema: {e}")
            
            # Test 4: Seed tables exist and ownership
            print(f"\n📊 Test 4: Seed Tables (using USER credentials)")
            seed_tables_result = {
                'tables': [], 
                'row_counts': {}, 
                'table_owners': {},
                'status': 'pending'
            }
            expected_tables = ['intpk', 'intpk001', 'dtix', 'dtix001']
            
            try:
                # Use USER engine (self.simple_test.engine) to verify user can access tables
                with self.simple_test.engine.connect() as conn:
                    # First, verify which user we're connected as
                    verify_user = conn.execute(text("SELECT USER_NAME()"))
                    current_user = verify_user.scalar()
                    print(f"   Connected as user: {current_user}")
                    
                    for table_name in expected_tables:
                        # Check table exists and count rows (as regular user)
                        check_table = text(f"""
                            SELECT COUNT(*) as row_count
                            FROM {schema}.{table_name}
                        """)
                        try:
                            result = conn.execute(check_table)
                            row_count = result.scalar()
                            seed_tables_result['tables'].append(table_name)
                            seed_tables_result['row_counts'][table_name] = row_count
                            
                            # Check table ownership (tables inherit schema owner if principal_id is NULL)
                            check_owner = text(f"""
                                SELECT 
                                    COALESCE(
                                        USER_NAME(t.principal_id),
                                        USER_NAME(s.principal_id)
                                    ) as owner
                                FROM sys.tables t
                                JOIN sys.schemas s ON t.schema_id = s.schema_id
                                WHERE s.name = :schema_name AND t.name = :table_name
                            """)
                            owner_result = conn.execute(check_owner, {
                                'schema_name': schema,
                                'table_name': table_name
                            })
                            owner = owner_result.scalar()
                            seed_tables_result['table_owners'][table_name] = owner
                            
                            # Check if user owns the table
                            owns_table = (owner == user or owner == 'dbo')
                            ownership_icon = "👤" if owner == user else "🔧" if owner == 'dbo' else "⚠️"
                            print(f"   ✅ {schema}.{table_name}: {row_count} rows {ownership_icon} (owner: {owner})")
                        except Exception as e:
                            print(f"   ❌ {schema}.{table_name}: Not found or error - {e}")
                    
                    if len(seed_tables_result['tables']) == len(expected_tables):
                        seed_tables_result['status'] = 'success'
                    elif len(seed_tables_result['tables']) > 0:
                        seed_tables_result['status'] = 'partial'
                    else:
                        seed_tables_result['status'] = 'not_found'
            except Exception as e:
                seed_tables_result['status'] = 'error'
                seed_tables_result['error'] = str(e)[:200]
                print(f"   ❌ Error checking tables: {e}")
            
            results['seed_tables'] = seed_tables_result
            
            # Test 5: Lakeflow Connect setup (replication mode)
            print(f"\n📊 Test 5: Lakeflow Connect Setup")
            try:
                from .LfcCDC import LfcCDC
                
                dba_engine = SimpleSqlalchemy.create_dba_engine(self.simple_test._secrets_json, target_database=catalog)
                cdc = LfcCDC(
                    engine=self.simple_test.engine,
                    schema=schema,
                    dba_engine=dba_engine,
                    secrets_json=self.simple_test._secrets_json
                )
                
                # Clear cache and test
                if cdc.provider:
                    cdc.provider.cdc_supported = None
                
                is_cdc_supported = cdc.is_cdc_supported()
                detected_mode = 'both' if is_cdc_supported else 'ct'
                stored_mode = self.simple_test._secrets_json.get('replication_mode')
                
                results['lakeflow_connect_setup'] = {
                    'status': 'success',
                    'stored_mode': stored_mode,
                    'detected_mode': detected_mode,
                    'match': (stored_mode == detected_mode)
                }
                
                if is_cdc_supported:
                    print(f"   ✅ CDC Supported: Mode = BOTH (CDC + CT)")
                else:
                    print(f"   ℹ️  CDC Not Supported: Mode = CT only")
                    reason = cdc.get_cdc_failure_reason()
                    if reason:
                        print(f"   Reason: {reason}")
                
                if stored_mode == detected_mode:
                    print(f"   ✅ Stored mode matches detected mode: {stored_mode}")
                else:
                    print(f"   ⚠️  Mode mismatch: Stored='{stored_mode}' vs Detected='{detected_mode}'")
                
                dba_engine.dispose()
            except Exception as e:
                results['lakeflow_connect_setup'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Error: {e}")
            
            # Test 6: Databricks connection exists
            print(f"\n📊 Test 6: Databricks Connection")
            try:
                if self.simple_test.workspace_client:
                    lfc_conn = LfcConn(workspace_client=self.simple_test.workspace_client)
                    connection_name = self.simple_test._secrets_json.get('connection_name', 
                                                            f"{self.simple_test.lfc_env.get_connection_prefix()}_{host_fqdn.split('.')[0]}")
                    
                    try:
                        conn_obj = self.simple_test.workspace_client.connections.get(connection_name)
                        results['connection_exists'] = {
                            'status': 'success',
                            'connection_name': connection_name,
                            'connection_type': str(conn_obj.connection_type),
                            'comment': conn_obj.comment
                        }
                        print(f"   ✅ Connection exists: {connection_name}")
                        print(f"   Type: {conn_obj.connection_type}")
                    except Exception as e:
                        if 'does not exist' in str(e):
                            results['connection_exists'] = {
                                'status': 'not_found',
                                'connection_name': connection_name,
                                'error': 'Connection not found in Databricks'
                            }
                            print(f"   ❌ Connection NOT found: {connection_name}")
                        else:
                            raise
                else:
                    results['connection_exists'] = {'status': 'skipped', 'message': 'No workspace_client'}
                    print(f"   ℹ️  Skipped: No workspace_client available")
            except Exception as e:
                results['connection_exists'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Error: {e}")
            
            # Test 7: Databricks secrets exist
            print(f"\n📊 Test 7: Databricks Secrets")
            try:
                if self.simple_test.workspace_client:
                    lfc_secrets = LfcSecrets(workspace_client=self.simple_test.workspace_client)
                    scope_name = self.simple_test.lfc_env.get_scope_name()
                    secret_key = f"{host_fqdn}_json"
                    
                    try:
                        secret_value = self.simple_test.workspace_client.secrets.get_secret(scope=scope_name, key=secret_key)
                        results['secrets_exist'] = {
                            'status': 'success',
                            'scope': scope_name,
                            'key': secret_key
                        }
                        print(f"   ✅ Secret exists: {scope_name}/{secret_key}")
                    except Exception as e:
                        if 'does not exist' in str(e):
                            results['secrets_exist'] = {
                                'status': 'not_found',
                                'scope': scope_name,
                                'key': secret_key,
                                'error': 'Secret not found in Databricks'
                            }
                            print(f"   ❌ Secret NOT found: {scope_name}/{secret_key}")
                        else:
                            raise
                else:
                    results['secrets_exist'] = {'status': 'skipped', 'message': 'No workspace_client'}
                    print(f"   ℹ️  Skipped: No workspace_client available")
            except Exception as e:
                results['secrets_exist'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Error: {e}")
            
            # Test 8: Local credentials exist
            print(f"\n📊 Test 8: Local Credentials")
            try:
                cred_manager = SimpleLocalCred()
                connection_name = self.simple_test._secrets_json.get('connection_name',
                                                        f"{self.simple_test.lfc_env.get_connection_prefix()}_{host_fqdn.split('.')[0]}")
                
                creds = cred_manager.find_credentials(connection_name=connection_name)
                if creds:
                    results['local_credentials'] = {
                        'status': 'success',
                        'filename': creds[0]['_filename'],
                        'connection_name': connection_name
                    }
                    print(f"   ✅ Local credentials exist: {creds[0]['_filename']}")
                else:
                    results['local_credentials'] = {
                        'status': 'not_found',
                        'connection_name': connection_name,
                        'error': 'Credentials file not found'
                    }
                    print(f"   ❌ Local credentials NOT found for: {connection_name}")
            except Exception as e:
                results['local_credentials'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Error: {e}")
            
            # Test 9: Values match across connection, secrets, and local credentials
            print(f"\n📊 Test 9: Values Match Across Sources")
            values_match_result = {'matches': [], 'mismatches': [], 'status': 'pending'}
            
            try:
                # Compare key values
                if (results['local_credentials'] and results['local_credentials'].get('status') == 'success'):
                    cred_manager = SimpleLocalCred()
                    connection_name = self.simple_test._secrets_json.get('connection_name')
                    creds = cred_manager.find_credentials(connection_name=connection_name)
                    if creds:
                        creds = creds[0]
                        local_host = creds.get('host_fqdn')
                        secrets_host = self.simple_test._secrets_json.get('host_fqdn')
                        
                        if local_host == secrets_host:
                            values_match_result['matches'].append(f"host_fqdn: {local_host}")
                            print(f"   ✅ host_fqdn matches: {local_host}")
                        else:
                            values_match_result['mismatches'].append(f"host_fqdn: local={local_host}, secrets={secrets_host}")
                            print(f"   ❌ host_fqdn mismatch: local={local_host}, secrets={secrets_host}")
                
                if len(values_match_result['mismatches']) == 0:
                    values_match_result['status'] = 'success'
                    print(f"   ✅ All checked values match")
                else:
                    values_match_result['status'] = 'mismatch'
                    print(f"   ⚠️  Found {len(values_match_result['mismatches'])} mismatches")
            except Exception as e:
                values_match_result['status'] = 'error'
                values_match_result['error'] = str(e)[:200]
                print(f"   ❌ Error: {e}")
            
            results['values_match'] = values_match_result
            
            # Test 10: Auto-cleanup disabled (for persistent databases)
            print(f"\n📊 Test 10: Auto-Cleanup Status")
            try:
                # Check if this is a newly created database
                if self.simple_test._db_creator and hasattr(self.simple_test._db_creator, 'auto_cleanup'):
                    auto_cleanup = self.simple_test._db_creator.auto_cleanup
                    results['auto_cleanup_disabled'] = {
                        'status': 'success',
                        'auto_cleanup': auto_cleanup,
                        'correct': not auto_cleanup  # Should be False for persistent
                    }
                    if not auto_cleanup:
                        print(f"   ✅ Auto-cleanup DISABLED (correct for persistent database)")
                    else:
                        print(f"   ⚠️  Auto-cleanup ENABLED (resources will be deleted on cleanup)")
                else:
                    # Database was reused from existing credentials
                    results['auto_cleanup_disabled'] = {
                        'status': 'skipped',
                        'message': 'Database reused from existing credentials'
                    }
                    print(f"   ℹ️  Database reused from credentials (no cleanup queue)")
            except Exception as e:
                results['auto_cleanup_disabled'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Error: {e}")
            
            # Test 11: Permission verification including CT enablement check
            print(f"\n📊 Test 11: Permission Verification (CT Enablement)")
            try:
                from .LfcDbPerm import LfcDbPerm
                
                # Create db_config from secrets_json
                db_config = {
                    'db_type': 'sqlserver',
                    'database': catalog,
                    'schema': schema,
                    'user_username': user,
                    'user_password': self.simple_test._secrets_json.get('password'),
                    'dba_username': dba_user,
                    'dba_password': self.simple_test._secrets_json.get('dba', {}).get('password'),
                    'host': self.simple_test._secrets_json.get('host_fqdn'),
                    'port': self.simple_test._secrets_json.get('port', 1433)
                }
                
                # Run LfcDbPerm verification
                perm_manager = LfcDbPerm(self.simple_test.engine, db_config)
                perm_results = perm_manager.verify_permissions()
                
                # Extract CT check specifically
                ct_check = None
                for check in perm_results.get('checks', []):
                    if check.get('check') == 'ct_enablement':
                        ct_check = check
                        break
                
                results['permission_verification'] = perm_results
                
                if ct_check:
                    if ct_check['status'] == 'success':
                        print(f"   ✅ {ct_check['message']}")
                    elif ct_check['status'] == 'error':
                        print(f"   ❌ {ct_check['message']}")
                        if 'missing_ct_tables' in ct_check:
                            print(f"   📋 Missing CT on tables: {', '.join(ct_check['missing_ct_tables'])}")
                        if 'recommendation' in ct_check:
                            print(f"   💡 Recommendation: {ct_check['recommendation']}")
                    elif ct_check['status'] == 'warning':
                        print(f"   ⚠️  {ct_check['message']}")
                else:
                    print(f"   ℹ️  CT check not found in results")
                    
            except ImportError:
                results['permission_verification'] = {'status': 'skipped', 'message': 'LfcDbPerm not available'}
                print(f"   ℹ️  Skipped: LfcDbPerm not available")
            except Exception as e:
                results['permission_verification'] = {'status': 'error', 'error': str(e)[:200]}
                print(f"   ❌ Error: {e}")
            
            # Evaluate overall results
            user_catalog_ok = (results['user_access'] and 
                             results['user_access'].get('catalog', {}).get('status') == 'success')
            user_master_ok = (results['user_access'] and 
                            results['user_access'].get('master', {}).get('status') == 'success')
            schema_ok = results['schema_exists'] and results['schema_exists'].get('status') == 'success'
            tables_ok = results['seed_tables'] and results['seed_tables'].get('status') in ['success', 'partial']
            lfc_ok = results['lakeflow_connect_setup'] and results['lakeflow_connect_setup'].get('status') == 'success'
            conn_ok = results['connection_exists'] and results['connection_exists'].get('status') in ['success', 'skipped']
            secrets_ok = results['secrets_exist'] and results['secrets_exist'].get('status') in ['success', 'skipped']
            local_creds_ok = results['local_credentials'] and results['local_credentials'].get('status') == 'success'
            
            results['correct_setup'] = (user_catalog_ok and user_master_ok and schema_ok and 
                                       tables_ok and lfc_ok and conn_ok and secrets_ok and local_creds_ok)
            
            # Determine final status
            critical_failures = not (user_catalog_ok and user_master_ok)
            if results['correct_setup']:
                results['status'] = 'success'
                results['message'] = 'All comprehensive database tests passed'
            elif critical_failures:
                results['status'] = 'failed'
                results['message'] = 'Critical failures in user access'
            else:
                results['status'] = 'partial'
                results['message'] = 'Some tests passed but issues found'
            
            # Summary
            expected_tables = ['intpk', 'intpk001', 'dtix', 'dtix001']
            print(f"\n" + "=" * 80)
            print(f"📊 COMPREHENSIVE TEST SUMMARY")
            print(f"=" * 80)
            print(f"User Access: {results['user_access'].get('catalog', {}).get('status')} (catalog), " +
                  f"{results['user_access'].get('master', {}).get('status')} (master)")
            print(f"DBA Access: {results['dba_access'].get('catalog', {}).get('status')} (catalog), " +
                  f"{results['dba_access'].get('master', {}).get('status')} (master)")
            
            # Schema with ownership
            schema_info = results['schema_exists']
            schema_owner = schema_info.get('owner', 'unknown')
            print(f"Schema Exists: {schema_info.get('status')} (owner: {schema_owner})")
            print(f"Seed Tables: {results['seed_tables'].get('status')} " +
                  f"({len(results['seed_tables'].get('tables', []))}/{len(expected_tables)} found)")
            print(f"LFC Setup: {results['lakeflow_connect_setup'].get('status')}")
            print(f"Connection: {results['connection_exists'].get('status')}")
            print(f"Secrets: {results['secrets_exist'].get('status')}")
            print(f"Local Credentials: {results['local_credentials'].get('status')}")
            print(f"Values Match: {results['values_match'].get('status')}")
            print(f"Auto-Cleanup: {results['auto_cleanup_disabled'].get('status')}")
            
            # Add permission verification status
            perm_status = results.get('permission_verification', {}).get('status', 'not_run')
            ct_status = 'not_checked'
            if 'permission_verification' in results and 'checks' in results['permission_verification']:
                for check in results['permission_verification']['checks']:
                    if check.get('check') == 'ct_enablement':
                        ct_status = check.get('status', 'unknown')
                        break
            print(f"Permission Verification: {perm_status} (CT: {ct_status})")
            
            print(f"\n{'✅' if results['correct_setup'] else '❌'} Overall: {results['status']} - {results['message']}")
            print(f"=" * 80)
            
        except Exception as e:
            results['status'] = 'error'
            results['message'] = str(e)
            print(f"❌ Error during comprehensive test: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    


