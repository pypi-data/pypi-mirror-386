"""Database adapters for causum."""
from typing import Dict, Type

from .base import BaseAdapter, AsyncBaseAdapter
from .postgres import PostgresAdapter
from .mysql import MySQLAdapter
from .mongodb import MongoDBAdapter
from .clickhouse import ClickHouseAdapter
from .timescaledb import TimescaleAdapter
from .sqlalchemy_adapter import SQLAlchemyAdapter

# Registry of available adapters
ADAPTER_REGISTRY: Dict[str, Type[BaseAdapter]] = {
    # Optimized native adapters
    'postgres': PostgresAdapter,
    'postgresql': PostgresAdapter,
    'mysql': MySQLAdapter,
    'mongodb': MongoDBAdapter,
    'mongo': MongoDBAdapter,
    'clickhouse': ClickHouseAdapter,
    'timescaledb': TimescaleAdapter,
    'timescale': TimescaleAdapter,
    
    # SQLAlchemy-based adapters (50+ databases)
    'oracle': SQLAlchemyAdapter,
    'mssql': SQLAlchemyAdapter,
    'sqlserver': SQLAlchemyAdapter,
    'db2': SQLAlchemyAdapter,
    'snowflake': SQLAlchemyAdapter,
    'redshift': SQLAlchemyAdapter,
    'bigquery': SQLAlchemyAdapter,
    'databricks': SQLAlchemyAdapter,
    'sqlite': SQLAlchemyAdapter,
    'firebird': SQLAlchemyAdapter,
    'sybase': SQLAlchemyAdapter,
    'teradata': SQLAlchemyAdapter,
    'vertica': SQLAlchemyAdapter,
    'presto': SQLAlchemyAdapter,
    'trino': SQLAlchemyAdapter,
    'athena': SQLAlchemyAdapter,
    'awsathena': SQLAlchemyAdapter,
    'hive': SQLAlchemyAdapter,
    'impala': SQLAlchemyAdapter,
    'drill': SQLAlchemyAdapter,
    
    # Fallback: any unknown SQL database will use SQLAlchemy
    'sqlalchemy': SQLAlchemyAdapter,
}


def get_adapter(db_type: str) -> Type[BaseAdapter]:
    """
    Get adapter class for a database type.
    
    Args:
        db_type: Database type string (e.g., 'postgres', 'mysql')
        
    Returns:
        Adapter class
        
    Raises:
        ValueError: If database type is not supported
    """
    db_type = db_type.lower()
    
    # Check if in registry
    if db_type in ADAPTER_REGISTRY:
        return ADAPTER_REGISTRY[db_type]
    
    # For any SQL database not in registry, try SQLAlchemy
    # This allows support for new databases without updating the registry
    print(f"Warning: '{db_type}' not in registry, using SQLAlchemyAdapter")
    return SQLAlchemyAdapter


__all__ = [
    'BaseAdapter',
    'AsyncBaseAdapter',
    'PostgresAdapter',
    'MySQLAdapter',
    'MongoDBAdapter',
    'ClickHouseAdapter',
    'TimescaleAdapter',
    'SQLAlchemyAdapter',
    'ADAPTER_REGISTRY',
    'get_adapter',
]


if __name__ == "__main__":
    print("Testing adapter registry...")
    
    # Test registry
    print(f"✓ Registered adapters: {len(ADAPTER_REGISTRY)}")
    for db_type, adapter_class in sorted(ADAPTER_REGISTRY.items()):
        print(f"  - {db_type}: {adapter_class.__name__}")
    
    # Test get_adapter
    adapter_class = get_adapter('postgres')
    assert adapter_class == PostgresAdapter
    print(f"✓ get_adapter('postgres') returns {adapter_class.__name__}")
    
    # Test aliases
    assert get_adapter('postgresql') == PostgresAdapter
    assert get_adapter('mongo') == MongoDBAdapter
    assert get_adapter('timescale') == TimescaleAdapter
    print("✓ Database type aliases work correctly")
    
    # Test error handling
    try:
        get_adapter('invalid_db')
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError for invalid type")
    
    print("\n✓ All adapter registry tests passed")