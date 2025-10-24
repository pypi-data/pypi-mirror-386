from typing import Any, Dict, List, Optional, AsyncGenerator

try:
    import aioodbc
except ImportError:
    aioodbc = None  # type: ignore

from ..core.database import Database
from ..core.cache import Cache


class MSSQLDatabase(Database):
    """Microsoft SQL Server database implementation using aioodbc with connection pooling."""
    
    def __init__(
        self,
        database: str,
        host: str = 'localhost',
        port: int = 1433,
        username: str = 'sa',
        password: Optional[str] = None,
        cache: Optional[Cache] = None,
        driver: str = 'ODBC Driver 17 for SQL Server',
        min_pool_size: int = 1,
        max_pool_size: int = 10,
        timeout: int = 30
    ):
        if aioodbc is None:
            raise ImportError(
                "aioodbc is required for MSSQL support. "
                "Install it with: pip install glean-database[mssql]"
            )
        """Initialize MSSQL connection with pooling.
        
        Args:
            database: Database name
            host: Database host
            port: Database port
            username: Database user
            password: Database password
            cache: Optional cache backend
            driver: ODBC driver name (default: 'ODBC Driver 17 for SQL Server')
            min_pool_size: Minimum number of connections in pool (default: 1)
            max_pool_size: Maximum number of connections in pool (default: 10)
            timeout: Connection timeout in seconds (default: 30)
        """
        super().__init__(cache)
        
        # Build ODBC connection string
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
        )
        
        self._connection_string = conn_str
        self._pool_params = {
            'minsize': min_pool_size,
            'maxsize': max_pool_size,
            'timeout': timeout
        }
        self._pool: Optional[aioodbc.Pool] = None

    async def connect(self) -> bool:
        """Establish connection to the database."""
        try:
            self._pool = await aioodbc.create_pool(
                dsn=self._connection_string,
                **self._pool_params
            )
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        """Close connection to the database."""
        if self._pool:
            try:
                self._pool.close()
                await self._pool.wait_closed()
                self._connected = False
                return True
            except Exception:
                return False
        return True

    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        if not self._pool:
            raise RuntimeError("Database not connected")

        # Check cache first if available
        if self._cache:
            cache_key = f"mssql:{query}:{str(params)}"
            cached_result = await self._cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Convert named parameters to positional for MSSQL (uses ?)
        query_params = None
        if params:
            query_params = tuple(params.values())
            # Replace :param with ?
            for key in params.keys():
                query = query.replace(f":{key}", "?")

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, query_params or ())
                
                # Fetch all rows
                rows = await cursor.fetchall()
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Convert to list of dicts
                results = [dict(zip(columns, row)) for row in rows]
                
                # Cache results if cache is available
                if self._cache:
                    await self._cache.set(cache_key, results)
                    
                return results

    async def execute(self, statement: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute a statement that modifies the database."""
        if not self._pool:
            raise RuntimeError("Database not connected")

        # Convert named parameters to positional for MSSQL
        query_params = None
        if params:
            query_params = tuple(params.values())
            for key in params.keys():
                statement = statement.replace(f":{key}", "?")

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(statement, query_params or ())
                await conn.commit()
                return cursor.rowcount
    
    async def query_stream(self, query: str, params: Optional[Dict[str, Any]] = None,
                          chunk_size: int = 100) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream query results for large datasets.
        
        Yields results one at a time without loading entire dataset into memory.
        
        Args:
            query: SQL query to execute
            params: Optional query parameters
            chunk_size: Number of rows to fetch at a time (default: 100)
            
        Yields:
            Dict representing each row
        """
        if not self._pool:
            raise RuntimeError("Database not connected")

        # Convert named parameters to positional for MSSQL
        query_params = None
        if params:
            query_params = tuple(params.values())
            for key in params.keys():
                query = query.replace(f":{key}", "?")

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, query_params or ())
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                while True:
                    rows = await cursor.fetchmany(chunk_size)
                    if not rows:
                        break
                    
                    for row in rows:
                        yield dict(zip(columns, row))
