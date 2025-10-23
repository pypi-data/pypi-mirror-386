"""
Client module for Holo Search SDK.

Provides the main client interface for connecting to and managing database connections.
"""

from typing import Any, Dict, List, Mapping, Optional, Union

from psycopg.abc import Query

from .backend import HoloDB, HoloTable
from .exceptions import ConnectionError
from .types import (
    BaseQuantizationType,
    ConnectionConfig,
    DistanceType,
    PreciseIOType,
    PreciseQuantizationType,
)


class Client:
    """
    Main client class for Holo Search SDK.

    Provides methods to connect to databases, manage collections,
    and perform database-level operations.
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        access_key_id: str,
        access_key_secret: str,
        schema: str = "public",
    ):
        """
        Initialize the client with database URI and configuration.

        Args:
            host (str): Hostname of the database.
            port (int): Port of the database.
            database (str): Name of the database.
            access_key_id (str): Access key ID for database authentication.
            access_key_secret (str): Access key secret for database authentication.
            schema (str): Schema of the database.
        """
        self._config: ConnectionConfig = ConnectionConfig(
            host, port, database, access_key_id, access_key_secret, schema
        )
        self._backend: Optional[HoloDB] = None
        self._opened_tables: Dict[str, HoloTable] = {}

    def connect(self) -> "Client":
        """Establish connection to the database."""
        try:
            self._backend = HoloDB(config=self._config)
            self._backend.connect()
            return self
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {str(e)}")

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._backend:
            self._backend.disconnect()
            self._backend = None
            self._opened_tables.clear()

    def execute(self, sql: Query, fetch_result: bool = False):
        """
        Execute a SQL query.

        Args:
            sql: SQL query to execute
            fetch_result: Whether to fetch the result of the query
        """
        if not self._backend:
            raise ConnectionError("Client not connected. Call connect() first.")
        return self._backend.execute(sql, fetch_result)

    # def create_table(
    #     self,
    #     table_name: str,
    #     columns: Mapping[str, Union[str, Tuple[str, str]]],
    #     exist_ok: bool = True,
    # ) -> HoloTable:
    #     """
    #     Create a new table in Hologres database.
    #     Args:
    #         table_name (str): The name of the table to be created
    #         columns (Dict[str, Union[str, Tuple[str, str]]]): Dictionary of column definitions
    #             - Dictionary key is the column name
    #             - Dictionary value can be one of the following formats:
    #                 * str: Column type only, e.g., 'VARCHAR(255)', 'TEXT', 'INTEGER'
    #                 * Tuple[str, str]: (column_type, constraints), e.g., ('VARCHAR(255)', 'PRIMARY KEY')
    #         exist_ok: If True, do not raise an error if the table already exists.
    #     """
    #     if not self._backend:
    #         raise ConnectionError("Client not connected. Call connect() first.")
    #     table = self._backend.create_table(table_name, columns, exist_ok)
    #     self._opened_tables[table_name] = table
    #     return table

    def check_table_exist(self, table_name: str) -> bool:
        """
        Check if the table exists.

        Args:
            table_name (str): Name of the table.
        """
        if not self._backend:
            raise ConnectionError("Client not connected. Call connect() first.")
        return self._backend.check_table_exist(table_name)

    def open_table(self, table_name: str) -> HoloTable:
        """
        Open an existing table in Hologres database.

        Args:
            table_name: Table name

        Returns:
            HoloTable: Table instance
        """
        if not self._backend:
            raise ConnectionError("Client not connected. Call connect() first.")
        table = self._backend.open_table(table_name)
        self._opened_tables[table_name] = table
        return table

    def drop_table(self, table_name: str) -> None:
        """
        Drop a table if it exists.

        Args:
            table_name: Table name
        """
        if not self._backend:
            raise ConnectionError("Client not connected. Call connect() first.")
        if table_name in self._opened_tables:
            del self._opened_tables[table_name]
        self._backend.drop_table(table_name)

    def insert_one(
        self,
        table_name: str,
        values: List[Any],
        column_names: Optional[List[str]] = None,
    ) -> HoloTable:
        """
        Insert one record into the table.

        Args:
            table_name (str): Table name
            values (List[Any]): Values to insert.
            column_names ([List[str]]): Column names. Defaults to None.
        """
        table = self._find_table(table_name)
        return table.insert_one(values, column_names)

    def insert_multi(
        self,
        table_name: str,
        values: List[List[Any]],
        column_names: Optional[List[str]] = None,
    ) -> HoloTable:
        """
        Insert multiple records into the table.

        Args:
            table_name (str): Table name.
            values (List[List[Any]]): Values to insert.
            column_names ([List[str]]): Column names. Defaults to None.
        """
        table = self._find_table(table_name)
        return table.insert_multi(values, column_names)

    def set_vector_index(
        self,
        table_name: str,
        column: str,
        distance_method: DistanceType,
        max_degree: int = 32,
        ef_construction: int = 200,
        base_quantization_type: BaseQuantizationType = "rabitq",
        use_reorder: bool = False,
        precise_quantization_type: PreciseQuantizationType = "fp32",
        precise_io_type: PreciseIOType = "block_memory_io",
    ) -> HoloTable:
        """
        Set a vector index for a column.

        Args:
            table_name (str): Table name.
            column (str): Column name.
            distance_method (str): Distance method. Available options are "Euclidean", "InnerProduct", "Cosine".
            max_degree (int): During the graph construction process, each vertex will attempt to connect to its nearest max_degree vertices.
            ef_construction (int): Used to control the search depth during the graph construction process.
            base_quantization_type (str): Base quantization type. Available options are "sq8", "sq8_uniform", "fp16", "fp32", "rabitq".
            use_reorder (bool): Whether to use the HGraph high-precision index.
            precise_quantization_type (str): Precise quantization type. Available options are "sq8", "sq8_uniform", "fp16", "fp32".
            precise_io_type (str): Precise IO type. Available options are "block_memory_io", "reader_io".
        """
        table = self._find_table(table_name)
        return table.set_vector_index(
            column,
            distance_method,
            max_degree,
            ef_construction,
            base_quantization_type,
            use_reorder,
            precise_quantization_type,
            precise_io_type,
        )

    def set_vector_indexes(
        self, table_name: str, column_configs: Dict[str, Mapping[str, Union[str, int]]]
    ) -> HoloTable:
        """
        Set multiple vector indexes with different configurations.

        Args:
            table_name (str): Table name.
            column_configs (Dict[str, Dict]): Dictionary mapping column names to their index configurations.
                                              Each config should contain 'distance_method' and optionally 'base_quantization_type'.

        Example:
            table.set_vector_indexes({
                "column_name": {
                    "distance_method": "L2",
                    "max_degree": 32,
                    "ef_construction": 200,
                    "base_quantization_type": "rabitq",
                    "use_reorder": False,
                    "precise_quantization_type": "fp32",
                    "precise_io_type": "block_memory_io"
                }
            })
        """
        table = self._find_table(table_name)
        return table.set_vector_indexes(column_configs)

    def delete_vector_indexes(self, table_name: str) -> HoloTable:
        """
        Delete all vector indexes.

        Args:
            table_name (str): Table name.
        """
        table = self._find_table(table_name)
        return table.delete_vector_indexes()

    def _find_table(self, table_name: str) -> HoloTable:
        if not self._backend:
            raise ConnectionError("Client not connected. Call connect() first.")
        if table_name not in self._opened_tables:
            table = self._backend.open_table(table_name)
            self._opened_tables[table_name] = table
        else:
            table = self._opened_tables[table_name]
        return table

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def connect(
    host: str,
    port: int,
    database: str,
    access_key_id: str,
    access_key_secret: str,
    schema: str = "public",
) -> Client:
    """
    Create and return a new client instance.

    Args:
        host (str): Hostname of the database.
        port (int): Port of the database.
        database (str): Name of the database.
        access_key_id (str): Access key ID for database authentication.
        access_key_secret (str): Access key secret for database authentication.
        schema (str): Schema of the database.

    Returns:
        Client instance
    """
    return Client(
        host, port, database, access_key_id, access_key_secret, schema
    ).connect()
