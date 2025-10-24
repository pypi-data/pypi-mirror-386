"""Configuration management for causum."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .exceptions import ConfigurationError, ProfileNotFoundError


class DatabaseProfile(BaseModel):
    """Database connection profile."""
    type: str = Field(..., description="Database type (postgres, mysql, mongodb, etc.)")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: Optional[str] = Field(default=None, description="Database username")
    password: Optional[str] = Field(default=None, description="Database password")
    ssl: bool = Field(default=False, description="Use SSL connection")
    pool_size: int = Field(default=5, description="Connection pool size")
    pool_timeout: int = Field(default=30, description="Connection pool timeout")
    auth_source: Optional[str] = Field(default=None, description="Auth source (MongoDB)")
    
    @field_validator('password', mode='before')
    @classmethod
    def resolve_env_var(cls, v: Optional[str]) -> Optional[str]:
        """Resolve environment variables in password field."""
        if v and isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            return os.getenv(env_var)
        return v


class GlobalConfig(BaseModel):
    """Global configuration settings."""
    governance_url: str = Field(
        default="http://localhost:5555/metadata",
        description="Governance API endpoint"
    )
    governance_timeout: int = Field(default=5, description="Governance API timeout (seconds)")
    governance_retry: int = Field(default=3, description="Governance API retry attempts")
    async_governance: bool = Field(default=True, description="Use async governance calls")
    fail_open: bool = Field(
        default=True,
        description="Continue on governance failures"
    )
    enable_cache: bool = Field(default=True, description="Enable query result caching")
    cache_ttl: int = Field(default=300, description="Cache TTL (seconds)")
    max_rows_default: int = Field(default=1000, description="Default max rows to return")
    log_level: str = Field(default="info", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")


class ProfileManager:
    """Manages database connection profiles."""
    
    def __init__(
        self,
        profiles: Optional[Union[Dict[str, Any], str, Path]] = None,
        global_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ProfileManager.
        
        Args:
            profiles: Dictionary of profiles, or path to profiles JSON file
            global_config: Global configuration dictionary
        """
        self._profiles: Dict[str, DatabaseProfile] = {}
        self._global_config: GlobalConfig
        
        # Load profiles
        if profiles is None:
            profiles = self._find_default_profiles()
        
        if isinstance(profiles, (str, Path)):
            self._load_from_file(Path(profiles))
        elif isinstance(profiles, dict):
            self._load_from_dict(profiles)
        else:
            raise ConfigurationError(f"Invalid profiles type: {type(profiles)}")
        
        # Load global config
        if global_config:
            self._global_config = GlobalConfig(**global_config)
        else:
            self._global_config = GlobalConfig()
    
    def _find_default_profiles(self) -> Optional[Path]:
        """Find default profiles file in standard locations."""
        search_paths = [
            Path("/etc/causum/profiles.json"),
            Path.home() / ".causum" / "profiles.json",
            Path("./profiles.json"),
            Path("./examples/profiles.json"),
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    def _load_from_file(self, path: Path) -> None:
        """Load profiles from JSON file."""
        if not path.exists():
            raise ConfigurationError(f"Profiles file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            self._load_from_dict(data)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in profiles file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading profiles file: {e}")
    
    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load profiles from dictionary."""
        # Check if using new format with 'profiles' and 'global' keys
        if "profiles" in data:
            profiles_data = data["profiles"]
            if "global" in data:
                self._global_config = GlobalConfig(**data["global"])
        else:
            # Assume entire dict is profiles
            profiles_data = data
        
        # Load each profile
        for name, config in profiles_data.items():
            try:
                self._profiles[name] = DatabaseProfile(**config)
            except Exception as e:
                raise ConfigurationError(f"Error loading profile '{name}': {e}")
    
    def get_profile(self, name: str) -> DatabaseProfile:
        """Get a profile by name."""
        if name not in self._profiles:
            raise ProfileNotFoundError(
                f"Profile '{name}' not found. Available profiles: {list(self._profiles.keys())}"
            )
        return self._profiles[name]
    
    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        return list(self._profiles.keys())
    
    @property
    def global_config(self) -> GlobalConfig:
        """Get global configuration."""
        return self._global_config
    
    def add_profile(self, name: str, profile: Union[DatabaseProfile, Dict[str, Any]]) -> None:
        """Add or update a profile."""
        if isinstance(profile, dict):
            profile = DatabaseProfile(**profile)
        self._profiles[name] = profile
    
    def remove_profile(self, name: str) -> None:
        """Remove a profile."""
        if name in self._profiles:
            del self._profiles[name]


if __name__ == "__main__":
    # Test configuration
    print("Testing ProfileManager...")
    
    # Test 1: Create from dict
    profiles_dict = {
        "postgres_test": {
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "password": "testpass"
        },
        "mongo_test": {
            "type": "mongodb",
            "host": "localhost",
            "port": 27017,
            "database": "testdb",
            "username": None,
            "password": None
        }
    }
    
    manager = ProfileManager(profiles=profiles_dict)
    print(f"✓ Created manager with {len(manager.list_profiles())} profiles")
    print(f"  Profiles: {manager.list_profiles()}")
    
    # Test 2: Get profile
    profile = manager.get_profile("postgres_test")
    print(f"✓ Retrieved profile: {profile.type} at {profile.host}:{profile.port}")
    
    # Test 3: Add profile
    manager.add_profile("mysql_test", {
        "type": "mysql",
        "host": "localhost",
        "port": 3306,
        "database": "testdb",
        "username": "root",
        "password": "secret"
    })
    print(f"✓ Added new profile. Total profiles: {len(manager.list_profiles())}")
    
    # Test 4: Global config
    print(f"✓ Global config - governance URL: {manager.global_config.governance_url}")
    print(f"  Cache enabled: {manager.global_config.enable_cache}")
    
    # Test 5: Environment variable resolution
    os.environ["TEST_DB_PASSWORD"] = "env_password"
    test_profile = DatabaseProfile(
        type="postgres",
        host="localhost",
        port=5432,
        database="test",
        password="${TEST_DB_PASSWORD}"
    )
    print(f"✓ Environment variable resolved: {test_profile.password == 'env_password'}")
    
    # Test 6: Error handling
    try:
        manager.get_profile("nonexistent")
        print("✗ Should have raised ProfileNotFoundError")
    except ProfileNotFoundError as e:
        print(f"✓ Correctly raised ProfileNotFoundError: {e}")
    
    print("\n✓ All configuration tests passed")