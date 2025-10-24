#!/usr/bin/env python3
"""Test MongoDB connection and authentication."""

import os
from causum import UniversalClient

def test_mongo_connection():
    """Test basic MongoDB connection and see what we can access."""
    
    client = UniversalClient(profiles="./profiles.json")
    
    try:
        print("Testing MongoDB Connection")
        print("=" * 40)
        
        # Test basic connection
        print("\n1. Testing basic connection:")
        result = client.execute(
            profile="mongodb_ed",
            query="db.test.find({})",
            max_rows=1
        )
        
        if result['status'] == 'success':
            print("✓ Basic connection works")
        else:
            print(f"✗ Connection failed: {result['error']}")
        
        # Test if we can access specific collections directly
        print("\n2. Testing direct collection access:")
        collections_to_test = [
            "conditions_ed", "vitals_ed", "observations_ed", 
            "medications_dispense_ed", "encounters_ed", "procedures_ed"
        ]
        
        found_collections = []
        for coll_name in collections_to_test:
            result = client.execute(
                profile="mongodb_ed",
                query=f"db.{coll_name}.find({{}})",
                max_rows=1
            )
            
            if result['status'] == 'success':
                count_result = client.execute(
                    profile="mongodb_ed",
                    query=f"db.{coll_name}.count_documents({{}})",
                    max_rows=1
                )
                count = count_result['data'][0]['count'] if count_result['status'] == 'success' else 0
                found_collections.append((coll_name, count))
                print(f"✓ Found collection '{coll_name}': {count} documents")
            else:
                print(f"✗ Collection '{coll_name}' not accessible: {result['error']}")
        
        print(f"\n✓ Found {len(found_collections)} accessible collections")
        
        # Test a sample query on the first found collection
        if found_collections:
            first_coll, count = found_collections[0]
            print(f"\n3. Testing sample query on '{first_coll}':")
            result = client.execute(
                profile="mongodb_ed",
                query=f"db.{first_coll}.find({{}})",
                max_rows=3
            )
            
            if result['status'] == 'success':
                print(f"✓ Sample query successful: {len(result['data'])} documents returned")
                if result['data']:
                    print(f"  Sample document keys: {list(result['data'][0].keys())}")
            else:
                print(f"✗ Sample query failed: {result['error']}")
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    test_mongo_connection()
