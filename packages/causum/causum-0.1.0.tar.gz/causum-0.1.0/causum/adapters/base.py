"""Base adapter interface for database connections."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..config import DatabaseProfile


class BaseAdapter(ABC):
    """Base class for all database adapters."""
    
    def __init__(self, profile: DatabaseProfile):
        """
        Initialize adapter with a database profile.
        
        Args:
            profile: Database connection profile
        """
        self.profile = profile
        self._connection = None
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query: Query string (SQL or database-specific)
            params: Query parameters
            max_rows: Maximum number of rows to return
            timeout: Query timeout in seconds
            
        Returns:
            List of result rows as dictionaries
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get database schema information.
        
        Returns:
            Dictionary containing schema information
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if connection is alive.
        
        Returns:
            True if connection is alive, False otherwise
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self._connection is not None
    
    @property
    def database_type(self) -> str:
        """Get database type."""
        return self.profile.type


class AsyncBaseAdapter(ABC):
    """Base class for async database adapters."""
    
    def __init__(self, profile: DatabaseProfile):
        """
        Initialize async adapter with a database profile.
        
        Args:
            profile: Database connection profile
        """
        self.profile = profile
        self._connection = None
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query: Query string (SQL or database-specific)
            params: Query parameters
            max_rows: Maximum number of rows to return
            timeout: Query timeout in seconds
            
        Returns:
            List of result rows as dictionaries
        """
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """
        Get database schema information.
        
        Returns:
            Dictionary containing schema information
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if connection is alive.
        
        Returns:
            True if connection is alive, False otherwise
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self._connection is not None
    
    @property
    def database_type(self) -> str:
        """Get database type."""
        return self.profile.type


if __name__ == "__main__":
    from ..config import DatabaseProfile
    
    print("Testing BaseAdapter interface...")
    
    # Create a mock adapter for testing
    class MockAdapter(BaseAdapter):
        def connect(self):
            self._connection = "mock_connection"
            print("  Connected to mock database")
        
        def disconnect(self):
            self._connection = None
            print("  Disconnected from mock database")
        
        def execute(self, query, params=None, max_rows=None, timeout=None):
            return [{"id": 1, "name": "test"}]
        
        def get_schema(self):
            return {"tables": ["test_table"]}
        
        def test_connection(self):
            return self._connection is not None
    
    # Test adapter
    profile = DatabaseProfile(
        type="mock",
        host="localhost",
        port=5432,
        database="testdb"
    )
    
    adapter = MockAdapter(profile)
    print(f"✓ Created adapter for {adapter.database_type}")
    print(f"  Connected: {adapter.is_connected}")
    
    # Test context manager
    with adapter:
        print(f"✓ Context manager - Connected: {adapter.is_connected}")
        result = adapter.execute("SELECT * FROM test")
        print(f"✓ Execute returned {len(result)} rows")
        schema = adapter.get_schema()
        print(f"✓ Schema has {len(schema['tables'])} tables")
        print(f"✓ Test connection: {adapter.test_connection()}")
    
    print(f"✓ After context - Connected: {adapter.is_connected}")
    
    print("\n✓ All base adapter tests passed")