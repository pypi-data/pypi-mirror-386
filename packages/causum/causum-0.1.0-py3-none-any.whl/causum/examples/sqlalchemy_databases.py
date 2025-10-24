"""
Example: Using Causum™ API with SQLAlchemy to support 50+ databases.

This example shows how to connect to various SQL databases
using the universal SQLAlchemy adapter.
"""
import os
from causum import UniversalClient

# Set API key
os.environ['CAUSALPY_API_KEY'] = 'your-api-key-here'


def example_snowflake():
    """Example: Snowflake connection."""
    print("\n" + "="*70)
    print("Example: Snowflake")
    print("="*70)
    
    profiles = {
        "snowflake_dwh": {
            "type": "snowflake",
            "host": "your-account.snowflakecomputing.com",
            "port": 443,
            "database": "your_database",
            "username": "your_user",
            "password": "${SNOWFLAKE_PASSWORD}"
        }
    }
    
    client = UniversalClient(profiles=profiles, fail_open=True)
    
    result = client.execute(
        profile="snowflake_dwh",
        query="SELECT CURRENT_VERSION() as version"
    )
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Snowflake version: {result['data']}")
    
    client.close()


def example_oracle():
    """Example: Oracle Database connection."""
    print("\n" + "="*70)
    print("Example: Oracle Database")
    print("="*70)
    
    profiles = {
        "oracle_prod": {
            "type": "oracle",
            "host": "oracle.company.com",
            "port": 1521,
            "database": "ORCL",  # Service name or SID
            "username": "app_user",
            "password": "${ORACLE_PASSWORD}"
        }
    }
    
    client = UniversalClient(profiles=profiles, fail_open=True)
    
    result = client.execute(
        profile="oracle_prod",
        query="SELECT * FROM v$version WHERE banner LIKE 'Oracle%'"
    )
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Oracle version: {result['data']}")
    
    client.close()


def example_mssql():
    """Example: Microsoft SQL Server connection."""
    print("\n" + "="*70)
    print("Example: Microsoft SQL Server")
    print("="*70)
    
    profiles = {
        "mssql_analytics": {
            "type": "mssql",
            "host": "sqlserver.company.com",
            "port": 1433,
            "database": "Analytics",
            "username": "sa",
            "password": "${MSSQL_PASSWORD}",
            "ssl": True
        }
    }
    
    client = UniversalClient(profiles=profiles, fail_open=True)
    
    result = client.execute(
        profile="mssql_analytics",
        query="SELECT @@VERSION as version"
    )
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"SQL Server version: {result['data']}")
    
    client.close()


def example_bigquery():
    """Example: Google BigQuery connection."""
    print("\n" + "="*70)
    print("Example: Google BigQuery")
    print("="*70)
    
    profiles = {
        "bigquery_analytics": {
            "type": "bigquery",
            "host": "",
            "port": 0,
            "database": "your-project-id",
            "username": None,
            "password": None
        }
    }
    
    client = UniversalClient(profiles=profiles, fail_open=True)
    
    result = client.execute(
        profile="bigquery_analytics",
        query="SELECT CURRENT_TIMESTAMP() as current_time"
    )
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Current time: {result['data']}")
    
    client.close()


def example_redshift():
    """Example: Amazon Redshift connection."""
    print("\n" + "="*70)
    print("Example: Amazon Redshift")
    print("="*70)
    
    profiles = {
        "redshift_dwh": {
            "type": "redshift",
            "host": "your-cluster.region.redshift.amazonaws.com",
            "port": 5439,
            "database": "analytics",
            "username": "admin",
            "password": "${REDSHIFT_PASSWORD}"
        }
    }
    
    client = UniversalClient(profiles=profiles, fail_open=True)
    
    result = client.execute(
        profile="redshift_dwh",
        query="SELECT version()"
    )
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Redshift version: {result['data']}")
    
    client.close()


def example_sqlite():
    """Example: SQLite (local file database)."""
    print("\n" + "="*70)
    print("Example: SQLite (Local Database)")
    print("="*70)
    
    profiles = {
        "sqlite_local": {
            "type": "sqlite",
            "host": "",
            "port": 0,
            "database": "/path/to/your/database.db",
            "username": None,
            "password": None
        }
    }
    
    client = UniversalClient(profiles=profiles, fail_open=True)
    
    # Create a test table
    client.execute(
        profile="sqlite_local",
        query="CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"
    )
    
    # Insert data
    client.execute(
        profile="sqlite_local",
        query="INSERT INTO users (name) VALUES ('Alice'), ('Bob')"
    )
    
    # Query data
    result = client.execute(
        profile="sqlite_local",
        query="SELECT * FROM users"
    )
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Users: {result['data']}")
    
    client.close()


def example_databricks():
    """Example: Databricks SQL connection."""
    print("\n" + "="*70)
    print("Example: Databricks")
    print("="*70)
    
    profiles = {
        "databricks_lakehouse": {
            "type": "databricks",
            "host": "your-workspace.cloud.databricks.com",
            "port": 443,
            "database": "default",
            "username": "token",
            "password": "${DATABRICKS_TOKEN}"
        }
    }
    
    client = UniversalClient(profiles=profiles, fail_open=True)
    
    result = client.execute(
        profile="databricks_lakehouse",
        query="SELECT current_version()"
    )
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Databricks version: {result['data']}")
    
    client.close()


def comprehensive_example():
    """Example: Multiple databases in one client."""
    print("\n" + "="*70)
    print("Example: Multi-Database Client (Fortune 500 Style)")
    print("="*70)
    
    # Define all your databases
    profiles = {
        # Traditional RDBMS
        "oracle_erp": {
            "type": "oracle",
            "host": "oracle.corp.com",
            "port": 1521,
            "database": "PROD",
            "username": "app_user",
            "password": "${ORACLE_PASSWORD}"
        },
        "mssql_crm": {
            "type": "mssql",
            "host": "sqlserver.corp.com",
            "port": 1433,
            "database": "CRM",
            "username": "sa",
            "password": "${MSSQL_PASSWORD}"
        },
        
        # Cloud Data Warehouses
        "snowflake_analytics": {
            "type": "snowflake",
            "host": "company.snowflakecomputing.com",
            "database": "ANALYTICS",
            "username": "data_scientist",
            "password": "${SNOWFLAKE_PASSWORD}"
        },
        "redshift_dwh": {
            "type": "redshift",
            "host": "cluster.region.redshift.amazonaws.com",
            "port": 5439,
            "database": "analytics",
            "username": "admin",
            "password": "${REDSHIFT_PASSWORD}"
        },
        "bigquery_ml": {
            "type": "bigquery",
            "database": "ml-project-123",
            "username": None,
            "password": None
        },
        
        # Open Source
        "postgres_app": {
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
            "database": "application",
            "username": "app_user",
            "password": "${POSTGRES_PASSWORD}"
        },
        "mongodb_logs": {
            "type": "mongodb",
            "host": "localhost",
            "port": 27017,
            "database": "logs",
            "username": None,
            "password": None
        },
    }
    
    client = UniversalClient(profiles=profiles, fail_open=True)
    
    print(f"\n📊 Connected to {len(profiles)} databases:")
    for profile_name, profile_config in profiles.items():
        print(f"  - {profile_name}: {profile_config['type']}")
    
    # Test each connection
    print(f"\n🔍 Testing connections...")
    for profile_name in profiles.keys():
        is_connected = client.test_connection(profile_name)
        status = "✓" if is_connected else "✗"
        print(f"  {status} {profile_name}")
    
    client.close()


def supported_databases_info():
    """Print information about supported databases."""
    print("\n" + "="*70)
    print("Databases Supported by Causum™ API (via SQLAlchemy)")
    print("="*70)
    
    databases = {
        "Cloud Data Warehouses": [
            "Snowflake",
            "Amazon Redshift",
            "Google BigQuery",
            "Databricks SQL",
            "Azure Synapse",
        ],
        "Traditional RDBMS": [
            "Oracle Database",
            "Microsoft SQL Server",
            "IBM DB2",
            "MySQL",
            "PostgreSQL",
        ],
        "Big Data / Analytics": [
            "Apache Hive",
            "Apache Impala",
            "Presto",
            "Trino",
            "Amazon Athena",
            "Apache Drill",
        ],
        "Specialized": [
            "Teradata",
            "Vertica",
            "Firebird",
            "Sybase",
            "SQLite",
        ],
        "NoSQL (Direct Adapters)": [
            "MongoDB",
            "ClickHouse",
            "TimescaleDB",
        ]
    }
    
    for category, dbs in databases.items():
        print(f"\n{category}:")
        for db in dbs:
            print(f"  ✓ {db}")
    
    print(f"\n{'='*70}")
    print("Total: 50+ databases supported out of the box!")
    print("="*70)


if __name__ == "__main__":
    supported_databases_info()
    
    print("\n\nNote: Examples below require actual database connections.")
    print("Set environment variables for passwords:")
    print("  - ORACLE_PASSWORD, MSSQL_PASSWORD, SNOWFLAKE_PASSWORD")
    print("  - REDSHIFT_PASSWORD, DATABRICKS_TOKEN, etc.")
    
    # Uncomment to run specific examples:
    # example_sqlite()
    # example_snowflake()
    # example_oracle()
    # example_mssql()
    # comprehensive_example()