import duckdb

from arthur_common.config.config import Config
from arthur_common.models.schema_definitions import SEGMENTATION_ALLOWED_DTYPES, DType


def is_column_possible_segmentation(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    column_name: str,
    column_dtype: DType,
) -> bool:
    """Returns whether column fits segmentation criteria:
    1. Has fewer than SEGMENTATION_COL_UNIQUE_VALUE_LIMIT unique values.
    2. Has an allowed DType.

    PreReq: Table with column should already be loaded in DuckDB
    column_name already has DuckDB escape identifier for the query syntax
    """
    segmentation_col_unique_val_limit = Config.segmentation_col_unique_values_limit()
    if column_dtype not in SEGMENTATION_ALLOWED_DTYPES:
        return False

    # check column for unique value count - count distinct values in this column
    distinct_count_query = f"""
        SELECT COUNT(DISTINCT {column_name}) as distinct_count
        FROM {table}
    """
    result = conn.sql(distinct_count_query).fetchone()
    distinct_count = result[0] if result else 0

    return distinct_count < segmentation_col_unique_val_limit
