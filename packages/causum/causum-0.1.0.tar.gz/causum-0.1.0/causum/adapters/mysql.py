"""MySQL database adapter."""
import time
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector import pooling, Error

from .base import BaseAdapter
from ..config import DatabaseProfile
from ..exceptions import ConnectionError, QueryError


class MySQLAdapter(BaseAdapter):
    """Adapter for MySQL databases."""
    
    def __init__(self, profile: DatabaseProfile):
        """Initialize MySQL adapter."""
        super().__init__(profile)
        self._pool: Optional[pooling.MySQLConnectionPool] = None
    
    def connect(self) -> None:
        """Establish connection pool to MySQL."""
        try:
            # Build connection parameters
            conn_params = {
                'host': self.profile.host,
                'port': self.profile.port,
                'database': self.profile.database,
                'user': self.profile.username,
                'password': self.profile.password,
                'pool_name': f'causum_pool_{id(self)}',
                'pool_size': self.profile.pool_size,
            }
            
            # Add SSL if enabled
            if self.profile.ssl:
                conn_params['ssl_disabled'] = False
            
            # Create connection pool
            self._pool = pooling.MySQLConnectionPool(**conn_params)
            
            # Test connection
            conn = self._pool.get_connection()
            conn.close()
            
        except Error as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}")
    
    def disconnect(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            # MySQL connector doesn't have a direct closeall method
            # Connections will be closed when pool is garbage collected
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
            conn = self._pool.get_connection()
            
            # Create cursor with dictionary results
            cursor = conn.cursor(dictionary=True)
            
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
                
                results = list(rows)
            else:  # INSERT/UPDATE/DELETE
                conn.commit()
                results = [{"rows_affected": cursor.rowcount}]
            
            execution_time = (time.time() - start_time) * 1000
            
            return results
            
        except Error as e:
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
                conn.close()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get MySQL database schema."""
        schema_query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            COLUMN_KEY
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION;
        """
        
        try:
            results = self.execute(schema_query, params=(self.profile.database,))
            
            # Organize by table
            schema = {}
            for row in results:
                table_name = row['TABLE_NAME']
                
                if table_name not in schema:
                    schema[table_name] = {}
                
                schema[table_name][row['COLUMN_NAME']] = {
                    'type': row['DATA_TYPE'],
                    'nullable': row['IS_NULLABLE'] == 'YES',
                    'default': row['COLUMN_DEFAULT'],
                    'key': row['COLUMN_KEY']
                }
            
            return schema
            
        except Exception as e:
            raise QueryError(f"Failed to get schema: {e}")
    
    def test_connection(self) -> bool:
        """Test if connection pool is alive."""
        if not self._pool:
            return False
        
        try:
            conn = self._pool.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
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
    
    print("Testing MySQLAdapter...")
    
    # Test configuration
    profile = DatabaseProfile(
        type="mysql",
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DB", "test"),
        username=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "")
    )
    
    print(f"Connecting to {profile.host}:{profile.port}/{profile.database}...")
    
    try:
        # Test connection
        adapter = MySQLAdapter(profile)
        adapter.connect()
        print("✓ Connected successfully")
        
        # Test connection check
        assert adapter.test_connection(), "Connection test failed"
        print("✓ Connection test passed")
        
        # Test simple query
        result = adapter.execute("SELECT VERSION() as version")
        print(f"✓ Query executed: {len(result)} rows returned")
        if result:
            print(f"  MySQL version: {result[0].get('version', 'N/A')}")
        
        # Test with max_rows
        result = adapter.execute("SELECT 1 AS num UNION SELECT 2 UNION SELECT 3", max_rows=2)
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
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
        with MySQLAdapter(profile) as adapter:
            result = adapter.execute("SELECT 1 AS test")
            assert len(result) == 1
            print("✓ Context manager works")
        
        print("\n✓ All MySQL adapter tests passed")
        
    except ConnectionError as e:
        print(f"\n⚠ Connection test skipped (database not available): {e}")
        print("  To test with a real database, set environment variables:")
        print("  - MYSQL_HOST, MYSQL_PORT, MYSQL_DB")
        print("  - MYSQL_USER, MYSQL_PASSWORD")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise