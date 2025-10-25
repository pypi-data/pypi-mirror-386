"""
SimpleLocalCred - Centralized Local Credentials Management

This module provides a single, authoritative source for managing local database
credentials files stored in ~/.lfcddemo. It ensures consistency across all modules
that need to save or load credentials.

Key Features:
- Centralized filename generation (always uses database hostname, never laptop hostname)
- Unified credentials saving and loading
- Automatic credential format conversion
- Pattern-based credential file discovery
- Credential validation and error handling

Usage:
    from lfcdemolib import SimpleLocalCred
    
    # Save credentials
    cred_manager = SimpleLocalCred()
    cred_manager.save_credentials(db_details, db_type, cloud, schema)
    
    # Find matching credentials
    creds = cred_manager.find_credentials(db_type='sqlserver', cloud='azure')
    
    # Load specific file
    creds = cred_manager.load_credentials(filename)
"""

import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class SimpleLocalCred:
    """Centralized management of local database credentials"""
    
    # Credentials directory
    CREDENTIALS_DIR = Path.home() / '.lfcddemo'
    
    # Filename pattern: {cloud}_{db_type}_v1_{connection_name}_credentials.json
    FILENAME_TEMPLATE = "{cloud}_{db_type}_v1_{connection_name}_credentials.json"
    
    def __init__(self):
        """Initialize credentials manager"""
        # Ensure credentials directory exists
        self.CREDENTIALS_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def generate_filename(cloud: str, db_type: str, connection_name: str) -> str:
        """Generate credentials filename using database hostname
        
        IMPORTANT: connection_name should ALWAYS contain the database hostname,
        NOT the laptop hostname. The database hostname must be set before calling
        this method.
        
        Args:
            cloud: Cloud provider (azure, aws, gcp)
            db_type: Database type (sqlserver, mysql, postgresql)
            connection_name: Connection name (e.g., robert_lee_hwn72k3ybliojtas)
                            Must contain database hostname!
            
        Returns:
            str: Filename for credentials file
            
        Example:
            >>> generate_filename('azure', 'sqlserver', 'robert_lee_hwn72k3ybliojtas')
            'azure_sqlserver_v1_robert_lee_hwn72k3ybliojtas_credentials.json'
        """
        return SimpleLocalCred.FILENAME_TEMPLATE.format(
            cloud=cloud,
            db_type=db_type,
            connection_name=connection_name
        )
    
    def save_credentials(self,
                        db_details: Dict[str, Any],
                        db_type: str,
                        cloud: str,
                        schema: str) -> tuple[Path, Dict[str, Any]]:
        """Save database credentials to local file
        
        Args:
            db_details: Database connection details from SimpleDB
            db_type: Database type (sqlserver, mysql, postgresql)
            cloud: Cloud provider (azure, aws, gcp)
            schema: Database schema name
            
        Returns:
            tuple: (filepath, credentials_data)
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = [
            'connection_name', 'db_host_fqdn', 'db_catalog',
            'user_username', 'user_password',
            'dba_username', 'dba_password',
            'db_port', 'replication_mode'
        ]
        
        missing_fields = [f for f in required_fields if f not in db_details]
        if missing_fields:
            raise ValueError(f"Missing required fields in db_details: {', '.join(missing_fields)}")
        
        # Validate that connection_name uses database hostname, not laptop hostname
        connection_name = db_details['connection_name']
        db_hostname = db_details['db_host_fqdn'].split('.')[0].lower()
        
        if db_hostname not in connection_name:
            import socket
            laptop_hostname = socket.gethostname().split('.')[0].lower()
            if laptop_hostname in connection_name:
                raise ValueError(
                    f"connection_name '{connection_name}' appears to use laptop hostname '{laptop_hostname}' "
                    f"instead of database hostname '{db_hostname}'. "
                    f"Update connection_name to use database hostname before saving credentials."
                )
        
        # Create credentials data
        creds_data = {
            'connection_name': connection_name,
            'db_type': db_type,
            'cloud_provider': cloud,
            'host': db_details['db_host_fqdn'],
            'host_fqdn': db_details['db_host_fqdn'],
            'catalog': db_details['db_catalog'],
            'database': db_details['db_catalog'],
            'schema': schema,
            'username': db_details['user_username'],
            'user': db_details['user_username'],
            'password': db_details['user_password'],
            'dba_username': db_details['dba_username'],
            'dba_user': db_details['dba_username'],
            'dba_password': db_details['dba_password'],
            'port': str(db_details['db_port']),  # Ensure string for consistency
            'replication_mode': db_details['replication_mode'],
            'location': db_details.get('location', 'Unknown'),
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        # Generate filename
        filename = self.generate_filename(cloud, db_type, connection_name)
        filepath = self.CREDENTIALS_DIR / filename
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(creds_data, f, indent=2)
        
        print(f"💾 Database credentials saved to: {filepath}")
        print(f"   Connection: {connection_name}")
        print(f"   Server: {db_details['db_host_fqdn']}")
        print(f"   Database: {db_details['db_catalog']}")
        print(f"   Schema: {schema}")
        
        return filepath, creds_data
    
    def load_credentials(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load credentials from a specific file
        
        Args:
            filename: Credentials filename (basename only, not full path)
            
        Returns:
            dict: Credentials data, or None if file doesn't exist
        """
        filepath = self.CREDENTIALS_DIR / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r') as f:
                creds_data = json.load(f)
            
            # Update last_accessed timestamp
            creds_data['last_accessed'] = datetime.datetime.now().isoformat()
            
            return creds_data
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error loading credentials from {filepath}: {e}")
            return None
    
    def find_credentials(self,
                        db_type: Optional[str] = None,
                        cloud: Optional[str] = None,
                        connection_name: Optional[str] = None,
                        hostname: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find credentials matching the specified criteria
        
        Args:
            db_type: Filter by database type (optional)
            cloud: Filter by cloud provider (optional)
            connection_name: Filter by connection name (optional)
            hostname: Filter by database hostname (optional)
            
        Returns:
            list: List of matching credentials dictionaries, sorted by creation date (newest first)
        """
        matches = []
        
        # Get all credentials files
        pattern = "*_credentials.json"
        credential_files = list(self.CREDENTIALS_DIR.glob(pattern))
        
        for filepath in credential_files:
            creds = self.load_credentials(filepath.name)
            if not creds:
                continue
            
            # Apply filters
            if db_type and creds.get('db_type') != db_type:
                continue
            
            # Handle both old format (cloud_provider) and v2 format (cloud.provider)
            # Also handle case-insensitive matching
            if cloud:
                # Get cloud provider from either format
                cred_cloud = creds.get('cloud_provider')  # Old format
                if not cred_cloud:
                    # V2 format - check nested cloud object
                    cloud_obj = creds.get('cloud', {})
                    cred_cloud = cloud_obj.get('provider', '')
                
                # Compare case-insensitively
                if cred_cloud.lower() != cloud.lower():
                    continue
            
            if connection_name and creds.get('connection_name') != connection_name:
                continue
            
            if hostname:
                host_fqdn = creds.get('host_fqdn', '')
                db_hostname = host_fqdn.split('.')[0].lower()
                if db_hostname != hostname.lower():
                    continue
            
            # Add filepath for reference
            creds['_filepath'] = str(filepath)
            creds['_filename'] = filepath.name
            matches.append(creds)
        
        # Sort by creation date (newest first)
        matches.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return matches
    
    def find_most_recent(self,
                        db_type: Optional[str] = None,
                        cloud: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find the most recently created credentials matching criteria
        
        Args:
            db_type: Filter by database type (optional)
            cloud: Filter by cloud provider (optional)
            
        Returns:
            dict: Most recent credentials, or None if no matches
        """
        matches = self.find_credentials(db_type=db_type, cloud=cloud)
        return matches[0] if matches else None
    
    def update_credentials(self, filename: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in a credentials file
        
        Args:
            filename: Credentials filename
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        filepath = self.CREDENTIALS_DIR / filename
        
        if not filepath.exists():
            print(f"⚠️  Credentials file not found: {filename}")
            return False
        
        try:
            # Load existing credentials
            with open(filepath, 'r') as f:
                creds_data = json.load(f)
            
            # Apply updates
            creds_data.update(updates)
            creds_data['updated_at'] = datetime.datetime.now().isoformat()
            
            # Save back to file
            with open(filepath, 'w') as f:
                json.dump(creds_data, f, indent=2)
            
            print(f"✅ Updated credentials: {filename}")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Error updating credentials {filename}: {e}")
            return False
    
    def delete_credentials(self, filename: str, force: bool = False) -> bool:
        """Delete a credentials file with deployment safety check
        
        This is the ONLY authorized method for deleting credentials files.
        All other modules MUST use this method instead of directly deleting files.
        
        Safety Features:
        - Checks if credentials have been deployed to any workspace
        - Prevents accidental deletion of credentials still in use
        - Requires force=True to delete deployed credentials
        
        Args:
            filename: Credentials filename (basename only, not full path)
            force: If True, allow deletion even if deployed (default: False)
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If credentials are deployed and force=False
        """
        filepath = self.CREDENTIALS_DIR / filename
        
        if not filepath.exists():
            print(f"⚠️  Credentials file not found: {filename}")
            return False
        
        try:
            # Load credentials to check deployment status
            with open(filepath, 'r') as f:
                creds_data = json.load(f)
            
            # Check if credentials have been deployed
            deployed_list = creds_data.get('deployed', [])
            
            if deployed_list and not force:
                print(f"❌ Cannot delete credentials: {filename}")
                print(f"   This credential has been deployed to {len(deployed_list)} workspace(s):")
                for deployment in deployed_list:
                    workspace_name = deployment.get('workspace_name', 'unknown')
                    connection_name = deployment.get('connection_name', 'unknown')
                    deployed_at = deployment.get('deployed_at', 'unknown')
                    print(f"   - {workspace_name}: {connection_name} (deployed: {deployed_at})")
                print()
                print("⚠️  To delete this credential, you must FIRST:")
                print("   1. Delete the deployments using: --delete")
                print(f"      python3 deploy_credentials_to_workspaces.py --creds-file ~/.lfcddemo/{filename} --delete")
                print("   2. Then delete the local credential file")
                print()
                print("   OR use force=True to override this safety check (NOT RECOMMENDED)")
                return False
            
            # If deployed but force=True, show warning
            if deployed_list and force:
                print(f"⚠️  WARNING: Force deleting credentials deployed to {len(deployed_list)} workspace(s)")
                for deployment in deployed_list:
                    workspace_name = deployment.get('workspace_name', 'unknown')
                    print(f"   - {workspace_name}")
                print()
            
            # Delete the file
            filepath.unlink()
            
            if deployed_list:
                print(f"🗑️  Deleted credentials: {filename} (FORCED - deployments may still exist)")
            else:
                print(f"🗑️  Deleted credentials: {filename}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Error reading credentials file {filename}: {e}")
            print(f"   File may be corrupted. Use force=True to delete anyway.")
            return False
        except IOError as e:
            print(f"❌ Error deleting credentials {filename}: {e}")
            return False
    
    def convert_to_secrets_json(self, creds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert credentials format to secrets_json format (v2)
        
        Args:
            creds_data: Credentials data from file (v2 format)
            
        Returns:
            dict: secrets_json v2 format
        """
        # Handle both 'database' and 'catalog' field names
        catalog = creds_data.get('catalog') or creds_data.get('database', '')
        
        # Convert port to int if it's a string
        port = creds_data.get('port')
        if isinstance(port, str):
            port = int(port) if port.isdigit() else self._get_default_port(creds_data.get('db_type', 'sqlserver'))
        elif port is None:
            port = self._get_default_port(creds_data.get('db_type', 'sqlserver'))
        
        # Check for required replication_mode field
        if 'replication_mode' not in creds_data:
            raise ValueError(
                f"Missing 'replication_mode' in credentials. "
                f"Please run update_existing_replication_mode.py to detect and set the mode."
            )
        
        # Extract DBA credentials - handle both nested and flat formats
        dba_obj = creds_data.get('dba', {})
        if dba_obj:
            # Nested format: dba.user and dba.password
            dba_user = dba_obj.get('user', '')
            dba_password = dba_obj.get('password', '')
        else:
            # Flat format: dba_username and dba_password (from save_credentials)
            dba_user = creds_data.get('dba_username') or creds_data.get('dba_user', '')
            dba_password = creds_data.get('dba_password', '')
        
        # Extract cloud object - handle both nested and flat formats
        cloud_obj = creds_data.get('cloud', {})
        if cloud_obj:
            # Nested format: cloud.provider, cloud.location, cloud.resource_group
            cloud_provider = cloud_obj.get('provider', 'azure')
            cloud_location = cloud_obj.get('location', 'Unknown')
            cloud_resource_group = cloud_obj.get('resource_group', 'Unknown')
        else:
            # Flat format: cloud_provider and location (from save_credentials)
            cloud_provider = creds_data.get('cloud_provider', 'azure')
            cloud_location = creds_data.get('location', 'Unknown')
            cloud_resource_group = 'Unknown'
        
        # Return v2 format secrets_json
        return {
            'version': 'v2',
            'name': creds_data.get('name', creds_data.get('connection_name', '')),
            'host_fqdn': creds_data.get('host_fqdn', creds_data.get('host', '')),
            'catalog': catalog,
            'schema': creds_data.get('schema', 'lfcddemo'),
            'user': creds_data.get('user', creds_data.get('username', '')),
            'password': creds_data.get('password', ''),
            'dba': {
                'user': dba_user,
                'password': dba_password
            },
            'port': port,
            'db_type': creds_data.get('db_type', 'sqlserver'),
            'replication_mode': creds_data['replication_mode'],
            'cloud': {
                'provider': cloud_provider,
                'location': cloud_location,
                'resource_group': cloud_resource_group
            }
        }
    
    @staticmethod
    def _get_default_port(db_type: str) -> int:
        """Get default port for database type"""
        ports = {
            'sqlserver': 1433,
            'mysql': 3306,
            'postgresql': 5432
        }
        return ports.get(db_type.lower(), 1433)
    
    def list_all_credentials(self) -> List[Dict[str, Any]]:
        """List all credentials files with summary information
        
        Returns:
            list: List of credential summaries
        """
        all_creds = []
        pattern = "*_credentials.json"
        credential_files = list(self.CREDENTIALS_DIR.glob(pattern))
        
        for filepath in credential_files:
            creds = self.load_credentials(filepath.name)
            if creds:
                # Get cloud provider from either format
                cloud_provider = creds.get('cloud_provider')  # Old format
                if not cloud_provider:
                    cloud_obj = creds.get('cloud', {})
                    cloud_provider = cloud_obj.get('provider', 'unknown')
                
                summary = {
                    'filename': filepath.name,
                    'connection_name': creds.get('connection_name') or creds.get('name'),
                    'db_type': creds.get('db_type'),
                    'cloud_provider': cloud_provider,
                    'host_fqdn': creds.get('host_fqdn') or creds.get('host'),
                    'database': creds.get('catalog') or creds.get('database'),
                    'schema': creds.get('schema'),
                    'replication_mode': creds.get('replication_mode'),
                    'created_at': creds.get('created_at'),
                    'updated_at': creds.get('updated_at')
                }
                all_creds.append(summary)
        
        # Sort by creation date (newest first)
        all_creds.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return all_creds
    
    def print_credentials_summary(self):
        """Print a formatted summary of all credentials"""
        all_creds = self.list_all_credentials()
        
        if not all_creds:
            print("📂 No credentials found in ~/.lfcddemo")
            return
        
        print(f"📂 Found {len(all_creds)} credentials file(s) in ~/.lfcddemo")
        print()
        
        for i, creds in enumerate(all_creds, 1):
            print(f"{i}. {creds['filename']}")
            print(f"   Connection: {creds['connection_name']}")
            print(f"   Type: {creds['db_type']} on {creds['cloud_provider']}")
            print(f"   Host: {creds['host_fqdn']}")
            print(f"   Database: {creds['database']}")
            print(f"   Schema: {creds['schema']}")
            print(f"   Replication: {creds['replication_mode']}")
            print(f"   Created: {creds['created_at']}")
            if creds.get('updated_at'):
                print(f"   Updated: {creds['updated_at']}")
            print()

