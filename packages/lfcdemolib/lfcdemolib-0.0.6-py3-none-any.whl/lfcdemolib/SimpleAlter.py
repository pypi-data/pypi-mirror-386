"""
SimpleAlter.py - Database Column Management

This module provides functionality to add and drop columns from database tables.
It focuses on columns with 'field' prefix and automatically discovers supported
data types for each database dialect.
"""

import sqlalchemy as sa
from sqlalchemy import inspect
from typing import Dict, List, Optional, Literal, Union
import re
import warnings


class SimpleAlter:
    """Manages database column alterations with automatic data type discovery"""
    
    def __init__(self, engine, schema: str = None):
        """Initialize SimpleAlter with database engine and optional schema
        
        Args:
            engine: SQLAlchemy engine for database connection
            schema: Optional schema name for table operations
        """
        self.engine = engine
        self.schema = schema
        self.dialect = engine.dialect.name.lower()
        self.inspector = inspect(engine)
        
        # Discover supported data types for this database
        self.supported_types = self._discover_data_types()
    
    def _discover_data_types(self) -> Dict[str, Dict]:
        """Automatically discover supported data types for the current database"""
        type_mapping = {
            'mssql': {
                'string': {
                    'short': 'NVARCHAR(50)',
                    'medium': 'NVARCHAR(255)', 
                    'long': 'NVARCHAR(MAX)',
                    'text': 'NTEXT'
                },
                'integer': {
                    'small': 'SMALLINT',
                    'medium': 'INT',
                    'large': 'BIGINT'
                },
                'decimal': {
                    'currency': 'DECIMAL(18,2)',
                    'percentage': 'DECIMAL(5,2)',
                    'precise': 'DECIMAL(28,8)'
                },
                'datetime': {
                    'date': 'DATE',
                    'datetime': 'DATETIME2(7)',
                    'timestamp': 'DATETIMEOFFSET(7)'
                },
                'boolean': {
                    'flag': 'BIT'
                },
                'binary': {
                    'small': 'VARBINARY(255)',
                    'large': 'VARBINARY(MAX)'
                }
            },
            'postgresql': {
                'string': {
                    'short': 'VARCHAR(50)',
                    'medium': 'VARCHAR(255)',
                    'long': 'TEXT',
                    'text': 'TEXT'
                },
                'integer': {
                    'small': 'SMALLINT',
                    'medium': 'INTEGER',
                    'large': 'BIGINT'
                },
                'decimal': {
                    'currency': 'DECIMAL(18,2)',
                    'percentage': 'DECIMAL(5,2)',
                    'precise': 'DECIMAL(28,8)'
                },
                'datetime': {
                    'date': 'DATE',
                    'datetime': 'TIMESTAMP',
                    'timestamp': 'TIMESTAMPTZ'
                },
                'boolean': {
                    'flag': 'BOOLEAN'
                },
                'binary': {
                    'small': 'BYTEA',
                    'large': 'BYTEA'
                }
            },
            'mysql': {
                'string': {
                    'short': 'VARCHAR(50)',
                    'medium': 'VARCHAR(255)',
                    'long': 'TEXT',
                    'text': 'LONGTEXT'
                },
                'integer': {
                    'small': 'SMALLINT',
                    'medium': 'INT',
                    'large': 'BIGINT'
                },
                'decimal': {
                    'currency': 'DECIMAL(18,2)',
                    'percentage': 'DECIMAL(5,2)',
                    'precise': 'DECIMAL(28,8)'
                },
                'datetime': {
                    'date': 'DATE',
                    'datetime': 'DATETIME',
                    'timestamp': 'TIMESTAMP'
                },
                'boolean': {
                    'flag': 'BOOLEAN'
                },
                'binary': {
                    'small': 'VARBINARY(255)',
                    'large': 'LONGBLOB'
                }
            },
            'oracle': {
                'string': {
                    'short': 'VARCHAR2(50)',
                    'medium': 'VARCHAR2(255)',
                    'long': 'CLOB',
                    'text': 'CLOB'
                },
                'integer': {
                    'small': 'NUMBER(5)',
                    'medium': 'NUMBER(10)',
                    'large': 'NUMBER(19)'
                },
                'decimal': {
                    'currency': 'NUMBER(18,2)',
                    'percentage': 'NUMBER(5,2)',
                    'precise': 'NUMBER(28,8)'
                },
                'datetime': {
                    'date': 'DATE',
                    'datetime': 'TIMESTAMP',
                    'timestamp': 'TIMESTAMP WITH TIME ZONE'
                },
                'boolean': {
                    'flag': 'NUMBER(1) CHECK (flag IN (0,1))'
                },
                'binary': {
                    'small': 'RAW(255)',
                    'large': 'BLOB'
                }
            }
        }
        
        return type_mapping.get(self.dialect, type_mapping['postgresql'])  # Default to PostgreSQL
    
    def get_supported_types(self) -> Dict[str, Dict]:
        """Get supported data types for the current database"""
        return self.supported_types
    
    def add_field_column(self, table_name: str, field_name: str, 
                        data_type: str, subtype: str = 'medium',
                        nullable: bool = True, default_value: str = None, 
                        length: int = None) -> Dict[str, any]:
        """Add a column with 'field' prefix to a table
        
        Args:
            table_name: Name of the table to alter
            field_name: Name of the field (will be prefixed with 'field_' if not already)
            data_type: Data type category (string, integer, decimal, datetime, boolean, binary)
            subtype: Subtype within the category (short, medium, long, etc.)
            nullable: Whether the column allows NULL values
            default_value: Optional default value for the column
            length: Optional length for string types (overrides subtype default)
            
        Returns:
            dict: Result of the add column operation
        """
        try:
            # Ensure field name starts with 'field_'
            if not field_name.lower().startswith('field_'):
                field_name = f"field_{field_name}"
            
            # Validate data type
            if data_type not in self.supported_types:
                return {
                    'status': 'error',
                    'message': f'Unsupported data type: {data_type}. Supported: {list(self.supported_types.keys())}'
                }
            
            if subtype not in self.supported_types[data_type]:
                return {
                    'status': 'error',
                    'message': f'Unsupported subtype: {subtype} for {data_type}. Supported: {list(self.supported_types[data_type].keys())}'
                }
            
            # Get the SQL data type
            sql_type = self.supported_types[data_type][subtype]
            
            # Override length for string types if specified
            if length is not None and data_type == 'string':
                if self.dialect == 'mssql':
                    sql_type = f'NVARCHAR({length})'
                elif self.dialect == 'mysql':
                    sql_type = f'VARCHAR({length})'
                elif self.dialect == 'postgresql':
                    sql_type = f'VARCHAR({length})'
                else:
                    sql_type = f'VARCHAR({length})'
            
            # Check if column already exists
            if self._column_exists(table_name, field_name):
                return {
                    'status': 'warning',
                    'message': f'Column {field_name} already exists in table {table_name}'
                }
            
            # Build ALTER TABLE statement
            qualified_table = self._get_qualified_table_name(table_name)
            null_clause = "NULL" if nullable else "NOT NULL"
            default_clause = f" DEFAULT {default_value}" if default_value else ""
            
            alter_sql = f"ALTER TABLE {qualified_table} ADD {field_name} {sql_type} {null_clause}{default_clause}"
            
            with self.engine.connect() as conn:
                conn.execute(sa.text(alter_sql))
                conn.commit()
            
            print(f"✅ Added column: {field_name} ({sql_type}) to {qualified_table}")
            
            return {
                'status': 'success',
                'table_name': table_name,
                'column_name': field_name,
                'sql_type': sql_type,
                'nullable': nullable,
                'default_value': default_value,
                'length': length,
                'sql_executed': alter_sql
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to add column {field_name} to {table_name}: {str(e)}'
            }
    
    def drop_field_column(self, table_name: str, field_name: str) -> Dict[str, any]:
        """Drop a column with 'field' prefix from a table
        
        Args:
            table_name: Name of the table to alter
            field_name: Name of the field to drop (must start with 'field_')
            
        Returns:
            dict: Result of the drop column operation
        """
        try:
            # Ensure field name starts with 'field_'
            if not field_name.lower().startswith('field_'):
                return {
                    'status': 'error',
                    'message': f'Column name must start with "field_", got: {field_name}'
                }
            
            # Check if column exists
            if not self._column_exists(table_name, field_name):
                return {
                    'status': 'warning',
                    'message': f'Column {field_name} does not exist in table {table_name}'
                }
            
            # Build ALTER TABLE statement
            qualified_table = self._get_qualified_table_name(table_name)
            
            # Different syntax for different databases
            if self.dialect == 'mssql':
                alter_sql = f"ALTER TABLE {qualified_table} DROP COLUMN {field_name}"
            else:
                alter_sql = f"ALTER TABLE {qualified_table} DROP COLUMN {field_name}"
            
            with self.engine.connect() as conn:
                conn.execute(sa.text(alter_sql))
                conn.commit()
            
            print(f"🗑️ Dropped column: {field_name} from {qualified_table}")
            
            return {
                'status': 'success',
                'table_name': table_name,
                'column_name': field_name,
                'sql_executed': alter_sql
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to drop column {field_name} from {table_name}: {str(e)}'
            }
    
    def list_field_columns(self, table_name: str) -> Dict[str, any]:
        """List all columns with 'field_' prefix in a table
        
        Args:
            table_name: Name of the table to inspect
            
        Returns:
            dict: List of field columns and their properties
        """
        try:
            # Get table columns
            columns = self.inspector.get_columns(table_name, schema=self.schema)
            
            # Filter columns that start with 'field_'
            field_columns = [
                col for col in columns 
                if col['name'].lower().startswith('field_')
            ]
            
            return {
                'status': 'success',
                'table_name': table_name,
                'field_columns': field_columns,
                'count': len(field_columns)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to list field columns for {table_name}: {str(e)}'
            }
    
    def add_multiple_field_columns(self, table_name: str, 
                                  columns: List[Dict[str, any]]) -> Dict[str, any]:
        """Add multiple field columns to a table
        
        Args:
            table_name: Name of the table to alter
            columns: List of column definitions, each containing:
                    - field_name: Name of the field
                    - data_type: Data type category
                    - subtype: Subtype (optional, defaults to 'medium')
                    - nullable: Whether nullable (optional, defaults to True)
                    - default_value: Default value (optional)
        
        Returns:
            dict: Results of all add column operations
        """
        results = []
        success_count = 0
        error_count = 0
        
        for col_def in columns:
            result = self.add_field_column(
                table_name=table_name,
                field_name=col_def['field_name'],
                data_type=col_def['data_type'],
                subtype=col_def.get('subtype', 'medium'),
                nullable=col_def.get('nullable', True),
                default_value=col_def.get('default_value')
            )
            
            results.append(result)
            
            if result['status'] == 'success':
                success_count += 1
            elif result['status'] == 'error':
                error_count += 1
        
        return {
            'status': 'completed',
            'table_name': table_name,
            'total_columns': len(columns),
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }
    
    def drop_all_field_columns(self, table_name: str) -> Dict[str, any]:
        """Drop all columns with 'field_' prefix from a table
        
        Args:
            table_name: Name of the table to alter
            
        Returns:
            dict: Results of all drop column operations
        """
        # First, get list of field columns
        field_list = self.list_field_columns(table_name)
        
        if field_list['status'] != 'success':
            return field_list
        
        if field_list['count'] == 0:
            return {
                'status': 'success',
                'message': f'No field columns found in table {table_name}',
                'dropped_count': 0
            }
        
        results = []
        success_count = 0
        error_count = 0
        
        for column in field_list['field_columns']:
            result = self.drop_field_column(table_name, column['name'])
            results.append(result)
            
            if result['status'] == 'success':
                success_count += 1
            elif result['status'] == 'error':
                error_count += 1
        
        return {
            'status': 'completed',
            'table_name': table_name,
            'total_columns': len(field_list['field_columns']),
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }
    
    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        try:
            columns = self.inspector.get_columns(table_name, schema=self.schema)
            return any(col['name'].lower() == column_name.lower() for col in columns)
        except Exception:
            return False
    
    def _get_qualified_table_name(self, table_name: str) -> str:
        """Get qualified table name with schema if specified"""
        if self.schema:
            if self.dialect == 'mssql':
                return f"[{self.schema}].[{table_name}]"
            else:
                return f'"{self.schema}"."{table_name}"'
        else:
            if self.dialect == 'mssql':
                return f"[{table_name}]"
            else:
                return f'"{table_name}"'
    
    def get_column_info(self, table_name: str, column_name: str) -> Dict[str, any]:
        """Get detailed information about a specific column
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            dict: Column information including type, nullable, default, etc.
        """
        try:
            columns = self.inspector.get_columns(table_name, schema=self.schema)
            
            for col in columns:
                if col['name'].lower() == column_name.lower():
                    return {
                        'status': 'success',
                        'table_name': table_name,
                        'column_info': col
                    }
            
            return {
                'status': 'not_found',
                'message': f'Column {column_name} not found in table {table_name}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to get column info: {str(e)}'
            }
    
    def suggest_data_type(self, sample_values: List[any]) -> Dict[str, str]:
        """Suggest appropriate data type based on sample values
        
        Args:
            sample_values: List of sample values to analyze
            
        Returns:
            dict: Suggested data type and subtype
        """
        if not sample_values:
            return {'data_type': 'string', 'subtype': 'medium'}
        
        # Remove None values for analysis
        non_null_values = [v for v in sample_values if v is not None]
        
        if not non_null_values:
            return {'data_type': 'string', 'subtype': 'medium'}
        
        # Check if all values are integers
        if all(isinstance(v, int) for v in non_null_values):
            max_val = max(abs(v) for v in non_null_values)
            if max_val < 32767:
                return {'data_type': 'integer', 'subtype': 'small'}
            elif max_val < 2147483647:
                return {'data_type': 'integer', 'subtype': 'medium'}
            else:
                return {'data_type': 'integer', 'subtype': 'large'}
        
        # Check if all values are floats/decimals
        if all(isinstance(v, (float, int)) for v in non_null_values):
            return {'data_type': 'decimal', 'subtype': 'precise'}
        
        # Check if all values are booleans
        if all(isinstance(v, bool) for v in non_null_values):
            return {'data_type': 'boolean', 'subtype': 'flag'}
        
        # Check if all values are strings
        if all(isinstance(v, str) for v in non_null_values):
            max_length = max(len(v) for v in non_null_values)
            if max_length <= 50:
                return {'data_type': 'string', 'subtype': 'short'}
            elif max_length <= 255:
                return {'data_type': 'string', 'subtype': 'medium'}
            else:
                return {'data_type': 'string', 'subtype': 'long'}
        
        # Default to medium string
        return {'data_type': 'string', 'subtype': 'medium'}
    
    def create_field_columns_from_data(self, table_name: str, 
                                      data_dict: Dict[str, List[any]]) -> Dict[str, any]:
        """Create field columns based on sample data analysis
        
        Args:
            table_name: Name of the table to alter
            data_dict: Dictionary where keys are field names and values are sample data lists
            
        Returns:
            dict: Results of column creation with suggested types
        """
        column_definitions = []
        
        for field_name, sample_values in data_dict.items():
            suggestion = self.suggest_data_type(sample_values)
            
            column_definitions.append({
                'field_name': field_name,
                'data_type': suggestion['data_type'],
                'subtype': suggestion['subtype'],
                'nullable': True,  # Default to nullable for new columns
                'suggested_from_data': True
            })
        
        result = self.add_multiple_field_columns(table_name, column_definitions)
        result['type_suggestions'] = {
            col_def['field_name']: {
                'data_type': col_def['data_type'],
                'subtype': col_def['subtype']
            }
            for col_def in column_definitions
        }
        
        return result
