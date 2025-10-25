"""
DemoInstance - Simplified Demo Initialization

This module provides a simplified facade for creating and managing demo instances.
Handles scheduler, DbxRest, and SimpleDML initialization with proper singleton
management and caching.

Usage:
    from lfcdemolib import DemoInstance
    
    # Simple one-liner
    d = DemoInstance(config_dict, dbutils)
    
    # With Spark session
    d = DemoInstance(config_dict, dbutils, spark)
    
    # Access components
    d.secrets_json        # From DbxRest
    d.create_pipeline()   # DbxRest methods
    d.dml                 # SimpleDML instance
    d.scheduler           # Shared scheduler
    d.spark               # Spark session (if provided)
    
    # Multiple configs
    d1 = DemoInstance(config1, dbutils)
    d2 = DemoInstance(config2, dbutils, spark)  # Reuses scheduler, caches instances
"""

from typing import Dict, Any, Optional
from .LfcScheduler import LfcScheduler
from .DbxRest import DbxRest
from .SimpleDML import SimpleDML
from .LfcNotebookConfig import LfcNotebookConfig


class DemoInstance:
    """Simplified demo instance creation and management
    
    Provides a single-line initialization for demo notebooks that handles:
    - Scheduler singleton management
    - DbxRest instance caching by connection+mode
    - SimpleDML instance caching by connection
    - Automatic reinitialization control
    
    Class-level caching ensures instances are reused across multiple calls
    with the same configuration.
    
    Attributes:
        config: LfcNotebookConfig instance
        dbx: DbxRest instance
        dml: SimpleDML instance
        scheduler: Shared LfcScheduler instance
        dbutils: Databricks dbutils object
        spark: Spark session object (optional)
    """
    
    # Class-level shared state (singleton pattern)
    _scheduler: Optional[LfcScheduler] = None
    _dmls: Dict[str, SimpleDML] = {}
    _dbxs: Dict[str, DbxRest] = {}
    
    def __init__(self, config_dict: Dict[str, Any], dbutils: Any, spark: Any = None, re_calc_on_re_run: bool = True):
        """Initialize or retrieve cached demo instances
        
        Args:
            config_dict: Configuration dictionary for LfcNotebookConfig
            dbutils: Databricks dbutils object
            spark: Spark session object (optional, for future use)
            re_calc_on_re_run: Whether to reinitialize DbxRest on rerun (default: True)
        
        Example:
            d = DemoInstance(config_dict, dbutils)
            d = DemoInstance(config_dict, dbutils, spark)
            d.create_pipeline(...)
            df = d.dml.get_recent_data()
        """
        # Store dbutils and spark for future use
        self.dbutils = dbutils
        self.spark = spark
        # Create or get shared scheduler
        if DemoInstance._scheduler is None:
            DemoInstance._scheduler = LfcScheduler()
            print("🔧 Created shared scheduler for all demo instances")
        
        # Create config
        self.config = LfcNotebookConfig(config_dict)
        
        # Generate cache keys
        dbx_key = f"{self.config.source_connection_name}_{self.config.cdc_qbc}"
        dml_key = self.config.source_connection_name
        
        # Store keys as instance attributes for tuple unpacking
        self._dbx_key = dbx_key
        self._dml_key = dml_key
        
        # Create or get DbxRest instance
        if dbx_key not in DemoInstance._dbxs:
            print(f"📦 Creating new DbxRest instance: {dbx_key}")
            DemoInstance._dbxs[dbx_key] = DbxRest(
                dbutils=dbutils,
                lfc_scheduler=DemoInstance._scheduler,
                config=self.config
            )
        elif re_calc_on_re_run:
            print(f"🔄 Reinitializing existing DbxRest instance: {dbx_key}")
            DemoInstance._dbxs[dbx_key].initialize(re_calc=True)
        else:
            print(f"♻️  Reusing cached DbxRest instance: {dbx_key}")
        
        # Create or get SimpleDML instance
        if dml_key not in DemoInstance._dmls:
            print(f"📦 Creating new SimpleDML instance: {dml_key}")
            DemoInstance._dmls[dml_key] = SimpleDML(
                secrets_json=DemoInstance._dbxs[dbx_key].secrets_json,
                lfc_scheduler=DemoInstance._scheduler,
                config=self.config
            )
        else:
            print(f"♻️  Reusing cached SimpleDML instance: {dml_key}")
        
        # Expose instances as attributes
        self.dbx = DemoInstance._dbxs[dbx_key]
        self.dml = DemoInstance._dmls[dml_key]
        self.scheduler = DemoInstance._scheduler
        
        # Store keys for reference
        self._dbx_key = dbx_key
        self._dml_key = dml_key
    
    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to DbxRest instance
        
        This allows DemoInstance to be used as a drop-in replacement for DbxRest.
        All DbxRest methods and properties are accessible directly on DemoInstance.
        
        Args:
            name: Attribute name
            
        Returns:
            Attribute value from self.dbx
            
        Example:
            d = DemoInstance(config_dict, dbutils)
            d.secrets_json        # Delegates to d.dbx.secrets_json
            d.create_pipeline()   # Delegates to d.dbx.create_pipeline()
        """
        try:
            return getattr(self.dbx, name)
        except AttributeError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}' "
                f"(not found in DemoInstance or DbxRest)"
            )
    
    @classmethod
    def get_all_instances(cls) -> Dict[str, Any]:
        """Get all cached instances
        
        Returns:
            dict: Dictionary with 'scheduler', 'dbxs', and 'dmls' keys
            
        Example:
            instances = DemoInstance.get_all_instances()
            print(f"Scheduler: {instances['scheduler']}")
            print(f"DbxRest instances: {list(instances['dbxs'].keys())}")
            print(f"SimpleDML instances: {list(instances['dmls'].keys())}")
        """
        return {
            'scheduler': cls._scheduler,
            'dbxs': cls._dbxs,
            'dmls': cls._dmls
        }
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached instances
        
        Useful for testing or when you want to force recreation of all instances.
        
        Example:
            DemoInstance.clear_cache()
            d = DemoInstance(config_dict, dbutils)  # Fresh instances
        """
        cls._dmls.clear()
        cls._dbxs.clear()
        if cls._scheduler is not None:
            cls._scheduler.shutdown(wait=False)
            cls._scheduler = None
        print("🗑️  Cleared all cached instances")
    
    @classmethod
    def get_cached_instance(cls, connection_name: str, cdc_qbc: str = None) -> Optional['DemoInstance']:
        """Get a cached instance by connection name
        
        Args:
            connection_name: Source connection name
            cdc_qbc: CDC/QBC mode (optional, uses first match if not provided)
            
        Returns:
            DemoInstance if found, None otherwise
            
        Example:
            d = DemoInstance.get_cached_instance('lfcddemo-azure-mysql')
        """
        if cdc_qbc:
            dbx_key = f"{connection_name}_{cdc_qbc}"
            if dbx_key in cls._dbxs:
                # Create a shell instance (without calling __init__)
                instance = cls.__new__(cls)
                instance.dbx = cls._dbxs[dbx_key]
                instance.dml = cls._dmls.get(connection_name)
                instance.scheduler = cls._scheduler
                instance.config = instance.dbx.config
                instance._dbx_key = dbx_key
                instance._dml_key = connection_name
                return instance
        else:
            # Find first matching connection
            for key in cls._dbxs:
                if key.startswith(connection_name):
                    instance = cls.__new__(cls)
                    instance.dbx = cls._dbxs[key]
                    instance.dml = cls._dmls.get(connection_name)
                    instance.scheduler = cls._scheduler
                    instance.config = instance.dbx.config
                    instance._dbx_key = key
                    instance._dml_key = connection_name
                    return instance
        return None
    
    def __iter__(self):
        """Make instance iterable for tuple unpacking
        
        Allows backward-compatible syntax:
            d, config, dbxs, dmls, dbx_key, dml_key, scheduler = lfcdemolib.DemoInstance(config_dict, dbutils)
        
        Returns tuple of:
            (self, config, dbxs, dmls, dbx_key, dml_key, scheduler)
        """
        return iter((self, self.config, DemoInstance._dbxs, DemoInstance._dmls, self._dbx_key, self._dml_key, DemoInstance._scheduler))
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"DemoInstance(connection={self.config.source_connection_name}, "
            f"mode={self.config.cdc_qbc}, "
            f"dbx_cached={self._dbx_key in DemoInstance._dbxs}, "
            f"dml_cached={self._dml_key in DemoInstance._dmls})"
        )

