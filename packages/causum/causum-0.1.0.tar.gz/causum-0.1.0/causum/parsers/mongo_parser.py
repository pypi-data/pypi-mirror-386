"""MongoDB query parser."""
import json
import re
from typing import Any, Dict, List, Optional

from causum.exceptions import ParserError


class MongoQueryParser:
    """Parser for MongoDB queries."""
    
    def parse(self, query: str) -> Dict[str, Any]:
        """
        Parse MongoDB query and extract metadata.
        
        Args:
            query: MongoDB query string (e.g., "db.collection.find({})", "show dbs", "show collections", "use dbname")
            
        Returns:
            Dictionary with parsed metadata
        """
        try:
            query = query.strip()
            
            # Handle administrative commands
            if query.lower() == "show dbs":
                return {
                    'operation': 'SHOW_DBS',
                    'collection': None,
                    'fields': [],
                    'has_filter': False,
                    'is_aggregation': False,
                    'is_admin_command': True
                }
            elif query.lower() == "show collections":
                return {
                    'operation': 'SHOW_COLLECTIONS',
                    'collection': None,
                    'fields': [],
                    'has_filter': False,
                    'is_aggregation': False,
                    'is_admin_command': True
                }
            elif query.startswith("use "):
                db_name = query[4:].strip()
                return {
                    'operation': 'USE_DATABASE',
                    'collection': None,
                    'fields': [],
                    'has_filter': False,
                    'is_aggregation': False,
                    'is_admin_command': True,
                    'database': db_name
                }
            
            # Extract collection and operation
            collection, operation, args = self._parse_query_structure(query)
            
            # Extract fields from query args
            fields = self._extract_fields(args, operation)
            
            metadata = {
                'operation': operation.upper(),
                'collection': collection,
                'fields': fields,
                'has_filter': self._has_filter(args),
                'is_aggregation': operation == 'aggregate',
                'is_admin_command': False
            }
            
            return metadata
            
        except Exception as e:
            raise ParserError(f"Failed to parse MongoDB query: {e}")
    
    def _parse_query_structure(self, query: str) -> tuple[str, str, str]:
        """
        Parse the query structure to extract collection, operation, and arguments.
        
        Args:
            query: MongoDB query string
            
        Returns:
            Tuple of (collection_name, operation, arguments)
        """
        # Pattern: db.collection.operation(args)
        pattern = r'db\.([a-zA-Z0-9_]+)\.([a-zA-Z_]+)\((.*)\)$'
        match = re.match(pattern, query, re.DOTALL)
        
        if not match:
            raise ParserError("Invalid MongoDB query format. Expected: db.collection.operation(...)")
        
        collection = match.group(1)
        operation = match.group(2)
        args = match.group(3).strip()
        
        return collection, operation, args
    
    def _extract_fields(self, args: str, operation: str) -> List[str]:
        """
        Extract field names from query arguments.
        
        Args:
            args: Query arguments string
            operation: Operation type (find, aggregate, etc.)
            
        Returns:
            List of field names
        """
        fields = set()
        
        if not args:
            return []
        
        try:
            # Try to parse as JSON
            parsed_args = json.loads(args) if args else {}
            
            if operation == 'find':
                # Extract fields from filter
                if isinstance(parsed_args, dict):
                    fields.update(self._extract_fields_from_dict(parsed_args))
            
            elif operation == 'aggregate':
                # Extract fields from pipeline stages
                if isinstance(parsed_args, list):
                    for stage in parsed_args:
                        if isinstance(stage, dict):
                            fields.update(self._extract_fields_from_dict(stage))
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract field names with regex
            field_pattern = r'["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?\s*:'
            matches = re.findall(field_pattern, args)
            fields.update(matches)
        
        return sorted(fields)
    
    def _extract_fields_from_dict(self, obj: Any, prefix: str = "") -> set:
        """
        Recursively extract field names from dictionary.
        
        Args:
            obj: Dictionary or value to extract fields from
            prefix: Prefix for nested fields
            
        Returns:
            Set of field names
        """
        fields = set()
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Skip MongoDB operators (starting with $)
                if not key.startswith('$'):
                    full_key = f"{prefix}.{key}" if prefix else key
                    fields.add(full_key)
                    
                    # Recurse into nested objects
                    if isinstance(value, dict):
                        fields.update(self._extract_fields_from_dict(value, full_key))
                elif isinstance(value, dict):
                    # Still recurse into operator values
                    fields.update(self._extract_fields_from_dict(value, prefix))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            fields.update(self._extract_fields_from_dict(item, prefix))
        
        return fields
    
    def _has_filter(self, args: str) -> bool:
        """Check if query has filter conditions."""
        if not args or args == '{}':
            return False
        
        try:
            parsed = json.loads(args) if args else {}
            return bool(parsed)
        except json.JSONDecodeError:
            return bool(args)
    
    def get_collection_from_query(self, query: str) -> str:
        """
        Extract collection name from query.
        
        Args:
            query: MongoDB query string
            
        Returns:
            Collection name
        """
        try:
            collection, _, _ = self._parse_query_structure(query)
            return collection
        except Exception:
            return "unknown"
    
    def get_fields_from_query(self, query: str) -> List[str]:
        """
        Extract field names from query.
        
        Args:
            query: MongoDB query string
            
        Returns:
            List of field names
        """
        try:
            metadata = self.parse(query)
            return metadata['fields']
        except Exception:
            return []


if __name__ == "__main__":
    print("Testing MongoQueryParser...")
    
    parser = MongoQueryParser()
    
    # Test 1: Simple find
    query1 = "db.users.find({})"
    result1 = parser.parse(query1)
    print(f"✓ Parsed simple find:")
    print(f"  Operation: {result1['operation']}")
    print(f"  Collection: {result1['collection']}")
    print(f"  Has filter: {result1['has_filter']}")
    
    # Test 2: Find with filter
    query2 = 'db.users.find({"age": {"$gt": 25}, "status": "active"})'
    result2 = parser.parse(query2)
    print(f"\n✓ Parsed find with filter:")
    print(f"  Collection: {result2['collection']}")
    print(f"  Fields: {result2['fields']}")
    print(f"  Has filter: {result2['has_filter']}")
    
    # Test 3: Aggregation pipeline
    query3 = 'db.orders.aggregate([{"$match": {"status": "completed"}}, {"$group": {"_id": "$customer_id", "total": {"$sum": "$amount"}}}])'
    result3 = parser.parse(query3)
    print(f"\n✓ Parsed aggregation:")
    print(f"  Collection: {result3['collection']}")
    print(f"  Is aggregation: {result3['is_aggregation']}")
    print(f"  Fields: {result3['fields']}")
    
    # Test 4: Collection extraction
    collection = parser.get_collection_from_query(query2)
    print(f"\n✓ Extracted collection: {collection}")
    assert collection == "users"
    
    # Test 5: Field extraction
    fields = parser.get_fields_from_query(query2)
    print(f"\n✓ Extracted fields: {fields}")
    assert "age" in fields
    assert "status" in fields
    
    # Test 6: Count documents
    query4 = 'db.products.count_documents({"category": "electronics"})'
    result4 = parser.parse(query4)
    print(f"\n✓ Parsed count_documents:")
    print(f"  Operation: {result4['operation']}")
    print(f"  Collection: {result4['collection']}")
    
    # Test 7: find_one
    query5 = 'db.users.find_one({"_id": "123"})'
    result5 = parser.parse(query5)
    print(f"\n✓ Parsed find_one:")
    print(f"  Operation: {result5['operation']}")
    
    # Test 8: Administrative commands
    print(f"\n--- Testing Administrative Commands ---")
    
    # Test show dbs
    query6 = "show dbs"
    result6 = parser.parse(query6)
    print(f"\n✓ Parsed show dbs:")
    print(f"  Operation: {result6['operation']}")
    print(f"  Is admin command: {result6['is_admin_command']}")
    
    # Test show collections
    query7 = "show collections"
    result7 = parser.parse(query7)
    print(f"\n✓ Parsed show collections:")
    print(f"  Operation: {result7['operation']}")
    print(f"  Is admin command: {result7['is_admin_command']}")
    
    # Test use database
    query8 = "use my_database"
    result8 = parser.parse(query8)
    print(f"\n✓ Parsed use database:")
    print(f"  Operation: {result8['operation']}")
    print(f"  Database: {result8['database']}")
    print(f"  Is admin command: {result8['is_admin_command']}")
    
    print("\n✓ All MongoDB parser tests passed")