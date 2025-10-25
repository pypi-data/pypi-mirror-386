"""
LFC Demo Library - Lakeflow Connect Demo Components

This package provides utilities for Databricks Lakeflow Connect demonstrations:
- LfcScheduler: Background scheduler manager for asynchronous operations
- DbxRest: Databricks REST API management with cleanup queue and scheduler integration
- SimpleDML: Simple data manipulation language operations with capacity management
- LfcSchEvo: Lakeflow Connect Schema Evolution DDL support objects
- LfcConn: Lakeflow Connect Databricks Connection Management
- LfcSecrets: Lakeflow Connect Databricks Secrets Management
- LfcEnv: Lakeflow Connect Environment and User Information Management
- LfcDbPerm: Lakeflow Connect Database Permission Management
- LfcToken: Lakeflow Connect Token Management with Auto-Renewal
- SimpleAlter: Column addition and removal operations
- SimpleDDL: Data definition language operations
- LfcCDC: Change data capture management
- SimpleDB: Multi-cloud database creation and management using Terraform
- SimpleCloudBase: Base classes for cloud provider abstraction
- SimpleAzure: Azure-specific cloud provider implementation
- SimpleTest: Comprehensive testing module for all Simple components
- SimpleSqlalchemy: Centralized SQLAlchemy engine creation and management
- LfcCredentialModel: Pydantic models for database credential validation (V2 format)
- LfcNotebookConfig: Pydantic model for notebook configuration validation

Version tracking:
- Current version is stored in lfc/VERSION file
- Import version: from lfcdemolib import __version__
"""

# Import version first
from lfcdemolib.__version__ import __version__

from .LfcScheduler import LfcScheduler
try:
    from .DbxRest import DbxRest
    from .DemoInstance import DemoInstance
except ImportError:
    # DbxRest/DemoInstance may not be available in non-Databricks environments
    DbxRest = None
    DemoInstance = None
from .SimpleSqlalchemy import SimpleSqlalchemy, create_engine_from_secrets, create_dba_engine
from .SimpleConn import SimpleConn
from .SimpleLocalCred import SimpleLocalCred
from .LfcCredentialModel import LfcCredential, DbaCredentials, CloudInfo
from .LfcNotebookConfig import LfcNotebookConfig, DatabaseConfig
from .SimpleDML import SimpleDML
from .LfcSchEvo import LfcSchEvo
from .LfcConn import LfcConn
from .LfcSecrets import LfcSecrets
from .LfcEnv import LfcEnv, get_firstname_lastname, get_scope_name, get_connection_prefix
from .LfcDbPerm import LfcDbPerm, setup_permissive_permissions, setup_strict_permissions, verify_database_permissions
from .LfcToken import LfcToken, create_token_manager, get_token_with_auto_renewal
from .SimpleAlter import SimpleAlter
from .SimpleDDL import SimpleDDL
from .LfcCDC import LfcCDC
from .SimpleDB import SimpleDB, create_database_if_connection_missing
from .SimpleCloudBase import (
    CloudProviderBase, DatabaseProviderBase, TerraformProviderBase,
    SqlServerProvider, MySqlProvider, PostgreSqlProvider,
    get_cloud_provider, get_database_provider, get_connection_suffix
)
from .SimpleAzure import AzureProvider
from .SimpleTest import SimpleTest
from .TestComprehensive import TestComprehensive
from .TestDmlOnly import TestDmlOnly
from .TestDedicatedSchema import TestDedicatedSchema
from .TestFullDatabase import TestFullDatabase
from .TestAsyncParallel import TestAsyncParallel
from .SimpleMonitor import SimpleMonitor, PerformanceMetrics, SchemaMetrics, DMLOperationMetrics
from .SimpleReport import SimpleReport

# Build __all__ list dynamically based on what's available
__all__ = ["LfcScheduler", "SimpleSqlalchemy", "create_engine_from_secrets", "create_dba_engine", "SimpleConn", "SimpleLocalCred",
           "LfcCredential", "DbaCredentials", "CloudInfo",
           "LfcNotebookConfig", "DatabaseConfig",
           "SimpleDML", "LfcSchEvo", "LfcConn", "LfcSecrets", "LfcEnv", "get_firstname_lastname", "get_scope_name", "get_connection_prefix", 
           "LfcDbPerm", "setup_permissive_permissions", "setup_strict_permissions", "verify_database_permissions",
           "LfcToken", "create_token_manager", "get_token_with_auto_renewal",
           "SimpleAlter", "SimpleDDL", "LfcCDC", "SimpleDB", 
           "create_database_if_connection_missing", 
           "CloudProviderBase", "DatabaseProviderBase", "TerraformProviderBase",
           "SqlServerProvider", "MySqlProvider", "PostgreSqlProvider",
           "get_cloud_provider", "get_database_provider", "get_connection_suffix",
           "AzureProvider", "SimpleTest", "SimpleMonitor", 
           "PerformanceMetrics", "SchemaMetrics", "DMLOperationMetrics", "SimpleReport",
           "TestComprehensive", "TestDmlOnly", "TestDedicatedSchema", 
           "TestFullDatabase", "TestAsyncParallel"]

# Add DbxRest and DemoInstance to __all__ only if they're available
if DbxRest is not None:
    __all__.insert(0, "DbxRest")
if DemoInstance is not None:
    __all__.insert(0, "DemoInstance")
