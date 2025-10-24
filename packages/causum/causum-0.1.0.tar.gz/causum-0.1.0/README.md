# Causum™ API

**Universal Database Client for NL→Query and RAG Systems with Built-in Governance**

`causum` is a unified database client designed for NL→Query and RAG (Retrieval-Augmented Generation) systems. It provides a single interface to query multiple database types while embedding causality for advanced automations, governance, and compliance.

## Features

✅ **Framework Integrations** - Works with LangChain, LlamaIndex, and standalone  
✅ **Built-in Governance** - Validation rules, real-time feedback, compliance trails  
✅ **RAG-Optimized** - Causal inference, deeper and more precise insights  
✅ **Framework Integrations** - Works with LangChain, LlamaIndex, and standalone  
✅ **Query Semantics** - Currently supporting 55 databases  
✅ **Type-Safe** - Full type hints and Pydantic models  

## Installation

```bash
# Basic installation
pip install causum

# With LangChain support
pip install causum[langchain]

# With LlamaIndex support
pip install causum[llamaindex]

# With all integrations
pip install causum[all]
```

## Quick Start

### 1. Set up your profiles

Create a `profiles.json` file:

```json
{
  "profiles": {
    "postgres_db": {
      "type": "postgres",
      "host": "localhost",
      "port": 5432,
      "database": "mydb",
      "username": "user",
      "password": "${POSTGRES_PASSWORD}"
    },
    "mongo_db": {
      "type": "mongodb",
      "host": "localhost",
      "port": 27017,
      "database": "mydb"
    }
  },
  "global": {
    "governance_url": "http://localhost:5000/metadata",
    "enable_cache": true,
    "cache_ttl": 300
  }
}
```

### 2. Set your API key

```bash
export CAUSUM_API_KEY="your-api-key-here"
```

### 3. Use the client

```python
from causum import UniversalClient

# Initialize
client = UniversalClient(profiles_path="./profiles.json")

# Query PostgreSQL
result = client.execute(
    profile="postgres_db",
    query="SELECT * FROM patients LIMIT 10"
)

print(result['data'])
print(result['metadata'])

# Query MongoDB
result = client.execute(
    profile="mongo_db",
    query='db.users.find({"age": {"$gt": 25}})'
)

# Clean up
client.close()
```

## Supported Databases

causum supports **50+ databases** through a combination of optimized native adapters and SQLAlchemy integration:

### Native Adapters (Optimized Performance)

| Database | Type String | Status |
|----------|-------------|--------|
| PostgreSQL | `postgres`, `postgresql` | ✅ Native |
| MySQL | `mysql` | ✅ Native |
| MongoDB | `mongodb`, `mongo` | ✅ Native |
| ClickHouse | `clickhouse` | ✅ Native |
| TimescaleDB | `timescaledb`, `timescale` | ✅ Native |

### SQLAlchemy Adapter (50+ Databases)

**Cloud Data Warehouses:**
- Snowflake (`snowflake`)
- Amazon Redshift (`redshift`)
- Google BigQuery (`bigquery`)
- Databricks SQL (`databricks`)
- Azure Synapse (`mssql`)

**Traditional RDBMS:**
- Oracle Database (`oracle`)
- Microsoft SQL Server (`mssql`, `sqlserver`)
- IBM DB2 (`db2`)
- SQLite (`sqlite`)
- Firebird (`firebird`)
- Sybase (`sybase`)

**Big Data / Analytics:**
- Apache Hive (`hive`)
- Apache Impala (`impala`)
- Presto (`presto`)
- Trino (`trino`)
- Amazon Athena (`athena`)
- Apache Drill (`drill`)

**Specialized:**
- Teradata (`teradata`)
- Vertica (`vertica`)
- And many more...

**Usage Example:**
```python
# Any SQLAlchemy-supported database works out of the box
profiles = {
    "snowflake_dwh": {
        "type": "snowflake",
        "host": "account.snowflakecomputing.com",
        "database": "analytics",
        "username": "user",
        "password": "${SNOWFLAKE_PASSWORD}"
    },
    "oracle_erp": {
        "type": "oracle",
        "host": "oracle.company.com",
        "port": 1521,
        "database": "PROD",
        "username": "app_user",
        "password": "${ORACLE_PASSWORD}"
    }
}
```

## Configuration

### Profiles File

Profiles can be loaded from:
- `/etc/causum/profiles.json`
- `~/.causum/profiles.json`
- `./profiles.json`
- Custom path

### Environment Variables

- `CAUSUM_API_KEY` - API key for governance service (required)
- `{DB}_PASSWORD` - Database passwords (referenced as `${DB_PASSWORD}` in profiles)

### Programmatic Configuration

```python
from causum import UniversalClient

client = UniversalClient(
    profiles={
        "my_db": {
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
            "database": "mydb",
            "username": "user",
            "password": "secret"
        }
    },
    governance_url="http://localhost:5000/metadata",
    enable_cache=True,
    fail_open=True
)
```

## Result Format

All queries return a standardized result dictionary:

```python
{
    "status": "success" | "error",
    "data": [...],  # Query results as list of dicts
    "governance_response": {...},  # Response from the causal/governance API
    "metadata": {
        "db": "postgres",
        "schema": "public.patients",
        "fields": ["id", "name", "age"],
        "operation": "SELECT",
        "row_count": 10,
        "execution_time_ms": 25.5,
        "query_hash": "abc123",
        "cached": false,
        "truncated": false,
        "timestamp": "2025-10-17T14:32:10Z"
    },
    "schema_info": {...},  # Optional schema information
    "error": null | {
        "code": "ERROR_CODE",
        "message": "Error message",
        "details": {...}
    }
}
```

## Advanced Usage

### Caching

```python
client = UniversalClient(
    profiles_path="./profiles.json",
    enable_cache=True,
    cache_ttl=300  # 5 minutes
)

# First call - queries database
result1 = client.execute(profile="db", query="SELECT * FROM users")

# Second call - returns cached result
result2 = client.execute(profile="db", query="SELECT * FROM users")
assert result2['metadata']['cached'] == True
```

### User Context

```python
result = client.execute(
    profile="postgres_db",
    query="SELECT * FROM patients",
    user_context={
        "rag_session_id": "session-123",
        "user_query": "How many patients?",
        "app_name": "my-rag-app"
    }
)
```

### Schema Introspection

```python
# Get database schema
schema = client.get_schema("postgres_db")

for table_name, columns in schema['public'].items():
    print(f"Table: {table_name}")
    for col_name, col_info in columns.items():
        print(f"  {col_name}: {col_info['type']}")
```

### Context Manager

```python
with UniversalClient(profiles_path="./profiles.json") as client:
    result = client.execute(profile="db", query="SELECT 1")
    # Connections automatically closed
```

## Framework Integrations

### LangChain

```python
from causum.integrations.langchain import create_db_tools
from langchain.agents import initialize_agent
from langchain.chat_models import ChatOpenAI

# Create tools from profiles
tools = create_db_tools(
    profiles_path="./profiles.json",
    profiles=["postgres_db", "mongo_db"]
)

# Use in agent
llm = ChatOpenAI(temperature=0)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

response = agent.run("How many patients were admitted in 2020?")
```

### LlamaIndex

```python
from causum.integrations.llamaindex import DatabaseQueryTool
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI

# Create tool
db_tool = DatabaseQueryTool(
    profile="postgres_db",
    description="Query patient database"
)

# Use in agent
llm = OpenAI(model="gpt-4")
agent = ReActAgent.from_tools([db_tool], llm=llm)

response = agent.chat("What's the average age of ICU patients?")
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Documentation: [GitHub README](https://gitlab.com/causum/causum-py.git)
- Issues: [GitHub Issues](https://gitlab.com/causum/causum-py.git/issues)
- Email: support@causum.com