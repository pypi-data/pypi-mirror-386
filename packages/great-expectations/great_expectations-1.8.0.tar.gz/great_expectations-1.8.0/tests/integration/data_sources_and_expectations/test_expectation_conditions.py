from datetime import datetime, timezone

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.compatibility.bigquery import BIGQUERY_TYPES
from great_expectations.compatibility.postgresql import POSTGRESQL_TYPES
from great_expectations.compatibility.snowflake import SNOWFLAKE_TYPES
from great_expectations.compatibility.sqlalchemy import sqltypes
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.expectations.conditions import Column
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    spark_filesystem_csv_datasource_test_config = SparkFilesystemCsvDatasourceTestConfig(
        column_types={
            "created_at": PYSPARK_TYPES.TimestampType,
            "updated_at": PYSPARK_TYPES.DateType,
            "amount": PYSPARK_TYPES.FloatType,
            "quantity": PYSPARK_TYPES.IntegerType,
            "name": PYSPARK_TYPES.StringType,
        },
    )
except ModuleNotFoundError:
    spark_filesystem_csv_datasource_test_config = SparkFilesystemCsvDatasourceTestConfig()

DATA = pd.DataFrame(
    {
        "created_at": [
            datetime(year=2021, month=1, day=30, tzinfo=timezone.utc),
            datetime(year=2022, month=1, day=30, tzinfo=timezone.utc),
            datetime(year=2023, month=1, day=30, tzinfo=timezone.utc),
        ],
        "updated_at": [
            datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
        ],
        "amount": [1.00, 2.00, 3.00],
        "quantity": [1, 2, 3],
        "name": ["albert", "issac", "galileo"],
    }
)


# some backends fail to load datetimes into the database unless they are strings
DATA_WITH_STRING_DATETIMES = pd.DataFrame(
    {
        "created_at": [
            str(datetime(year=2021, month=1, day=30, tzinfo=timezone.utc)),
            str(datetime(year=2022, month=1, day=30, tzinfo=timezone.utc)),
            str(datetime(year=2023, month=1, day=30, tzinfo=timezone.utc)),
        ],
        "updated_at": [
            datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
        ],
        "amount": [1.00, 2.00, 3.00],
        "quantity": [1, 2, 3],
        "name": ["albert", "issac", "galileo"],
    }
)


PANDAS_TEST_CASES = [
    pytest.param(
        'name=="albert"',
        id="text-eq",
    ),
    pytest.param(
        "quantity<3",
        id="number-lt",
    ),
    pytest.param(
        "quantity==1",
        id="number-eq",
    ),
    pytest.param(
        "updated_at<datetime.date(2021,2,1)",
        id="datetime.date-lt",
    ),
    pytest.param(
        "updated_at>datetime.date(2021,1,30)",
        id="datetime.date-gt",
    ),
    pytest.param(
        "updated_at==datetime.date(2021,1,31)",
        id="datetime.date-eq",
    ),
    pytest.param(
        "created_at<datetime.datetime(2021,1,31,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-lt",
    ),
    pytest.param(
        "created_at>datetime.datetime(2021,1,29,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-gt",
    ),
    pytest.param(
        "created_at==datetime.datetime(2021,1,30,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-eq",
    ),
    pytest.param(
        Column(name="name") == "albert",
        id="condition-text-eq",
    ),
    pytest.param(
        Column(name="quantity") < 3,
        id="condition-number-lt",
    ),
    pytest.param(
        Column(name="quantity") > 0,
        id="condition-number-gt",
    ),
    pytest.param(
        Column(name="quantity").is_in([1, 2]),
        id="condition-in",
    ),
    pytest.param(
        Column(name="name").is_not_null(),
        id="condition-not-null",
    ),
    pytest.param(
        (Column(name="quantity") > 0) & (Column(name="quantity") < 3),
        id="condition-and",
    ),
    pytest.param(
        (Column(name="name") == "albert") | (Column(name="name") == "issac"),
        id="condition-or",
    ),
]


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(),
        PandasFilesystemCsvDatasourceTestConfig(
            read_options={
                "parse_dates": ["created_at", "updated_at"],
                "date_format": "mixed",
            },
        ),
    ],
    data=DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    PANDAS_TEST_CASES,
)
def test_expect_column_min_to_be_between__pandas_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="pandas",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


SQL_TEST_CASES = [
    pytest.param(
        'col("name")=="albert"',
        id="text-eq",
    ),
    pytest.param(
        'col("quantity")<3',
        id="number-lt",
    ),
    pytest.param(
        'col("quantity")==1',
        id="number-eq",
    ),
    pytest.param(
        'col("updated_at")<date("2021-02-01"))',
        id="date-lt",
    ),
    pytest.param(
        'col("updated_at")>date("2021-01-30"))',
        id="date-gt",
    ),
    pytest.param(
        'col("updated_at")==date("2021-01-31"))',
        id="date-eq",
    ),
    pytest.param(
        'col("created_at")<date("2021-01-31 00:00:00"))',
        id="datetime-lt",
    ),
    pytest.param(
        'col("created_at")>date("2021-01-29 00:00:00"))',
        id="datetime-gt",
    ),
    pytest.param(
        Column(name="name") == "albert",
        id="condition-text-eq",
    ),
    pytest.param(
        Column(name="quantity") < 3,
        id="condition-number-lt",
    ),
    pytest.param(
        Column(name="quantity") > 0,
        id="condition-number-gt",
    ),
    pytest.param(
        Column(name="quantity").is_in([1, 2]),
        id="condition-in",
    ),
    pytest.param(
        Column(name="name").is_not_null(),
        id="condition-not-null",
    ),
    pytest.param(
        (Column(name="quantity") > 0) & (Column(name="quantity") < 3),
        id="condition-and",
    ),
    pytest.param(
        (Column(name="quantity") == 1) | (Column(name="quantity") == 2),
        id="condition-or",
    ),
]

SPARK_TEST_CASES = SQL_TEST_CASES


@parameterize_batch_for_data_sources(
    data_source_configs=[
        BigQueryDatasourceTestConfig(
            column_types={
                "created_at": BIGQUERY_TYPES.DATETIME,
                "updated_at": BIGQUERY_TYPES.DATE,
            }
        ),
        MSSQLDatasourceTestConfig(),
        MySQLDatasourceTestConfig(
            column_types={
                "created_at": sqltypes.TIMESTAMP(timezone=True),
                "updated_at": sqltypes.DATE,
            }
        ),
        PostgreSQLDatasourceTestConfig(
            column_types={
                "created_at": POSTGRESQL_TYPES.TIMESTAMP,
                "updated_at": POSTGRESQL_TYPES.DATE,
            }
        ),
        SqliteDatasourceTestConfig(),
    ],
    data=DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    SQL_TEST_CASES,
)
def test_expect_column_min_to_be_between__sql_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="great_expectations",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        DatabricksDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(
            column_types={
                "created_at": SNOWFLAKE_TYPES.TIMESTAMP_TZ,
                "updated_at": sqltypes.DATE,  # snowflake.sqlalchemy missing snowflake DATE type
            }
        ),
    ],
    data=DATA_WITH_STRING_DATETIMES,
)
@pytest.mark.parametrize(
    "row_condition",
    SQL_TEST_CASES,
)
def test_expect_column_min_to_be_between__snowflake_databricks_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="great_expectations",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[spark_filesystem_csv_datasource_test_config],
    data=DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    SPARK_TEST_CASES,
)
def test_expect_column_min_to_be_between__spark_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="great_expectations",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


class TestPandasConditionClassAcrossExpectationTypes:
    """Simple tests to ensure that pandas properly utilizes row condition from each
    type of expectation (ColumnMapExpectation, ColumnPairMapExpectation, etc)
    """

    @parameterize_batch_for_data_sources(
        data_source_configs=[PandasDataFrameDatasourceTestConfig()],
        data=DATA,
    )
    def test_column_aggregate_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnAggregateExpectation with Condition row_condition."""
        row_condition = (Column(name="quantity") > 0) & (Column(name="quantity") < 3)
        expectation = gxe.ExpectColumnMinToBeBetween(
            column="amount",
            min_value=0.5,
            max_value=1.5,
            row_condition=row_condition,
            condition_parser="pandas",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[PandasDataFrameDatasourceTestConfig()],
        data=DATA,
    )
    def test_column_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnMapExpectation with Condition row_condition."""
        row_condition = Column(name="name") == "albert"
        expectation = gxe.ExpectColumnValuesToBeBetween(
            column="quantity",
            min_value=0.5,
            max_value=1.5,
            row_condition=row_condition,
            condition_parser="pandas",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[PandasDataFrameDatasourceTestConfig()],
        data=DATA,
    )
    def test_column_pair_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnPairMapExpectation with Condition row_condition."""
        row_condition = Column(name="quantity") < 3
        expectation = gxe.ExpectColumnPairValuesToBeEqual(
            column_A="quantity",
            column_B="quantity",
            row_condition=row_condition,
            condition_parser="pandas",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[PandasDataFrameDatasourceTestConfig()],
        data=DATA,
    )
    def test_multicolumn_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test MulticolumnMapExpectation with Condition row_condition."""
        row_condition = Column(name="quantity") > 0
        expectation = gxe.ExpectCompoundColumnsToBeUnique(
            column_list=["name", "quantity"],
            row_condition=row_condition,
            condition_parser="pandas",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[PandasDataFrameDatasourceTestConfig()],
        data=DATA,
    )
    def test_batch_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test BatchExpectation  with Condition row_condition."""
        row_condition = Column(name="name") == "albert"
        expectation = gxe.ExpectTableRowCountToBeBetween(
            min_value=1,
            max_value=1,
            row_condition=row_condition,
            condition_parser="pandas",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success


class TestSparkConditionClassAcrossExpectationTypes:
    """Simple tests to ensure that Spark properly utilizes row condition from each
    type of expectation (ColumnMapExpectation, ColumnPairMapExpectation, etc)
    """

    @parameterize_batch_for_data_sources(
        data_source_configs=[spark_filesystem_csv_datasource_test_config],
        data=DATA,
    )
    def test_column_aggregate_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnAggregateExpectation with Condition row_condition."""
        row_condition = (Column(name="quantity") > 0) & (Column(name="quantity") < 3)
        expectation = gxe.ExpectColumnMinToBeBetween(
            column="amount",
            min_value=0.5,
            max_value=1.5,
            row_condition=row_condition,
            condition_parser="spark",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[spark_filesystem_csv_datasource_test_config],
        data=DATA,
    )
    def test_column_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnMapExpectation with Condition row_condition."""
        row_condition = Column(name="name") == "albert"
        expectation = gxe.ExpectColumnValuesToBeBetween(
            column="quantity",
            min_value=0.5,
            max_value=1.5,
            row_condition=row_condition,
            condition_parser="spark",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[spark_filesystem_csv_datasource_test_config],
        data=DATA,
    )
    def test_column_pair_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnPairMapExpectation with Condition row_condition."""
        row_condition = Column(name="quantity") < 3
        expectation = gxe.ExpectColumnPairValuesToBeEqual(
            column_A="quantity",
            column_B="quantity",
            row_condition=row_condition,
            condition_parser="spark",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[spark_filesystem_csv_datasource_test_config],
        data=DATA,
    )
    def test_multicolumn_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test MulticolumnMapExpectation with Condition row_condition."""
        row_condition = Column(name="quantity") < 3
        expectation = gxe.ExpectCompoundColumnsToBeUnique(
            column_list=["quantity", "name"],
            row_condition=row_condition,
            condition_parser="spark",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[spark_filesystem_csv_datasource_test_config],
        data=DATA,
    )
    def test_batch_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test BatchExpectation  with Condition row_condition."""
        row_condition = Column(name="name") == "albert"
        expectation = gxe.ExpectTableRowCountToBeBetween(
            min_value=1,
            max_value=1,
            row_condition=row_condition,
            condition_parser="spark",
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success


class TestSQLConditionClassAcrossExpectationTypes:
    """Simple tests to ensure that SQL properly utilizes row condition from each
    type of expectation (ColumnMapExpectation, ColumnPairMapExpectation, etc)
    """

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            BigQueryDatasourceTestConfig(
                column_types={
                    "created_at": BIGQUERY_TYPES.DATETIME,
                    "updated_at": BIGQUERY_TYPES.DATE,
                }
            ),
            MSSQLDatasourceTestConfig(),
            MySQLDatasourceTestConfig(
                column_types={
                    "created_at": sqltypes.TIMESTAMP(timezone=True),
                    "updated_at": sqltypes.DATE,
                }
            ),
            PostgreSQLDatasourceTestConfig(
                column_types={
                    "created_at": POSTGRESQL_TYPES.TIMESTAMP,
                    "updated_at": POSTGRESQL_TYPES.DATE,
                }
            ),
            SqliteDatasourceTestConfig(),
        ],
        data=DATA,
    )
    def test_column_aggregate_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnAggregateExpectation with Condition row_condition."""
        row_condition = (Column(name="quantity") > 0) & (Column(name="quantity") < 3)
        expectation = gxe.ExpectColumnMinToBeBetween(
            column="amount",
            min_value=0.5,
            max_value=1.5,
            row_condition=row_condition,
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            BigQueryDatasourceTestConfig(
                column_types={
                    "created_at": BIGQUERY_TYPES.DATETIME,
                    "updated_at": BIGQUERY_TYPES.DATE,
                }
            ),
            MSSQLDatasourceTestConfig(),
            MySQLDatasourceTestConfig(
                column_types={
                    "created_at": sqltypes.TIMESTAMP(timezone=True),
                    "updated_at": sqltypes.DATE,
                }
            ),
            PostgreSQLDatasourceTestConfig(
                column_types={
                    "created_at": POSTGRESQL_TYPES.TIMESTAMP,
                    "updated_at": POSTGRESQL_TYPES.DATE,
                }
            ),
            SqliteDatasourceTestConfig(),
        ],
        data=DATA,
    )
    def test_column_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnMapExpectation with Condition row_condition."""
        row_condition = Column(name="name") == "albert"
        expectation = gxe.ExpectColumnValuesToBeBetween(
            column="quantity",
            min_value=0.5,
            max_value=1.5,
            row_condition=row_condition,
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            BigQueryDatasourceTestConfig(
                column_types={
                    "created_at": BIGQUERY_TYPES.DATETIME,
                    "updated_at": BIGQUERY_TYPES.DATE,
                }
            ),
            MSSQLDatasourceTestConfig(),
            MySQLDatasourceTestConfig(
                column_types={
                    "created_at": sqltypes.TIMESTAMP(timezone=True),
                    "updated_at": sqltypes.DATE,
                }
            ),
            PostgreSQLDatasourceTestConfig(
                column_types={
                    "created_at": POSTGRESQL_TYPES.TIMESTAMP,
                    "updated_at": POSTGRESQL_TYPES.DATE,
                }
            ),
            SqliteDatasourceTestConfig(),
        ],
        data=DATA,
    )
    def test_column_pair_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test ColumnPairMapExpectation with Condition row_condition."""
        row_condition = Column(name="quantity") < 3
        expectation = gxe.ExpectColumnPairValuesToBeEqual(
            column_A="quantity",
            column_B="quantity",
            row_condition=row_condition,
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            BigQueryDatasourceTestConfig(
                column_types={
                    "created_at": BIGQUERY_TYPES.DATETIME,
                    "updated_at": BIGQUERY_TYPES.DATE,
                }
            ),
            MSSQLDatasourceTestConfig(),
            MySQLDatasourceTestConfig(
                column_types={
                    "created_at": sqltypes.TIMESTAMP(timezone=True),
                    "updated_at": sqltypes.DATE,
                }
            ),
            PostgreSQLDatasourceTestConfig(
                column_types={
                    "created_at": POSTGRESQL_TYPES.TIMESTAMP,
                    "updated_at": POSTGRESQL_TYPES.DATE,
                }
            ),
            SqliteDatasourceTestConfig(),
        ],
        data=DATA,
    )
    def test_multicolumn_map_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test MulticolumnMapExpectation with Condition row_condition."""
        row_condition = Column(name="quantity") < 3
        expectation = gxe.ExpectCompoundColumnsToBeUnique(
            column_list=["quantity", "name"],
            row_condition=row_condition,
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            BigQueryDatasourceTestConfig(
                column_types={
                    "created_at": BIGQUERY_TYPES.DATETIME,
                    "updated_at": BIGQUERY_TYPES.DATE,
                }
            ),
            MSSQLDatasourceTestConfig(),
            MySQLDatasourceTestConfig(
                column_types={
                    "created_at": sqltypes.TIMESTAMP(timezone=True),
                    "updated_at": sqltypes.DATE,
                }
            ),
            PostgreSQLDatasourceTestConfig(
                column_types={
                    "created_at": POSTGRESQL_TYPES.TIMESTAMP,
                    "updated_at": POSTGRESQL_TYPES.DATE,
                }
            ),
            SqliteDatasourceTestConfig(),
        ],
        data=DATA,
    )
    def test_batch_expectation_with_condition_row_condition(
        self, batch_for_datasource: Batch
    ) -> None:
        """Test BatchExpectation  with Condition row_condition."""
        row_condition = Column(name="name") == "albert"
        expectation = gxe.ExpectTableRowCountToBeBetween(
            min_value=1,
            max_value=1,
            row_condition=row_condition,
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success
