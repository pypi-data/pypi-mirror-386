# lfcdemolib

**Lakehouse Federation Connect Demo Library**

A comprehensive Python library for building and managing Databricks Lakeflow Connect (LFC) demonstrations with support for multiple cloud providers and database types.

## Features

- **Simplified Demo Initialization**: One-line setup for Databricks notebooks with `DemoInstance`
- **Multi-Database Support**: SQL Server, MySQL, PostgreSQL, Oracle
- **Cloud Provider Support**: Azure, Oracle Cloud Infrastructure (OCI)
- **Change Data Capture (CDC)**: Built-in CDC/CT (Change Tracking) implementations
- **Schema Evolution**: Automatic schema evolution and migration handling
- **Connection Management**: Secure credential storage and retrieval
- **DML Operations**: Simplified data manipulation with automatic scheduling
- **REST API Integration**: Databricks workspace API wrapper
- **Test Framework**: Comprehensive testing utilities for database operations

## Installation

```bash
pip install lfcdemolib
```

**All database drivers are included** as core dependencies:
- pymysql (MySQL)
- psycopg2-binary (PostgreSQL)
- pymssql (SQL Server)
- oracledb (Oracle)

### Optional Dependencies

For development tools:

```bash
# Development tools (pytest, black, flake8, mypy, isort)
pip install "lfcdemolib[dev]"

# Documentation tools (sphinx)
pip install "lfcdemolib[docs]"
```

## Quick Start

### Databricks Notebook

```python
import lfcdemolib

# Configuration
config_dict = {
    "source_connection_name": "lfcddemo-azure-mysql-both",
    "cdc_qbc": "cdc",
    "database": {
        "cloud": "azure",
        "type": "mysql"
    }
}

# One-line initialization
d = lfcdemolib.DemoInstance(config_dict, dbutils, spark)

# Create pipeline
d.create_pipeline(pipeline_spec)

# Execute DML operations
d.dml.execute_delete_update_insert()

# Get recent data
df = d.dml.get_recent_data()
display(df)
```

### Tuple Unpacking (Advanced)

```python
# Get all components
d, config, dbxs, dmls, dbx_key, dml_key, scheduler = lfcdemolib.DemoInstance(
    config_dict, 
    dbutils, 
    spark
)

# Use individual components
config.source_connection_name
dmls[dml_key].execute_delete_update_insert()
scheduler.get_jobs()
```

## Core Components

### DemoInstance

Simplified facade for demo initialization with automatic caching and scheduler management.

```python
d = lfcdemolib.DemoInstance(config_dict, dbutils, spark)
```

**Features:**
- Singleton scheduler management
- Automatic instance caching
- Simplified one-line initialization
- Delegates to DbxRest for Databricks operations

### LfcScheduler

Background task scheduler using APScheduler.

```python
scheduler = lfcdemolib.LfcScheduler()
scheduler.add_job(my_function, 'interval', seconds=60)
```

### DbxRest

Databricks REST API client with connection and secret management.

```python
dbx = lfcdemolib.DbxRest(dbutils=dbutils, config=config, lfc_scheduler=scheduler)
dbx.create_pipeline(spec)
```

### SimpleDML

Simplified DML operations with automatic scheduling.

```python
dml = lfcdemolib.SimpleDML(secrets_json, config=config, lfc_scheduler=scheduler)
dml.execute_delete_update_insert()
df = dml.get_recent_data()
```

### Pydantic Models

Type-safe configuration and credential management.

```python
from lfcdemolib import LfcNotebookConfig, LfcCredential

# Validate configuration
config = LfcNotebookConfig(config_dict)

# Validate credentials
credential = LfcCredential(secrets_json)
```

## Database Support

### Supported Databases

- **SQL Server**: CDC and Change Tracking (CT) support
- **MySQL**: Full replication support
- **PostgreSQL**: Logical replication support
- **Oracle**: 19c and later

### Supported Cloud Providers

- **Azure**: SQL Database, Azure Database for MySQL/PostgreSQL
- **OCI**: Oracle Cloud Infrastructure databases

## Configuration

### LfcNotebookConfig

```python
config_dict = {
    "source_connection_name": "lfcddemo-azure-mysql-both",  # Required
    "cdc_qbc": "cdc",                                      # Required: "cdc" or "qbc"
    "target_catalog": "main",                               # Optional: defaults to "main"
    "source_schema": None,                                  # Optional: auto-detect
    "database": {                                           # Required if connection_name is blank
        "cloud": "azure",                                   # "azure" or "oci"
        "type": "mysql"                                     # "mysql", "postgresql", "sqlserver", "oracle"
    }
}
```

### LfcCredential (V2 Format)

```python
credential = {
    "host_fqdn": "myserver.database.windows.net",
    "port": 3306,
    "catalog": "mydb",
    "schema": "dbo",
    "username": "user",
    "password": "pass",
    "db_type": "mysql",
    "cloud": {
        "provider": "azure",
        "region": "eastus"
    },
    "dba": {
        "username": "admin",
        "password": "adminpass"
    }
}
```

## Advanced Features

### Automatic Scheduling

```python
# DML operations run automatically
d = lfcdemolib.DemoInstance(config_dict, dbutils, spark)
# Auto-scheduled DML operations every 10 seconds
```

### Custom Scheduler Jobs

```python
def my_task():
    print("Running custom task")

d.scheduler.add_job(my_task, 'interval', seconds=30, id='my_task')
```

### Connection Management

```python
from lfcdemolib import LfcConn

# Manage Databricks connections
lfc_conn = LfcConn(workspace_client=workspace_client)
connection = lfc_conn.get_connection(connection_name)
```

### Secret Management

```python
from lfcdemolib import LfcSecrets

# Manage Databricks secrets
lfc_secrets = LfcSecrets(workspace_client=workspace_client)
secret = lfc_secrets.get_secret(scope='lfcddemo', key='mysql_password')
```

### Local Credential Storage

```python
from lfcdemolib import SimpleLocalCred

# Save credentials locally
cred_manager = SimpleLocalCred()
cred_manager.save_credentials(db_details, db_type='mysql', cloud='azure')

# Load credentials
credential = cred_manager.get_credential(
    host='myserver.database.windows.net',
    db_type='mysql'
)
```

## Testing

### SimpleTest

Comprehensive database test suite.

```python
from lfcdemolib import SimpleTest

tester = SimpleTest(workspace_client, config)
results = tester.run_comprehensive_tests()
```

## Command-Line Tools

### Deploy Credentials

```bash
cd lfc/db/bin
python deploy_credentials_to_workspaces.py \
    --credential-file ~/.lfcddemo/credentials.json \
    --target-workspace prod
```

### Convert Secrets

```bash
python convert_secret_to_credential.py \
    --scope-name lfcddemo \
    --secret-name mysql-connection \
    --source azure
```

## Examples

### Multi-Database Demo

```python
import lfcdemolib

# MySQL
mysql_d = lfcdemolib.DemoInstance(mysql_config, dbutils, spark)
mysql_d.create_pipeline(mysql_spec)

# PostgreSQL
pg_d = lfcdemolib.DemoInstance(pg_config, dbutils, spark)
pg_d.create_pipeline(pg_spec)

# SQL Server
sqlserver_d = lfcdemolib.DemoInstance(sqlserver_config, dbutils, spark)
sqlserver_d.create_pipeline(sqlserver_spec)

# All share the same scheduler
print(mysql_d.scheduler is pg_d.scheduler)  # True
```

### Monitoring

```python
# Check active jobs
for job in d.scheduler.get_jobs():
    print(f"{job.id}: {job.next_run_time}")

# Check cleanup queue
for item in d.cleanup_queue.queue:
    print(item)
```

## Requirements

- Python >= 3.8
- Databricks Runtime 13.0+
- SQLAlchemy >= 1.4.0
- Pydantic >= 1.8.0 (v1 compatibility)
- APScheduler >= 3.9.0

## License

This project is licensed under the Databricks Labs License - see the [LICENSE](LICENSE) file for details.

## Contributing

This is a Databricks Labs project. Contributions are welcome! Please ensure:

- Code follows PEP 8 style guidelines
- All tests pass
- Documentation is updated
- Pydantic v1 compatibility is maintained

## Support

For issues, questions, or contributions, please contact the Databricks Labs team.

## Changelog

### Version 1.0.0

- Initial release
- DemoInstance facade for simplified initialization
- Support for MySQL, PostgreSQL, SQL Server, Oracle
- Azure and OCI cloud provider support
- Pydantic v1-based validation
- APScheduler integration
- Comprehensive test framework

---

**Databricks Labs** | [Documentation](#) | [Examples](#) | [API Reference](#)

