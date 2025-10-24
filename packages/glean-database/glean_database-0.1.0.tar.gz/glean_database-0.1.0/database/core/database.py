from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .cache import Cache

class Database(ABC):
    """Abstract base class for database implementations."""
    
    def __init__(self, cache: Optional[Cache] = None):
        """Initialize database with optional cache."""
        self._cache = cache
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the database."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to the database."""
        pass

    @abstractmethod
    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query: The query string to execute
            params: Optional parameters for the query
            
        Returns:
            List of dictionaries containing the query results
        """
        pass

    @abstractmethod
    async def execute(self, statement: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute a statement that modifies the database.
        
        Args:
            statement: The SQL statement to execute
            params: Optional parameters for the statement
            
        Returns:
            Number of rows affected
        """
        pass

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected