"""
SimpleAzure - Azure Cloud Provider Implementation

This module provides Azure-specific implementation for database provisioning:
- Azure SQL Server, MySQL, PostgreSQL support
- Terraform configuration generation for Azure resources
- Azure-specific resource management and cleanup
- Integration with Azure Resource Groups and networking

Key Features:
- Multi-database support (SQL Server, MySQL, PostgreSQL)
- Azure Resource Group management
- Firewall rule configuration
- Resource tagging and cleanup
"""

from typing import Dict, Any, List, Tuple, Optional
import datetime
import subprocess
import json
import math
try:
    from .SimpleCloudBase import CloudProviderBase, get_database_provider
except ImportError:
    # For direct module loading in tests
    from SimpleCloudBase import CloudProviderBase, get_database_provider


class AzureProvider(CloudProviderBase):
    """Azure cloud provider implementation"""
    
    def __init__(self, dbxrest: Any, config: Dict[str, Any], **kwargs):
        super().__init__(dbxrest, config, **kwargs)
        self.location = kwargs.get('location', 'Central US')
        self.resource_group_name = kwargs.get('resource_group_name')
        
        # Set default resource group if not provided
        if not self.resource_group_name:
            if self.dbxrest and hasattr(self.dbxrest, 'my_email_text') and self.dbxrest.my_email_text:
                whoami = self.dbxrest.my_email_text.replace('@', '_').replace('.', '_')
            else:
                # Get username from OS when dbxrest is None or doesn't have email
                import os
                whoami = os.getenv('USER', os.getenv('USERNAME', 'unknown')).replace('.', '_')
            # Add timestamp to make resource group name unique
            import time
            timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
            self.resource_group_name = f"{whoami}_rg_{timestamp}"
    
    def get_provider_name(self) -> str:
        return 'azure'
    
    def get_supported_database_types(self) -> List[str]:
        return ['sqlserver', 'mysql', 'postgresql']
    
    def check_database_availability_in_region(self, db_type: str, region: str) -> bool:
        """Check if a database service is available in a specific Azure region
        
        Args:
            db_type: Database type ('sqlserver', 'mysql', 'postgresql')
            region: Azure region name
            
        Returns:
            bool: True if service is available in the region
        """
        try:
            # Map database types to Azure service names
            service_map = {
                'sqlserver': 'Microsoft.Sql/servers',
                'mysql': 'Microsoft.DBforMySQL/flexibleServers',
                'postgresql': 'Microsoft.DBforPostgreSQL/flexibleServers'
            }
            
            if db_type not in service_map:
                print(f"⚠️ Unknown database type: {db_type}")
                return False
            
            service_name = service_map[db_type]
            
            # Use Azure CLI to check provider availability
            cmd = [
                'az', 'provider', 'show',
                '--namespace', service_name.split('/')[0],
                '--query', f"resourceTypes[?resourceType=='{service_name.split('/')[1]}'].locations",
                '--output', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                locations_data = json.loads(result.stdout)
                if locations_data and len(locations_data) > 0:
                    available_locations = locations_data[0]  # First (and usually only) result
                    # Normalize region names for comparison
                    normalized_region = region.replace(' ', '').lower()
                    available_normalized = [loc.replace(' ', '').lower() for loc in available_locations]
                    return normalized_region in available_normalized
            
            print(f"⚠️ Could not check availability for {db_type} in {region}")
            return True  # Assume available if we can't check
            
        except Exception as e:
            print(f"⚠️ Error checking database availability: {e}")
            return True  # Assume available if error occurs
    
    def get_available_regions_for_database(self, db_type: str) -> List[str]:
        """Get list of Azure regions where a database service is available
        
        Args:
            db_type: Database type ('sqlserver', 'mysql', 'postgresql')
            
        Returns:
            List of available region names
        """
        try:
            # Map database types to Azure service names
            service_map = {
                'sqlserver': 'Microsoft.Sql/servers',
                'mysql': 'Microsoft.DBforMySQL/flexibleServers',
                'postgresql': 'Microsoft.DBforPostgreSQL/flexibleServers'
            }
            
            if db_type not in service_map:
                print(f"⚠️ Unknown database type: {db_type}")
                return ['Central US']  # Fallback
            
            service_name = service_map[db_type]
            
            # Use Azure CLI to get available locations
            cmd = [
                'az', 'provider', 'show',
                '--namespace', service_name.split('/')[0],
                '--query', f"resourceTypes[?resourceType=='{service_name.split('/')[1]}'].locations[0]",
                '--output', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                locations = json.loads(result.stdout)
                if locations:
                    return sorted(locations)
            
            print(f"⚠️ Could not get available regions for {db_type}")
            return ['Central US', 'East US', 'West US 2']  # Common fallback regions
            
        except Exception as e:
            print(f"⚠️ Error getting available regions: {e}")
            return ['Central US', 'East US', 'West US 2']  # Common fallback regions
    
    def calculate_distance_to_region(self, region: str, user_location: Tuple[float, float] = None) -> float:
        """Calculate approximate distance to an Azure region
        
        Args:
            region: Azure region name
            user_location: Optional tuple of (latitude, longitude). If None, uses US Central location
            
        Returns:
            Approximate distance in miles
        """
        # Approximate coordinates for major Azure regions
        region_coordinates = {
            'central us': (41.5868, -93.6250),
            'east us': (37.3719, -79.8164),
            'east us 2': (36.6681, -78.3889),
            'west us': (37.783, -122.417),
            'west us 2': (47.233, -119.852),
            'west us 3': (33.448, -112.073),
            'north central us': (41.8819, -87.6278),
            'south central us': (29.4167, -98.5),
            'canada central': (43.653, -79.383),
            'canada east': (46.817, -71.217),
            'brazil south': (-23.55, -46.633),
            'north europe': (53.3478, -6.2597),
            'west europe': (52.3667, 4.9),
            'uk south': (50.941, -0.799),
            'uk west': (53.427, -3.084),
            'france central': (46.3772, 2.3730),
            'germany west central': (50.110924, 8.682127),
            'norway east': (59.913, 10.752),
            'switzerland north': (47.451542, 8.564572),
            'sweden central': (60.67488, 17.14127),
            'uae north': (25.266, 55.316),
            'south africa north': (-25.731340, 28.218370),
            'australia east': (-33.86, 151.2094),
            'australia southeast': (-37.8136, 144.9631),
            'australia central': (-35.3075, 149.1244),
            'east asia': (22.267, 114.188),
            'southeast asia': (1.283, 103.833),
            'japan east': (35.68, 139.77),
            'japan west': (34.6939, 135.5022),
            'korea central': (37.5665, 126.9780),
            'korea south': (35.1796, 129.0756),
            'india central': (18.5822, 73.9197),
            'india south': (12.9822, 80.1636),
            'india west': (19.088, 72.868)
        }
        
        # Default to Central US location if user location not provided
        if user_location is None:
            user_location = (39.8283, -98.5795)  # Geographic center of US
        
        # Get region coordinates
        region_key = region.lower().replace(' ', ' ')
        if region_key not in region_coordinates:
            # Try without spaces
            region_key = region.lower().replace(' ', '')
            region_key = region_key.replace('centralus', 'central us')
            region_key = region_key.replace('eastus', 'east us')
            region_key = region_key.replace('westus', 'west us')
            region_key = region_key.replace('northcentralus', 'north central us')
            region_key = region_key.replace('southcentralus', 'south central us')
        
        if region_key not in region_coordinates:
            print(f"⚠️ Unknown region coordinates for: {region}")
            return 1000.0  # Default high distance
        
        region_coords = region_coordinates[region_key]
        
        # Calculate distance using Haversine formula
        lat1, lon1 = math.radians(user_location[0]), math.radians(user_location[1])
        lat2, lon2 = math.radians(region_coords[0]), math.radians(region_coords[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in miles
        r = 3956
        
        return c * r
    
    def find_closest_available_region(self, db_type: str, preferred_region: str = None, user_location: Tuple[float, float] = None) -> str:
        """Find the closest Azure region where a database service is available
        
        Args:
            db_type: Database type ('sqlserver', 'mysql', 'postgresql')
            preferred_region: Preferred region to check first
            user_location: Optional tuple of (latitude, longitude)
            
        Returns:
            Name of the closest available region
        """
        print(f"🔍 Finding closest available region for {db_type}...")
        
        # First check if preferred region is available
        if preferred_region:
            if self.check_database_availability_in_region(db_type, preferred_region):
                print(f"✅ {db_type} is available in preferred region: {preferred_region}")
                return preferred_region
            else:
                print(f"⚠️ {db_type} is not available in preferred region: {preferred_region}")
        
        # Get all available regions for this database type
        available_regions = self.get_available_regions_for_database(db_type)
        
        if not available_regions:
            print(f"⚠️ No available regions found for {db_type}, using Central US")
            return 'Central US'
        
        # Calculate distances and sort by proximity
        region_distances = []
        for region in available_regions:
            distance = self.calculate_distance_to_region(region, user_location)
            region_distances.append((region, distance))
        
        # Sort by distance
        region_distances.sort(key=lambda x: x[1])
        
        # Display options
        print(f"📍 Available regions for {db_type} (sorted by distance):")
        for i, (region, distance) in enumerate(region_distances[:5]):  # Show top 5
            print(f"   {i+1}. {region}: ~{distance:.0f} miles")
        
        closest_region = region_distances[0][0]
        print(f"🎯 Selected closest region: {closest_region}")
        
        return closest_region
    
    def generate_terraform_config(self, db_config: Dict[str, Any]) -> str:
        """Generate Azure Terraform configuration"""
        db_type = db_config.get('db_type', 'sqlserver')
        db_provider = get_database_provider(db_type)
        
        # Base Azure provider configuration
        config = f'''
# Configure the Azure Provider
terraform {{
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }}
    http = {{
      source  = "hashicorp/http"
      version = "~>3.0"
    }}
  }}
}}

# Configure the Microsoft Azure Provider
provider "azurerm" {{
  features {{}}
}}

# Create a resource group
resource "azurerm_resource_group" "main" {{
  name     = var.resource_group_name
  location = var.location

  tags = {{
    Owner       = var.owner
    RemoveAfter = var.remove_after
    Environment = "demo"
    Purpose     = "lfcdemo"
  }}
}}

# Locals for database-specific outputs
locals {{
  server_name = {self._get_server_name_local(db_type)}
  server_fqdn = {self._get_server_fqdn_local(db_type)}
  database_name = {self._get_database_name_local(db_type)}
  admin_username = {self._get_admin_username_local(db_type)}
}}
'''
        
        # Add database-specific resources
        if db_type == 'sqlserver':
            config += self._generate_sqlserver_resources()
        elif db_type == 'mysql':
            config += self._generate_mysql_resources()
        elif db_type == 'postgresql':
            config += self._generate_postgresql_resources()
        
        return config
    
    def _get_server_name_local(self, db_type: str) -> str:
        """Get server name local expression for Terraform"""
        if db_type == 'sqlserver':
            return 'azurerm_mssql_server.main.name'
        elif db_type == 'mysql':
            return 'azurerm_mysql_flexible_server.main.name'
        elif db_type == 'postgresql':
            return 'azurerm_postgresql_flexible_server.main.name'
        else:
            return '"unknown"'
    
    def _get_server_fqdn_local(self, db_type: str) -> str:
        """Get server FQDN local expression for Terraform"""
        if db_type == 'sqlserver':
            return 'azurerm_mssql_server.main.fully_qualified_domain_name'
        elif db_type == 'mysql':
            return 'azurerm_mysql_flexible_server.main.fqdn'
        elif db_type == 'postgresql':
            return 'azurerm_postgresql_flexible_server.main.fqdn'
        else:
            return '"unknown"'
    
    def _get_database_name_local(self, db_type: str) -> str:
        """Get database name local expression for Terraform"""
        if db_type == 'sqlserver':
            return 'azurerm_mssql_database.main.name'
        elif db_type == 'mysql':
            return 'azurerm_mysql_flexible_database.main.name'
        elif db_type == 'postgresql':
            return 'azurerm_postgresql_flexible_server_database.main.name'
        else:
            return '"unknown"'
    
    def _get_admin_username_local(self, db_type: str) -> str:
        """Get admin username local expression for Terraform"""
        if db_type == 'sqlserver':
            return 'azurerm_mssql_server.main.administrator_login'
        elif db_type == 'mysql':
            return 'azurerm_mysql_flexible_server.main.administrator_login'
        elif db_type == 'postgresql':
            return 'azurerm_postgresql_flexible_server.main.administrator_login'
        else:
            return '"unknown"'
    
    def _generate_sqlserver_resources(self) -> str:
        """Generate SQL Server specific resources"""
        return '''
# Create a SQL Server
resource "azurerm_mssql_server" "main" {
  name                         = var.sql_server_name
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = var.admin_username
  administrator_login_password = var.admin_password

  tags = {
    Owner       = var.owner
    RemoveAfter = var.remove_after
    Environment = "demo"
    Purpose     = "lfcdemo"
  }
}

# Create a SQL Database
resource "azurerm_mssql_database" "main" {
  name           = var.database_name
  server_id      = azurerm_mssql_server.main.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  license_type   = "LicenseIncluded"
  max_size_gb    = 2  # Basic tier maximum
  sku_name       = "Basic"  # Cheapest tier (~$5/month)

  tags = {
    Owner       = var.owner
    RemoveAfter = var.remove_after
    Environment = "demo"
    Purpose     = "lfcdemo"
  }
}

# Get current public IP
data "http" "current_ip" {
  url = "https://api.ipify.org"
}

# Create a firewall rule for current IP
resource "azurerm_mssql_firewall_rule" "allow_current_ip" {
  name             = "AllowCurrentIP"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = chomp(data.http.current_ip.response_body)
  end_ip_address   = chomp(data.http.current_ip.response_body)
}

# Create a firewall rule for all IPs (avoiding 0.0.0.0 policy restriction)
resource "azurerm_mssql_firewall_rule" "allow_all_ips" {
  name             = "AllowAllIPs"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "0.0.0.1"
  end_ip_address   = "255.255.255.255"
}
'''
    
    def _generate_mysql_resources(self) -> str:
        """Generate MySQL specific resources"""
        return '''
# Create a MySQL Server
resource "azurerm_mysql_flexible_server" "main" {
  name                   = var.sql_server_name
  resource_group_name    = azurerm_resource_group.main.name
  location              = azurerm_resource_group.main.location
  administrator_login    = var.admin_username
  administrator_password = var.admin_password
  
  sku_name = "B_Standard_B1ms"
  version  = "8.0.21"
  
  storage {
    size_gb = 32  # Minimum size for Burstable tier
  }

  tags = {
    Owner       = var.owner
    RemoveAfter = var.remove_after
    Environment = "demo"
    Purpose     = "lfcdemo"
  }
}

# Create a MySQL Database
resource "azurerm_mysql_flexible_database" "main" {
  name                = var.database_name
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_mysql_flexible_server.main.name
  charset             = "utf8"
  collation           = "utf8_unicode_ci"
}

# Create a firewall rule to allow all IPs (avoiding 0.0.0.0 policy restriction)
resource "azurerm_mysql_flexible_server_firewall_rule" "allow_all" {
  name             = "AllowAll"
  resource_group_name = azurerm_resource_group.main.name
  server_name      = azurerm_mysql_flexible_server.main.name
  start_ip_address = "0.0.0.1"
  end_ip_address   = "255.255.255.255"
}
'''
    
    def _generate_postgresql_resources(self) -> str:
        """Generate PostgreSQL specific resources"""
        return '''
# Create a PostgreSQL Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = var.sql_server_name
  resource_group_name    = azurerm_resource_group.main.name
  location              = azurerm_resource_group.main.location
  administrator_login    = var.admin_username
  administrator_password = var.admin_password
  
  sku_name = "B_Standard_B1ms"
  version  = "13"
  
  storage_mb = 32768  # 32GB minimum for Burstable tier

  tags = {
    Owner       = var.owner
    RemoveAfter = var.remove_after
    Environment = "demo"
    Purpose     = "lfcdemo"
  }
}

# Create a PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Create a firewall rule to allow all IPs (avoiding 0.0.0.0 policy restriction)
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_all" {
  name             = "AllowAll"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.1"
  end_ip_address   = "255.255.255.255"
}
'''
    
    def generate_terraform_variables(self) -> str:
        """Generate Terraform variables for Azure"""
        return '''
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "sql_server_name" {
  description = "Name of the database server"
  type        = string
}

variable "database_name" {
  description = "Name of the database"
  type        = string
}

variable "admin_username" {
  description = "Administrator username for database server"
  type        = string
}

variable "admin_password" {
  description = "Administrator password for database server"
  type        = string
  sensitive   = true
}

variable "owner" {
  description = "Owner tag for resources"
  type        = string
}

variable "remove_after" {
  description = "Date after which resources should be removed"
  type        = string
}
'''
    
    def generate_terraform_outputs(self) -> str:
        """Generate Terraform outputs for Azure"""
        # Note: This generates generic outputs that work with any database type
        # The actual resources will be created based on the db_type in main.tf
        return '''
output "resource_group_name" {
  description = "Name of the created resource group"
  value       = azurerm_resource_group.main.name
}

output "sql_server_name" {
  description = "Name of the created database server"
  value       = local.server_name
}

output "sql_server_fqdn" {
  description = "Fully qualified domain name of the database server"
  value       = local.server_fqdn
}

output "database_name" {
  description = "Name of the created database"
  value       = local.database_name
}

output "admin_username" {
  description = "Administrator username"
  value       = local.admin_username
  sensitive   = true
}
'''
    
    def generate_terraform_tfvars(self, db_config: Dict[str, Any]) -> str:
        """Generate terraform.tfvars for Azure"""
        remove_after = datetime.datetime.now().strftime('%Y-%m-%d')
        dbx_username = getattr(self.dbxrest, 'my_email', 'unknown')
        
        db_type = db_config.get('db_type', 'sqlserver')
        db_basename = db_config.get('db_basename', 'defaultdb')
        catalog_basename = db_config.get('catalog_basename', 'defaultcat')
        dba_username = db_config.get('dba_username', 'admin')
        dba_password = db_config.get('dba_password', 'password')
        
        # Convert underscores to hyphens for Azure SQL Server naming requirements
        # Azure SQL Server names can only contain lowercase letters, numbers, and hyphens
        azure_server_name = db_basename.replace('_', '-').lower()
        
        return f'''
resource_group_name = "{self.resource_group_name}"
location           = "{self.location}"
sql_server_name    = "{azure_server_name}"
database_name      = "{catalog_basename}"
admin_username     = "{dba_username}"
admin_password     = "{dba_password}"
owner              = "{dbx_username}"
remove_after       = "{remove_after}"
'''
    
    def get_connection_details(self, terraform_outputs: Dict[str, Any], db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract connection details from Terraform outputs"""
        db_type = db_config.get('db_type', 'sqlserver')
        db_provider = get_database_provider(db_type)
        
        return {
            'status': 'success',
            'db_host': terraform_outputs.get('sql_server_name', {}).get('value'),
            'db_host_fqdn': terraform_outputs.get('sql_server_fqdn', {}).get('value'),
            'db_port': db_provider.get_default_port(),
            'db_catalog': db_config.get('catalog_basename'),
            'dba_username': db_config.get('dba_username'),
            'dba_password': db_config.get('dba_password'),
            'user_username': db_config.get('user_username'),
            'user_password': db_config.get('user_password'),
            'resource_group': self.resource_group_name,
            'terraform_dir': db_config.get('terraform_dir'),
            'created_at': datetime.datetime.now().isoformat(),
            'cloud_provider': 'azure',
            'db_type': db_type
        }
    
    def get_firewall_rules_config(self) -> List[Dict[str, Any]]:
        """Get Azure-specific firewall rules configuration"""
        return [
            {
                'name': 'AllowAll',
                'start_ip': '0.0.0.0',
                'end_ip': '255.255.255.255',
                'description': 'Allow all IPs (demo only)'
            },
            {
                'name': 'AllowAzureServices',
                'start_ip': '0.0.0.0',
                'end_ip': '0.0.0.0',
                'description': 'Allow Azure services'
            }
        ]
    
    def get_resource_naming_convention(self, db_type: str, base_name: str) -> Dict[str, str]:
        """Get Azure resource naming convention"""
        try:
            from .SimpleCloudBase import get_connection_suffix
        except ImportError:
            from SimpleCloudBase import get_connection_suffix
        suffix = get_connection_suffix(db_type)
        
        return {
            'server_name': f"{base_name}-{suffix}",
            'resource_group': self.resource_group_name,
            'location': self.location
        }
