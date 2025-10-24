"""
Causum™ API - Universal Database Client for RAG Systems

A unified database client with built-in governance and metadata capture.
"""

__version__ = "0.1.0"

import dotenv
dotenv.load_dotenv()

from .client import UniversalClient
from .config import ProfileManager, DatabaseProfile, GlobalConfig
from .exceptions import (
    CausumAPIError,
    ConfigurationError,
    ConnectionError,
    QueryError,
    ParserError,
    AdapterError,
    GovernanceError,
    AuthenticationError,
    ProfileNotFoundError,
    UnsupportedDatabaseError,
)

__all__ = [
    # Main client
    'UniversalClient',
    
    # Configuration
    'ProfileManager',
    'DatabaseProfile',
    'GlobalConfig',
    
    # Exceptions
    'CausumAPIError',
    'ConfigurationError',
    'ConnectionError',
    'QueryError',
    'ParserError',
    'AdapterError',
    'GovernanceError',
    'AuthenticationError',
    'ProfileNotFoundError',
    'UnsupportedDatabaseError',
    
    # Version
    '__version__',
]