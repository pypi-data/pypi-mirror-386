"""
LfcNotebookConfig - Pydantic model for LFC Databricks notebook configuration

This module provides a Pydantic model for validating notebook configuration
parameters used in LFC (Lakeflow Connect) demos and pipelines.

Features:
- Automatic validation of required fields
- Type safety with IDE autocomplete
- Clear, detailed error messages
- Nested database configuration validation
- Default values for optional fields
- Compatible with both Pydantic v1 and v2
"""

from lfcdemolib._pydantic_compat import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, Dict, Any


class DatabaseConfig(BaseModel):
    """Database configuration nested object
    
    Contains cloud provider and database type information.
    """
    cloud: Literal["azure"] = Field(
        ..., 
        description="Cloud provider (currently only azure is supported)"
    )
    type: Literal["sqlserver", "postgresql", "mysql"] = Field(
        ..., 
        description="Database type"
    )
    
    @field_validator('cloud', 'type', pre=True)
    def normalize_to_lowercase(cls, v):
        """Normalize cloud and type to lowercase"""
        if isinstance(v, str):
            return v.lower()
        return v


class LfcNotebookConfig(BaseModel):
    """
    LFC Notebook Configuration Model
    
    Validates and normalizes configuration parameters for LFC Databricks notebooks.
    
    Validation Rules:
    - If source_connection_name is blank (""), database config MUST be provided
    - If source_connection_name is provided, database config is optional
    
    Example 1: With connection name (database optional):
        >>> config_data = {
        ...     "source_connection_name": "lfcddemo-azure-pg-both",
        ...     "cdc_qbc": "cdc",
        ...     "target_catalog": "main",
        ...     "source_schema": None
        ... }
        >>> config = LfcNotebookConfig.from_dict(config_data)
        >>> config.source_connection_name
        'lfcddemo-azure-pg-both'
    
    Example 2: Without connection name (database required):
        >>> config_data = {
        ...     "source_connection_name": "",
        ...     "cdc_qbc": "cdc",
        ...     "target_catalog": "main",
        ...     "source_schema": None,
        ...     "database": {
        ...         "cloud": "azure",
        ...         "type": "postgresql"
        ...     }
        ... }
        >>> config = LfcNotebookConfig.from_dict(config_data)
        >>> config.database.type
        'postgresql'
    """
    
    # Required fields
    source_connection_name: Literal[
        "lfcddemo-azure-sqlserver-both",
        "lfcddemo-azure-sqlserver-ct",
        "lfcddemo-azure-mysql-both",
        "lfcddemo-azure-pg-both",
        "lfcddemo-oci-19c",
        ""  # Empty string is allowed in the widget
    ] = Field(
        ...,
        description="Source database connection name (from Databricks Connections)"
    )
    
    cdc_qbc: Literal["cdc", "qbc"] = Field(
        ...,
        description="Replication mode: CDC (Change Data Capture) or QBC (Query-Based Change)"
    )
    
    # Optional fields with defaults
    target_catalog: str = Field(
        default="main",
        description="Target Unity Catalog name where data will be ingested (defaults to 'main' if blank or not provided)"
    )
    
    source_schema: Optional[str] = Field(
        default=None,
        description="Source database schema name (None = auto-detect or use default)"
    )
    
    # Nested database configuration (conditionally required - required if source_connection_name is blank)
    database: Optional[DatabaseConfig] = Field(
        default=None,
        description="Database configuration with cloud provider and type (required if source_connection_name is blank)"
    )
    
    @field_validator('target_catalog', pre=True, always=True)
    def validate_target_catalog(cls, v: Optional[str]) -> str:
        """Ensure target_catalog defaults to 'main' if blank or not provided
        
        Converts None or empty string to 'main'
        """
        if v is None or v == "":
            return "main"
        return v
    
    @model_validator(mode='after')
    def validate_connection_or_database(cls, values):
        """Validate that database config is provided if source_connection_name is blank
        
        Logic:
        - If source_connection_name is blank/empty, database config MUST be provided
        - If source_connection_name is provided, database config is optional
        
        Note: In Pydantic v2 with mode='after', values is the model instance.
              In Pydantic v1 (via compat layer), values is a dict.
        """
        # Handle both Pydantic v1 (dict) and v2 (model instance)
        if isinstance(values, dict):
            # Pydantic v1 via compatibility layer
            conn_name = values.get('source_connection_name', '')
            database = values.get('database')
        else:
            # Pydantic v2 - values is the model instance
            conn_name = values.source_connection_name
            database = values.database
        
        # If connection name is blank or empty, database config is required
        if not conn_name or conn_name == "":
            if not database:
                raise ValueError(
                    "database configuration is required when source_connection_name is blank. "
                    "Please provide database config with 'cloud' and 'type' fields."
                )
        
        return values
    
    @field_validator('database')
    def validate_database_config(cls, v: Optional[DatabaseConfig]) -> Optional[DatabaseConfig]:
        """Validate database config has required fields
        
        Note: Cross-field validation with source_connection_name is done in
        validate_connection_or_database model validator to maintain v1/v2 compatibility.
        """
        # Skip validation if database is None (optional field)
        if v is None:
            return v
        
        # Basic validation - ensure required fields are present
        if not hasattr(v, 'type') or not v.type:
            raise ValueError("database config must have 'type' field")
        if not hasattr(v, 'cloud') or not v.cloud:
            raise ValueError("database config must have 'cloud' field")
        
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format (matching original config structure)
        
        Returns:
            dict: Configuration in dictionary format
        """
        return self.dict(exclude_none=False)
    
    def to_config_dict(self) -> Dict[str, Any]:
        """Convert to config dictionary (with None values preserved)
        
        Returns:
            dict: Configuration in original format
        """
        return {
            'source_connection_name': self.source_connection_name,
            'cdc_qbc': self.cdc_qbc,
            'target_catalog': self.target_catalog,
            'source_schema': self.source_schema,
            'database': {
                'cloud': self.database.cloud,
                'type': self.database.type
            }
        }
    
    def __init__(self, __data: Dict[str, Any] = None, **kwargs):
        """Initialize LfcNotebookConfig from dict or keyword arguments
        
        Args:
            __data: Configuration dictionary (optional, for convenience)
            **kwargs: Configuration fields as keyword arguments
            
        Example:
            >>> # From dict:
            >>> config = LfcNotebookConfig(config_dict)
            >>> 
            >>> # From kwargs:
            >>> config = LfcNotebookConfig(
            ...     source_connection_name="lfcddemo-azure-pg-both",
            ...     cdc_qbc="cdc",
            ...     database={"cloud": "azure", "type": "postgresql"}
            ... )
        """
        if __data is not None:
            # If dict provided, merge with kwargs
            super().__init__(**{**__data, **kwargs})
        else:
            # If no dict, use kwargs only
            super().__init__(**kwargs)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LfcNotebookConfig':
        """Create LfcNotebookConfig from dictionary with automatic validation
        
        Args:
            data: Dictionary containing configuration data
            
        Returns:
            LfcNotebookConfig: Validated configuration object
            
        Raises:
            pydantic.ValidationError: If validation fails with detailed error messages
            
        Example:
            >>> try:
            ...     config = LfcNotebookConfig.from_dict({"invalid": "data"})
            ... except ValidationError as e:
            ...     print(e)  # Shows exactly which fields are missing/invalid
        """
        return cls(**data)
    
    @classmethod
    def from_widgets(cls, dbutils) -> 'LfcNotebookConfig':
        """Create LfcNotebookConfig from Databricks widgets
        
        Convenience method to read widget values and create a validated config.
        
        Args:
            dbutils: Databricks utilities object
            
        Returns:
            LfcNotebookConfig: Validated configuration object
            
        Example:
            >>> config = LfcNotebookConfig.from_widgets(dbutils)
            >>> print(f"Using connection: {config.source_connection_name}")
        """
        return cls(
            source_connection_name=dbutils.widgets.get("connection"),
            cdc_qbc=dbutils.widgets.get("cdc_qbc"),
            target_catalog=dbutils.widgets.get("target_catalog") if "target_catalog" in [w.name for w in dbutils.widgets.getAll()] else "main",
            source_schema=None,  # Default
            database={
                "cloud": dbutils.widgets.get("cloud"),
                "type": dbutils.widgets.get("db_type")
            }
        )
    
    def __str__(self) -> str:
        """String representation"""
        if self.database:
            return (
                f"LfcNotebookConfig("
                f"connection={self.source_connection_name}, "
                f"mode={self.cdc_qbc}, "
                f"db={self.database.type}, "
                f"cloud={self.database.cloud}, "
                f"catalog={self.target_catalog})"
            )
        else:
            return (
                f"LfcNotebookConfig("
                f"connection={self.source_connection_name}, "
                f"mode={self.cdc_qbc}, "
                f"catalog={self.target_catalog})"
            )
    
    def __repr__(self) -> str:
        """Developer representation"""
        return self.__str__()


# Convenience function for backward compatibility
def validate_config(data: Dict[str, Any]) -> LfcNotebookConfig:
    """Validate configuration data and return LfcNotebookConfig object
    
    Args:
        data: Dictionary containing configuration data
        
    Returns:
        LfcNotebookConfig: Validated configuration object
        
    Raises:
        pydantic.ValidationError: If validation fails
    """
    return LfcNotebookConfig.from_dict(data)

