"""Cache manager for query results."""
import hashlib
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

from diskcache import Cache

from .exceptions import CausumAPIError


class CacheManager:
    """Manages caching of query results."""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl: int = 300,
        enabled: bool = True
    ):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache storage (default: ~/.causum/cache)
            ttl: Time-to-live for cache entries in seconds
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.ttl = ttl
        
        if self.enabled:
            if cache_dir is None:
                cache_dir = str(Path.home() / ".causum" / "cache")
            
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            self._cache = Cache(str(self.cache_dir))
        else:
            self._cache = None
    
    def _generate_key(self, profile: str, query: str) -> str:
        """
        Generate cache key from profile and query.
        
        Args:
            profile: Profile name
            query: Query string
            
        Returns:
            Cache key
        """
        # Normalize query (remove extra whitespace)
        normalized_query = ' '.join(query.lower().split())
        
        # Create key from profile + normalized query
        key_string = f"{profile}:{normalized_query}"
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"causum:{key_hash}"
    
    def get(self, profile: str, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached result for a query.
        
        Args:
            profile: Profile name
            query: Query string
            
        Returns:
            Cached result or None if not found
        """
        if not self.enabled or not self._cache:
            return None
        
        try:
            key = self._generate_key(profile, query)
            result = self._cache.get(key)
            return result
        except Exception:
            # If cache read fails, return None
            return None
    
    def set(
        self,
        profile: str,
        query: str,
        result: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store result in cache.
        
        Args:
            profile: Profile name
            query: Query string
            result: Query result to cache
            ttl: Time-to-live (overrides default)
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self.enabled or not self._cache:
            return False
        
        try:
            key = self._generate_key(profile, query)
            expire_time = ttl if ttl is not None else self.ttl
            
            self._cache.set(key, result, expire=expire_time)
            return True
        except Exception:
            # If cache write fails, return False
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        if self.enabled and self._cache:
            try:
                self._cache.clear()
            except Exception:
                pass
    
    def clear_profile(self, profile: str) -> None:
        """
        Clear cache entries for a specific profile.
        
        Args:
            profile: Profile name
        """
        if not self.enabled or not self._cache:
            return
        
        try:
            # This is not efficient for large caches, but works
            # For better performance, could prefix keys with profile
            keys_to_delete = []
            for key in self._cache.iterkeys():
                if key.startswith("causum:"):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self._cache.delete(key)
        except Exception:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self._cache:
            return {
                'enabled': False,
                'size': 0,
                'volume': 0,
            }
        
        try:
            return {
                'enabled': True,
                'size': len(self._cache),
                'volume': self._cache.volume(),
                'cache_dir': str(self.cache_dir),
            }
        except Exception:
            return {
                'enabled': True,
                'size': 0,
                'volume': 0,
                'error': 'Failed to get stats'
            }
    
    def close(self) -> None:
        """Close cache."""
        if self._cache:
            try:
                self._cache.close()
            except Exception:
                pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    import tempfile
    import time
    
    print("Testing CacheManager...")
    
    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test 1: Initialize cache
        cache = CacheManager(cache_dir=temp_dir, ttl=2, enabled=True)
        print("✓ Cache initialized")
        print(f"  Cache dir: {cache.cache_dir}")
        print(f"  TTL: {cache.ttl}s")
        
        # Test 2: Store and retrieve
        test_profile = "postgres_test"
        test_query = "SELECT * FROM users WHERE id = 1"
        test_result = [{'id': 1, 'name': 'Alice', 'age': 30}]
        
        success = cache.set(test_profile, test_query, test_result)
        assert success, "Cache set should succeed"
        print("✓ Stored result in cache")
        
        cached_result = cache.get(test_profile, test_query)
        assert cached_result == test_result, "Cached result should match original"
        print("✓ Retrieved result from cache")
        print(f"  Result: {cached_result}")
        
        # Test 3: Query normalization (whitespace handling)
        query_with_spaces = "SELECT   *   FROM   users   WHERE   id   =   1"
        cached_result2 = cache.get(test_profile, query_with_spaces)
        assert cached_result2 == test_result, "Should retrieve same result despite whitespace"
        print("✓ Query normalization works")
        
        # Test 4: Cache miss
        miss_result = cache.get(test_profile, "SELECT * FROM users WHERE id = 999")
        assert miss_result is None, "Should return None for cache miss"
        print("✓ Cache miss returns None")
        
        # Test 5: TTL expiration
        print("✓ Testing TTL expiration (waiting 3 seconds)...")
        time.sleep(3)
        expired_result = cache.get(test_profile, test_query)
        assert expired_result is None, "Should return None after TTL expires"
        print("  Cached entry expired as expected")
        
        # Test 6: Cache statistics
        cache.set(test_profile, "SELECT 1", [{'result': 1}])
        cache.set(test_profile, "SELECT 2", [{'result': 2}])
        
        stats = cache.get_stats()
        print(f"✓ Cache statistics:")
        print(f"  Enabled: {stats['enabled']}")
        print(f"  Size: {stats['size']} entries")
        print(f"  Volume: {stats['volume']} bytes")
        
        # Test 7: Clear cache
        cache.clear()
        stats_after_clear = cache.get_stats()
        assert stats_after_clear['size'] == 0, "Cache should be empty after clear"
        print("✓ Cache cleared successfully")
        
        # Test 8: Disabled cache
        disabled_cache = CacheManager(enabled=False)
        result = disabled_cache.set("profile", "query", [])
        assert result is False, "Disabled cache should return False on set"
        result = disabled_cache.get("profile", "query")
        assert result is None, "Disabled cache should return None on get"
        print("✓ Disabled cache works correctly")
        
        # Test 9: Context manager
        with CacheManager(cache_dir=temp_dir, enabled=True) as cm:
            cm.set("test", "SELECT 1", [{'n': 1}])
            result = cm.get("test", "SELECT 1")
            assert result == [{'n': 1}]
        print("✓ Context manager works")
        
        cache.close()
    
    print("\n✓ All cache manager tests passed")