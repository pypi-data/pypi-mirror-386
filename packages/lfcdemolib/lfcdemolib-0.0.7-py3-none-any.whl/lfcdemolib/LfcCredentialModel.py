"""
LfcCredentialModel - Pydantic models for LFC database credentials

This module provides Pydantic models for validating and managing database credentials
with automatic type checking, validation, and clear error messages.

Features:
- Automatic validation of all required fields
- Type safety with IDE autocomplete
- Clear, detailed error messages
- Nested object validation (dba, cloud)
- Default value generation
- Field coercion (string ports -> int)
- Backward compatibility with dict format
- Compatible with both Pydantic v1 and v2
"""

from lfcdemolib._pydantic_compat import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, Dict, Any
from datetime import datetime
import json
from pathlib import Path


class DbaCredentials(BaseModel):
    """DBA credentials nested object
    
    Contains administrative credentials for database operations
    that require elevated privileges.
    """
    user: str = Field(..., description="DBA username", min_length=1)
    password: str = Field(..., description="DBA password", min_length=1)


class CloudInfo(BaseModel):
    """Cloud provider information nested object
    
    Contains cloud provider details for database instances.
    """
    provider: Literal["azure", "aws", "gcp"] = Field(
        ..., 
        description="Cloud provider name"
    )
    location: Optional[str] = Field(
        None, 
        description="Cloud region/location (e.g., 'East US', 'us-west-2')"
    )
    
    @field_validator('provider', pre=True)
    def normalize_provider(cls, v: str) -> str:
        """Normalize provider to lowercase"""
        if isinstance(v, str):
            return v.lower()
        return v


class LfcCredential(BaseModel):
    """
    LFC Credential Model (V2 Format)
    
    Validates and normalizes database credentials with automatic:
    - Type validation (db_type must be postgresql/mysql/sqlserver)
    - Required field checking (raises clear errors if missing)
    - Default values (schema, connection names)
    - Field normalization (lowercase db_type, strip whitespace)
    - Nested object validation (dba, cloud)
    - Port coercion (string "5432" -> int 5432)
    
    Example:
        >>> cred_data = {
        ...     "version": "v2",
        ...     "db_type": "postgresql",
        ...     "host_fqdn": "mydb.postgres.database.azure.com",
        ...     "catalog": "mydb",
        ...     "user": "myuser",
        ...     "password": "mypass",
        ...     "port": 5432,
        ...     "dba": {"user": "postgres", "password": "adminpass"},
        ...     "cloud": {"provider": "azure", "location": "East US"}
        ... }
        >>> cred = LfcCredential.from_dict(cred_data)
        >>> cred.db_type
        'postgresql'
        >>> cred.dba.user
        'postgres'
    """
    
    # Version
    version: Literal["v2"] = Field(
        default="v2", 
        description="Credential format version"
    )
    
    # Required fields
    db_type: Literal["postgresql", "mysql", "sqlserver"] = Field(
        ..., 
        description="Database type (postgresql, mysql, or sqlserver)"
    )
    host_fqdn: str = Field(
        ..., 
        description="Fully qualified domain name of database server",
        min_length=1
    )
    catalog: str = Field(
        ..., 
        description="Database/catalog name",
        min_length=1
    )
    user: str = Field(
        ..., 
        description="Regular user username",
        min_length=1
    )
    password: str = Field(
        ..., 
        description="Regular user password",
        min_length=1
    )
    port: int = Field(
        ..., 
        description="Database port number",
        ge=1,
        le=65535
    )
    
    # Nested objects (required)
    dba: DbaCredentials = Field(
        ..., 
        description="DBA credentials for administrative operations"
    )
    cloud: CloudInfo = Field(
        ..., 
        description="Cloud provider information"
    )
    
    # Optional fields with defaults
    schema_name: Optional[str] = Field(
        None, 
        alias='schema',
        description="Default schema (auto-generated based on db_type if not provided)"
    )
    replication_mode: Optional[str] = Field(
        None, 
        description="Replication mode (CDC or CT)"
    )
    name: Optional[str] = Field(
        None, 
        description="Connection display name (auto-generated if not provided)"
    )
    connection_name: Optional[str] = Field(
        None, 
        description="Connection identifier (auto-generated if not provided)"
    )
    created_at: Optional[datetime] = Field(
        None, 
        description="Creation timestamp"
    )
    
    # Additional optional fields
    terraform_dir: Optional[str] = Field(None, description="Terraform directory path")
    
    @field_validator('db_type', pre=True)
    def normalize_and_validate_db_type(cls, v: str) -> str:
        """Normalize db_type to lowercase
        
        Note: Cross-field validation (checking against host_fqdn) is done in
        the model validator to maintain v1/v2 compatibility.
        """
        if isinstance(v, str):
            v = v.lower()
        
        return v
    
    @field_validator('port', pre=True)
    def coerce_port(cls, v) -> int:
        """Coerce port to integer if it's a string"""
        if isinstance(v, str):
            if v.isdigit():
                return int(v)
            else:
                raise ValueError(f"Port must be a number, got: {v}")
        return v
    
    @model_validator(mode='after')
    def set_defaults(cls, values):
        """Set default values for schema, names, and created_at
        
        Note: In Pydantic v2 with mode='after', values is the model instance.
              In Pydantic v1 (via compat layer), values is a dict.
        """
        # Handle both Pydantic v1 (dict) and v2 (model instance)
        if isinstance(values, dict):
            # Pydantic v1 - values is a dict
            # Set default schema based on database type if not provided
            if values.get('schema_name') is None:
                db_type = values.get('db_type', 'postgresql')
                catalog = values.get('catalog', '')
                schema_defaults = {
                    'postgresql': 'public',
                    'mysql': catalog,  # MySQL uses database as schema
                    'sqlserver': 'dbo'
                }
                values['schema_name'] = schema_defaults.get(db_type, 'public')
            
            # Set default connection names if not provided
            if values.get('name') is None and values.get('cloud') and values.get('db_type') and values.get('catalog'):
                cloud_provider = values['cloud'].provider if hasattr(values['cloud'], 'provider') else 'unknown'
                values['name'] = f"{cloud_provider}-{values['db_type']}-{values['catalog']}"
            
            if values.get('connection_name') is None:
                values['connection_name'] = values.get('name')
            
            # Set created_at timestamp if not provided
            if values.get('created_at') is None:
                values['created_at'] = datetime.now()
            
            # Validate db_type against hostname
            if values.get('host_fqdn') and values.get('db_type'):
                host = values['host_fqdn'].lower()
                db_type = values['db_type']
                
                if 'postgres' in host and db_type not in ['postgresql', 'postgres']:
                    print(f"⚠️  WARNING: Host '{host}' suggests PostgreSQL but db_type is '{db_type}' - using '{db_type}'")
                elif 'mysql' in host and db_type != 'mysql':
                    print(f"⚠️  WARNING: Host '{host}' suggests MySQL but db_type is '{db_type}' - using '{db_type}'")
                elif ('sqlserver' in host or 'database.windows.net' in host) and db_type not in ['sqlserver', 'mssql']:
                    print(f"⚠️  WARNING: Host '{host}' suggests SQL Server but db_type is '{db_type}' - using '{db_type}'")
        else:
            # Pydantic v2 - values is the model instance
            # Set default schema based on database type if not provided
            if values.schema_name is None:
                db_type = values.db_type or 'postgresql'
                catalog = values.catalog or ''
                schema_defaults = {
                    'postgresql': 'public',
                    'mysql': catalog,  # MySQL uses database as schema
                    'sqlserver': 'dbo'
                }
                values.schema_name = schema_defaults.get(db_type, 'public')
            
            # Set default connection names if not provided
            if values.name is None and values.cloud and values.db_type and values.catalog:
                cloud_provider = values.cloud.provider if hasattr(values.cloud, 'provider') else 'unknown'
                values.name = f"{cloud_provider}-{values.db_type}-{values.catalog}"
            
            if values.connection_name is None:
                values.connection_name = values.name
            
            # Set created_at timestamp if not provided
            if values.created_at is None:
                values.created_at = datetime.now()
            
            # Validate db_type against hostname
            if values.host_fqdn and values.db_type:
                host = values.host_fqdn.lower()
                db_type = values.db_type
                
                if 'postgres' in host and db_type not in ['postgresql', 'postgres']:
                    print(f"⚠️  WARNING: Host '{host}' suggests PostgreSQL but db_type is '{db_type}' - using '{db_type}'")
                elif 'mysql' in host and db_type != 'mysql':
                    print(f"⚠️  WARNING: Host '{host}' suggests MySQL but db_type is '{db_type}' - using '{db_type}'")
                elif ('sqlserver' in host or 'database.windows.net' in host) and db_type not in ['sqlserver', 'mssql']:
                    print(f"⚠️  WARNING: Host '{host}' suggests SQL Server but db_type is '{db_type}' - using '{db_type}'")
        
        return values
    
    def to_secrets_json(self) -> Dict[str, Any]:
        """Convert to secrets_json format for backward compatibility
        
        Returns:
            dict: Credential data in dictionary format
        """
        return self.dict(exclude_none=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format
        
        Returns:
            dict: Credential data in dictionary format
        """
        return self.dict(exclude_none=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LfcCredential':
        """Create LfcCredential from dictionary with automatic validation
        
        Args:
            data: Dictionary containing credential data
            
        Returns:
            LfcCredential: Validated credential object
            
        Raises:
            pydantic.ValidationError: If validation fails with detailed error messages
            
        Example:
            >>> try:
            ...     cred = LfcCredential.from_dict({"invalid": "data"})
            ... except ValidationError as e:
            ...     print(e)  # Shows exactly which fields are missing/invalid
        """
        return cls(**data)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'LfcCredential':
        """Load and validate credential from JSON file
        
        Args:
            filepath: Path to JSON credential file
            
        Returns:
            LfcCredential: Validated credential object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
            pydantic.ValidationError: If credential data is invalid
        """
        path = Path(filepath)
        with path.open('r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def get_default_port(self) -> int:
        """Get default port for the database type
        
        Returns:
            int: Default port number
        """
        ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'sqlserver': 1433
        }
        return ports.get(self.db_type, self.port)
    
    def to_sqlalchemy_params(self, use_dba: bool = False, target_database: Optional[str] = None) -> Dict[str, Any]:
        """Convert to parameters suitable for SimpleSqlalchemy.create_engine()
        
        Args:
            use_dba: Whether to use DBA credentials
            target_database: Override database name
            
        Returns:
            dict: Parameters for create_engine()
        """
        if use_dba:
            username = self.dba.user
            password = self.dba.password
        else:
            username = self.user
            password = self.password
        
        return {
            'db_type': self.db_type,
            'host': self.host_fqdn,
            'database': target_database or self.catalog,
            'username': username,
            'password': password,
            'port': self.port,
            'cloud': self.cloud.provider
        }
    
    def __str__(self) -> str:
        """String representation (hides passwords)"""
        return (
            f"LfcCredential("
            f"db_type={self.db_type}, "
            f"host={self.host_fqdn}, "
            f"catalog={self.catalog}, "
            f"user={self.user}, "
            f"cloud={self.cloud.provider})"
        )
    
    def __repr__(self) -> str:
        """Developer representation (hides passwords)"""
        return self.__str__()


# Convenience function for backward compatibility
def validate_credential(data: Dict[str, Any]) -> LfcCredential:
    """Validate credential data and return LfcCredential object
    
    Args:
        data: Dictionary containing credential data
        
    Returns:
        LfcCredential: Validated credential object
        
    Raises:
        pydantic.ValidationError: If validation fails
    """
    return LfcCredential.from_dict(data)

