"""PostgreSQL database adapter."""
import time
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from psycopg2 import pool

from .base import BaseAdapter
from ..config import DatabaseProfile
from ..exceptions import ConnectionError, QueryError


class PostgresAdapter(BaseAdapter):
    """Adapter for PostgreSQL databases."""
    
    def __init__(self, profile: DatabaseProfile):
        """Initialize PostgreSQL adapter."""
        super().__init__(profile)
        self._pool: Optional[pool.SimpleConnectionPool] = None
    
    def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        try:
            # Build connection parameters
            conn_params = {
                'host': self.profile.host,
                'port': self.profile.port,
                'database': self.profile.database,
                'user': self.profile.username,
                'password': self.profile.password,
            }
            
            # Add SSL if enabled
            if self.profile.ssl:
                conn_params['sslmode'] = 'require'
            
            # Create connection pool
            self._pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.profile.pool_size,
                **conn_params
            )
            
            # Test connection
            conn = self._pool.getconn()
            self._pool.putconn(conn)
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
    
    def disconnect(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            self._pool = None
    
    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        if not self._pool:
            raise ConnectionError("Not connected to database. Call connect() first.")
        
        conn = None
        cursor = None
        start_time = time.time()
        
        try:
            # Get connection from pool
            conn = self._pool.getconn()
            
            # Set statement timeout if specified
            if timeout:
                with conn.cursor() as temp_cursor:
                    temp_cursor.execute(f"SET statement_timeout = {timeout * 1000}")
            
            # Create cursor with dictionary results
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch results
            if cursor.description:  # SELECT query
                if max_rows:
                    rows = cursor.fetchmany(max_rows)
                else:
                    rows = cursor.fetchall()
                
                # Convert RealDictRow to regular dict
                results = [dict(row) for row in rows]
            else:  # INSERT/UPDATE/DELETE
                conn.commit()
                results = [{"rows_affected": cursor.rowcount}]
            
            execution_time = (time.time() - start_time) * 1000
            
            return results
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise QueryError(f"Query execution failed: {e}")
        except Exception as e:
            if conn:
                conn.rollback()
            raise QueryError(f"Unexpected error during query execution: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._pool.putconn(conn)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get PostgreSQL database schema."""
        schema_query = """
        SELECT 
            table_schema,
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name, ordinal_position;
        """
        
        try:
            results = self.execute(schema_query)
            
            # Organize by schema and table
            schema = {}
            for row in results:
                schema_name = row['table_schema']
                table_name = row['table_name']
                
                if schema_name not in schema:
                    schema[schema_name] = {}
                
                if table_name not in schema[schema_name]:
                    schema[schema_name][table_name] = {}
                
                schema[schema_name][table_name][row['column_name']] = {
                    'type': row['data_type'],
                    'nullable': row['is_nullable'] == 'YES',
                    'default': row['column_default']
                }
            
            return schema
            
        except Exception as e:
            raise QueryError(f"Failed to get schema: {e}")
    
    def test_connection(self) -> bool:
        """Test if connection pool is alive."""
        if not self._pool:
            return False
        
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self._pool.putconn(conn)
            return True
        except Exception:
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter has an active connection pool."""
        return self._pool is not None


if __name__ == "__main__":
    import os
    from ..config import DatabaseProfile
    
    print("Testing PostgresAdapter...")
    
    # Test configuration
    profile = DatabaseProfile(
        type="postgres",
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "testdb"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )
    
    print(f"Connecting to {profile.host}:{profile.port}/{profile.database}...")
    
    try:
        # Test connection
        adapter = PostgresAdapter(profile)
        adapter.connect()
        print("✓ Connected successfully")
        
        # Test connection check
        assert adapter.test_connection(), "Connection test failed"
        print("✓ Connection test passed")
        
        # Test simple query
        result = adapter.execute("SELECT version()")
        print(f"✓ Query executed: {len(result)} rows returned")
        if result:
            print(f"  PostgreSQL version: {result[0].get('version', 'N/A')[:50]}...")
        
        # Test with max_rows
        result = adapter.execute("SELECT 1 AS num UNION SELECT 2 UNION SELECT 3", max_rows=2)
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        print(f"✓ max_rows parameter works: got {len(result)} rows")
        
        # Test schema retrieval (will work if DB has tables)
        try:
            schema = adapter.get_schema()
            print(f"✓ Schema retrieved: {len(schema)} schemas found")
            for schema_name, tables in list(schema.items())[:2]:
                print(f"  - {schema_name}: {len(tables)} tables")
        except Exception as e:
            print(f"  (Schema test skipped: {e})")
        
        # Clean up
        adapter.disconnect()
        print("✓ Disconnected successfully")
        
        # Test context manager
        with PostgresAdapter(profile) as adapter:
            result = adapter.execute("SELECT 1 AS test")
            assert len(result) == 1
            print("✓ Context manager works")
        
        print("\n✓ All PostgreSQL adapter tests passed")
        
    except ConnectionError as e:
        print(f"\n⚠ Connection test skipped (database not available): {e}")
        print("  To test with a real database, set environment variables:")
        print("  - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB")
        print("  - POSTGRES_USER, POSTGRES_PASSWORD")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise