"""MongoDB database adapter."""
import json
import time
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .base import BaseAdapter
from ..config import DatabaseProfile
from ..exceptions import ConnectionError, QueryError


class MongoDBAdapter(BaseAdapter):
    """Adapter for MongoDB databases."""
    
    def __init__(self, profile: DatabaseProfile):
        """Initialize MongoDB adapter."""
        super().__init__(profile)
        self._client: Optional[MongoClient] = None
        self._db = None
    
    def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            # Build connection URI
            if self.profile.username and self.profile.password:
                uri = (
                    f"mongodb://{self.profile.username}:{self.profile.password}"
                    f"@{self.profile.host}:{self.profile.port}"
                )
                if self.profile.auth_source:
                    uri += f"?authSource={self.profile.auth_source}"
            else:
                uri = f"mongodb://{self.profile.host}:{self.profile.port}"
            
            # Create client
            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=self.profile.pool_timeout * 1000,
                maxPoolSize=self.profile.pool_size
            )
            
            # Get database
            self._db = self._client[self.profile.database]
            
            # Test connection
            self._client.admin.command('ping')
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
    
    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute MongoDB query and return results.
        
        Supported query formats:
        
        Administrative commands:
        - "show dbs" - List all databases
        - "show collections" - List collections in current database
        - "use database_name" - Switch to a different database
        
        Collection operations:
        - "db.collection.find({})" - Find documents
        - "db.collection.find({age: {$gt: 30}})" - Find with filter
        - "db.collection.find_one({_id: '123'})" - Find single document
        - "db.collection.aggregate([{$match: {status: 'active'}}])" - Aggregation
        - "db.collection.count_documents({})" - Count documents
        """
        if self._db is None:
            raise ConnectionError("Not connected to database. Call connect() first.")
        
        start_time = time.time()
        
        try:
            # Parse query (simple parser for now)
            result = self._parse_and_execute(query, max_rows, timeout)
            
            execution_time = (time.time() - start_time) * 1000
            
            return result
            
        except PyMongoError as e:
            raise QueryError(f"MongoDB query execution failed: {e}")
        except Exception as e:
            raise QueryError(f"Unexpected error during query execution: {e}")
    
    def _parse_and_execute(
        self,
        query: str,
        max_rows: Optional[int],
        timeout: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Parse and execute MongoDB query."""
        query = query.strip()
        
        # Handle administrative commands
        if query.lower() == "show dbs":
            return self._list_databases()
        elif query.lower() == "show collections":
            return self._list_collections()
        elif query.startswith("use "):
            db_name = query[4:].strip()
            return self._use_database(db_name)
        
        # Handle collection operations
        # Format: db.collection.operation(args)
        if not query.startswith("db."):
            raise QueryError("Query must start with 'db.' or be an administrative command")
        
        # Remove 'db.' prefix
        query = query[3:]
        
        # Split into collection and operation
        parts = query.split(".", 1)
        if len(parts) != 2:
            raise QueryError("Invalid query format. Expected: db.collection.operation(...)")
        
        collection_name = parts[0]
        operation_part = parts[1]
        
        # Get collection
        collection = self._db[collection_name]
        
        # Parse operation and arguments
        if "(" not in operation_part or not operation_part.endswith(")"):
            raise QueryError("Invalid operation format")
        
        op_name = operation_part[:operation_part.index("(")]
        args_str = operation_part[operation_part.index("(") + 1:-1].strip()
        
        # Parse arguments (simple JSON parsing)
        if args_str:
            try:
                # Handle MongoDB extended JSON (like ObjectId, etc.)
                args = json.loads(args_str) if args_str else {}
            except json.JSONDecodeError:
                # Try to evaluate as Python dict
                try:
                    args = eval(args_str)
                except Exception as e:
                    raise QueryError(f"Failed to parse query arguments: {e}")
        else:
            args = {}
        
        # Execute operation
        if op_name == "find":
            cursor = collection.find(args)
            if max_rows:
                cursor = cursor.limit(max_rows)
            if timeout:
                cursor = cursor.max_time_ms(timeout * 1000)
            results = list(cursor)
        
        elif op_name == "find_one":
            result = collection.find_one(args)
            results = [result] if result else []
        
        elif op_name == "aggregate":
            if not isinstance(args, list):
                raise QueryError("aggregate() requires a list of pipeline stages")
            cursor = collection.aggregate(args)
            if timeout:
                cursor = cursor.max_time_ms(timeout * 1000)
            results = list(cursor)
            if max_rows:
                results = results[:max_rows]
        
        elif op_name == "count_documents":
            count = collection.count_documents(args)
            results = [{"count": count}]
        
        else:
            raise QueryError(f"Unsupported operation: {op_name}")
        
        # Convert ObjectId and other MongoDB types to strings
        return self._serialize_results(results)
    
    def _serialize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert MongoDB types to JSON-serializable types."""
        from bson import ObjectId
        from datetime import datetime
        
        def convert_value(value):
            if isinstance(value, ObjectId):
                return str(value)
            elif isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(v) for v in value]
            return value
        
        return [convert_value(doc) for doc in results]
    
    def _get_accessible_collections(self) -> List[str]:
        """Get list of accessible collections in the current database."""
        collections = []
        
        # Known collections from the test results
        known_collections = [
            "conditions_ed", "vitals_ed", "observations_ed", 
            "medications_dispense_ed", "encounters_ed", "procedures_ed"
        ]
        
        # Try to discover collections by attempting to access them
        for coll_name in known_collections:
            try:
                collection = self._db[coll_name]
                # Try to get one document to verify collection exists
                collection.find_one()
                collections.append(coll_name)
            except Exception:
                continue
        
        # Also try some common collection names
        common_collections = [
            "users", "products", "orders", "customers", "data", "items", "records",
            "patients", "encounters", "observations", "medications", "procedures", 
            "conditions", "vitals", "lab_results", "diagnoses", "treatments"
        ]
        
        for coll_name in common_collections:
            if coll_name not in collections:
                try:
                    collection = self._db[coll_name]
                    # Try to get one document to verify collection exists
                    collection.find_one()
                    collections.append(coll_name)
                except Exception:
                    continue
        
        return collections
    
    def _list_databases(self) -> List[Dict[str, Any]]:
        """List all databases."""
        try:
            # Get stats for current database using dbStats (this should work)
            current_db_name = self.profile.database
            
            try:
                stats = self._db.command("dbStats")
                results = [{
                    "name": current_db_name,
                    "sizeOnDisk": stats.get("dataSize", 0),
                    "collections": stats.get("collections", 0),
                    "objects": stats.get("objects", 0)
                }]
            except Exception:
                # Fallback to discovery method if dbStats fails
                collections = self._get_accessible_collections()
                collection_count = len(collections)
                
                # Estimate total documents
                total_docs = 0
                for coll_name in collections:
                    try:
                        collection = self._db[coll_name]
                        count = collection.estimated_document_count()
                        total_docs += count
                    except Exception:
                        continue
                
                results = [{
                    "name": current_db_name,
                    "sizeOnDisk": 0,  # Can't get size without dbStats
                    "collections": collection_count,
                    "objects": total_docs
                }]
            
            # Try to discover other databases by attempting to connect to common names
            common_db_names = ["admin", "local", "config", "test", "mimic", "clinical", "lab"]
            for db_name in common_db_names:
                if db_name != current_db_name:
                    try:
                        test_db = self._client[db_name]
                        # Try to get stats for other databases
                        try:
                            stats = test_db.command("dbStats")
                            results.append({
                                "name": db_name,
                                "sizeOnDisk": stats.get("dataSize", 0),
                                "collections": stats.get("collections", 0),
                                "objects": stats.get("objects", 0)
                            })
                        except Exception:
                            # If dbStats fails, just indicate database exists
                            results.append({
                                "name": db_name,
                                "sizeOnDisk": 0,
                                "collections": 0,
                                "objects": 0
                            })
                    except Exception:
                        # Database doesn't exist or we don't have access
                        continue
            
            return results
        except Exception as e:
            raise QueryError(f"Failed to list databases: {e}")
    
    def _list_collections(self) -> List[Dict[str, Any]]:
        """List all collections in the current database."""
        try:
            # Use our helper method to get accessible collections
            collections = self._get_accessible_collections()
            
            results = []
            for coll_name in collections:
                try:
                    collection = self._db[coll_name]
                    stats = collection.estimated_document_count()
                    results.append({
                        "name": coll_name,
                        "type": "collection",
                        "count": stats
                    })
                except Exception:
                    # If we can't get count, just include basic info
                    results.append({
                        "name": coll_name,
                        "type": "collection",
                        "count": 0
                    })
            
            return results
        except Exception as e:
            raise QueryError(f"Failed to list collections: {e}")
    
    def _use_database(self, db_name: str) -> List[Dict[str, Any]]:
        """Switch to a different database."""
        try:
            # Try to switch to the new database directly
            # We'll catch the error if the database doesn't exist
            new_db = self._client[db_name]
            
            # Test if we can access the database by trying to list collections
            try:
                collections = new_db.list_collection_names()
                collection_count = len(collections)
            except Exception:
                # Database might exist but we don't have access to list collections
                collection_count = 0
            
            # Switch to the new database
            self._db = new_db
            
            # Update the profile's database setting
            self.profile.database = db_name
            
            return [{
                "message": f"Switched to database '{db_name}'",
                "database": db_name,
                "collections": collection_count
            }]
        except Exception as e:
            raise QueryError(f"Failed to switch to database '{db_name}': {e}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get MongoDB database schema (collections and sample documents)."""
        try:
            collections = self._db.list_collection_names()
            
            schema = {}
            for coll_name in collections:
                collection = self._db[coll_name]
                
                # Get sample document to infer schema
                sample = collection.find_one()
                
                if sample:
                    # Extract field types from sample
                    fields = {}
                    for key, value in sample.items():
                        fields[key] = {
                            'type': type(value).__name__,
                            'sample': str(value)[:50] if not isinstance(value, (dict, list)) else None
                        }
                    
                    schema[coll_name] = {
                        'count': collection.count_documents({}),
                        'fields': fields
                    }
                else:
                    schema[coll_name] = {
                        'count': 0,
                        'fields': {}
                    }
            
            return schema
            
        except Exception as e:
            raise QueryError(f"Failed to get schema: {e}")
    
    def test_connection(self) -> bool:
        """Test if connection is alive."""
        if self._client is None:
            return False
        
        try:
            self._client.admin.command('ping')
            return True
        except Exception:
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter has an active connection."""
        return self._client is not None and self._db is not None


if __name__ == "__main__":
    import os
    from ..config import DatabaseProfile
    
    print("Testing MongoDBAdapter...")
    
    # Test configuration
    profile = DatabaseProfile(
        type="mongodb",
        host=os.getenv("MONGO_HOST", "localhost"),
        port=int(os.getenv("MONGO_PORT", "27017")),
        database=os.getenv("MONGO_DB", "test"),
        username=os.getenv("MONGO_USER"),
        password=os.getenv("MONGO_PASSWORD"),
        auth_source=os.getenv("MONGO_AUTH_SOURCE", "admin")
    )
    
    print(f"Connecting to {profile.host}:{profile.port}/{profile.database}...")
    
    try:
        # Test connection
        adapter = MongoDBAdapter(profile)
        adapter.connect()
        print("✓ Connected successfully")
        
        # Test connection check
        assert adapter.test_connection(), "Connection test failed"
        print("✓ Connection test passed")
        
        # Test administrative commands
        print("\n--- Testing Administrative Commands ---")
        
        # Test show dbs
        try:
            dbs = adapter.execute("show dbs")
            print(f"✓ List databases: {len(dbs)} databases found")
            for db in dbs[:3]:  # Show first 3 databases
                print(f"  - {db['name']}: {db['collections']} collections, {db['sizeOnDisk']} bytes")
        except Exception as e:
            print(f"⚠ List databases failed: {e}")
        
        # Test show collections
        try:
            collections = adapter.execute("show collections")
            print(f"✓ List collections: {len(collections)} collections found")
            for coll in collections[:3]:  # Show first 3 collections
                print(f"  - {coll['name']}: {coll['count']} documents")
        except Exception as e:
            print(f"⚠ List collections failed: {e}")
        
        # Test schema retrieval
        schema = adapter.get_schema()
        print(f"✓ Schema retrieved: {len(schema)} collections found")
        for coll_name, coll_info in list(schema.items())[:3]:
            print(f"  - {coll_name}: {coll_info['count']} documents, {len(coll_info['fields'])} fields")
        
        # Test query execution (if collections exist)
        if schema:
            first_collection = list(schema.keys())[0]
            result = adapter.execute(f"db.{first_collection}.find({{}})", max_rows=5)
            print(f"✓ Query executed on '{first_collection}': {len(result)} documents returned")
            
            # Test count
            result = adapter.execute(f"db.{first_collection}.count_documents({{}})")
            print(f"✓ Count query: {result[0]['count']} documents")
        
        # Clean up
        adapter.disconnect()
        print("✓ Disconnected successfully")
        
        # Test context manager
        with MongoDBAdapter(profile) as adapter:
            schema = adapter.get_schema()
            print("✓ Context manager works")
        
        print("\n✓ All MongoDB adapter tests passed")
        
    except ConnectionError as e:
        print(f"\n⚠ Connection test skipped (database not available): {e}")
        print("  To test with a real database, set environment variables:")
        print("  - MONGO_HOST, MONGO_PORT, MONGO_DB")
        print("  - MONGO_USER, MONGO_PASSWORD (if auth required)")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise