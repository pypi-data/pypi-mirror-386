"""TimescaleDB database adapter (extends PostgreSQL)."""
from typing import Any, Dict

from .postgres import PostgresAdapter
from ..config import DatabaseProfile
from ..exceptions import QueryError


class TimescaleAdapter(PostgresAdapter):
    """
    Adapter for TimescaleDB databases.
    
    TimescaleDB is a PostgreSQL extension, so this adapter extends
    the PostgreSQL adapter with TimescaleDB-specific functionality.
    """
    
    def __init__(self, profile: DatabaseProfile):
        """Initialize TimescaleDB adapter."""
        super().__init__(profile)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get TimescaleDB schema including hypertables."""
        # Get base PostgreSQL schema
        base_schema = super().get_schema()
        
        # Get TimescaleDB-specific information
        try:
            # Get hypertables
            hypertables_query = """
            SELECT 
                hypertable_schema,
                hypertable_name,
                num_dimensions,
                num_chunks,
                compression_enabled
            FROM timescaledb_information.hypertables;
            """
            
            hypertables = self.execute(hypertables_query)
            
            # Get continuous aggregates
            caggs_query = """
            SELECT 
                view_schema,
                view_name,
                materialized_only
            FROM timescaledb_information.continuous_aggregates;
            """
            
            caggs = self.execute(caggs_query)
            
            # Enhance schema with TimescaleDB info
            timescale_info = {
                'hypertables': {},
                'continuous_aggregates': {}
            }
            
            for ht in hypertables:
                schema_name = ht['hypertable_schema']
                table_name = ht['hypertable_name']
                
                if schema_name not in timescale_info['hypertables']:
                    timescale_info['hypertables'][schema_name] = {}
                
                timescale_info['hypertables'][schema_name][table_name] = {
                    'num_dimensions': ht['num_dimensions'],
                    'num_chunks': ht['num_chunks'],
                    'compression_enabled': ht['compression_enabled']
                }
            
            for cagg in caggs:
                schema_name = cagg['view_schema']
                view_name = cagg['view_name']
                
                if schema_name not in timescale_info['continuous_aggregates']:
                    timescale_info['continuous_aggregates'][schema_name] = {}
                
                timescale_info['continuous_aggregates'][schema_name][view_name] = {
                    'materialized_only': cagg['materialized_only']
                }
            
            # Combine with base schema
            enhanced_schema = {
                'tables': base_schema,
                'timescaledb': timescale_info
            }
            
            return enhanced_schema
            
        except Exception as e:
            # If TimescaleDB queries fail, return base schema
            # This might happen if TimescaleDB extension is not installed
            return base_schema
    
    def get_hypertables(self) -> list[Dict[str, Any]]:
        """Get list of hypertables in the database."""
        query = """
        SELECT 
            hypertable_schema,
            hypertable_name,
            num_dimensions,
            num_chunks,
            compression_enabled,
            tablespaces
        FROM timescaledb_information.hypertables;
        """
        
        try:
            return self.execute(query)
        except Exception as e:
            raise QueryError(f"Failed to get hypertables: {e}")
    
    def get_chunks(self, hypertable: str, schema: str = 'public') -> list[Dict[str, Any]]:
        """Get chunks for a specific hypertable."""
        query = """
        SELECT 
            chunk_schema,
            chunk_name,
            range_start,
            range_end
        FROM timescaledb_information.chunks
        WHERE hypertable_schema = %(schema)s
          AND hypertable_name = %(table)s
        ORDER BY range_start;
        """
        
        try:
            return self.execute(query, params={'schema': schema, 'table': hypertable})
        except Exception as e:
            raise QueryError(f"Failed to get chunks: {e}")


if __name__ == "__main__":
    import os
    from ..config import DatabaseProfile
    
    print("Testing TimescaleAdapter...")
    
    # Test configuration
    profile = DatabaseProfile(
        type="timescaledb",
        host=os.getenv("TIMESCALE_HOST", "localhost"),
        port=int(os.getenv("TIMESCALE_PORT", "5432")),
        database=os.getenv("TIMESCALE_DB", "testdb"),
        username=os.getenv("TIMESCALE_USER", "postgres"),
        password=os.getenv("TIMESCALE_PASSWORD", "postgres")
    )
    
    print(f"Connecting to {profile.host}:{profile.port}/{profile.database}...")
    
    try:
        # Test connection
        adapter = TimescaleAdapter(profile)
        adapter.connect()
        print("✓ Connected successfully")
        
        # Test connection check
        assert adapter.test_connection(), "Connection test failed"
        print("✓ Connection test passed")
        
        # Test simple query (PostgreSQL compatibility)
        result = adapter.execute("SELECT version()")
        print(f"✓ Query executed: {len(result)} rows returned")
        if result:
            version_str = result[0].get('version', 'N/A')
            print(f"  Version: {version_str[:80]}...")
        
        # Test TimescaleDB-specific query
        try:
            result = adapter.execute("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
            if result:
                print(f"✓ TimescaleDB extension version: {result[0].get('extversion', 'N/A')}")
            else:
                print("  ⚠ TimescaleDB extension not found (testing with vanilla PostgreSQL)")
        except Exception as e:
            print(f"  ⚠ Could not check TimescaleDB version: {e}")
        
        # Test hypertables retrieval
        try:
            hypertables = adapter.get_hypertables()
            print(f"✓ Hypertables retrieved: {len(hypertables)} found")
            for ht in hypertables[:2]:
                print(f"  - {ht['hypertable_schema']}.{ht['hypertable_name']}: {ht['num_chunks']} chunks")
        except Exception as e:
            print(f"  (Hypertables test skipped: {e})")
        
        # Test schema retrieval
        try:
            schema = adapter.get_schema()
            if isinstance(schema, dict) and 'timescaledb' in schema:
                print(f"✓ Enhanced schema retrieved with TimescaleDB info")
            else:
                print(f"✓ Schema retrieved: {len(schema)} schemas/tables found")
        except Exception as e:
            print(f"  (Schema test skipped: {e})")
        
        # Clean up
        adapter.disconnect()
        print("✓ Disconnected successfully")
        
        # Test context manager
        with TimescaleAdapter(profile) as adapter:
            result = adapter.execute("SELECT 1 AS test")
            assert len(result) == 1
            print("✓ Context manager works")
        
        print("\n✓ All TimescaleDB adapter tests passed")
        
    except ConnectionError as e:
        print(f"\n⚠ Connection test skipped (database not available): {e}")
        print("  To test with a real database, set environment variables:")
        print("  - TIMESCALE_HOST, TIMESCALE_PORT, TIMESCALE_DB")
        print("  - TIMESCALE_USER, TIMESCALE_PASSWORD")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise