"""Custom exceptions for causum."""


class CausumAPIError(Exception):
    """Base exception for all causum errors."""
    pass


class ConfigurationError(CausumAPIError):
    """Raised when configuration is invalid or missing."""
    pass


class ConnectionError(CausumAPIError):
    """Raised when database connection fails."""
    pass


class QueryError(CausumAPIError):
    """Raised when query execution fails."""
    pass


class ParserError(CausumAPIError):
    """Raised when query parsing fails."""
    pass


class AdapterError(CausumAPIError):
    """Raised when adapter encounters an error."""
    pass


class GovernanceError(CausumAPIError):
    """Raised when governance API call fails."""
    pass


class AuthenticationError(CausumAPIError):
    """Raised when authentication fails."""
    pass


class ProfileNotFoundError(ConfigurationError):
    """Raised when requested profile doesn't exist."""
    pass


class UnsupportedDatabaseError(CausumAPIError):
    """Raised when database type is not supported."""
    pass


if __name__ == "__main__":
    # Test exception hierarchy
    try:
        raise ConnectionError("Test connection error")
    except CausumAPIError as e:
        print(f"✓ Caught CausumAPIError: {e}")
    
    try:
        raise ProfileNotFoundError("Profile 'test' not found")
    except ConfigurationError as e:
        print(f"✓ Caught ConfigurationError: {e}")
    except CausumAPIError as e:
        print(f"✓ Caught CausumAPIError: {e}")
    
    print("\n✓ All exception tests passed")