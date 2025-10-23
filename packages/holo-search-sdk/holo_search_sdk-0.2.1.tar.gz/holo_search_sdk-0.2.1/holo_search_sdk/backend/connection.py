"""
Hologres backend implementation for Holo Search SDK.

Provides connection backend implementations and factory functions.
"""

from importlib.metadata import version
from typing import Any, List, Optional, Tuple, Union

import psycopg
from psycopg import Connection
from psycopg.abc import Params, Query

__version__ = version("holo-search-sdk")

from ..exceptions import ConnectionError, QueryError
from ..types import ConnectionConfig


class HoloConnect:
    """
    Connection class that wraps psycopg.connect with additional functionality.
    Provides a similar interface to psycopg.connect for Hologres database operations.
    """

    def __init__(self, config: ConnectionConfig):
        """
        Initialize HoloConnect.

        Args:
            config: ConnectionConfig object with connection parameters
        """
        self._connection: Optional[Connection] = None
        self._config: ConnectionConfig = config

    def get_config(self) -> ConnectionConfig:
        """Get connection configuration."""
        return self._config

    def connect(self) -> "HoloConnect":
        """Establish connection to Hologres database."""
        try:
            self._connection = psycopg.connect(
                host=self._config.host,
                port=self._config.port,
                dbname=self._config.database,
                user=self._config.access_key_id,
                password=self._config.access_key_secret,
                options=f"-c search_path={self._config.schema}",
                application_name=f"holo_search_sdk_{__version__}",
            )
            return self
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Hologres database: {str(e)}")

    def close(self) -> None:
        """Close connection to Hologres database."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(self, query: Query, params: Union[Params, None] = None) -> None:
        """
        Execute a query without return rows.

        Args:
            query: SQL query to execute
            params: Variables to bind to the query
        """
        if not self._connection:
            raise ConnectionError("Connection not established. Call connect() first.")

        cursor = None
        try:
            cursor = self._connection.cursor()
            _ = cursor.execute(query, params)
            self._connection.commit()
        except Exception as e:
            raise QueryError(f"Error executing SQL query: {e}")
        finally:
            if cursor:
                cursor.close()

    def fetchone(
        self, query: Query, params: Union[Params, None] = None
    ) -> Optional[Tuple[Any, ...]]:
        """
        Execute a query and fetch one row.

        Args:
            query: SQL query to execute
            params: Variables to bind to the query

        Returns:
            Optional[Tuple]: Single row or None
        """
        if not self._connection:
            raise ConnectionError("Connection not established. Call connect() first.")

        cursor = None
        try:
            cursor = self._connection.cursor()
            _ = cursor.execute(query, params)
            res = cursor.fetchone()
        except Exception as e:
            raise QueryError(f"Error executing SQL query: {e}")
        finally:
            if cursor:
                cursor.close()
        return res

    def fetchall(
        self, query: Query, params: Union[Params, None] = None
    ) -> List[Tuple[Any, ...]]:
        """
        Execute a query and fetch all rows.

        Args:
            query: SQL query to execute
            params: Variables to bind to the query

        Returns:
            List[Tuple]: List of all rows
        """
        if not self._connection:
            raise ConnectionError("Connection not established. Call connect() first.")

        cursor = None
        try:
            cursor = self._connection.cursor()
            _ = cursor.execute(query, params)
            res = cursor.fetchall()
        except Exception as e:
            raise QueryError(f"Error executing SQL query: {e}")
        finally:
            if cursor:
                cursor.close()
        return res

    def fetchmany(
        self,
        query: Query,
        params: Union[Params, None] = None,
        size: int = 0,
    ) -> List[Tuple[Any, ...]]:
        """
        Execute a query and fetch multiple rows.

        Args:
            query: SQL query to execute
            params: Variables to bind to the query
            size: Number of rows to fetch

        Returns:
            List[Tuple]: List of rows
        """
        if not self._connection:
            raise ConnectionError("Connection not established. Call connect() first.")

        cursor = None
        try:
            cursor = self._connection.cursor()
            _ = cursor.execute(query, params)
            res = cursor.fetchmany(size)
        except Exception as e:
            raise QueryError(f"Error executing SQL query: {e}")
        finally:
            if cursor:
                cursor.close()
        return res

    def __enter__(self):
        """Context manager entry."""
        if not self._connection:
            _ = self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
