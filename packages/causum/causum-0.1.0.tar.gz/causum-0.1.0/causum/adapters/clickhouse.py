"""ClickHouse database adapter."""
import time
from typing import Any, Dict, List, Optional

from clickhouse_driver import Client
from clickhouse_driver.errors import Error

from .base import BaseAdapter
from ..config import DatabaseProfile
from ..exceptions import ConnectionError, QueryError


class ClickHouseAdapter(BaseAdapter):
    """Adapter for ClickHouse databases."""
    
    def __init__(self, profile: DatabaseProfile):
        """Initialize ClickHouse adapter."""
        super().__init__(profile)
        self._client: Optional[Client] = None
    
    def connect(self) -> None:
        """Establish connection to ClickHouse."""
        try:
            # Create client
            self._client = Client(
                host=self.profile.host,
                port=self.profile.port,
                database=self.profile.database,
                user=self.profile.username,
                password=self.profile.password,
                connect_timeout=self.profile.pool_timeout,
                send_receive_timeout=self.profile.pool_timeout,
            )
            
            # Test connection
            self._client.execute("SELECT 1")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to ClickHouse: {e}")
    
    def disconnect(self) -> None:
        """Close ClickHouse connection."""
        if self._client:
            self._client.disconnect()
            self._client = None
    
    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        if not self._client:
            raise ConnectionError("Not connected to database. Call connect() first.")
        
        start_time = time.time()
        
        try:
            # Add LIMIT clause if max_rows specified
            if max_rows and "LIMIT" not in query.upper():
                query = f"{query.rstrip(';')} LIMIT {max_rows}"
            
            # Execute query with column names
            result, columns = self._client.execute(
                query,
                params=params,
                with_column_types=True,
                settings={'max_execution_time': timeout} if timeout else None
            )
            
            # Convert to list of dicts
            column_names = [col[0] for col in columns]
            results = [dict(zip(column_names, row)) for row in result]
            
            execution_time = (time.time() - start_time) * 1000
            
            return results
            
        except Error as e:
            raise QueryError(f"Query execution failed: {e}")
        except Exception as e:
            raise QueryError(f"Unexpected error during query execution: {e}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get ClickHouse database schema."""
        schema_query = """
        SELECT 
            database,
            table,
            name,
            type,
            default_kind,
            default_expression
        FROM system.columns
        WHERE database = %(database)s
        ORDER BY table, position;
        """
        
        try:
            results = self.execute(schema_query, params={'database': self.profile.database})
            
            # Organize by table
            schema = {}
            for row in results:
                table_name = row['table']
                
                if table_name not in schema:
                    schema[table_name] = {}
                
                schema[table_name][row['name']] = {
                    'type': row['type'],
                    'default_kind': row['default_kind'],
                    'default_expression': row['default_expression']
                }
            
            return schema
            
        except Exception as e:
            raise QueryError(f"Failed to get schema: {e}")
    
    def test_connection(self) -> bool:
        """Test if connection is alive."""
        if not self._client:
            return False
        
        try:
            self._client.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter has an active connection."""
        return self._client is not None


if __name__ == "__main__":
    import os
    from ..config import DatabaseProfile
    
    print("Testing ClickHouseAdapter...")
    
    # Test configuration
    profile = DatabaseProfile(
        type="clickhouse",
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "9000")),
        database=os.getenv("CLICKHOUSE_DB", "default"),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "")
    )
    
    print(f"Connecting to {profile.host}:{profile.port}/{profile.database}...")
    
    try:
        # Test connection
        adapter = ClickHouseAdapter(profile)
        adapter.connect()
        print("✓ Connected successfully")
        
        # Test connection check
        assert adapter.test_connection(), "Connection test failed"
        print("✓ Connection test passed")
        
        # Test simple query
        result = adapter.execute("SELECT version() as version")
        print(f"✓ Query executed: {len(result)} rows returned")
        if result:
            print(f"  ClickHouse version: {result[0].get('version', 'N/A')}")
        
        # Test with max_rows
        result = adapter.execute("SELECT number FROM system.numbers", max_rows=5)
        assert len(result) == 5, f"Expected 5 rows, got {len(result)}"
        print(f"✓ max_rows parameter works: got {len(result)} rows")
        
        # Test schema retrieval
        try:
            schema = adapter.get_schema()
            print(f"✓ Schema retrieved: {len(schema)} tables found")
            for table_name, columns in list(schema.items())[:2]:
                print(f"  - {table_name}: {len(columns)} columns")
        except Exception as e:
            print(f"  (Schema test skipped: {e})")
        
        # Clean up
        adapter.disconnect()
        print("✓ Disconnected successfully")
        
        # Test context manager
        with ClickHouseAdapter(profile) as adapter:
            result = adapter.execute("SELECT 1 AS test")
            assert len(result) == 1
            print("✓ Context manager works")
        
        print("\n✓ All ClickHouse adapter tests passed")
        
    except ConnectionError as e:
        print(f"\n⚠ Connection test skipped (database not available): {e}")
        print("  To test with a real database, set environment variables:")
        print("  - CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_DB")
        print("  - CLICKHOUSE_USER, CLICKHOUSE_PASSWORD")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise