from typing import Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

COL_A = "col_a"
COL_B = "col_b"


DATA = pd.DataFrame(
    {
        COL_A: ["aa", "ab", "ac", None],
        COL_B: ["aa", "bb", "cc", None],
    }
)

SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


class TestNormalSql:
    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="z%"),
                id="no_matches",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="_______"),
                id="too_many_underscores",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(
                    column=COL_B, like_pattern="a%", mostly=0.6
                ),
                id="mostly",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
    def test_success(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePattern,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="a%"),
                id="all_matches",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="__"),
                id="underscores_match",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(
                    column=COL_B, like_pattern="a%", mostly=0.7
                ),
                id="mostly_threshold_not_met",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
    def test_failure(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePattern,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert not result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[PostgreSQLDatasourceTestConfig()], data=DATA
    )
    def test_include_unexpected_rows_postgres(self, batch_for_datasource: Batch) -> None:
        """Test include_unexpected_rows for ExpectColumnValuesToNotMatchLikePattern."""
        expectation = gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="a%")
        result = batch_for_datasource.validate(
            expectation, result_format={"result_format": "BASIC", "include_unexpected_rows": True}
        )

        assert not result.success
        result_dict = result["result"]

        # Verify that unexpected_rows is present and contains the expected data
        assert "unexpected_rows" in result_dict
        assert result_dict["unexpected_rows"] is not None

        unexpected_rows_data = result_dict["unexpected_rows"]
        assert isinstance(unexpected_rows_data, list)

        # Should contain 3 rows where COL_A matches like_pattern "a%" ("aa", "ab", "ac" all match)
        assert len(unexpected_rows_data) == 3

        # Check that "aa", "ab", and "ac" appear in the unexpected rows data
        unexpected_rows_str = str(unexpected_rows_data)
        assert "aa" in unexpected_rows_str
        assert "ab" in unexpected_rows_str
        assert "ac" in unexpected_rows_str


class TestMSSQL:
    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="a[xzy]"),
                id="bracket_notation",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(
        data_source_configs=[MSSQLDatasourceTestConfig()], data=DATA
    )
    def test_success(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePattern,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="a[abc]"),
                id="bracket_notation_fail",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(
        data_source_configs=[MSSQLDatasourceTestConfig()], data=DATA
    )
    def test_failure(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePattern,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert not result.success
