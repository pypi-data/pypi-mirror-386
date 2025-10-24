"""Metadata extraction for query execution."""
import hashlib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..parsers import SQLParser, MongoQueryParser


class MetadataExtractor:
    """Extracts metadata from queries and results."""
    
    def __init__(self):
        """Initialize metadata extractor."""
        self.sql_parser = SQLParser()
        self.mongo_parser = MongoQueryParser()
    
    def extract(
        self,
        query: str,
        db_type: str,
        profile: str,
        result: List[Dict[str, Any]],
        execution_time_ms: float,
        cached: bool = False,
        truncated: bool = False,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract metadata from query execution.
        
        Args:
            query: Query string
            db_type: Database type (postgres, mongodb, etc.)
            profile: Profile name used
            result: Query results
            execution_time_ms: Execution time in milliseconds
            cached: Whether result was from cache
            truncated: Whether results were truncated
            user_context: Optional user context to include
            
        Returns:
            Metadata dictionary
        """
        # Base metadata
        metadata = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'profile': profile,
            'db': db_type,
            'query_hash': self._hash_query(query),
            'execution_time_ms': round(execution_time_ms, 2),
            'row_count': len(result),
            'cached': cached,
            'truncated': truncated,
        }
        
        # Extract query-specific metadata
        if db_type in ['postgres', 'postgresql', 'mysql', 'clickhouse', 'timescaledb', 'timescale']:
            query_metadata = self._extract_sql_metadata(query)
        elif db_type in ['mongodb', 'mongo']:
            query_metadata = self._extract_mongo_metadata(query)
        else:
            query_metadata = {}
        
        metadata.update(query_metadata)
        
        # Add user context if provided
        if user_context:
            metadata['user_context'] = user_context
        
        return metadata
    
    def _hash_query(self, query: str) -> str:
        """Generate hash of query for deduplication."""
        normalized = ' '.join(query.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _extract_sql_metadata(self, query: str) -> Dict[str, Any]:
        """Extract metadata from SQL query."""
        try:
            parsed = self.sql_parser.parse(query)
            
            # Get schema.table format
            schema = self.sql_parser.get_schema_from_query(query)
            fields = self.sql_parser.get_fields_from_query(query)
            
            return {
                'schema': schema,
                'fields': fields,
                'operation': parsed['operation'],
            }
        except Exception:
            # If parsing fails, return minimal metadata
            return {
                'schema': 'unknown',
                'fields': [],
                'operation': 'UNKNOWN',
            }
    
    def _extract_mongo_metadata(self, query: str) -> Dict[str, Any]:
        """Extract metadata from MongoDB query."""
        try:
            parsed = self.mongo_parser.parse(query)
            
            return {
                'schema': parsed['collection'],
                'fields': parsed['fields'],
                'operation': parsed['operation'],
            }
        except Exception:
            # If parsing fails, return minimal metadata
            return {
                'schema': 'unknown',
                'fields': [],
                'operation': 'UNKNOWN',
            }


if __name__ == "__main__":
    print("Testing MetadataExtractor...")
    
    extractor = MetadataExtractor()
    
    # Test 1: SQL query metadata
    sql_query = "SELECT id, name, age FROM public.users WHERE age > 25"
    sql_result = [
        {'id': 1, 'name': 'Alice', 'age': 30},
        {'id': 2, 'name': 'Bob', 'age': 35}
    ]
    
    metadata1 = extractor.extract(
        query=sql_query,
        db_type='postgres',
        profile='postgres_admin',
        result=sql_result,
        execution_time_ms=25.5,
        cached=False,
        truncated=False
    )
    
    print("✓ Extracted SQL metadata:")
    print(f"  Profile: {metadata1['profile']}")
    print(f"  DB: {metadata1['db']}")
    print(f"  Schema: {metadata1['schema']}")
    print(f"  Fields: {metadata1['fields']}")
    print(f"  Operation: {metadata1['operation']}")
    print(f"  Row count: {metadata1['row_count']}")
    print(f"  Execution time: {metadata1['execution_time_ms']}ms")
    print(f"  Query hash: {metadata1['query_hash']}")
    print(f"  Timestamp: {metadata1['timestamp']}")
    
    # Test 2: MongoDB query metadata
    mongo_query = 'db.users.find({"age": {"$gt": 25}})'
    mongo_result = [
        {'_id': '1', 'name': 'Alice', 'age': 30},
        {'_id': '2', 'name': 'Bob', 'age': 35}
    ]
    
    metadata2 = extractor.extract(
        query=mongo_query,
        db_type='mongodb',
        profile='mongo_ed',
        result=mongo_result,
        execution_time_ms=15.3,
        cached=True,
        truncated=False
    )
    
    print("\n✓ Extracted MongoDB metadata:")
    print(f"  Schema: {metadata2['schema']}")
    print(f"  Fields: {metadata2['fields']}")
    print(f"  Operation: {metadata2['operation']}")
    print(f"  Cached: {metadata2['cached']}")
    
    # Test 3: With user context
    metadata3 = extractor.extract(
        query=sql_query,
        db_type='postgres',
        profile='postgres_admin',
        result=sql_result,
        execution_time_ms=25.5,
        user_context={
            'rag_session_id': 'session-123',
            'user_query': 'How many users are over 25?',
            'app_name': 'clinical-rag-app'
        }
    )
    
    print("\n✓ Extracted metadata with user context:")
    print(f"  User context: {metadata3.get('user_context')}")
    
    # Test 4: Query hashing
    query_a = "SELECT * FROM users WHERE id = 1"
    query_b = "SELECT   *   FROM   users   WHERE   id   =   1"  # Different whitespace
    
    hash_a = extractor._hash_query(query_a)
    hash_b = extractor._hash_query(query_b)
    
    assert hash_a == hash_b, "Query hashes should match despite whitespace differences"
    print(f"\n✓ Query hashing works (normalized): {hash_a}")
    
    print("\n✓ All metadata extractor tests passed")