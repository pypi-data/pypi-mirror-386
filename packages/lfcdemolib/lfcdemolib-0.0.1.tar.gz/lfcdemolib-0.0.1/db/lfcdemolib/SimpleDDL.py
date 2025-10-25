"""
SimpleDDL - Simple Data Definition Language operations

This module provides DDL (Data Definition Language) operations for creating and dropping
test tables with proper indexing and auto-increment support across multiple databases.

Key Features:
- Create intpk tables (integer primary key with auto-increment)
- Create dtix tables (datetime index with integer column)
- Drop tables with intelligent suffix handling
- Multi-database support (MySQL, PostgreSQL, SQLite, Oracle, SQL Server)
- Automatic table name conflict resolution with numeric suffixes
- Schema-aware table operations
- Protected core columns (integer + datetime + string) that cannot be deleted or altered
- Guaranteed presence of at least one integer, datetime, and string column in every table
- Enhanced indexing on dtix tables (both datetime and integer columns indexed)
"""

import sqlalchemy as sa
from typing import Literal
from .LfcCDC import LfcCDC
from .LfcSchEvo import LfcSchEvo


class SimpleDDL:
    """SimpleDDL - Simple Data Definition Language operations
    
    Provides DDL operations for creating and dropping test tables with proper
    indexing and auto-increment support across multiple database systems.
    
    Table Types:
    - intpk: Integer primary key tables (id auto-increment, dt datetime indexed, ops string)
    - dtix: Datetime index tables (dt datetime indexed, id integer, ops string - no auto-increment)
    
    Protected Columns (cannot be deleted or altered during randomized tests):
    - intpk tables: 'id' (integer), 'dt' (datetime), 'ops' (string)
    - dtix tables: 'dt' (datetime), 'id' (integer), 'ops' (string)
    
    All tables are guaranteed to have at least one integer column, one datetime column, and one string column.
    The dtix tables also have indexes on both the datetime (dt) and integer (id) columns.
    """
    
    def __init__(self, engine, schema: str = None, enable_cdc: bool = True, enable_lfc: bool = False, 
                 replication_filter: Literal['both', 'pk_only', 'no_pk_only'] = 'both', secrets_json=None, test_instance=None, shared_state=None):
        """Initialize SimpleDDL with database engine and optional schema
        
        Args:
            engine: SQLAlchemy engine for database connection
            schema: Optional schema name for table operations
            enable_cdc: Whether to automatically enable CDC/CT for created tables (default: True)
            enable_lfc: Whether to setup DDL support objects for Databricks LFC (default: False)
            replication_filter: Control which tables to enable replication for:
                - 'both': Enable for all tables (default)
                - 'pk_only': Enable only for tables with primary keys
                - 'no_pk_only': Enable only for tables without primary keys
            secrets_json: Optional secrets containing DBA credentials for CDC/CT operations
            shared_state: Optional shared state dictionary for coordinating between modules
        """
        self.engine = engine
        self.shared_state = shared_state or {}
        
        # Set schema - should always be passed explicitly
        if schema is None:
            dialect = engine.dialect.name.lower()
            self.schema = 'lfcddemo'
            print(f"⚠️  WARNING: SimpleDDL initialized without schema parameter!")
            print(f"   Using default fallback schema: '{self.schema}'")
            print(f"   This should be passed explicitly from SimpleTest or calling code.")
            print(f"   Example: SimpleDDL(engine, schema='lfcddemo')")
        else:
            self.schema = schema
            
        self.enable_cdc = enable_cdc
        self.enable_lfc = enable_lfc
        self.replication_filter = replication_filter
        self.secrets_json = secrets_json
        self.test_instance = test_instance
        
        # Initialize CDC handler if CDC is enabled
        if enable_cdc:
            # Create DBA engine if secrets are provided
            dba_engine = None
            if secrets_json:
                try:
                    dba_engine = LfcCDC.create_dba_engine(secrets_json)
                except Exception as e:
                    print(f"⚠️ Could not create DBA engine: {e}. Using regular engine for CDC operations.")
            
            self.cdc = LfcCDC(engine, schema, replication_filter, dba_engine, secrets_json, shared_state)
        else:
            self.cdc = None
        
        # Initialize LFC handler if LFC is enabled
        if enable_lfc:
            self.lfc = LfcSchEvo(engine, schema, replication_filter, secrets_json)
        else:
            self.lfc = None
    
    def create_test_tables(self, base_names=None, count_per_type=1, force_recreate=False):
        """Create intpk and dtix test tables with auto-increment IDs and proper indexing
        
        Args:
            base_names: List of base table names (default: ['intpk', 'dtix'])
            count_per_type: Number of tables to create for each base name (default: 1)
            force_recreate: If True, drop existing tables before creating new ones
            
        Returns:
            dict: Created table names and their structures
        """
        if base_names is None:
            base_names = ['intpk', 'dtix']
        
        created_tables = {}
        dialect = self.engine.dialect.name
        
        with self.engine.connect() as conn:
            for base_name in base_names:
                # Create multiple tables for each base name
                for i in range(count_per_type):
                    # Always find next available table name (don't overwrite existing tables)
                    # This ensures we create new tables with incremented suffixes
                    table_name = self._get_available_table_name(conn, base_name)
                    
                    # Create table based on type
                    if base_name == 'intpk':
                        created_tables[table_name] = self._create_intpk_table(conn, table_name, dialect)
                    elif base_name == 'dtix':
                        created_tables[table_name] = self._create_dtix_table(conn, table_name, dialect)
                    else:
                        # Generic table with id, dt, ops
                        created_tables[table_name] = self._create_generic_table(conn, table_name, dialect)
                    
                    print(f"✅ Created table: {self._get_qualified_table_name_str(table_name)}")
                    
                    # Enable CDC/CT if requested
                    if self.enable_cdc and self.cdc:
                        # Pass primary key status based on table type
                        has_pk = base_name == 'intpk'  # intpk tables have primary key, dtix tables don't
                        cdc_result = self.cdc.enable_cdc_for_table(table_name, has_pk)
                        created_tables[table_name]['cdc_result'] = cdc_result
                        
                        # Check for errors or warnings in CDC result
                        if cdc_result.get('status') == 'error':
                            error_msg = cdc_result.get('message', 'Unknown CDC error')
                            print(f"❌ CDC/CT enable failed for {table_name}: {error_msg}")
                            created_tables[table_name]['has_error'] = True
                            created_tables[table_name]['error_message'] = error_msg
                        elif cdc_result.get('status') == 'warning':
                            warning_msg = cdc_result.get('message', 'Unknown CDC warning')
                            print(f"⚠️  CDC/CT warning for {table_name}: {warning_msg}")
                            created_tables[table_name]['has_warning'] = True
                            created_tables[table_name]['warning_message'] = warning_msg
                    
                    # Setup DDL support objects if requested (first table only)
                    if self.enable_lfc and self.lfc and len(created_tables) == 1:
                        # Check if CDC is supported and adjust LFC mode accordingly
                        lfc_mode = None
                        if self.cdc and hasattr(self.cdc, 'is_cdc_supported'):
                            if not self.cdc.is_cdc_supported() and self.cdc.cdc_supported is False:
                                # CDC is not supported, force CT-only mode
                                lfc_mode = 'CT'
                                print(f"🔄 CDC not supported on this database tier - setting up LFC for Change Tracking only")
                                print(f"   Reason: {self.cdc.get_cdc_failure_reason()}")
                            elif self.cdc.cdc_supported is None:
                                # CDC support unknown - test it by trying to enable CDC on a dummy operation
                                # This will set the cdc_supported flag
                                print(f"🔍 Testing CDC support on database tier...")
                                test_result = self.cdc._test_cdc_support()
                                if not test_result:
                                    lfc_mode = 'CT'
                                    print(f"🔄 CDC not supported - setting up LFC for Change Tracking only")
                            # If cdc_supported is True, use default mode
                        
                        # Setup DDL support objects with appropriate mode
                        lfc_result = self.lfc.setup_ddl_support_objects(mode=lfc_mode, test_instance=self.test_instance)
                        
                        # Ensure table_name exists in created_tables before accessing
                        if table_name in created_tables and lfc_result:
                            created_tables[table_name]['lfc_result'] = lfc_result
                        
                        if lfc_result and lfc_result.get('status') == 'success':
                            print(f"🔧 DDL support objects setup completed (mode: {lfc_result.get('mode', 'unknown')})")
                        elif lfc_result and lfc_result.get('status') == 'connection_failed':
                            print(f"⚠️ DDL support objects setup failed due to connection issues:")
                            print(f"   {lfc_result.get('message', 'Connection failed')}")
                            if lfc_result.get('suggestion'):
                                print(f"   💡 Suggestion: {lfc_result['suggestion']}")
                            if table_name in created_tables:
                                created_tables[table_name]['has_warning'] = True
                                created_tables[table_name]['lfc_warning'] = lfc_result.get('message')
                        elif lfc_result and lfc_result.get('status') == 'error':
                            print(f"❌ DDL support objects setup failed: {lfc_result.get('message', 'Unknown error')}")
                            if lfc_result.get('suggestion'):
                                print(f"   💡 Suggestion: {lfc_result['suggestion']}")
                            if table_name in created_tables:
                                created_tables[table_name]['has_error'] = True
                                created_tables[table_name]['lfc_error'] = lfc_result.get('message')
                        elif lfc_result:
                            print(f"⚠️ DDL support objects setup: {lfc_result.get('message', 'Unknown status')}")
                            if table_name in created_tables:
                                created_tables[table_name]['has_warning'] = True
                                created_tables[table_name]['lfc_warning'] = lfc_result.get('message')
        
        # Count errors and warnings
        tables_with_errors = sum(1 for table_info in created_tables.values() if table_info.get('has_error'))
        tables_with_warnings = sum(1 for table_info in created_tables.values() if table_info.get('has_warning'))
        
        print(f"📊 Summary: Created {len(created_tables)} tables total")
        if tables_with_errors > 0:
            print(f"❌ {tables_with_errors} table(s) with errors")
        if tables_with_warnings > 0:
            print(f"⚠️  {tables_with_warnings} table(s) with warnings")
        
        if self.enable_cdc and self.cdc:
            # Count CDC results
            cdc_enabled = sum(1 for table_info in created_tables.values() 
                            if table_info.get('cdc_result', {}).get('status') in ['enabled', 'warning'])
            cdc_skipped = sum(1 for table_info in created_tables.values() 
                            if table_info.get('cdc_result', {}).get('status') == 'skipped')
            
            print(f"🔄 CDC/CT operations: {cdc_enabled} enabled, {cdc_skipped} skipped (filter: {self.replication_filter})")
        
        return created_tables
    
    def drop_test_tables(self, base_names=None, count_per_type=1):
        """Drop test tables starting from the highest numbered suffix (drop from end)
        
        Args:
            base_names: List of base table names (default: ['intpk', 'dtix'])
            count_per_type: Number of tables to drop for each base name (default: 1)
            
        Returns:
            dict: Dropped table names and their details
        """
        if base_names is None:
            base_names = ['intpk', 'dtix']
        
        dropped_tables = {}
        
        with self.engine.connect() as conn:
            for base_name in base_names:
                # Find existing tables with this base name
                existing_tables = self._find_existing_tables(conn, base_name)
                
                # Sort by suffix number (highest first) to drop from end
                existing_tables.sort(key=lambda x: self._extract_suffix_number(x), reverse=True)
                
                # Drop the requested number of tables
                tables_to_drop = existing_tables[:count_per_type]
                
                for table_name in tables_to_drop:
                    if self._table_exists(conn, table_name):
                        # Disable CDC/CT before dropping if enabled
                        cdc_result = None
                        if self.enable_cdc and self.cdc:
                            cdc_result = self.cdc.disable_cdc_for_table(table_name)
                        
                        # Cleanup DDL support objects if this is the last table and LFC is enabled
                        lfc_result = None
                        if (self.enable_lfc and self.lfc and 
                            len(dropped_tables) == 0 and len(tables_to_drop) == 1):
                            lfc_result = self.lfc.cleanup_ddl_support_objects()
                            if lfc_result['status'] == 'success':
                                print(f"🧹 DDL support objects cleaned up")
                            else:
                                print(f"⚠️ DDL support objects cleanup: {lfc_result.get('message', 'Unknown error')}")
                        
                        self._drop_table(conn, table_name)
                        dropped_tables[table_name] = {
                            'table_name': table_name,
                            'qualified_name': self._get_qualified_table_name_str(table_name),
                            'base_name': base_name,
                            'suffix_number': self._extract_suffix_number(table_name),
                            'cdc_result': cdc_result,
                            'lfc_result': lfc_result
                        }
        
        print(f"📊 Summary: Dropped {len(dropped_tables)} tables total")
        if self.enable_cdc and self.cdc:
            print(f"🔄 CDC/CT disable operations attempted for all dropped tables")
        
        return dropped_tables
    
    def _find_existing_tables(self, conn, base_name):
        """Find all existing tables that match the base name pattern"""
        dialect = self.engine.dialect.name
        existing_tables = []
        
        if dialect == 'mysql':
            query = sa.text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND (table_name = :base_name OR table_name LIKE :pattern)
            """)
            result = conn.execute(query, {
                'base_name': base_name, 
                'pattern': f"{base_name}%"
            })
        elif dialect == 'postgresql':
            schema = self.schema or 'public'
            query = sa.text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = :schema 
                AND (table_name = :base_name OR table_name LIKE :pattern)
            """)
            result = conn.execute(query, {
                'schema': schema,
                'base_name': base_name, 
                'pattern': f"{base_name}%"
            })
        elif dialect == 'mssql':
            query = sa.text("""
                SELECT t.name as table_name FROM sys.tables t
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = ISNULL(:schema, 'dbo') 
                AND (t.name = :base_name OR t.name LIKE :pattern)
            """)
            result = conn.execute(query, {
                'schema': self.schema,
                'base_name': base_name, 
                'pattern': f"{base_name}%"
            })
        elif dialect == 'oracle':
            query = sa.text("""
                SELECT table_name FROM user_tables 
                WHERE table_name = UPPER(:base_name) 
                OR table_name LIKE UPPER(:pattern)
            """)
            result = conn.execute(query, {
                'base_name': base_name, 
                'pattern': f"{base_name}%"
            })
        elif dialect == 'sqlite':
            query = sa.text("""
                SELECT name as table_name FROM sqlite_master 
                WHERE type='table' 
                AND (name = :base_name OR name LIKE :pattern)
            """)
            result = conn.execute(query, {
                'base_name': base_name, 
                'pattern': f"{base_name}%"
            })
        else:
            # Fallback: check common patterns
            patterns_to_check = [base_name]
            for i in range(1, 100):  # Check first 99 suffixes
                patterns_to_check.append(f"{base_name}{i:03d}")
            
            for pattern in patterns_to_check:
                try:
                    qualified_name = self._get_qualified_table_name_str(pattern)
                    conn.execute(sa.text(f"SELECT 1 FROM {qualified_name} LIMIT 1"))
                    existing_tables.append(pattern)
                except:
                    continue
            return existing_tables
        
        # Extract table names from result
        for row in result:
            table_name = row[0]
            # Filter to only include exact matches or numbered suffixes
            if table_name == base_name or self._is_numbered_suffix(table_name, base_name):
                existing_tables.append(table_name)
        
        return existing_tables
    
    def _is_numbered_suffix(self, table_name, base_name):
        """Check if table_name is base_name with a numeric suffix"""
        if not table_name.startswith(base_name):
            return False
        
        suffix = table_name[len(base_name):]
        return suffix.isdigit() and len(suffix) > 0
    
    def _extract_suffix_number(self, table_name):
        """Extract numeric suffix from table name, return 0 if no suffix"""
        # Find the base name by checking against known patterns
        for base in ['intpk', 'dtix']:
            if table_name.startswith(base):
                suffix = table_name[len(base):]
                if suffix == '':
                    return 0  # Base table has lowest priority
                elif suffix.isdigit():
                    return int(suffix)
        
        # If no known base pattern, try to extract trailing digits
        i = len(table_name) - 1
        while i >= 0 and table_name[i].isdigit():
            i -= 1
        
        if i < len(table_name) - 1:
            return int(table_name[i+1:])
        
        return 0  # No numeric suffix
    
    def _get_available_table_name(self, conn, base_name):
        """Find available table name, adding numeric suffix if base name exists"""
        # Check if base name is available
        if not self._table_exists(conn, base_name):
            return base_name
        
        # Find next available suffix
        for i in range(1, 1000):  # Support up to 999 suffixes
            suffix = f"{i:03d}"  # 001, 002, etc.
            table_name = f"{base_name}{suffix}"
            if not self._table_exists(conn, table_name):
                return table_name
        
        raise RuntimeError(f"Could not find available name for table {base_name} (tried up to 999 suffixes)")
    
    def _table_exists(self, conn, table_name):
        """Check if table exists in the database"""
        dialect = self.engine.dialect.name
        qualified_name = self._get_qualified_table_name_str(table_name)
        
        if dialect == 'mysql':
            query = sa.text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = DATABASE() AND table_name = :table_name
            """)
            result = conn.execute(query, {'table_name': table_name}).scalar()
        elif dialect == 'postgresql':
            schema = self.schema or 'public'
            query = sa.text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = :schema AND table_name = :table_name
            """)
            result = conn.execute(query, {'schema': schema, 'table_name': table_name}).scalar()
        elif dialect == 'mssql':
            query = sa.text("""
                SELECT COUNT(*) FROM sys.tables t
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = ISNULL(:schema, 'dbo') AND t.name = :table_name
            """)
            result = conn.execute(query, {'schema': self.schema, 'table_name': table_name}).scalar()
        elif dialect == 'oracle':
            query = sa.text("""
                SELECT COUNT(*) FROM user_tables WHERE table_name = UPPER(:table_name)
            """)
            result = conn.execute(query, {'table_name': table_name}).scalar()
        elif dialect == 'sqlite':
            query = sa.text("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name = :table_name
            """)
            result = conn.execute(query, {'table_name': table_name}).scalar()
        else:
            # Fallback: try to select from table
            try:
                conn.execute(sa.text(f"SELECT 1 FROM {qualified_name} LIMIT 1"))
                return True
            except:
                return False
        
        return result > 0
    
    def _drop_table(self, conn, table_name):
        """Drop table if it exists"""
        qualified_name = self._get_qualified_table_name_str(table_name)
        try:
            conn.execute(sa.text(f"DROP TABLE {qualified_name}"))
            conn.commit()
            print(f"🗑️ Dropped existing table: {qualified_name}")
        except Exception as e:
            print(f"⚠️ Could not drop table {qualified_name}: {e}")
    
    def _create_intpk_table(self, conn, table_name, dialect):
        """Create intpk table: id (auto-increment), dt (datetime indexed), ops (string)"""
        qualified_name = self._get_qualified_table_name_str(table_name)
        
        if dialect == 'mysql':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ops VARCHAR(50) DEFAULT 'insert',
                    INDEX idx_{table_name}_dt (dt)
                )
            """
        elif dialect == 'postgresql':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    id SERIAL PRIMARY KEY,
                    dt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ops VARCHAR(50) DEFAULT 'insert'
                );
                CREATE INDEX idx_{table_name}_dt ON {qualified_name} (dt);
            """
        elif dialect == 'mssql':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    dt DATETIME2 NOT NULL DEFAULT GETDATE(),
                    ops VARCHAR(50) DEFAULT 'insert'
                );
                CREATE INDEX idx_{table_name}_dt ON {qualified_name} (dt);
            """
        elif dialect == 'oracle':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    ops VARCHAR2(50) DEFAULT 'insert'
                );
                CREATE INDEX idx_{table_name}_dt ON {qualified_name} (dt);
            """
        elif dialect == 'sqlite':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ops TEXT DEFAULT 'insert'
                );
                CREATE INDEX idx_{table_name}_dt ON {qualified_name} (dt);
            """
        else:
            # Generic fallback
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ops VARCHAR(50) DEFAULT 'insert'
                )
            """
        
        conn.execute(sa.text(create_sql))
        conn.commit()
        
        return {
            'table_name': table_name,
            'qualified_name': qualified_name,
            'columns': ['id', 'dt', 'ops'],
            'indexes': ['idx_' + table_name + '_dt'],
            'type': 'intpk'
        }
    
    def _create_dtix_table(self, conn, table_name, dialect):
        """Create dtix table: dt (datetime indexed), id (integer), ops (string) - no auto-increment ID"""
        qualified_name = self._get_qualified_table_name_str(table_name)
        
        if dialect == 'mysql':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    id INT DEFAULT 0,
                    ops VARCHAR(50) DEFAULT 'insert',
                    INDEX idx_{table_name}_dt (dt),
                    INDEX idx_{table_name}_id (id)
                )
            """
        elif dialect == 'postgresql':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    dt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    id INTEGER DEFAULT 0,
                    ops VARCHAR(50) DEFAULT 'insert'
                );
                CREATE INDEX idx_{table_name}_dt ON {qualified_name} (dt);
                CREATE INDEX idx_{table_name}_id ON {qualified_name} (id);
            """
        elif dialect == 'mssql':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    dt DATETIME2 NOT NULL DEFAULT GETDATE(),
                    id INT DEFAULT 0,
                    ops VARCHAR(50) DEFAULT 'insert'
                );
                CREATE INDEX idx_{table_name}_dt ON {qualified_name} (dt);
                CREATE INDEX idx_{table_name}_id ON {qualified_name} (id);
            """
        elif dialect == 'oracle':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    id NUMBER DEFAULT 0,
                    ops VARCHAR2(50) DEFAULT 'insert'
                );
                CREATE INDEX idx_{table_name}_dt ON {qualified_name} (dt);
                CREATE INDEX idx_{table_name}_id ON {qualified_name} (id);
            """
        elif dialect == 'sqlite':
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    id INTEGER DEFAULT 0,
                    ops TEXT DEFAULT 'insert'
                );
                CREATE INDEX idx_{table_name}_dt ON {qualified_name} (dt);
                CREATE INDEX idx_{table_name}_id ON {qualified_name} (id);
            """
        else:
            # Generic fallback
            create_sql = f"""
                CREATE TABLE {qualified_name} (
                    dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    id INT DEFAULT 0,
                    ops VARCHAR(50) DEFAULT 'insert'
                )
            """
        
        conn.execute(sa.text(create_sql))
        conn.commit()
        
        return {
            'table_name': table_name,
            'qualified_name': qualified_name,
            'columns': ['dt', 'id', 'ops'],
            'indexes': ['idx_' + table_name + '_dt', 'idx_' + table_name + '_id'],
            'type': 'dtix'
        }
    
    def _create_generic_table(self, conn, table_name, dialect):
        """Create generic table with id, dt, ops"""
        return self._create_intpk_table(conn, table_name, dialect)
    
    def _get_qualified_table_name_str(self, table_name):
        """Get qualified table name as string (for SQL generation)"""
        if self.schema:
            return f"{self.schema}.{table_name}"
        return table_name
    
    def get_protected_columns(self, table_name):
        """Get list of protected columns that should not be deleted or altered
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            list: List of protected column names
        """
        # Determine table type based on name pattern
        if table_name.startswith('intpk'):
            # intpk tables: id (integer), dt (datetime), ops (string) are protected
            return ['id', 'dt', 'ops']
        elif table_name.startswith('dtix'):
            # dtix tables: dt (datetime), id (integer), ops (string) are protected  
            return ['dt', 'id', 'ops']
        else:
            # Generic tables: assume intpk structure
            return ['id', 'dt', 'ops']
    
    def get_core_column_info(self, table_name):
        """Get information about core columns (integer, datetime, and string)
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            dict: Information about core columns including integer_column, datetime_column, 
                  string_column, protected_columns, and table_type
        """
        if table_name.startswith('intpk'):
            return {
                'integer_column': 'id',
                'datetime_column': 'dt',
                'string_column': 'ops',
                'protected_columns': ['id', 'dt', 'ops'],
                'table_type': 'intpk'
            }
        elif table_name.startswith('dtix'):
            return {
                'integer_column': 'id', 
                'datetime_column': 'dt',
                'string_column': 'ops',
                'protected_columns': ['dt', 'id', 'ops'],
                'table_type': 'dtix'
            }
        else:
            # Generic tables: assume intpk structure
            return {
                'integer_column': 'id',
                'datetime_column': 'dt',
                'string_column': 'ops', 
                'protected_columns': ['id', 'dt', 'ops'],
                'table_type': 'generic'
            }
    
    def is_column_protected(self, table_name, column_name):
        """Check if a column is protected from deletion/alteration
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to check
            
        Returns:
            bool: True if column is protected, False otherwise
        """
        protected_columns = self.get_protected_columns(table_name)
        return column_name in protected_columns
    
    def validate_column_operation(self, table_name, column_name, operation='delete'):
        """Validate if a column operation is allowed
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            operation: Type of operation ('delete', 'alter', 'modify')
            
        Returns:
            dict: Validation result with status and message
        """
        if self.is_column_protected(table_name, column_name):
            core_info = self.get_core_column_info(table_name)
            return {
                'allowed': False,
                'status': 'error',
                'message': f"Column '{column_name}' is protected and cannot be {operation}d. "
                          f"Protected columns for {table_name}: {core_info['protected_columns']}",
                'protected_columns': core_info['protected_columns'],
                'table_type': core_info['table_type']
            }
        
        return {
            'allowed': True,
            'status': 'success', 
            'message': f"Column '{column_name}' can be {operation}d"
        }
