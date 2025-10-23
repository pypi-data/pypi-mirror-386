"""
Hologres backend implementation for Holo Search SDK.

Provides integration with Hologres for full-text and vector search.
"""

import json
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union, cast

from psycopg import sql as psql
from typing_extensions import LiteralString, Self

from ..exceptions import SqlError
from ..types import (
    BaseQuantizationType,
    DistanceType,
    PreciseIOType,
    PreciseQuantizationType,
    VectorSearchFunction,
)
from .connection import HoloConnect
from .query import QueryBuilder


class HoloTable:
    """
    Table class for Holo Search SDK.
    """

    def __init__(self, db: HoloConnect, name: str):
        """
        Initialize the Table instance.

        Args:
            db (HoloConnect): Database connection.
            name (str): Name of the table.
        """
        self._db: HoloConnect = db
        self._name: str = name
        self._column_distance_methods: Dict[str, DistanceType] = {}

    def get_name(self) -> str:
        """
        Get the name of the table.

        Returns:
            str: Name of the table.
        """
        return self._name

    def insert_one(
        self, values: List[Any], column_names: Optional[List[str]] = None
    ) -> Self:
        """
        Insert one record into the table.

        Args:
            values (List[Any]): Values to insert.
            column_names ([List[str]]): Column names. Defaults to None.
        """
        sql = psql.SQL("INSERT INTO {} ").format(psql.Identifier(self._name))
        if column_names:
            sql += psql.SQL("({}) ").format(
                psql.SQL(", ").join(map(psql.Identifier, column_names))
            )
        sql += psql.SQL("VALUES ({});").format(
            psql.SQL(", ").join(psql.Placeholder() * len(values))
        )
        params = tuple(values)
        self._db.execute(sql, params)
        return self

    def insert_multi(
        self, values: List[List[Any]], column_names: Optional[List[str]] = None
    ) -> Self:
        """
        Insert multiple records into the table.

        Args:
            values (List[List[Any]]): Values to insert.
            column_names ([List[str]]): Column names. Defaults to None.
        """
        if not values:
            return self

        sql = psql.SQL("INSERT INTO {} ").format(psql.Identifier(self._name))
        if column_names:
            sql += psql.SQL("({}) ").format(
                psql.SQL(", ").join(map(psql.Identifier, column_names))
            )

        params: tuple[Any] = tuple()
        rows_sql: list[psql.Composed] = list()
        for row in values:
            params += tuple(row)
            rows_sql.append(
                psql.SQL("({})").format(
                    psql.SQL(", ").join(psql.Placeholder() * len(row))
                )
            )
        sql += psql.SQL("VALUES {};").format(psql.SQL(", ").join(rows_sql))

        self._db.execute(sql, params)
        return self

    def set_vector_index(
        self,
        column: str,
        distance_method: DistanceType,
        max_degree: int = 32,
        ef_construction: int = 200,
        base_quantization_type: BaseQuantizationType = "rabitq",
        use_reorder: bool = False,
        precise_quantization_type: PreciseQuantizationType = "fp32",
        precise_io_type: PreciseIOType = "block_memory_io",
    ) -> Self:
        """
        Set a vector index for a column.

        Args:
            column (str): Column name.
            distance_method (str): Distance method. Available options are "Euclidean", "InnerProduct", "Cosine".
            max_degree (int): During the graph construction process, each vertex will attempt to connect to its nearest max_degree vertices.
            ef_construction (int): Used to control the search depth during the graph construction process.
            base_quantization_type (str): Base quantization type. Available options are "sq8", "sq8_uniform", "fp16", "fp32", "rabitq".
            use_reorder (bool): Whether to use the HGraph high-precision index.
            precise_quantization_type (str): Precise quantization type. Available options are "sq8", "sq8_uniform", "fp16", "fp32".
            precise_io_type (str): Precise IO type. Available options are "block_memory_io", "reader_io".
        """
        builder_params = psql.SQL(
            '{{"max_degree": {}, "ef_construction": {}, "base_quantization_type": {}, "use_reorder": {}, "precise_quantization_type": {}, "precise_io_type": {}}}'
        ).format(
            psql.Literal(max_degree),
            psql.Literal(ef_construction),
            psql.Identifier(base_quantization_type),
            psql.Literal(use_reorder),
            psql.Identifier(precise_quantization_type),
            psql.Identifier(precise_io_type),
        )
        sql = psql.SQL(
            "CALL set_table_property({}, 'vectors', '{{{}: {{"
            + '"algorithm": "HGraph", "distance_method": {}, "builder_params": {}'
            + "}}}}');"
        ).format(
            psql.Literal(self._name),
            psql.Identifier(column),
            psql.Identifier(distance_method),
            builder_params,
        )
        self._db.execute(sql)
        self._column_distance_methods[column] = distance_method
        return self

    def set_vector_indexes(
        self, column_configs: Mapping[str, Mapping[str, Union[str, int, bool]]]
    ) -> Self:
        """
        Set multiple vector indexes with different configurations.

        Args:
            column_configs (Dict[str, Dict]): Dictionary mapping column names to their index configurations.
                                              Each config should contain 'distance_method' and optionally 'base_quantization_type'.

        Example:
            table.set_vector_indexes({
                "column_name": {
                    "distance_method": "Euclidean",
                    "max_degree": 32,
                    "ef_construction": 200,
                    "base_quantization_type": "rabitq",
                    "use_reorder": False,
                    "precise_quantization_type": "fp32",
                    "precise_io_type": "block_memory_io"
                }
            })
        """
        vectors_config = None

        for column, config in column_configs.items():
            builder_params = psql.SQL(
                '{{"max_degree": {}, "ef_construction": {}, "base_quantization_type": {}, "use_reorder": {}, "precise_quantization_type": {}, "precise_io_type": {}}}'
            ).format(
                psql.Literal(config.get("max_degree", 32)),
                psql.Literal(config.get("ef_construction", 200)),
                psql.Identifier(str(config.get("base_quantization_type", "rabitq"))),
                psql.Literal(config.get("use_reorder", False)),
                psql.Identifier(str(config.get("precise_quantization_type", "fp32"))),
                psql.Identifier(str(config.get("precise_io_type", "block_memory_io"))),
            )
            single_config = psql.SQL(
                '{}: {{"algorithm": "HGraph", "distance_method": {}, "builder_params": {}}}'
            ).format(
                psql.Identifier(column),
                psql.Identifier(str(config["distance_method"])),
                builder_params,
            )
            if vectors_config is None:
                vectors_config = single_config
            else:
                vectors_config += psql.SQL(", ") + single_config

        sql = psql.SQL(
            """
            CALL set_table_property(
                {},
                'vectors',
                '{{{}}}');
            """
        ).format(psql.Literal(self._name), vectors_config)
        self._db.execute(sql)
        for column, config in column_configs.items():
            self._column_distance_methods[column] = cast(
                DistanceType, config["distance_method"]
            )
        return self

    def delete_vector_indexes(self) -> Self:
        """
        Delete all vector indexes.
        """
        sql = psql.SQL(
            """
        CALL set_table_property(
            {},
            'vectors',
            '{{}}');
        """
        ).format(psql.Literal(self._name))
        self._db.execute(sql)
        self._column_distance_methods.clear()
        return self

    def _get_column_distance_method(self, column: str) -> Optional[DistanceType]:
        sql = psql.SQL(
            "SELECT property_value FROM hologres.hg_table_properties WHERE table_namespace = {} and table_name = {} and property_key = 'vectors';"
        ).format(psql.Literal(self._db.get_config().schema), psql.Literal(self._name))
        res = self._db.fetchone(sql)
        if res is None:
            return None
        else:
            try:
                distance_method = cast(
                    DistanceType, json.loads(res[0])[column]["distance_method"]
                )
                self._column_distance_methods[column] = distance_method
                return distance_method
            except:
                return None

    def search_vector(
        self,
        vector: Sequence[Union[str, float]],
        column: str,
        output_name: Optional[LiteralString] = None,
        distance_method: Optional[DistanceType] = None,
    ) -> QueryBuilder:
        """
        Search for vectors in the table.

        Args:
            vector (Union[str, float]): Vector to search for.
            column (str): Column to search in.
            output_name (str): Name of the output column.
            distance_method (DistanceType): Distance method to use.

        Returns:
            QueryBuilder: QueryBuilder object.
        """
        if distance_method is not None:
            _distance_method = distance_method
        elif column in self._column_distance_methods:
            _distance_method = self._column_distance_methods[column]
        else:
            _distance_method = self._get_column_distance_method(column)
        if _distance_method is None:
            raise SqlError(f"Distance method must be set for column {column}")
        search_func = VectorSearchFunction[_distance_method]
        vector_array = "{" + ",".join(map(str, vector)) + "}"
        sql = psql.SQL("{}({}, {})").format(
            psql.SQL(search_func), psql.Identifier(column), psql.Literal(vector_array)
        )
        if output_name:
            return QueryBuilder(self._db, self._name).select((sql, output_name))
        else:
            return QueryBuilder(self._db, self._name).select(sql)
