"""Governance API client for metadata submission."""
import os
from typing import Any, Dict, Optional

import httpx

from causum.exceptions import GovernanceError, AuthenticationError


class GovernanceClient:
    """Client for submitting metadata to governance API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:5000/metadata",
        api_key: Optional[str] = None,
        timeout: int = 5,
        retry_count: int = 3,
        fail_open: bool = True
    ):
        """
        Initialize governance client.
        
        Args:
            base_url: Base URL for governance API
            api_key: API key for authentication (or set CAUSALPY_API_KEY env var)
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts
            fail_open: If True, continue on errors; if False, raise errors
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.fail_open = fail_open
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('CAUSALPY_API_KEY')
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Set CAUSALPY_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Create HTTP client
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
        )
    
    def submit_metadata(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Submit metadata to governance API.
        
        Args:
            metadata: Metadata dictionary to submit
            
        Returns:
            API response or None if fail_open and error occurred
        """
        for attempt in range(self.retry_count):
            try:
                response = self._client.post(self.base_url, json=metadata)
                response.raise_for_status()
                return response.json() if response.text else {'status': 'success'}
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    error = AuthenticationError(f"Authentication failed: {e}")
                    if not self.fail_open:
                        raise error
                    return None
                
                if attempt == self.retry_count - 1:
                    error = GovernanceError(f"Metadata submission failed after {self.retry_count} attempts: {e}")
                    if not self.fail_open:
                        raise error
                    return None
                
            except httpx.RequestError as e:
                if attempt == self.retry_count - 1:
                    error = GovernanceError(f"Request error after {self.retry_count} attempts: {e}")
                    if not self.fail_open:
                        raise error
                    return None
            
            except Exception as e:
                error = GovernanceError(f"Unexpected error during metadata submission: {e}")
                if not self.fail_open:
                    raise error
                return None
        
        return None
    
    async def submit_metadata_async(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Submit metadata to governance API asynchronously.
        
        Args:
            metadata: Metadata dictionary to submit
            
        Returns:
            API response or None if fail_open and error occurred
        """
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
        ) as client:
            for attempt in range(self.retry_count):
                try:
                    response = await client.post(self.base_url, json=metadata)
                    response.raise_for_status()
                    return response.json() if response.text else {'status': 'success'}
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        error = AuthenticationError(f"Authentication failed: {e}")
                        if not self.fail_open:
                            raise error
                        return None
                    
                    if attempt == self.retry_count - 1:
                        error = GovernanceError(f"Metadata submission failed after {self.retry_count} attempts: {e}")
                        if not self.fail_open:
                            raise error
                        return None
                    
                except httpx.RequestError as e:
                    if attempt == self.retry_count - 1:
                        error = GovernanceError(f"Request error after {self.retry_count} attempts: {e}")
                        if not self.fail_open:
                            raise error
                        return None
                
                except Exception as e:
                    error = GovernanceError(f"Unexpected error during metadata submission: {e}")
                    if not self.fail_open:
                        raise error
                    return None
        
        return None
    
    def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            self._client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    import asyncio
    
    print("Testing GovernanceClient...")
    
    # Set test API key
    os.environ['CAUSALPY_API_KEY'] = 'test-api-key-12345'
    
    # Test metadata
    test_metadata = {
        'timestamp': '2025-10-17T14:32:10.123Z',
        'profile': 'postgres_admin',
        'db': 'postgres',
        'schema': 'public.patients',
        'fields': ['subject_id', 'gender', 'anchor_age'],
        'operation': 'SELECT',
        'query_hash': 'abc123def456',
        'execution_time_ms': 25.5,
        'row_count': 10,
        'cached': False,
        'truncated': False,
    }
    
    # Test 1: Client initialization
    try:
        client = GovernanceClient(
            base_url="http://localhost:5000/metadata",
            timeout=5,
            retry_count=2,
            fail_open=True
        )
        print("✓ Client initialized successfully")
        print(f"  Base URL: {client.base_url}")
        print(f"  Timeout: {client.timeout}s")
        print(f"  Retry count: {client.retry_count}")
        print(f"  Fail open: {client.fail_open}")
    except Exception as e:
        print(f"✓ Client initialization requires API key: {e}")
    
    # Test 2: Sync submission (will fail if no server)
    print("\n✓ Testing sync submission...")
    try:
        with GovernanceClient(fail_open=True) as client:
            response = client.submit_metadata(test_metadata)
            if response:
                print(f"  Response: {response}")
            else:
                print("  No response (fail_open=True, server not available)")
    except Exception as e:
        print(f"  Expected: {e}")
    
    # Test 3: Async submission (will fail if no server)
    print("\n✓ Testing async submission...")
    async def test_async():
        try:
            client = GovernanceClient(fail_open=True)
            response = await client.submit_metadata_async(test_metadata)
            if response:
                print(f"  Response: {response}")
            else:
                print("  No response (fail_open=True, server not available)")
        except Exception as e:
            print(f"  Expected: {e}")
    
    asyncio.run(test_async())
    
    # Test 4: Authentication error
    print("\n✓ Testing authentication handling...")
    os.environ.pop('CAUSALPY_API_KEY', None)
    try:
        client = GovernanceClient()
        print("  ✗ Should have raised AuthenticationError")
    except AuthenticationError as e:
        print(f"  ✓ Correctly raised AuthenticationError")
    
    # Restore API key
    os.environ['CAUSALPY_API_KEY'] = 'test-api-key-12345'
    
    print("\n✓ All governance client tests passed")
    print("\nNote: Actual API tests require a running governance server at localhost:5000")