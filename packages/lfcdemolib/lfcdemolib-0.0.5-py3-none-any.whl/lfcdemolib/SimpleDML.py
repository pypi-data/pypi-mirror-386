"""
SimpleDML - Simple Data Manipulation Language Operations

This module provides simple DML operations with capacity management and recent data focus.
It caps the number of recent DML operations even when the number of clients is unknown
by looking at the effective changes on the tables periodically.

Key Features:
- Monitors effective table changes through polling intervals
- Caps DML operations based on actual table state, not client count
- DELETE operations (remove old rows based on time threshold)
- UPDATE operations (modify existing rows with new timestamps)  
- INSERT operations (add new rows with current timestamps)
- Combined DELETE_UPDATE_INSERT operations (coordinated execution)
- Round-robin table selection for load balancing
- Multi-database support (MySQL, PostgreSQL, SQLite, Oracle, SQL Server)
- Intelligent capacity management regardless of unknown client scenarios
"""

import sqlalchemy as sa
import urllib.parse
import pandas as pd
import queue
import datetime
import random
import threading
from typing import Literal, Optional
from sqlalchemy.dialects.mssql import NVARCHAR
from sqlalchemy import TypeDecorator
from .LfcNotebookConfig import LfcNotebookConfig
from .LfcCredentialModel import LfcCredential
from .SimpleConn import SimpleConn
from .LfcScheduler import LfcScheduler
from pydantic import ValidationError

# Register SQL Server sysname type to suppress SQLAlchemy warnings
class SYSNAME(TypeDecorator):
    """SQL Server sysname type (equivalent to NVARCHAR(128) NOT NULL)"""
    impl = NVARCHAR
    cache_ok = True
    
    def __init__(self):
        super().__init__(length=128)

# Register the sysname type with SQL Server dialect
try:
    from sqlalchemy.dialects import mssql
    mssql.base.ischema_names['sysname'] = SYSNAME
except ImportError:
    # mssql dialect not available, skip registration
    pass

class SimpleDML:
    """SimpleDML - Simple Data Manipulation Language Operations
    
    Provides simple DML operations with capacity management and recent data focus.
    Caps the number of recent DML operations even when the number of clients is unknown
    by monitoring effective changes on tables through polling intervals. Uses actual
    table state to determine capacity limits rather than relying on client count.
    
    Initialization:
    ===============
    Direct instantiation with secrets_json - both secrets_json and config are REQUIRED:
    
        dml = SimpleDML(
            secrets_json=d.secrets_json,      # V2 credentials (REQUIRED - validated with LfcCredential)
            config=config,                    # Notebook config (REQUIRED - validated with LfcNotebookConfig)
            lfc_scheduler=scheduler,          # Optional: LfcScheduler for auto-scheduling DML operations
            metadata_refresh_interval=300     # Optional: refresh metadata every 5 minutes
        )
    
    Both secrets_json and config are validated using Pydantic models:
    - secrets_json → LfcCredential (V2 format only)
    - config → LfcNotebookConfig (accepts dict or LfcNotebookConfig instance)
    
    Instance Attributes:
    ===================
    After initialization, the following attributes are available:
    - self.credential: LfcCredential - Validated credential object from secrets_json
    - self.engine: SQLAlchemy Engine - Database connection engine
    - self.config: LfcNotebookConfig - Validated notebook configuration
    - self.schema: str - Database schema (from credential, config, or defaults)
    - self.metadata: SQLAlchemy MetaData - Database metadata for table operations
    
    Example Usage:
    ==============
    
        # Setup config
        config = {
            "source_connection_name": "lfcddemo-azure-sqlserver",
            "cdc_qbc": "cdc",
            "target_catalog": "main",
            "source_schema": None,
            "database": {"cloud": "azure", "type": "sqlserver"}
        }
        
        # Create scheduler and DbxRest
        scheduler = lfcdemolib.LfcScheduler()
        d = lfcdemolib.DbxRest(dbutils=dbutils, config=config, lfc_scheduler=scheduler)
        
        # Create SimpleDML directly
        dml = SimpleDML(d.secrets_json, config=config, lfc_scheduler=scheduler)
    
    Default Configuration:
    - DEFAULT_MAX_ROWS = 10 (maximum rows to process per operation)
    - DEFAULT_TIME_WINDOW_SECONDS = 60 (1 minute polling/time window for operations)
    
    Core Strategy:
    - Polls tables at regular intervals to assess effective changes
    - Caps DML operations based on actual recent activity in tables
    - Works regardless of unknown number of concurrent clients
    - Maintains data consistency through intelligent capacity management
    - Uses round-robin table selection for balanced load distribution
    """
    
    DRIVERS = {
        "mysql": "mysql+pymysql",
        "postgresql": "postgresql+psycopg2", 
        "sqlserver": "mssql+pymssql",
        "oracle": "oracle+oracledb",
        "sqlite": "sqlite"
    }
    
    DATETIME_COLUMN_NAMES = ['dt', 'created_at', 'updated_at', 'timestamp']
    DATETIME_COLUMN_NAMES_CASEFOLDED = [name.casefold() for name in DATETIME_COLUMN_NAMES]
    DATETIME_TYPE_PATTERNS = [
        'datetime', 'timestamp', 'timestamptz', 'datetime2', 
        'smalldatetime', 'datetimeoffset', 'timestamp with time zone',
        'timestamp without time zone'
    ]
    
    # Default configuration values
    DEFAULT_MAX_ROWS = 10
    DEFAULT_TIME_WINDOW_SECONDS = 60
    
    def __init__(self, secrets_json, config, lfc_scheduler: Optional[LfcScheduler] = None, 
                 metadata_refresh_interval: int = None,
                 time_window_seconds: int = None, run_duration_sec: int = 3600, 
                 workspace_client=None, auto_recreate: bool = False):
        """Initialize SimpleDML with secrets_json and config
        
        Args:
            secrets_json: Dictionary containing V2 connection credentials (REQUIRED)
                         Will be validated using LfcCredential Pydantic model
                         Schema is extracted from secrets_json.schema
            config: Configuration dict or LfcNotebookConfig instance (REQUIRED)
                   If dict, will be converted to LfcNotebookConfig
                   If config.source_schema is provided, it overrides the schema from secrets_json
            lfc_scheduler: Optional LfcScheduler instance for auto-scheduling DML operations
            metadata_refresh_interval: Interval for metadata refresh (default: from config or None)
            time_window_seconds: Time window for DML operations (default: from config or 60s)
            run_duration_sec: Duration for scheduled operations (default: 3600s)
            workspace_client: Optional Databricks WorkspaceClient for auto-recreation
            auto_recreate: Whether to automatically recreate database on connection failure (default: False)
        
        Schema Priority (highest to lowest):
            1. config.source_schema (if explicitly provided)
            2. secrets_json.schema (from LfcCredential)
            3. Database-specific defaults (dbo/public/catalog)
            
        Raises:
            ValueError: If config is not provided, secrets_json validation fails, or schema cannot be determined
            TypeError: If config is not dict or LfcNotebookConfig
            ValidationError: If secrets_json doesn't match V2 format
        """
        # Validate secrets_json using LfcCredential Pydantic model
        try:
            credential = LfcCredential.from_dict(secrets_json)
            print(f"✅ Validated secrets for {credential.connection_name or credential.name or 'connection'}")
        except ValidationError as e:
            # Provide helpful error message with details
            error_details = []
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                msg = error['msg']
                error_details.append(f"{field}: {msg}")
            raise ValueError(
                f"Invalid V2 secrets format: {'; '.join(error_details)}. "
                f"Provided fields: {list(secrets_json.keys())}"
            ) from e
        
        if config is None:
            raise ValueError(
                "config is required. Provide either a dict or LfcNotebookConfig instance."
            )
        
        # Convert config to LfcNotebookConfig if it's a dict
        if isinstance(config, dict):
            config = LfcNotebookConfig(config)
        elif not isinstance(config, LfcNotebookConfig):
            raise TypeError(
                f"config must be dict or LfcNotebookConfig, got {type(config).__name__}"
            )
        
        # Create engine using SimpleConn
        conn = SimpleConn(workspace_client=workspace_client)
        engine = conn.create_engine_from_secrets(secrets_json, auto_recreate=auto_recreate)
        
        # Store credential, engine, and config
        self.credential = credential  # Store validated LfcCredential for later use
        self.engine = engine
        self.config = config
        
        # Extract schema: First from secrets_json (credential), then override with config if provided
        # Priority: config.source_schema > credential.schema_name > database-specific defaults
        self.schema = credential.schema_name  # Get schema from validated credential
        
        # Override with config.source_schema if explicitly provided
        if self.config.source_schema is not None:
            self.schema = self.config.source_schema
        
        # If still None, apply database-specific defaults
        if self.schema is None:
            db_dialect = engine.dialect.name.lower()
            if db_dialect in ['mssql', 'sqlserver']:
                self.schema = 'dbo'
            elif db_dialect in ['postgresql', 'postgres']:
                self.schema = 'public'
            elif db_dialect == 'mysql':
                # MySQL uses database as schema
                self.schema = engine.url.database
            else:
                # Default fallback
                self.schema = 'public'
        
        # Validate that schema is set and not empty
        if not self.schema or self.schema == '':
            raise ValueError(
                f"Schema could not be determined. "
                f"credential.schema_name={credential.schema_name}, "
                f"config.source_schema={self.config.source_schema}, "
                f"db_type={credential.db_type}. "
                f"Please explicitly set 'schema' in secrets_json or 'source_schema' in config."
            )
        
        # Extract configuration values from config if not provided as parameters
        if metadata_refresh_interval is None:
            metadata_refresh_interval = getattr(self.config, 'metadata_refresh_interval', None)
        
        if time_window_seconds is None:
            time_window_seconds = getattr(self.config, 'time_window_seconds', None)
            
        if run_duration_sec is None:
            config_run_duration = getattr(self.config, 'run_duration_sec', None)
            if config_run_duration is not None:
                run_duration_sec = config_run_duration
        
        # Initialize round-robin state
        self._table_index = 0
        self._table_lock = threading.Lock()
        self._table_list = []  # Initialize empty list
        
        # Initialize metadata and table queue
        self._refresh_metadata()
        
        # Auto-schedule if lfc_scheduler is provided
        if lfc_scheduler is not None:
            self.schedule_delete_update_insert(lfc_scheduler.scheduler, time_window_seconds, run_duration_sec)
            
            # Schedule metadata refresh if interval is specified
            if metadata_refresh_interval is not None:
                self.schedule_metadata_refresh(lfc_scheduler.scheduler, metadata_refresh_interval, run_duration_sec)
                print(f"✅ SimpleDML auto-scheduled: DML operations + metadata refresh every {metadata_refresh_interval}s for {run_duration_sec}s")
            else:
                print(f"✅ SimpleDML auto-scheduled: DML operations for {run_duration_sec}s")
    
    def _get_next_table(self):
        """Get next table using thread-safe round-robin index"""
        with self._table_lock:
            if not self._table_list:
                # Use schema name for all databases
                schema_path = self.schema
                print(f"⚠️ No tables available for round-robin selection in {schema_path}")
                print(f"   Metadata tables: {list(self.metadata.tables.keys()) if hasattr(self, 'metadata') else 'None'}")
                return None
            
            # Get current table and round-robin info
            table_key = self._table_list[self._table_index]
            current_position = self._table_index + 1
            total_tables = len(self._table_list)
            
            # Advance to next table (with wraparound)
            self._table_index = (self._table_index + 1) % len(self._table_list)
            
            # Verify table exists in metadata
            if table_key not in self.metadata.tables:
                print(f"⚠️ Table '{table_key}' not found in metadata. Available tables: {list(self.metadata.tables.keys())}")
                return None
            
            # Store round-robin info for use in logging
            table_obj = self.metadata.tables[table_key]
            table_obj._round_robin_info = f"{current_position}/{total_tables}"
            
            return table_obj
    
    def get_table_info(self):
        """Get information about available tables and round-robin state"""
        with self._table_lock:
            table_list = sorted(list(self.metadata.tables.keys()))  # Show sorted for readability
            return {
                'table_count': len(table_list),
                'tables': table_list,
                'current_index': self._table_index,
                'round_robin_order': self._table_list.copy() if hasattr(self, '_table_list') else [],
                'randomized_order': True
            }
    
    def test_round_robin(self, num_selections=5):
        """Test round-robin selection by getting multiple tables"""
        print(f"🔍 Testing round-robin selection ({num_selections} selections):")
        selections = []
        
        for i in range(num_selections):
            try:
                table = self._get_next_table()
                table_name = self._get_qualified_table_name(table)
                selections.append(table_name)
                print(f"  {i+1}. {table_name}")
            except Exception as e:
                print(f"  {i+1}. ERROR: {e}")
                break
        
        print(f"📊 Selection pattern: {' → '.join(selections)}")
        return selections
    
    def _get_table(self, table_name: str):
        """Get specific table by name"""
        for key in self.metadata.tables:
            if key.endswith(table_name) or key == table_name:
                return self.metadata.tables[key]
        raise ValueError(f"Table '{table_name}' not found")
    
    def _get_datetime_column(self, table):
        """Get first datetime column from table"""
        for col in table.columns:
            col_type_str = str(col.type).casefold()
            if any(dt_type in col_type_str for dt_type in self.DATETIME_TYPE_PATTERNS):
                return col
            elif col.name.casefold() in self.DATETIME_COLUMN_NAMES_CASEFOLDED:
                return col
        raise ValueError(f"No datetime column found in table {table.name}")
    
    def _has_ops_column(self, table):
        """Check if table has an 'ops' column using reflection"""
        return any(col.name.casefold() == 'ops' for col in table.columns)
    
    def _get_qualified_table_name(self, table):
        """Get fully qualified table name with schema.table format
        
        Note: Uses schema.table (2-part) format for all databases, not catalog.schema.table
        """
        # Build path as schema.table for all databases
        parts = []
        if self.schema:
            parts.append(self.schema)
        parts.append(table.name)
        return '.'.join(parts)
    
    def _refresh_metadata(self):
        """Refresh metadata and rebuild table queue (thread-safe)"""
        # Create new metadata object
        new_metadata = sa.MetaData()
        new_metadata.reflect(bind=self.engine, schema=self.schema)
        
        # Get new table list (sorted for consistent round-robin, then randomized once at startup)
        new_tables = sorted(list(new_metadata.tables.keys()))
        
        # Atomically replace old objects with new ones
        old_table_count = len(self.metadata.tables) if hasattr(self, 'metadata') else 0
        old_table_list = self._table_list.copy() if hasattr(self, '_table_list') else []
        
        with self._table_lock:
            self.metadata = new_metadata
            
            # Only reset round-robin index if table list actually changed
            if set(new_tables) != set(old_table_list):
                # Randomize only when table list changes (not on every refresh)
                random.shuffle(new_tables)
                self._table_list = new_tables
                self._table_index = 0  # Reset index only when tables change
                print(f"🔄 Round-robin reset: table list changed from {len(old_table_list)} to {len(new_tables)} tables")
                print(f"🔍 Table order: {self._table_list}")
            else:
                # Keep existing order and position if tables are the same
                # Don't randomize on every refresh - this was causing the position confusion
                if not old_table_list:
                    # First time initialization - randomize once
                    random.shuffle(new_tables)
                    self._table_list = new_tables
                    self._table_index = 0
                    print(f"🔍 Table order: {self._table_list}")
                else:
                    # Keep existing order and position
                    self._table_list = old_table_list
                    # No change to self._table_index
        
        new_table_count = len(new_tables)
        
        # Only report metadata refresh when table changes are detected
        if new_table_count != old_table_count:
            if new_table_count > old_table_count:
                change_info = f"(+{new_table_count - old_table_count} added)"
            else:
                change_info = f"(-{old_table_count - new_table_count} removed)"
            print(f"✅ Metadata refreshed: {old_table_count} → {new_table_count} tables {change_info}")
        
        return new_table_count
    
    def refresh_metadata(self):
        """Manually refresh metadata and table discovery
        
        Returns:
            int: Number of tables discovered after refresh
        """
        return self._refresh_metadata()
    
    def schedule_metadata_refresh(self, scheduler, refresh_interval_seconds: int, run_duration_sec: int = 3600):
        """Schedule automatic metadata refresh
        
        Args:
            scheduler: APScheduler instance
            refresh_interval_seconds: Seconds between metadata refreshes
            run_duration_sec: Total duration to run refreshes (default: 3600)
        """
        # Use unique job ID per database (host_fqdn + catalog)
        job_id = f"{self.credential.host_fqdn}_{self.credential.catalog}_metadata_refresh"
        print(f"🔄 Scheduling metadata refresh job: {job_id}")
        
        scheduler.add_job(
            self._refresh_metadata,
            'interval', 
            seconds=refresh_interval_seconds, 
            replace_existing=False, 
            id=job_id,
            end_date=datetime.datetime.now() + datetime.timedelta(seconds=run_duration_sec),
            next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=refresh_interval_seconds)
        )
    
    
    def get_table_info(self):
        """Get information about currently discovered tables
        
        Returns:
            dict: Information about tables including count, names, and schema
        """
        table_names = list(self.metadata.tables.keys())
        return {
            'schema': self.schema,
            'table_count': len(table_names),
            'table_names': table_names,
            'qualified_names': [self._get_qualified_table_name(self.metadata.tables[name]) for name in table_names]
        }
    
    def _get_time_threshold(self, seconds_back: int):
        """Get database-native time threshold"""
        dialect = self.engine.dialect.name
        if dialect == 'mysql':
            return sa.text(f"DATE_SUB(NOW(), INTERVAL {seconds_back} SECOND)")
        elif dialect == 'postgresql':
            return sa.text(f"NOW() - INTERVAL '{seconds_back} seconds'")
        elif dialect == 'mssql':
            return sa.text(f"DATEADD(second, -{seconds_back}, GETDATE())")
        elif dialect == 'oracle':
            return sa.text(f"SYSDATE - INTERVAL '{seconds_back}' SECOND")
        elif dialect == 'sqlite':
            return sa.text(f"datetime('now', '-{seconds_back} seconds')")
        else:
            return sa.text(f"DATE_SUB(NOW(), INTERVAL {seconds_back} SECOND)")
    
    def _get_current_time_sql(self):
        """Get database-specific current time SQL"""
        dialect = self.engine.dialect.name
        if dialect == 'mysql':
            return "NOW()"
        elif dialect == 'postgresql':
            return "NOW()"
        elif dialect == 'mssql':
            return "GETDATE()"
        elif dialect == 'sqlite':
            return "datetime('now')"
        elif dialect == 'oracle':
            return "SYSDATE"
        else:
            return "NOW()"
    
    def _build_limited_where_clause(self, qualified_table_name: str, dt_column_name: str, time_threshold, limit_rows_param: str = ":limit_rows", target_recent: bool = False):
        """Build database-specific WHERE clause with LIMIT/TOP for targeting specific rows
        
        Args:
            qualified_table_name: Full table name with schema
            dt_column_name: Name of the datetime column
            time_threshold: Time threshold for filtering
            limit_rows_param: Parameter name for limit (default: ":limit_rows")
            target_recent: If True, target recent rows (>=) instead of old rows (<)
        
        Returns:
            SQL WHERE clause string
        """
        dialect = self.engine.dialect.name
        
        # Determine comparison operator and sort order
        if target_recent:
            comparison_op = ">="
            order_by = "DESC"  # Most recent first
        else:
            comparison_op = "<"
            order_by = "ASC"  # Oldest first
        
        if dialect == 'mysql':
            return f"""
                WHERE {dt_column_name} {comparison_op} {time_threshold}
                ORDER BY {dt_column_name} {order_by}
                LIMIT {limit_rows_param}
            """
        elif dialect == 'postgresql':
            return f"""
                WHERE ctid IN (
                    SELECT ctid FROM {qualified_table_name} 
                    WHERE {dt_column_name} {comparison_op} {time_threshold}
                    ORDER BY {dt_column_name} {order_by}
                    LIMIT {limit_rows_param}
                )
            """
        elif dialect == 'sqlite':
            return f"""
                WHERE rowid IN (
                    SELECT rowid FROM {qualified_table_name} 
                    WHERE {dt_column_name} {comparison_op} {time_threshold}
                    ORDER BY {dt_column_name} {order_by}
                    LIMIT {limit_rows_param}
                )
            """
        elif dialect == 'mssql':
            return f"WHERE {dt_column_name} {comparison_op} {time_threshold}"
        elif dialect == 'oracle':
            return f"""
                WHERE ROWID IN (
                    SELECT ROWID FROM (
                        SELECT ROWID FROM {qualified_table_name} 
                        WHERE {dt_column_name} {comparison_op} {time_threshold}
                        ORDER BY {dt_column_name} {order_by}
                    ) WHERE ROWNUM <= {limit_rows_param}
                )
            """
        else:
            return f"""
                WHERE {dt_column_name} {comparison_op} {time_threshold}
                ORDER BY {dt_column_name} {order_by}
                LIMIT {limit_rows_param}
            """

    def _resolve_parameters(self, max_rows: int = None, time_window_seconds: int = None):
        """Resolve parameters to their default values if None"""
        if max_rows is None:
            max_rows = self.DEFAULT_MAX_ROWS
        if time_window_seconds is None:
            time_window_seconds = self.DEFAULT_TIME_WINDOW_SECONDS
        return max_rows, time_window_seconds
    
    def _calculate_rows_needed(self, table, max_rows: int = None, time_window_seconds: int = None):
        """Calculate rows needed by polling table state within time window
        
        Caps DML operations by examining actual recent changes in the table,
        regardless of unknown client activity. Uses polling interval to assess
        effective table state and determine appropriate capacity limits.
        """
        max_rows, time_window_seconds = self._resolve_parameters(max_rows, time_window_seconds)
            
        dt_column = self._get_datetime_column(table)
        time_threshold = self._get_time_threshold(time_window_seconds)
        
        with self.engine.connect() as conn:
            # Count recent records within the time window
            recent_count = conn.execute(sa.select(sa.func.count()).select_from(table).where(
                dt_column > time_threshold
            )).scalar()
            
            rows_needed = max(0, max_rows - recent_count)
            return dt_column, time_threshold, rows_needed

    def _execute_update(self, table, max_rows: int = None, time_window_seconds: int = None, 
                       dt_column=None, time_threshold=None, rows_needed=None, 
                       is_retry: bool = False):
        """Universal update method for all tables (uses synthetic key approach)
        
        Args:
            table: SQLAlchemy table object
            max_rows: Maximum number of rows to update
            time_window_seconds: Time window for row selection
            dt_column: Pre-calculated datetime column (optional)
            time_threshold: Pre-calculated time threshold (optional)
            rows_needed: For normal update: Pre-calculated rows needed (optional)
                        For retry: Number of rows just inserted (REQUIRED - must be passed in)
            is_retry: If True, targets RECENT rows (>=) for retry; if False, targets OLD rows (<)
            
        Returns:
            int: Number of rows updated
        """
        # Determine operation type for logging
        op_type = 'update_retry' if is_retry else 'update'
        
        if is_retry:
            # For retry, rows_needed MUST be provided (number of rows just inserted)
            if rows_needed is None or rows_needed <= 0:
                # No rows to update
                return 0
            
            # Get dt_column and time_threshold for WHERE clause
            if dt_column is None:
                dt_column = self._get_datetime_column(table)
            if time_threshold is None:
                time_threshold = self._get_time_threshold(
                    time_window_seconds if time_window_seconds else self.DEFAULT_TIME_WINDOW_SECONDS
                )
            
            # rows_needed already set to the exact number of inserted rows
            # Don't recalculate - just use what was passed in
        else:
            # For normal update, use provided or calculate for old rows
            if dt_column is None or time_threshold is None or rows_needed is None:
                dt_column, time_threshold, rows_needed = self._calculate_rows_needed(table, max_rows, time_window_seconds)
            
            if rows_needed <= 0:
                return 0
        
        with self.engine.connect() as conn:
            current_time_sql = self._get_current_time_sql()
            dialect = self.engine.dialect.name
            
            # Check if ops column exists and build SET clause accordingly
            has_ops = self._has_ops_column(table)
            if has_ops:
                set_clause = f"{dt_column.name} = {current_time_sql}, ops='{op_type}'"
            else:
                set_clause = f"{dt_column.name} = {current_time_sql}"
            
            # Build UPDATE SQL using consolidated helper methods
            qualified_table_name = self._get_qualified_table_name(table)
            
            # Determine comparison operator based on retry flag
            comparison_op = ">=" if is_retry else "<"
            
            if dialect == 'mssql':
                # SQL Server uses TOP syntax
                update_sql = sa.text(f"""
                    UPDATE TOP(:limit_rows) {qualified_table_name} 
                    SET {set_clause} 
                    WHERE {dt_column.name} {comparison_op} {time_threshold}
                """)
            else:
                # All other databases use the limited WHERE clause
                where_clause = self._build_limited_where_clause(
                    qualified_table_name, 
                    dt_column.name, 
                    time_threshold,
                    target_recent=is_retry  # Target recent rows if retry, old rows otherwise
                )
                update_sql = sa.text(f"""
                    UPDATE {qualified_table_name} 
                    SET {set_clause} 
                    {where_clause}
                """)
            
            result = conn.execute(update_sql, {'limit_rows': rows_needed})
            conn.commit()
            return result.rowcount
    
    def _execute_update_retry(self, table, inserted_count: int, time_window_seconds: int = None, dt_column=None):
        """Execute UPDATE on recently inserted rows (for retry after INSERT)
        
        This is a convenience wrapper around _execute_update with is_retry=True.
        Targets RECENT rows (>= time_threshold) instead of OLD rows (< time_threshold).
        Updates exactly the number of rows that were just inserted.
        
        Args:
            table: SQLAlchemy table object
            inserted_count: Number of rows just inserted (will update this many rows)
            time_window_seconds: Time window for targeting recent rows (optional)
            dt_column: Pre-calculated datetime column (optional)
            
        Returns:
            int: Number of rows updated
        """
        return self._execute_update(
            table, 
            max_rows=None,  # Not used for retry
            time_window_seconds=time_window_seconds, 
            dt_column=dt_column,
            time_threshold=None,  # Will be calculated
            rows_needed=inserted_count,  # Use exact inserted count
            is_retry=True
        )
    
    def _execute_delete(self, table, max_rows: int = None, time_window_seconds: int = None, dt_column=None, time_threshold=None, rows_needed=None):
        """Delete old rows and report count"""
        
        # Only calculate if not provided
        if dt_column is None or time_threshold is None or rows_needed is None:
            dt_column, time_threshold, rows_needed = self._calculate_rows_needed(table, max_rows, time_window_seconds)
        
        if rows_needed <= 0:
            return 0
        
        with self.engine.connect() as conn:
            dialect = self.engine.dialect.name
            
            # Build DELETE SQL using consolidated helper methods
            qualified_table_name = self._get_qualified_table_name(table)
            
            if dialect == 'mssql':
                # SQL Server uses TOP syntax
                delete_sql = sa.text(f"""
                    DELETE TOP(:limit_rows) FROM {qualified_table_name} 
                    WHERE {dt_column.name} < {time_threshold}
                """)
            else:
                # All other databases use the limited WHERE clause
                where_clause = self._build_limited_where_clause(qualified_table_name, dt_column.name, time_threshold)
                delete_sql = sa.text(f"""
                    DELETE FROM {qualified_table_name} 
                    {where_clause}
                """)
            
            # Execute delete
            delete_result = conn.execute(delete_sql, {'limit_rows': rows_needed})
            deleted_count = delete_result.rowcount
            
            conn.commit()
            return deleted_count

    def _execute_insert(self, table, num_rows: int, dt_column=None):
        """Insert new rows and report count"""
        
        if num_rows <= 0:
            return 0
        
        # Get datetime column if not provided
        if dt_column is None:
            dt_column = self._get_datetime_column(table)
        
        with self.engine.connect() as conn:
            current_time_sql = self._get_current_time_sql()
            
            # Check if ops column exists and build INSERT accordingly
            has_ops = self._has_ops_column(table)
            if has_ops:
                columns = f"{dt_column.name}, ops"
                values_list = [f"({current_time_sql}, 'insert')" for _ in range(num_rows)]
            else:
                columns = dt_column.name
                values_list = [f"({current_time_sql})" for _ in range(num_rows)]
            
            values_clause = ", ".join(values_list)
            
            # Build the complete multi-row INSERT statement
            qualified_table_name = self._get_qualified_table_name(table)
            insert_sql = sa.text(f"""
                INSERT INTO {qualified_table_name} ({columns}) 
                VALUES {values_clause}
            """)
            
            # Execute single multi-row INSERT statement
            result = conn.execute(insert_sql)
            inserted_count = result.rowcount
            
            conn.commit()
            return inserted_count

    def execute_delete(self, max_rows: int = None, time_window_seconds: int = None, table_name: str = None):
        """Execute delete - uses round-robin if no table specified"""
        table = self._get_table(table_name) if table_name else self._get_next_table()
        return self._execute_delete(table, max_rows, time_window_seconds)

    def execute_insert(self, num_rows: int = None, table_name: str = None):
        """Execute insert - uses round-robin if no table specified"""
        # Use default max_rows if num_rows not provided
        if num_rows is None:
            num_rows = self.DEFAULT_MAX_ROWS
        table = self._get_table(table_name) if table_name else self._get_next_table()
        return self._execute_insert(table, num_rows)

    def execute_update(self, max_rows: int = None, time_window_seconds: int = None, table_name: str = None):
        """Execute update - uses round-robin if no table specified"""
        table = self._get_table(table_name) if table_name else self._get_next_table()
        return self._execute_update(table, max_rows, time_window_seconds)

    def _execute_delete_update_insert(self, table, max_rows: int = None, time_window_seconds: int = None):
        """Execute DELETE, UPDATE, then INSERT - uses separate functions with detailed reporting
        
        If UPDATE returns 0 rows but INSERT returns non-zero rows, retry UPDATE to update the newly inserted data.
        """
        
        # Resolve parameters using consolidated method
        max_rows, time_window_seconds = self._resolve_parameters(max_rows, time_window_seconds)
        
        # Calculate once for DELETE operations
        dt_column, time_threshold, rows_needed = self._calculate_rows_needed(table, max_rows, time_window_seconds)
        
        # Execute DELETE first
        deleted_count = self._execute_delete(
            table, max_rows, time_window_seconds, 
            dt_column=dt_column, time_threshold=time_threshold, rows_needed=rows_needed
        )
        
        # Execute UPDATE second (on remaining data)
        update_result = self._execute_update(table, max_rows, time_window_seconds)
        
        # Execute INSERT third - insert rows_needed if table is empty, otherwise replace deleted rows
        table_name = self._get_qualified_table_name(table)
        round_robin_info = getattr(table, '_round_robin_info', '')
        round_robin_prefix = f"🎯 {round_robin_info} " if round_robin_info else ""
        
        update_retry_result = 0
        update_retry_triggered = False
        
        if deleted_count > 0:
            # Replace deleted rows
            inserted_count = self._execute_insert(table, deleted_count, dt_column)
            
            # Check if UPDATE returned 0 rows but INSERT returned non-zero rows
            if update_result == 0 and inserted_count > 0:
                update_retry_triggered = True
                update_retry_result = self._execute_update_retry(table, inserted_count, time_window_seconds, dt_column)
            
            print(f"{round_robin_prefix}🔄 {table_name}: DEL={deleted_count}, UPD={update_result}, INS={inserted_count}" + 
                  (f", UPD_RETRY={update_retry_result}" if update_retry_triggered else ""))
        elif rows_needed > 0:
            # Table is empty or insufficient recent data, insert needed rows to reach target
            inserted_count = self._execute_insert(table, rows_needed, dt_column)
            
            # Check if UPDATE returned 0 rows but INSERT returned non-zero rows
            if update_result == 0 and inserted_count > 0:
                update_retry_triggered = True
                update_retry_result = self._execute_update_retry(table, inserted_count, time_window_seconds, dt_column)
            
            print(f"{round_robin_prefix}📈 {table_name}: DEL={deleted_count}, UPD={update_result}, INS={inserted_count} (needed {rows_needed} rows)" +
                  (f", UPD_RETRY={update_retry_result}" if update_retry_triggered else ""))
        else:
            # No rows needed
            inserted_count = 0
            print(f"{round_robin_prefix}✅ {table_name}: DEL={deleted_count}, UPD={update_result}, INS={inserted_count} (sufficient data)")
        
        result = {
            'expected_rows_needed': rows_needed,
            'max_rows_target': max_rows,
            'deleted': deleted_count,
            'inserted': inserted_count,
            'updated': update_result,
            'total_operations': deleted_count + inserted_count + update_result
        }
        
        # Add retry information if it occurred
        if update_retry_triggered:
            result['update_retry_triggered'] = True
            result['update_retry_result'] = update_retry_result
            result['updated_total'] = update_result + update_retry_result
            result['total_operations'] = deleted_count + inserted_count + update_result + update_retry_result
        
        return result

    def execute_delete_update_insert(self, max_rows: int = None, time_window_seconds: int = None, table_name: str = None):
        """Execute DELETE, UPDATE, then INSERT - uses round-robin if no table specified"""
        table = self._get_table(table_name) if table_name else self._get_next_table()
        
        if table is None:
            # Use schema name for all databases
            schema_path = self.schema
            print(f"⚠️ No table available for DML operations in {schema_path}. Skipping execution.")
            return {
                'status': 'skipped',
                'reason': 'no_tables_available',
                'schema': schema_path,
                'message': f'No tables found in {schema_path} for DML operations'
            }
        
        return self._execute_delete_update_insert(table, max_rows, time_window_seconds)

    def get_recent_data(self, seconds_back: int = None, table_name: str = None):
        """Get recent data - uses round-robin if no table specified"""
        # Use default time window if not provided
        if seconds_back is None:
            seconds_back = self.DEFAULT_TIME_WINDOW_SECONDS
            
        table = self._get_table(table_name) if table_name else self._get_next_table()
        
        if table is None:
            # Use schema name for all databases
            schema_path = self.schema
            print(f"⚠️ No table available for data retrieval in {schema_path}. Returning empty DataFrame.")
            return pd.DataFrame()  # Return empty DataFrame
        
        dt_column = self._get_datetime_column(table)
        time_threshold = self._get_time_threshold(seconds_back)
        
        query = sa.select(table).where(dt_column >= time_threshold).order_by(dt_column.desc())
        return pd.read_sql(query, self.engine)

    def schedule_delete_update_insert(self, scheduler, time_window_seconds:int = None, run_duration_sec:int = 3600):
        """Schedule automatic DELETE/UPDATE/INSERT operations
        
        Args:
            scheduler: APScheduler instance
            time_window_seconds: Interval between operations (default: DEFAULT_TIME_WINDOW_SECONDS)
            run_duration_sec: Total duration to run operations (default: 3600)
        """
        if time_window_seconds is None:
            time_window_seconds = self.DEFAULT_TIME_WINDOW_SECONDS
        
        # Use unique job ID per database (host_fqdn + catalog)
        job_id = f"{self.credential.host_fqdn}_{self.credential.catalog}_dml_update"
        print(f"🔄 Scheduling DML job: {job_id}")
        
        scheduler.add_job(self.execute_delete_update_insert, 
            'interval', seconds=time_window_seconds, replace_existing=False, id=job_id, 
            end_date=datetime.datetime.now() + datetime.timedelta(seconds=run_duration_sec), 
            next_run_time=datetime.datetime.now() )        