"""
Standalone example of using Causum™ API without any framework.

This example shows how to use Causum™ API directly in your Python application.
"""
import os
from causum import UniversalClient

# Set API key (or use environment variable CAUSALPY_API_KEY)
# os.environ['CAUSALPY_API_KEY'] = 'your-api-key-here'


def main():
    """Main example function."""
    
    # Initialize client with profiles file
    client = UniversalClient(
        profiles="./profiles.json",
        governance_url="http://localhost:5000/metadata",
        enable_cache=True,
        fail_open=True
    )
    
    print("Available profiles:", client.list_profiles())
    
    # Example 1: Simple query
    print("\n" + "="*60)
    print("Example 1: Simple PostgreSQL Query")
    print("="*60)
    
    result = client.execute(
        profile="postgres_admin",
        query="SELECT * FROM patients LIMIT 5"
    )
    
    if result['status'] == 'success':
        print(f"Retrieved {len(result['data'])} rows")
        print("First row:", result['data'][0] if result['data'] else "No data")
        print("Metadata:", result['metadata'])
    else:
        print("Error:", result['error'])
    
    # Example 2: Query with parameters (for SQL databases)
    print("\n" + "="*60)
    print("Example 2: Parameterized Query")
    print("="*60)
    
    result = client.execute(
        profile="postgres_admin",
        query="SELECT * FROM patients WHERE gender = %(gender)s LIMIT 5",
        params={'gender': 'F'}
    )
    
    if result['status'] == 'success':
        print(f"Retrieved {len(result['data'])} female patients")
    else:
        print("Error:", result['error'])
    
    # Example 3: MongoDB query
    print("\n" + "="*60)
    print("Example 3: MongoDB Query")
    print("="*60)
    
    result = client.execute(
        profile="mongo_ed",
        query='db.stays.find({"disposition": "admitted"})',
        max_rows=10
    )
    
    if result['status'] == 'success':
        print(f"Retrieved {len(result['data'])} stays")
        print("Metadata:", result['metadata'])
    else:
        print("Error:", result['error'])
    
    # Example 4: Get schema information
    print("\n" + "="*60)
    print("Example 4: Schema Introspection")
    print("="*60)
    
    try:
        schema = client.get_schema("postgres_admin")
        print(f"Schema retrieved: {len(schema)} schemas/tables")
        # Print first few tables
        for schema_name, tables in list(schema.items())[:2]:
            print(f"\nSchema: {schema_name}")
            for table_name, columns in list(tables.items())[:2]:
                print(f"  Table: {table_name} ({len(columns)} columns)")
                for col_name, col_info in list(columns.items())[:3]:
                    print(f"    - {col_name}: {col_info.get('type')}")
    except Exception as e:
        print(f"Schema error: {e}")
    
    # Example 5: Test connection
    print("\n" + "="*60)
    print("Example 5: Test Connections")
    print("="*60)
    
    for profile in client.list_profiles():
        is_connected = client.test_connection(profile)
        status = "✓" if is_connected else "✗"
        print(f"{status} {profile}: {'Connected' if is_connected else 'Failed'}")
    
    # Example 6: Using context manager
    print("\n" + "="*60)
    print("Example 6: Context Manager")
    print("="*60)
    
    with UniversalClient(profiles_path="./profiles.json") as c:
        result = c.execute(
            profile="postgres_admin",
            query="SELECT COUNT(*) as total FROM patients"
        )
        if result['status'] == 'success':
            print("Total patients:", result['data'][0]['total'])
    
    print("\n✓ All examples completed")
    
    # Clean up
    client.close()


if __name__ == "__main__":
    main()