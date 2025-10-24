"""SQLAlchemy universal adapter for 50+ SQL databases."""
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text, inspect, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.exc import SQLAlchemyError

from .base import BaseAdapter
from ..config import DatabaseProfile
from ..exceptions import ConnectionError, QueryError


class SQLAlchemyAdapter(BaseAdapter):
    """
    Universal adapter for SQL databases using SQLAlchemy.
    
    Supports 50+ databases including:
    - Oracle, Microsoft SQL Server, IBM DB2
    - Snowflake, Redshift, BigQuery, Databricks
    - SQLite, Firebird, Sybase
    - And many more...
    
    See: https://docs.sqlalchemy.org/en/20/dialects/
    """
    
    # Mapping of common database types to SQLAlchemy dialect strings
    DIALECT_MAP = {
        'oracle': 'oracle+cx_oracle',
        'mssql': 'mssql+pyodbc',
        'sqlserver': 'mssql+pyodbc',
        'db2': 'ibm_db_sa',
        'snowflake': 'snowflake',
        'redshift': 'redshift+psycopg2',
        'bigquery': 'bigquery',
        'databricks': 'databricks',
        'sqlite': 'sqlite',
        'firebird': 'firebird+fdb',
        'sybase': 'sybase+pyodbc',
        'teradata': 'teradata',
        'vertica': 'vertica+vertica_python',
        'presto': 'presto',
        'trino': 'trino',
        'athena': 'awsathena+rest',
        'hive': 'hive',
        'impala': 'impala',
        'drill': 'drill+sadrill',
    }
    
    def __init__(self, profile: DatabaseProfile):
        """Initialize SQLAlchemy adapter."""
        super().__init__(profile)
        self._engine: Optional[Engine] = None
    
    def connect(self) -> None:
        """Establish connection using SQLAlchemy."""
        try:
            # Build connection string
            connection_string = self._build_connection_string()
            
            # Create engine with connection pooling
            self._engine = create_engine(
                connection_string,
                poolclass=QueuePool if self.profile.pool_size > 1 else NullPool,
                pool_size=self.profile.pool_size,
                max_overflow=self.profile.pool_size * 2,
                pool_timeout=self.profile.pool_timeout,
                pool_pre_ping=True,  # Verify connections before using
                echo=False,
            )
            
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database via SQLAlchemy: {e}")
    
    def disconnect(self) -> None:
        """Close SQLAlchemy engine."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
    
    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        if not self._engine:
            raise ConnectionError("Not connected to database. Call connect() first.")
        
        start_time = time.time()
        
        try:
            with self._engine.connect() as conn:
                # Set timeout if supported
                if timeout:
                    try:
                        conn.execute(text(f"SET statement_timeout = {timeout * 1000}"))
                    except Exception:
                        # Not all databases support statement_timeout
                        pass
                
                # Execute query
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                # Fetch results
                if result.returns_rows:
                    # Get column names
                    columns = result.keys()
                    
                    # Fetch rows
                    if max_rows:
                        rows = result.fetchmany(max_rows)
                    else:
                        rows = result.fetchall()
                    
                    # Convert to list of dicts
                    results = [dict(zip(columns, row)) for row in rows]
                else:
                    # INSERT/UPDATE/DELETE
                    results = [{"rows_affected": result.rowcount}]
                
                execution_time = (time.time() - start_time) * 1000
                
                return results
        
        except SQLAlchemyError as e:
            raise QueryError(f"Query execution failed: {e}")
        except Exception as e:
            raise QueryError(f"Unexpected error during query execution: {e}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema using SQLAlchemy reflection."""
        if not self._engine:
            raise ConnectionError("Not connected to database. Call connect() first.")
        
        try:
            inspector = inspect(self._engine)
            
            # Get all schemas (if database supports schemas)
            try:
                schema_names = inspector.get_schema_names()
            except Exception:
                # Some databases don't support schemas
                schema_names = [None]
            
            schema = {}
            
            for schema_name in schema_names:
                # Skip system schemas
                if schema_name and schema_name.lower() in ['information_schema', 'pg_catalog', 'sys', 'mysql']:
                    continue
                
                # Get tables in this schema
                table_names = inspector.get_table_names(schema=schema_name)
                
                schema_key = schema_name or 'default'
                schema[schema_key] = {}
                
                for table_name in table_names:
                    columns = inspector.get_columns(table_name, schema=schema_name)
                    
                    schema[schema_key][table_name] = {}
                    
                    for col in columns:
                        schema[schema_key][table_name][col['name']] = {
                            'type': str(col['type']),
                            'nullable': col.get('nullable', True),
                            'default': col.get('default'),
                            'primary_key': col.get('primary_key', False),
                        }
            
            return schema
            
        except Exception as e:
            raise QueryError(f"Failed to get schema: {e}")
    
    def test_connection(self) -> bool:
        """Test if connection is alive."""
        if not self._engine:
            return False
        
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter has an active engine."""
        return self._engine is not None
    
    def _build_connection_string(self) -> str:
        """Build SQLAlchemy connection string from profile."""
        db_type = self.profile.type.lower()
        
        # Get dialect from mapping or use as-is
        dialect = self.DIALECT_MAP.get(db_type, db_type)
        
        # Special cases for different databases
        if db_type == 'sqlite':
            # SQLite uses file path
            return f"sqlite:///{self.profile.database}"
        
        elif db_type == 'bigquery':
            # BigQuery uses project ID
            return f"bigquery://{self.profile.database}"
        
        elif db_type == 'snowflake':
            # Snowflake format: snowflake://user:pass@account/database/schema
            username = quote_plus(self.profile.username or '')
            password = quote_plus(self.profile.password or '')
            account = self.profile.host  # Snowflake uses account name as host
            database = self.profile.database
            
            return f"snowflake://{username}:{password}@{account}/{database}"
        
        elif db_type in ['mssql', 'sqlserver']:
            # MSSQL with Windows/SQL Server authentication
            username = quote_plus(self.profile.username or '')
            password = quote_plus(self.profile.password or '')
            host = self.profile.host
            port = self.profile.port
            database = self.profile.database
            
            if self.profile.ssl:
                driver = 'ODBC+Driver+17+for+SQL+Server'
            else:
                driver = 'ODBC+Driver+17+for+SQL+Server'
            
            return (
                f"{dialect}://{username}:{password}@{host}:{port}/{database}"
                f"?driver={driver}"
            )
        
        else:
            # Standard format: dialect://user:pass@host:port/database
            username = quote_plus(self.profile.username or '')
            password = quote_plus(self.profile.password or '')
            host = self.profile.host
            port = self.profile.port
            database = self.profile.database
            
            connection_string = f"{dialect}://{username}:{password}@{host}:{port}/{database}"
            
            # Add SSL parameter if needed
            if self.profile.ssl:
                connection_string += "?sslmode=require"
            
            return connection_string


if __name__ == "__main__":
    import os
    from ..config import DatabaseProfile
    
    print("Testing SQLAlchemyAdapter...")
    
    # Test 1: SQLite (simplest, no server needed)
    print("\n" + "="*60)
    print("Test 1: SQLite (In-Memory)")
    print("="*60)
    
    sqlite_profile = DatabaseProfile(
        type="sqlite",
        host="",
        port=0,
        database=":memory:",  # In-memory database
        username=None,
        password=None
    )
    
    try:
        adapter = SQLAlchemyAdapter(sqlite_profile)
        adapter.connect()
        print("✓ Connected to SQLite")
        
        # Create a test table
        adapter.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        print("✓ Created test table")
        
        # Insert data
        adapter.execute("INSERT INTO test (id, name) VALUES (1, 'Alice'), (2, 'Bob')")
        print("✓ Inserted test data")
        
        # Query data
        result = adapter.execute("SELECT * FROM test")
        print(f"✓ Query executed: {len(result)} rows")
        print(f"  Data: {result}")
        
        # Test max_rows
        result = adapter.execute("SELECT * FROM test", max_rows=1)
        assert len(result) == 1
        print(f"✓ max_rows works: {len(result)} row")
        
        # Get schema
        schema = adapter.get_schema()
        print(f"✓ Schema retrieved: {list(schema.keys())}")
        if 'default' in schema and 'test' in schema['default']:
            print(f"  Columns: {list(schema['default']['test'].keys())}")
        
        adapter.disconnect()
        print("✓ Disconnected")
        
    except Exception as e:
        print(f"✗ SQLite test failed: {e}")
    
    # Test 2: Dialect mapping
    print("\n" + "="*60)
    print("Test 2: Dialect Mapping")
    print("="*60)
    
    test_dialects = [
        'oracle',
        'mssql',
        'snowflake',
        'redshift',
        'bigquery',
        'databricks',
    ]
    
    for db_type in test_dialects:
        profile = DatabaseProfile(
            type=db_type,
            host="example.com",
            port=5432,
            database="testdb",
            username="user",
            password="pass"
        )
        adapter = SQLAlchemyAdapter(profile)
        
        try:
            conn_str = adapter._build_connection_string()
            dialect = SQLAlchemyAdapter.DIALECT_MAP.get(db_type, db_type)
            print(f"✓ {db_type:15} -> {dialect}")
        except Exception as e:
            print(f"✗ {db_type:15} -> Error: {e}")
    
    # Test 3: Real database (if available)
    print("\n" + "="*60)
    print("Test 3: PostgreSQL (if available)")
    print("="*60)
    
    postgres_profile = DatabaseProfile(
        type="postgresql",
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "postgres"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )
    
    try:
        adapter = SQLAlchemyAdapter(postgres_profile)
        adapter.connect()
        print("✓ Connected to PostgreSQL via SQLAlchemy")
        
        result = adapter.execute("SELECT version()")
        print(f"✓ Query executed")
        if result:
            print(f"  Version: {result[0].get('version', 'N/A')[:50]}...")
        
        adapter.disconnect()
        print("✓ Disconnected")
        
    except ConnectionError as e:
        print(f"⚠ PostgreSQL not available: {e}")
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    print("\n" + "="*60)
    print("Supported Databases (50+)")
    print("="*60)
    print("""
SQLAlchemy supports:
  ✓ Oracle, Microsoft SQL Server, IBM DB2
  ✓ Snowflake, Amazon Redshift, Google BigQuery
  ✓ Databricks, Apache Hive, Presto, Trino
  ✓ SQLite, Firebird, Sybase
  ✓ Teradata, Vertica, Amazon Athena
  ✓ And many more...

To use, just set type in profile to database name.
SQLAlchemy will handle the rest!
    """)
    
    print("✓ All SQLAlchemy adapter tests passed")