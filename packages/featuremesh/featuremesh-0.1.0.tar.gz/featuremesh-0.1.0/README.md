# FeatureMesh Python Client

FeatureMesh Python client library for executing FeatureQL queries using various database backends.

## Installation

```bash
pip install featuremesh
```

## Features

- **Multiple Backend Support**: DuckDB, Trino, BigQuery, DataFusion
- **Offline & Online Modes**: Execute queries on SQL backends or FeatureMesh serving
- **Python Integration**: Query results returned as DataFrames
- **Jupyter Magic Commands**: Execute queries directly in notebooks

## Quick Start

### Offline Client (Local SQL Execution)

Execute FeatureQL queries via local SQL backends like DuckDB:

```python
from featuremesh import OfflineClient, Backend
import duckdb

# Create a SQL executor function for DuckDB
def query_duckdb(sql: str):
    """Execute SQL query and return results as DataFrame."""
    conn = duckdb.connect(":memory:")
    result = conn.sql(sql)
    return result.df()

# Create an offline client
client = OfflineClient(
    access_token=__YOUR_ACCESS_TOKEN__,
    backend=Backend.DUCKDB,
    sql_executor=query_duckdb
)

# Execute a FeatureQL query
result = client.query("""
    WITH 
        FEATURE1 := INPUT(BIGINT) 
    SELECT 
        FEATURE1 := BIND_TABLE(ARRAY[1, 2, 3]),
        FEATURE2 := FEATURE1 * 2
""")

# Access results
print(result.dataframe)  # Pandas DataFrame
print(result.sql)        # Translated SQL
print(result.success)    # True if query succeeded
```

### Online Client (API Execution)

Execute FeatureQL queries via the FeatureMesh serving API:

```python
from featuremesh import OnlineClient

# Create an online client
client = OnlineClient(access_token=__YOUR_ACCESS_TOKEN__)

# Execute a FeatureQL query
result = client.query("""
    WITH 
        FEATURE1 := INPUT(BIGINT) 
    SELECT 
        FEATURE1 := BIND_TABLE(ARRAY[1, 2, 3]),
        FEATURE2 := FEATURE1 * 2
""")

# Access results
print(result.dataframe)
```

### Translation Only

Translate FeatureQL to SQL without executing:

```python
# Only available with OfflineClient
featureql_query = """
    WITH 
        FEATURE1 := INPUT(BIGINT) 
    SELECT 
        FEATURE1 := BIND_TABLE(ARRAY[1, 2, 3]),
        FEATURE2 := FEATURE1 * 2
"""
translate_result = client.translate(featureql_query)

print(translate_result.sql)      # Generated SQL
print(translate_result.success)  # True if translation succeeded
```

## Jupyter Notebook Integration

Load the FeatureMesh magic extension in Jupyter:

```python
%load_ext featuremesh
```

Set a default client:

```python
from featuremesh import set_default, OfflineClient, Backend
import duckdb

# Create SQL executor
def query_duckdb(sql: str):
    return duckdb.sql(sql).df()

# Create and set default client
client = OfflineClient(
    access_token=__YOUR_ACCESS_TOKEN__,
    backend=Backend.DUCKDB,
    sql_executor=query_duckdb
)

set_default("client", client)
```

Execute queries using the `%%featureql` cell magic:

```python
%%featureql

WITH 
    FEATURE1 := INPUT(BIGINT) 
SELECT 
    FEATURE1 := BIND_TABLE(ARRAY[1, 2, 3]),
    FEATURE2 := FEATURE1 * 2
```
|FEATURE1|FEATURE2|
|--------|--------|
|1|2|
|2|4|
|3|6|

### Available Magic Options

- `--client CLIENT`: Use a specific client variable from the notebook namespace
- `--debug`: Enable debug mode for detailed query information
- `--show-sql`: Print the translated SQL query
- `--hide-dataframe`: Hide the DataFrame output
- `--show-slt`: Print the SLT (SQL Logic Test) format
- `--hook VARIABLE`: Store complete results as a dictionary in a variable

Example:

```python
%%featureql --client client_duckdb --show-sql --hook results

WITH 
    FEATURE1 := INPUT(BIGINT) 
SELECT 
    FEATURE1 := BIND_TABLE(ARRAY[1, 2, 3]),
    FEATURE2 := FEATURE1 * 2
```

## Configuration

Configure default settings using `set_default()`:

```python
from featuremesh import set_default

# API endpoints
set_default("registry.host", "https://api.featuremesh.com")
set_default("registry.path", "/v1/featureql")
set_default("registry.timeout", 30)

# Display preferences
set_default("debug_mode", False)
set_default("show_sql", True)

# Get current settings
from featuremesh import get_default, get_all_defaults

debug_mode = get_default("debug_mode")
all_settings = get_all_defaults()
```

## Supported Backends

### DuckDB

```python
from featuremesh import OfflineClient, Backend
import duckdb

# Option 1: Using a persistent connection
_duckdb_conn = None

def get_duckdb_conn(storage_path: str = ":memory:"):
    """Get or create a DuckDB connection."""
    global _duckdb_conn
    if _duckdb_conn is None:
        _duckdb_conn = duckdb.connect(storage_path)
    return _duckdb_conn

def query_duckdb(sql: str, storage_path: str = ":memory:"):
    """Execute SQL query and return results as DataFrame."""
    conn = get_duckdb_conn(storage_path)
    result = conn.sql(sql)
    return result.df()

client = OfflineClient(
    access_token=__YOUR_ACCESS_TOKEN__,
    backend=Backend.DUCKDB,
    sql_executor=query_duckdb
)

# Option 2: Simple in-memory executor
def simple_duckdb_executor(sql: str):
    return duckdb.sql(sql).df()

client = OfflineClient(
    access_token=__YOUR_ACCESS_TOKEN__,
    backend=Backend.DUCKDB,
    sql_executor=simple_duckdb_executor
)
```

### Trino

```python
from featuremesh import OfflineClient, Backend
import pandas as pd
import trino.dbapi

def query_trino(sql: str):
    """Execute SQL query on Trino and return results as DataFrame."""
    # Configure your Trino connection details
    conn = trino.dbapi.connect(
        host="localhost",  # or host.docker.internal for docker
        port=8080,
        user="admin",
        catalog="memory",
        schema="default"
    )
    cur = conn.cursor()
    cur.execute(sql)
    
    # Fetch results
    cols = cur.description
    rows = cur.fetchall()
    
    if len(rows) > 0:
        df = pd.DataFrame(rows, columns=[col[0] for col in cols])
        return df
    else:
        return pd.DataFrame()

client = OfflineClient(
    access_token=__YOUR_ACCESS_TOKEN__,
    backend=Backend.TRINO,
    sql_executor=query_trino
)

# For production with OAuth2 authentication:
import trino.auth

def query_trino_oauth(sql: str):
    """Execute SQL query on Trino with OAuth2 authentication."""
    conn = trino.dbapi.connect(
        host="trino.your-domain.com",
        port=443,
        user="your-username",
        catalog="your-catalog",
        schema="default",
        http_scheme="https",
        auth=trino.auth.OAuth2Authentication()
    )
    cur = conn.cursor()
    cur.execute(sql)
    cols = cur.description
    rows = cur.fetchall()
    
    if len(rows) > 0:
        return pd.DataFrame(rows, columns=[col[0] for col in cols])
    return pd.DataFrame()
```

### BigQuery

```python
from featuremesh import OfflineClient, Backend
from google.cloud import bigquery

def query_bigquery(sql: str):
    """Execute SQL query on BigQuery and return results as DataFrame."""
    client = bigquery.Client(project=__YOUR_PROJECT_ID__)
    return client.query(sql).to_dataframe()

client = OfflineClient(
    access_token=__YOUR_ACCESS_TOKEN__,
    backend=Backend.BIGQUERY,
    sql_executor=query_bigquery
)
```

## Error Handling

All operations return result objects with error information:

```python
result = client.query("""
    WITH 
        FEATURE1 := INPUT(BIGINT) 
    SELECT 
        FEATURE1 := BIND_TABLE(ARRAY[1, 2, 3]),
        FEATURE2 := FEATURE1 * 2
""")

if result.success:
    print("Query succeeded!")
    print(result.dataframe)
else:
    print("Query failed!")
    for error in result.errors:
        print(f"Error [{error.code}]: {error.message}")
        if error.context:
            print(f"Context: {error.context}")
```

Display utilities are also available:

```python
from featuremesh import display_errors, display_warnings

display_errors(result.errors)
display_warnings(result.warnings)
```

## Debug Mode

Enable debug mode to see detailed translation information:

```python
result = client.query("""
    WITH 
        FEATURE1 := INPUT(BIGINT) 
    SELECT 
        FEATURE1 := BIND_TABLE(ARRAY[1, 2, 3]),
        FEATURE2 := FEATURE1 * 2
""", debug_mode=True)

if result.debug_logs:
    print(result.debug_logs)
```

## Result Objects

### QueryResult

Returned by `client.query()`:

```python
@dataclass
class QueryResult:
    featureql: str                    # Original FeatureQL query
    sql: Optional[str]                # Translated SQL
    dataframe: Optional[pd.DataFrame] # Query results
    slt: Optional[str]                # SLT format (offline only)
    warnings: list[Warning]           # Non-blocking warnings
    errors: list[Error]               # Errors that occurred
    backend: Optional[str]            # Backend used
    debug_mode: bool                  # Debug mode enabled
    debug_logs: Optional[dict]        # Debug information
    client_type: str                  # "OfflineClient" or "OnlineClient"
    success: bool                     # Property: True if no errors
```

### TranslateResult

Returned by `client.translate()` (OfflineClient only):

```python
@dataclass
class TranslateResult:
    featureql: str                  # Original FeatureQL query
    sql: Optional[str]              # Translated SQL
    warnings: list[Warning]         # Non-blocking warnings
    errors: list[Error]             # Errors that occurred
    full_response: Optional[dict]   # Full API response
    backend: Optional[str]          # Backend used
    debug_mode: bool                # Debug mode enabled
    debug_logs: Optional[dict]      # Debug information
    client_type: str                # "OfflineClient"
    success: bool                   # Property: True if no errors
```

## License

MIT License

## Support

For issues, questions, or contributions, please visit:
- Homepage: http://featuremesh.com
- Email: info@featuremesh.com

## Version

Current version: See `featuremesh.__version__`

```python
import featuremesh
print(featuremesh.__version__)
```
