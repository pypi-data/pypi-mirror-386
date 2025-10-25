"""
SimpleCloudBase - Base Classes for Cloud Provider Abstraction

This module provides base classes for cloud provider implementations:
- CloudProviderBase: Abstract base class for cloud providers
- DatabaseProviderBase: Abstract base class for database types
- TerraformProviderBase: Base class for Terraform-based provisioning

Key Features:
- Extensible architecture for multiple cloud providers
- Database type abstraction
- Terraform configuration generation
- Standardized cleanup and resource management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Literal
import datetime
import json


class CloudProviderBase(ABC):
    """Abstract base class for cloud provider implementations"""
    
    def __init__(self, dbxrest: Any, config: Dict[str, Any], **kwargs):
        self.dbxrest = dbxrest
        self.config = config
        self.provider_config = kwargs
        
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the cloud provider name"""
        pass
    
    @abstractmethod
    def get_supported_database_types(self) -> List[str]:
        """Get list of supported database types for this provider"""
        pass
    
    @abstractmethod
    def generate_terraform_config(self, db_config: Dict[str, Any]) -> str:
        """Generate main Terraform configuration"""
        pass
    
    @abstractmethod
    def generate_terraform_variables(self) -> str:
        """Generate Terraform variables.tf"""
        pass
    
    @abstractmethod
    def generate_terraform_outputs(self) -> str:
        """Generate Terraform outputs.tf"""
        pass
    
    @abstractmethod
    def generate_terraform_tfvars(self, db_config: Dict[str, Any]) -> str:
        """Generate terraform.tfvars"""
        pass
    
    @abstractmethod
    def get_connection_details(self, terraform_outputs: Dict[str, Any], db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract connection details from Terraform outputs"""
        pass


class DatabaseProviderBase(ABC):
    """Abstract base class for database type implementations"""
    
    def __init__(self, db_type: str):
        self.db_type = db_type
    
    @abstractmethod
    def get_database_type(self) -> str:
        """Get the database type name"""
        pass
    
    @abstractmethod
    def get_default_port(self) -> str:
        """Get default port for this database type"""
        pass
    
    @abstractmethod
    def get_connection_type(self) -> str:
        """Get Databricks connection type"""
        pass
    
    @abstractmethod
    def get_connection_options(self, connection_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get database-specific connection options"""
        pass
    
    @abstractmethod
    def get_terraform_resource_config(self) -> Dict[str, Any]:
        """Get database-specific Terraform resource configuration"""
        pass


class TerraformProviderBase:
    """Base class for Terraform-based cloud provisioning"""
    
    def __init__(self, cloud_provider: CloudProviderBase, db_provider: DatabaseProviderBase):
        self.cloud_provider = cloud_provider
        self.db_provider = db_provider
        
    def get_terraform_provider_config(self) -> str:
        """Get Terraform provider configuration"""
        return self.cloud_provider.generate_terraform_config({})
    
    def get_common_tags(self) -> Dict[str, str]:
        """Get common resource tags"""
        remove_after = datetime.datetime.now().strftime('%Y-%m-%d')
        dbx_username = getattr(self.cloud_provider.dbxrest, 'my_email', 'unknown')
        
        return {
            'Owner': dbx_username,
            'RemoveAfter': remove_after,
            'Environment': 'demo',
            'Purpose': 'lfcdemo',
            'CloudProvider': self.cloud_provider.get_provider_name(),
            'DatabaseType': self.db_provider.get_database_type()
        }


# Database type implementations
class SqlServerProvider(DatabaseProviderBase):
    """SQL Server database provider"""
    
    def __init__(self):
        super().__init__('sqlserver')
    
    def get_database_type(self) -> str:
        return 'sqlserver'
    
    def get_default_port(self) -> str:
        return '1433'
    
    def get_connection_type(self) -> str:
        return 'SQLSERVER'
    
    def get_connection_options(self, connection_details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "host": connection_details['db_host_fqdn'],
            "port": connection_details['db_port'],
            "user": connection_details['user_username'],
            "password": connection_details['user_password'],
            "trustServerCertificate": "true"
        }
    
    def get_terraform_resource_config(self) -> Dict[str, Any]:
        return {
            'version': '12.0',
            'collation': 'SQL_Latin1_General_CP1_CI_AS',
            'license_type': 'LicenseIncluded',
            'max_size_gb': 32,
            'sku_name': 'S0'
        }


class MySqlProvider(DatabaseProviderBase):
    """MySQL database provider"""
    
    def __init__(self):
        super().__init__('mysql')
    
    def get_database_type(self) -> str:
        return 'mysql'
    
    def get_default_port(self) -> str:
        return '3306'
    
    def get_connection_type(self) -> str:
        return 'MYSQL'
    
    def get_connection_options(self, connection_details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "host": connection_details['db_host_fqdn'],
            "port": connection_details['db_port'],
            "user": connection_details['user_username'],
            "password": connection_details['user_password']
        }
    
    def get_terraform_resource_config(self) -> Dict[str, Any]:
        return {
            'version': '8.0',
            'tier': 'Basic',
            'capacity': 2,
            'size_gb': 20
        }


class PostgreSqlProvider(DatabaseProviderBase):
    """PostgreSQL database provider"""
    
    def __init__(self):
        super().__init__('postgresql')
    
    def get_database_type(self) -> str:
        return 'postgresql'
    
    def get_default_port(self) -> str:
        return '5432'
    
    def get_connection_type(self) -> str:
        return 'POSTGRESQL'
    
    def get_connection_options(self, connection_details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "host": connection_details['db_host_fqdn'],
            "port": connection_details['db_port'],
            "user": connection_details['user_username'],
            "password": connection_details['user_password'],
            "sslmode": "require"
        }
    
    def get_terraform_resource_config(self) -> Dict[str, Any]:
        return {
            'version': '13',
            'tier': 'Basic',
            'capacity': 2,
            'size_gb': 20
        }


# Factory functions
def get_database_provider(db_type: str) -> DatabaseProviderBase:
    """Factory function to get database provider"""
    providers = {
        'sqlserver': SqlServerProvider,
        'mysql': MySqlProvider,
        'postgresql': PostgreSqlProvider
    }
    
    provider_class = providers.get(db_type.lower())
    if not provider_class:
        raise ValueError(f"Unsupported database type: {db_type}")
    
    return provider_class()


def get_cloud_provider(cloud_type: str, dbxrest: Any, config: Dict[str, Any], **kwargs) -> CloudProviderBase:
    """Factory function to get cloud provider"""
    # Import here to avoid circular imports
    if cloud_type.lower() == 'azure':
        try:
            from .SimpleAzure import AzureProvider
        except ImportError:
            from SimpleAzure import AzureProvider
        return AzureProvider(dbxrest, config, **kwargs)
    else:
        raise ValueError(f"Unsupported cloud provider: {cloud_type}")


def get_connection_suffix(db_type: str) -> str:
    """Get connection name suffix for database type"""
    suffixes = {
        'sqlserver': 'sq',
        'mysql': 'my',
        'postgresql': 'pg',
        'oracle': 'or'
    }
    return suffixes.get(db_type.lower(), 'db')
