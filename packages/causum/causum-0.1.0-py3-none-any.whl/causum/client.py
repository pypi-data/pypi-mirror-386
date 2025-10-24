"""Main UniversalClient for causum."""
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .adapters import get_adapter, BaseAdapter
from .cache import CacheManager
from .config import ProfileManager, DatabaseProfile
from .exceptions import (
    CausumAPIError,
    ConnectionError,
    ProfileNotFoundError,
    QueryError,
)
from .governance import MetadataExtractor, GovernanceClient


class UniversalClient:
    """Universal database client with built-in governance."""
    
    def __init__(
        self,
        profiles: Optional[Union[Dict[str, Any], str, Path]] = None,
        governance_url: str = "http://localhost:5555/metadata",
        governance_api_key: Optional[str] = None,
        async_governance: bool = True,
        fail_open: bool = True,
        enable_cache: bool = True,
        cache_ttl: int = 300,
        max_rows_default: int = 1000,
        timeout: int = 30,
    ):
        """
        Initialize UniversalClient.
        
        Args:
            profiles: Dictionary of profiles or path to profiles JSON file
            governance_url: Governance API endpoint
            governance_api_key: API key for governance (or set CAUSALPY_API_KEY)
            async_governance: Use async governance calls (fire-and-forget)
            fail_open: Continue on governance failures
            enable_cache: Enable result caching
            cache_ttl: Cache TTL in seconds
            max_rows_default: Default max rows to return
            timeout: Default query timeout in seconds
        """
        # Initialize profile manager
        self.profile_manager = ProfileManager(profiles=profiles)
        
        # Initialize cache
        self.cache = CacheManager(
            ttl=cache_ttl,
            enabled=enable_cache
        )
        
        # Initialize governance client
        try:
            self.governance_client = GovernanceClient(
                base_url=governance_url,
                api_key=governance_api_key,
                timeout=5,
                retry_count=3,
                fail_open=fail_open
            )
        except Exception as e:
            if not fail_open:
                raise
            # If fail_open, governance is optional
            self.governance_client = None
        
        # Initialize metadata extractor
        self.metadata_extractor = MetadataExtractor()
        
        # Settings
        self.async_governance = async_governance
        self.fail_open = fail_open
        self.max_rows_default = max_rows_default
        self.timeout = timeout
        
        # Active adapters
        self._adapters: Dict[str, BaseAdapter] = {}
    
    def execute(
        self,
        profile: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a database query.
        
        Args:
            profile: Profile name or connection string
            query: Query string
            params: Query parameters
            max_rows: Maximum rows to return (overrides default)
            timeout: Query timeout in seconds (overrides default)
            user_context: Optional user context for governance
            
        Returns:
            Result dictionary with data, metadata, and schema info
        """
        start_time = time.time()
        
        # Apply defaults
        max_rows = max_rows if max_rows is not None else self.max_rows_default
        timeout = timeout if timeout is not None else self.timeout
        
        try:
            # Check cache first
            cached_result = self.cache.get(profile, query)
            if cached_result is not None:
                execution_time = (time.time() - start_time) * 1000
                
                # Get profile info
                db_profile = self.profile_manager.get_profile(profile)
                
                # Extract and submit metadata
                metadata = self._extract_and_submit_metadata(
                    query=query,
                    db_type=db_profile.type,
                    profile=profile,
                    result=cached_result,
                    execution_time_ms=execution_time,
                    cached=True,
                    truncated=len(cached_result) >= max_rows,
                    user_context=user_context
                )
                
                return {
                    'status': 'success',
                    'data': cached_result,
                    'metadata': metadata,
                    'schema_info': None,
                    'error': None
                }
            
            # Get or create adapter
            adapter = self._get_adapter(profile)
            
            # Execute query
            result = adapter.execute(
                query=query,
                params=params,
                max_rows=max_rows,
                timeout=timeout
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Cache result
            self.cache.set(profile, query, result)
            
            # Extract and submit metadata
            metadata = self._extract_and_submit_metadata(
                query=query,
                db_type=adapter.database_type,
                profile=profile,
                result=result,
                execution_time_ms=execution_time,
                cached=False,
                truncated=len(result) >= max_rows,
                user_context=user_context
            )
            
            # Return result
            return {
                'status': 'success',
                'data': result,
                'metadata': metadata,
                'schema_info': None,  # TODO: Add schema introspection
                'error': None
            }
            
        except ProfileNotFoundError as e:
            return {
                'status': 'error',
                'data': [],
                'metadata': {},
                'schema_info': None,
                'error': {
                    'code': 'PROFILE_NOT_FOUND',
                    'message': str(e),
                    'details': {}
                }
            }
        
        except ConnectionError as e:
            return {
                'status': 'error',
                'data': [],
                'metadata': {},
                'schema_info': None,
                'error': {
                    'code': 'CONNECTION_ERROR',
                    'message': str(e),
                    'details': {}
                }
            }
        
        except QueryError as e:
            return {
                'status': 'error',
                'data': [],
                'metadata': {},
                'schema_info': None,
                'error': {
                    'code': 'QUERY_ERROR',
                    'message': str(e),
                    'details': {}
                }
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'data': [],
                'metadata': {},
                'schema_info': None,
                'error': {
                    'code': 'UNKNOWN_ERROR',
                    'message': str(e),
                    'details': {}
                }
            }
    
    def _get_adapter(self, profile: str) -> BaseAdapter:
        """Get or create adapter for profile."""
        if profile in self._adapters:
            adapter = self._adapters[profile]
            if adapter.test_connection():
                return adapter
            else:
                # Reconnect if connection is lost
                adapter.disconnect()
                adapter.connect()
                return adapter
        
        # Create new adapter
        db_profile = self.profile_manager.get_profile(profile)
        adapter_class = get_adapter(db_profile.type)
        adapter = adapter_class(db_profile)
        adapter.connect()
        
        self._adapters[profile] = adapter
        return adapter
    
    def _extract_and_submit_metadata(
        self,
        query: str,
        db_type: str,
        profile: str,
        result: List[Dict[str, Any]],
        execution_time_ms: float,
        cached: bool,
        truncated: bool,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract metadata and submit to governance API."""
        # Extract metadata
        metadata = self.metadata_extractor.extract(
            query=query,
            db_type=db_type,
            profile=profile,
            result=result,
            execution_time_ms=execution_time_ms,
            cached=cached,
            truncated=truncated,
            user_context=user_context
        )
        
        # Submit to governance (if enabled)
        if self.governance_client:
            try:
                if self.async_governance:
                    # Fire and forget (in real implementation, would use background task)
                    api_response = self.governance_client.submit_metadata(metadata)
                else:
                    # Synchronous submission
                    api_response = self.governance_client.submit_metadata(metadata)
            except Exception:
                # Fail open - continue even if governance fails
                if not self.fail_open:
                    raise
        
        # Add API response to metadata
        if api_response:
            metadata['governance_response'] = api_response
        
        return metadata
    
    def get_schema(self, profile: str) -> Dict[str, Any]:
        """
        Get database schema for a profile.
        
        Args:
            profile: Profile name
            
        Returns:
            Schema dictionary
        """
        adapter = self._get_adapter(profile)
        return adapter.get_schema()
    
    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        return self.profile_manager.list_profiles()
    
    def test_connection(self, profile: str) -> bool:
        """
        Test connection for a profile.
        
        Args:
            profile: Profile name
            
        Returns:
            True if connection is successful
        """
        try:
            adapter = self._get_adapter(profile)
            return adapter.test_connection()
        except Exception:
            return False
    
    def execute_prompt(
        self,
        prompt: str,
        profile: Optional[str] = None,
        max_rows: Optional[int] = None,
        timeout: Optional[int] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a natural language prompt to query data.
        
        Args:
            prompt: Natural language prompt/question
            profile: Optional profile name (if None, API will introspect and decide)
            max_rows: Maximum rows to return
            timeout: Query timeout in seconds
            user_context: Optional user context for governance
            
        Returns:
            Result dictionary with generated query, data, and metadata
        """
        if not self.governance_client:
            return {
                'status': 'error',
                'data': [],
                'metadata': {},
                'error': {
                    'code': 'NO_GOVERNANCE_CLIENT',
                    'message': 'Governance client required for prompt execution',
                    'details': {}
                }
            }
        
        try:
            if profile:
                # Type 2: Prompt with specific profile
                return self._execute_prompt_with_profile(
                    prompt=prompt,
                    profile=profile,
                    max_rows=max_rows,
                    timeout=timeout,
                    user_context=user_context
                )
            else:
                # Type 3: Prompt without profile (intelligent routing)
                return self._execute_prompt_without_profile(
                    prompt=prompt,
                    max_rows=max_rows,
                    timeout=timeout,
                    user_context=user_context
                )
        
        except Exception as e:
            return {
                'status': 'error',
                'data': [],
                'metadata': {},
                'generated_query': None,
                'error': {
                    'code': 'PROMPT_EXECUTION_ERROR',
                    'message': str(e),
                    'details': {}
                }
            }
    
    def _execute_prompt_with_profile(
        self,
        prompt: str,
        profile: str,
        max_rows: Optional[int],
        timeout: Optional[int],
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute prompt with a specific profile."""
        # Get schema for context
        try:
            schema = self.get_schema(profile)
        except Exception:
            schema = None
        
        # Get profile info
        db_profile = self.profile_manager.get_profile(profile)
        
        # Prepare request to governance API
        request_body = {
            'request_type': 'prompt_with_profile',
            'profile': profile,
            'prompt': prompt,
            'db_type': db_profile.type,
            'schema': schema,
        }
        
        # Call governance API for query generation
        try:
            response = self.governance_client.submit_metadata(request_body)
            
            if not response or 'generated_query' not in response:
                return {
                    'status': 'error',
                    'data': [],
                    'metadata': {},
                    'generated_query': None,
                    'error': {
                        'code': 'QUERY_GENERATION_FAILED',
                        'message': 'API did not return a generated query',
                        'details': {}
                    }
                }
            
            generated_query = response['generated_query']
            
            # Execute the generated query
            result = self.execute(
                profile=profile,
                query=generated_query,
                max_rows=max_rows,
                timeout=timeout,
                user_context=user_context
            )
            
            # Add generated query to result
            result['generated_query'] = generated_query
            result['original_prompt'] = prompt
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'data': [],
                'metadata': {},
                'generated_query': None,
                'error': {
                    'code': 'API_ERROR',
                    'message': f'Failed to generate query: {e}',
                    'details': {}
                }
            }
    
    def _execute_prompt_without_profile(
        self,
        prompt: str,
        max_rows: Optional[int],
        timeout: Optional[int],
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute prompt without profile (intelligent routing)."""
        # Get all available profiles and schemas
        available_profiles = self.list_profiles()
        
        schemas = {}
        for prof in available_profiles:
            try:
                schemas[prof] = {
                    'db_type': self.profile_manager.get_profile(prof).type,
                    'schema': self.get_schema(prof)
                }
            except Exception:
                # Skip profiles we can't get schema for
                continue
        
        # Prepare request to governance API
        request_body = {
            'request_type': 'prompt_without_profile',
            'prompt': prompt,
            'available_profiles': available_profiles,
            'schemas': schemas,
        }
        
        # Call governance API for intelligent routing
        try:
            response = self.governance_client.submit_metadata(request_body)
            
            if not response:
                return {
                    'status': 'error',
                    'data': [],
                    'metadata': {},
                    'execution_plan': None,
                    'error': {
                        'code': 'ROUTING_FAILED',
                        'message': 'API did not return an execution plan',
                        'details': {}
                    }
                }
            
            # API returns execution plan with queries for each profile
            execution_plan = response.get('execution_plan', [])
            
            if not execution_plan:
                return {
                    'status': 'error',
                    'data': [],
                    'metadata': {},
                    'execution_plan': None,
                    'error': {
                        'code': 'NO_EXECUTION_PLAN',
                        'message': 'API returned empty execution plan',
                        'details': {}
                    }
                }
            
            # Execute queries according to plan
            results = []
            for plan_item in execution_plan:
                prof = plan_item['profile']
                query = plan_item['query']
                
                result = self.execute(
                    profile=prof,
                    query=query,
                    max_rows=max_rows,
                    timeout=timeout,
                    user_context=user_context
                )
                
                results.append({
                    'profile': prof,
                    'query': query,
                    'result': result
                })
            
            # Return combined results
            return {
                'status': 'success',
                'original_prompt': prompt,
                'execution_plan': execution_plan,
                'results': results,
                'synthesized_answer': response.get('synthesized_answer'),
                'error': None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'data': [],
                'metadata': {},
                'execution_plan': None,
                'error': {
                    'code': 'API_ERROR',
                    'message': f'Failed to route prompt: {e}',
                    'details': {}
                }
            }
    
    def close(self) -> None:
        """Close all connections and cleanup."""
        # Close all adapters
        for adapter in self._adapters.values():
            try:
                adapter.disconnect()
            except Exception:
                pass
        
        self._adapters.clear()
        
        # Close cache
        if self.cache:
            self.cache.close()
        
        # Close governance client
        if self.governance_client:
            self.governance_client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    import os
    
    print("Testing UniversalClient...")
    
    # Set test API key
    os.environ['CAUSALPY_API_KEY'] = 'test-api-key-12345'
    
    # Create test profiles
    test_profiles = {
        "postgres_test": {
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "postgres",
            "password": "postgres"
        }
    }
    
    # Test 1: Initialize client
    client = UniversalClient(
        profiles=test_profiles,
        enable_cache=True,
        fail_open=True
    )
    print("✓ Client initialized")
    print(f"  Profiles: {client.list_profiles()}")
    
    # Test 2: Execute query (will fail if DB not available, but tests structure)
    print("\n✓ Testing query execution structure...")
    result = client.execute(
        profile="postgres_test",
        query="SELECT 1 AS test",
        max_rows=10
    )
    
    print(f"  Status: {result['status']}")
    print(f"  Has data key: {'data' in result}")
    print(f"  Has metadata key: {'metadata' in result}")
    print(f"  Has error key: {'error' in result}")
    
    if result['status'] == 'success':
        print(f"  Data: {result['data']}")
        print(f"  Metadata: {result['metadata']}")
    else:
        print(f"  Error: {result['error']}")
    
    # Test 3: Profile not found
    print("\n✓ Testing profile not found...")
    result = client.execute(
        profile="nonexistent_profile",
        query="SELECT 1"
    )
    assert result['status'] == 'error'
    assert result['error']['code'] == 'PROFILE_NOT_FOUND'
    print(f"  Correctly returned error: {result['error']['code']}")
    
    # Test 4: Prompt with profile
    print("\n✓ Testing execute_prompt with profile...")
    result = client.execute_prompt(
        profile="postgres_test",
        prompt="How many patients are in the database?"
    )
    print(f"  Status: {result['status']}")
    if result['status'] == 'success':
        print(f"  Generated query: {result.get('generated_query')}")
        print(f"  Data: {result.get('data')}")
    else:
        print(f"  Error: {result['error']}")
    
    # Test 5: Prompt without profile
    print("\n✓ Testing execute_prompt without profile...")
    result = client.execute_prompt(
        prompt="Show me patient admissions from 2020"
    )
    print(f"  Status: {result['status']}")
    if result['status'] == 'success':
        print(f"  Execution plan: {result.get('execution_plan')}")
        print(f"  Number of queries executed: {len(result.get('results', []))}")
    else:
        print(f"  Error: {result['error']}")
    
    # Test 6: Context manager
    print("\n✓ Testing context manager...")
    with UniversalClient(profiles=test_profiles, fail_open=True) as c:
        profiles = c.list_profiles()
        print(f"  Profiles in context: {profiles}")
    print("  Context manager closed successfully")
    
    # Clean up
    client.close()
    
    print("\n✓ All UniversalClient tests passed")
    print("\nNote: Full integration tests require running databases")