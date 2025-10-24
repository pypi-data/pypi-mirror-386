import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.values_match_regex_values import (
    ColumnValuesMatchRegexValues,
    ColumnValuesMatchRegexValuesResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import SQL_DATA_SOURCES, SnowflakeDatasourceTestConfig

COLUMN_NAME = "whatevs"
BIG_NUMBER = 101
MATCH_ALL_REGEX = ".+"

DATA_FRAME = pd.DataFrame({COLUMN_NAME: ["abc", "def", "ghi", "1ab2", None]})
DATA_FRAME_WITH_LOTS_OF_VALUES = pd.DataFrame({COLUMN_NAME: ["A"] * BIG_NUMBER})

SQL_DATA_SOURCES_EXCEPT_SNOWFLAKE = [
    datasource
    for datasource in SQL_DATA_SOURCES
    if not isinstance(datasource, SnowflakeDatasourceTestConfig)
]


class TestColumnValuesMatchRegexValues:
    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES_EXCEPT_SNOWFLAKE,
        data=DATA_FRAME,
    )
    def test_partial_match_characters(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexValues(column=COLUMN_NAME, regex="ab")
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexValuesResult)
        assert sorted(metric_result.value) == ["1ab2", "abc"]

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_special_characters(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexValues(column=COLUMN_NAME, regex="^(a|d).+")
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexValuesResult)
        assert sorted(metric_result.value) == ["abc", "def"]

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME_WITH_LOTS_OF_VALUES,
    )
    def test_default_limit(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexValues(column=COLUMN_NAME, regex=MATCH_ALL_REGEX)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexValuesResult)
        assert len(metric_result.value) == 20

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME_WITH_LOTS_OF_VALUES,
    )
    def test_custom_limit(self, batch_for_datasource: Batch) -> None:
        limit = 7
        metric = ColumnValuesMatchRegexValues(
            column=COLUMN_NAME, regex=MATCH_ALL_REGEX, limit=limit
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexValuesResult)
        assert len(metric_result.value) == limit
