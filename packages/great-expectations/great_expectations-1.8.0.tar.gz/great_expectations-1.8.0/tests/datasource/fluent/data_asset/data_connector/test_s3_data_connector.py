import logging
import os
import re
import uuid
from typing import TYPE_CHECKING, List

import pandas as pd
import pytest
from moto import mock_s3

from great_expectations.core import IDDict
from great_expectations.core.batch import LegacyBatchDefinition
from great_expectations.core.partitioners import FileNamePartitionerPath, FileNamePartitionerYearly
from great_expectations.core.util import S3Url
from great_expectations.datasource.fluent import BatchRequest
from great_expectations.datasource.fluent.data_connector import (
    S3DataConnector,
)
from great_expectations.datasource.fluent.data_connector.azure_blob_storage_data_connector import (
    sanitize_prefix,
)
from great_expectations.datasource.fluent.data_connector.file_path_data_connector import (
    MissingFilePathTemplateMapFnError,
    sanitize_prefix_for_gcs_and_s3,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.data_connector import (
        DataConnector,
    )

logger = logging.getLogger(__name__)

try:
    import boto3  # : disable=E0602
except ImportError:
    logger.debug("Unable to load boto3; install optional boto3 dependency for support.")


@pytest.fixture
def aws_region():
    """AWS region for testing."""
    return "us-east-1"


@pytest.fixture
def s3_bucket_name():
    """S3 bucket name for testing."""
    return f"test-bucket-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_df():
    """Sample pandas DataFrame for testing."""
    return pd.DataFrame(data={"col1": [1, 2], "col2": [3, 4]})


def create_s3_setup(bucket_name: str, region: str = "us-east-1"):
    """Helper function to create S3 resources within a @mock_s3 context."""
    conn = boto3.resource("s3", region_name=region)
    conn.create_bucket(Bucket=bucket_name)
    client = boto3.client("s3", region_name=region)
    return client, bucket_name


@pytest.mark.big
@mock_s3
def test_basic_instantiation(s3_bucket_name, aws_region, test_df):
    client, bucket = create_s3_setup(s3_bucket_name, aws_region)

    keys: List[str] = [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]
    for key in keys:
        client.put_object(Bucket=bucket, Body=test_df.to_csv(index=False).encode("utf-8"), Key=key)

    my_data_connector: DataConnector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]
    batching_regex = re.compile(r"alpha-(.*)\.csv")
    matching_data_references = my_data_connector.get_matched_data_references(regex=batching_regex)
    assert len(matching_data_references) == 3
    assert matching_data_references[:3] == [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]


@pytest.mark.big
@mock_s3
def test_instantiation_batching_regex_does_not_match_paths(s3_bucket_name, aws_region, test_df):
    client, bucket = create_s3_setup(s3_bucket_name, aws_region)

    keys: List[str] = [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]
    for key in keys:
        client.put_object(Bucket=bucket, Body=test_df.to_csv(index=False).encode("utf-8"), Key=key)

    my_data_connector: DataConnector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]
    batching_regex = re.compile(r"beta-(.*)\.csv")
    matching_data_references = my_data_connector.get_matched_data_references(regex=batching_regex)
    assert len(matching_data_references) == 0
    assert matching_data_references[:3] == []


@pytest.mark.big
@mock_s3
def test_return_all_batch_definitions_unsorted(s3_bucket_name, aws_region, test_df):
    client, bucket = create_s3_setup(s3_bucket_name, aws_region)

    keys: List[str] = [
        "alex_2020-08-09_1000.csv",
        "eugene_2020-08-09_1500.csv",
        "james_2020-08-11_1009.csv",
        "abe_2020-08-09_1040.csv",
        "will_2020-08-09_1002.csv",
        "james_2020-07-13_1567.csv",
        "eugene_2020-11-29_1900.csv",
        "will_2020-08-10_1001.csv",
        "james_2020-08-10_1003.csv",
        "alex_2020-08-19_1300.csv",
    ]
    for key in keys:
        client.put_object(Bucket=bucket, Body=test_df.to_csv(index=False).encode("utf-8"), Key=key)
    my_data_connector: DataConnector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    # with missing BatchRequest arguments
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        my_data_connector.get_batch_definition_list()

    batching_regex = re.compile(
        r"(?P<name>.+)_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})_(?P<price>.*)\.csv"
    )
    partitioner = FileNamePartitionerYearly(regex=batching_regex)

    # with empty options
    unsorted_batch_definition_list: List[LegacyBatchDefinition] = (
        my_data_connector.get_batch_definition_list(
            BatchRequest(
                datasource_name="my_file_path_datasource",
                data_asset_name="my_s3_data_asset",
                options={},
                partitioner=partitioner,
            )
        )
    )
    processed_batching_regex = re.compile(
        "(?P<path>(?P<name>.+)_(?P<year>\\d{4})-(?P<month>\\d{2})-(?P<day>\\d{2})_(?P<price>.*)\\.csv)"
    )
    expected: List[LegacyBatchDefinition] = [
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "abe_2020-08-09_1040.csv",
                    "name": "abe",
                    "year": "2020",
                    "month": "08",
                    "day": "09",
                    "price": "1040",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "alex_2020-08-09_1000.csv",
                    "name": "alex",
                    "year": "2020",
                    "month": "08",
                    "day": "09",
                    "price": "1000",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "alex_2020-08-19_1300.csv",
                    "name": "alex",
                    "year": "2020",
                    "month": "08",
                    "day": "19",
                    "price": "1300",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "eugene_2020-08-09_1500.csv",
                    "name": "eugene",
                    "year": "2020",
                    "month": "08",
                    "day": "09",
                    "price": "1500",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "eugene_2020-11-29_1900.csv",
                    "name": "eugene",
                    "year": "2020",
                    "month": "11",
                    "day": "29",
                    "price": "1900",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "james_2020-07-13_1567.csv",
                    "name": "james",
                    "year": "2020",
                    "month": "07",
                    "day": "13",
                    "price": "1567",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "james_2020-08-10_1003.csv",
                    "name": "james",
                    "year": "2020",
                    "month": "08",
                    "day": "10",
                    "price": "1003",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "james_2020-08-11_1009.csv",
                    "name": "james",
                    "year": "2020",
                    "month": "08",
                    "day": "11",
                    "price": "1009",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "will_2020-08-09_1002.csv",
                    "name": "will",
                    "year": "2020",
                    "month": "08",
                    "day": "09",
                    "price": "1002",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "will_2020-08-10_1001.csv",
                    "name": "will",
                    "year": "2020",
                    "month": "08",
                    "day": "10",
                    "price": "1001",
                }
            ),
            batching_regex=processed_batching_regex,
        ),
    ]
    assert expected == unsorted_batch_definition_list

    # with specified Batch query options
    unsorted_batch_definition_list = my_data_connector.get_batch_definition_list(
        BatchRequest(
            datasource_name="my_file_path_datasource",
            data_asset_name="my_s3_data_asset",
            options={"name": "alex", "year": "2020", "month": "08", "day": "19", "price": "1300"},
            partitioner=partitioner,
        )
    )
    assert expected[2:3] == unsorted_batch_definition_list


@pytest.mark.big
@mock_s3
def test_return_only_unique_batch_definitions(s3_bucket_name, aws_region, test_df):
    client, bucket = create_s3_setup(s3_bucket_name, aws_region)

    keys: List[str] = [
        "A/file_1.csv",
        "A/file_2.csv",
        "A/file_3.csv",
        "B/file_1.csv",
        "B/file_2.csv",
    ]
    for key in keys:
        client.put_object(Bucket=bucket, Body=test_df.to_csv(index=False).encode("utf-8"), Key=key)
    processed_batching_regex = re.compile("(?P<path>B/(?P<filename>.+).*\\.csv)")
    expected: List[LegacyBatchDefinition] = [
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict({"path": "B/file_1.csv", "filename": "file_1"}),
            batching_regex=processed_batching_regex,
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_s3_data_asset",
            batch_identifiers=IDDict({"path": "B/file_2.csv", "filename": "file_2"}),
            batching_regex=processed_batching_regex,
        ),
    ]

    my_data_connector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="B",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )

    batching_regex = re.compile(r"(?P<filename>.+).*\.csv")
    unsorted_batch_definition_list: List[LegacyBatchDefinition] = (
        my_data_connector.get_batch_definition_list(
            BatchRequest(
                datasource_name="my_file_path_datasource",
                data_asset_name="my_s3_data_asset",
                options={},
                partitioner=FileNamePartitionerPath(regex=batching_regex),
            )
        )
    )
    assert expected == unsorted_batch_definition_list


@pytest.mark.big
@mock_s3
def test_data_reference_count_methods(s3_bucket_name, aws_region, test_df):
    client, bucket = create_s3_setup(s3_bucket_name, aws_region)

    keys: List[str] = [
        "A/file_1.csv",
        "A/file_2.csv",
        "A/file_3.csv",
        "B/file_1.csv",
        "B/file_2.csv",
    ]
    for key in keys:
        client.put_object(Bucket=bucket, Body=test_df.to_csv(index=False).encode("utf-8"), Key=key)

    my_data_connector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="A",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "A/file_1.csv",
        "A/file_2.csv",
        "A/file_3.csv",
    ]

    batching_regex = re.compile(r"(?P<name>.+).*\.csv")
    matching_data_references = my_data_connector.get_matched_data_references(regex=batching_regex)
    assert len(matching_data_references) == 3
    assert matching_data_references[:3] == [
        "A/file_1.csv",
        "A/file_2.csv",
        "A/file_3.csv",
    ]


@pytest.mark.big
@mock_s3
def test_alpha(s3_bucket_name, aws_region, test_df):
    client, bucket = create_s3_setup(s3_bucket_name, aws_region)

    keys: List[str] = [
        "test_dir_alpha/A.csv",
        "test_dir_alpha/B.csv",
        "test_dir_alpha/C.csv",
        "test_dir_alpha/D.csv",
    ]
    for key in keys:
        client.put_object(Bucket=bucket, Body=test_df.to_csv(index=False).encode("utf-8"), Key=key)

    my_data_connector: DataConnector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="test_dir_alpha",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 4
    assert my_data_connector.get_data_references()[:3] == [
        "test_dir_alpha/A.csv",
        "test_dir_alpha/B.csv",
        "test_dir_alpha/C.csv",
    ]

    batching_regex = re.compile(r"(?P<part_1>.*)\.csv")
    matching_data_references = my_data_connector.get_matched_data_references(regex=batching_regex)
    assert len(matching_data_references) == 4
    assert matching_data_references[:3] == [
        "test_dir_alpha/A.csv",
        "test_dir_alpha/B.csv",
        "test_dir_alpha/C.csv",
    ]

    # Try to fetch a batch from a nonexistent asset
    my_batch_request = BatchRequest(
        datasource_name="BASE",
        data_asset_name="A",
        options={},
        partitioner=FileNamePartitionerPath(regex=batching_regex),
    )
    my_batch_definition_list = my_data_connector.get_batch_definition_list(
        batch_request=my_batch_request
    )
    assert len(my_batch_definition_list) == 0

    my_batch_request = BatchRequest(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        options={"part_1": "B"},
        partitioner=FileNamePartitionerPath(regex=batching_regex),
    )
    my_batch_definition_list = my_data_connector.get_batch_definition_list(
        batch_request=my_batch_request
    )
    assert len(my_batch_definition_list) == 1


@pytest.mark.big
@mock_s3
def test_foxtrot(s3_bucket_name, aws_region, test_df):
    client, bucket = create_s3_setup(s3_bucket_name, aws_region)

    keys: List[str] = [
        "test_dir_foxtrot/A/A-1.csv",
        "test_dir_foxtrot/A/A-2.csv",
        "test_dir_foxtrot/A/A-3.csv",
        "test_dir_foxtrot/B/B-1.txt",
        "test_dir_foxtrot/B/B-2.txt",
        "test_dir_foxtrot/B/B-3.txt",
        "test_dir_foxtrot/C/C-2017.csv",
        "test_dir_foxtrot/C/C-2018.csv",
        "test_dir_foxtrot/C/C-2019.csv",
        "test_dir_foxtrot/D/D-aaa.csv",
        "test_dir_foxtrot/D/D-bbb.csv",
        "test_dir_foxtrot/D/D-ccc.csv",
        "test_dir_foxtrot/D/D-ddd.csv",
        "test_dir_foxtrot/D/D-eee.csv",
    ]
    for key in keys:
        client.put_object(Bucket=bucket, Body=test_df.to_csv(index=False).encode("utf-8"), Key=key)

    my_data_connector: DataConnector

    my_data_connector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 0
    assert my_data_connector.get_data_references()[:3] == []

    batching_regex = re.compile(r"(?P<part_1>.+)-(?P<part_2>.*)\.csv")
    matching_data_references = my_data_connector.get_matched_data_references(regex=batching_regex)
    assert len(matching_data_references) == 0
    assert matching_data_references[:3] == []

    my_data_connector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="test_dir_foxtrot/A",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "test_dir_foxtrot/A/A-1.csv",
        "test_dir_foxtrot/A/A-2.csv",
        "test_dir_foxtrot/A/A-3.csv",
    ]

    batching_regex = re.compile(r"(?P<part_1>.+)-(?P<part_2>.*)\.csv")
    matched_data_references = my_data_connector.get_matched_data_references(regex=batching_regex)
    assert len(matched_data_references) == 3
    assert matched_data_references[:3] == [
        "test_dir_foxtrot/A/A-1.csv",
        "test_dir_foxtrot/A/A-2.csv",
        "test_dir_foxtrot/A/A-3.csv",
    ]

    my_data_connector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="test_dir_foxtrot/B",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "test_dir_foxtrot/B/B-1.txt",
        "test_dir_foxtrot/B/B-2.txt",
        "test_dir_foxtrot/B/B-3.txt",
    ]

    batching_regex = re.compile(r"(?P<part_1>.+)-(?P<part_2>.*)\.txt")
    matched_data_references = my_data_connector.get_matched_data_references(regex=batching_regex)
    assert len(matched_data_references) == 3
    assert matched_data_references[:3] == [
        "test_dir_foxtrot/B/B-1.txt",
        "test_dir_foxtrot/B/B-2.txt",
        "test_dir_foxtrot/B/B-3.txt",
    ]

    my_data_connector = S3DataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        s3_client=client,
        bucket=bucket,
        prefix="test_dir_foxtrot/C",
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "test_dir_foxtrot/C/C-2017.csv",
        "test_dir_foxtrot/C/C-2018.csv",
        "test_dir_foxtrot/C/C-2019.csv",
    ]

    batching_regex = re.compile(r"(?P<part_1>.+)-(?P<part_2>.*)\.csv")
    matched_data_references = my_data_connector.get_matched_data_references(regex=batching_regex)
    assert len(matched_data_references) == 3
    assert matched_data_references[:3] == [
        "test_dir_foxtrot/C/C-2017.csv",
        "test_dir_foxtrot/C/C-2018.csv",
        "test_dir_foxtrot/C/C-2019.csv",
    ]

    my_batch_request = BatchRequest(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_s3_data_asset",
        options={},
    )
    my_batch_definition_list: List[LegacyBatchDefinition] = (
        my_data_connector.get_batch_definition_list(batch_request=my_batch_request)
    )
    assert len(my_batch_definition_list) == 3


@pytest.mark.unit
def test_sanitize_prefix_behaves_the_same_as_local_files():
    def check_sameness(prefix, expected_output):
        s3_sanitized = sanitize_prefix_for_gcs_and_s3(text=prefix)
        file_system_sanitized = sanitize_prefix(prefix)
        if os.sep == "\\":  # Fix to ensure tests work on Windows
            file_system_sanitized = file_system_sanitized.replace("\\", "/")

        assert file_system_sanitized == expected_output, (
            f"Expected output does not match original sanitization behavior, got "
            f"{file_system_sanitized} instead of {expected_output}"
        )
        assert s3_sanitized == expected_output == file_system_sanitized, (
            f'S3 sanitized result is incorrect, "{s3_sanitized} instead of {expected_output}'
        )

    # Copy of all samples from tests/datasource/data_connector/test_file_path_data_connector.py
    check_sameness("foo/", "foo/")
    check_sameness("bar", "bar/")
    check_sameness("baz.txt", "baz.txt")
    check_sameness("a/b/c/baz.txt", "a/b/c/baz.txt")

    # A couple additional checks
    check_sameness("a/b/c", "a/b/c/")
    check_sameness("a.x/b/c", "a.x/b/c/")
    check_sameness("path/to/folder.something/", "path/to/folder.something/")
    check_sameness("path/to/folder.something", "path/to/folder.something")


@pytest.mark.unit
@mock_s3
@pytest.mark.parametrize(
    "whole_directory_override, expected_batch_count, expected_identifier_key",
    [
        pytest.param(
            True, 1, "path", id="with_whole_directory_override_returns_single_directory_batch"
        ),
        pytest.param(
            False,
            3,
            "filename",
            id="without_whole_directory_override_returns_individual_file_batches",
        ),
    ],
)
def test_s3_data_connector_whole_directory_path_override(
    whole_directory_override,
    expected_batch_count,
    expected_identifier_key,
    s3_bucket_name,
    aws_region,
):
    """Test S3DataConnector behavior with and without whole_directory_path_override parameter."""
    # Setup
    s3_client, bucket_name = create_s3_setup(s3_bucket_name, aws_region)

    prefix = "test_directory/"
    whole_directory_path = f"s3://{bucket_name}/{prefix}"

    # Create multiple files in the directory
    test_files = [
        f"{prefix}file1.csv",
        f"{prefix}file2.csv",
        f"{prefix}file3.csv",
    ]

    for file_path in test_files:
        s3_client.put_object(Bucket=bucket_name, Key=file_path, Body="col1,col2\n1,2\n3,4\n")

    # Create data connector with conditional whole_directory_path_override
    data_connector = S3DataConnector(
        datasource_name="my_s3_datasource",
        data_asset_name="my_data_asset",
        s3_client=s3_client,
        bucket=bucket_name,
        prefix=prefix,
        file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
        whole_directory_path_override=whole_directory_path if whole_directory_override else None,
    )

    # Create batch request with conditional partitioner
    batch_request = BatchRequest(
        datasource_name="my_s3_datasource",
        data_asset_name="my_data_asset",
        options={},
        partitioner=None
        if whole_directory_override
        else FileNamePartitionerPath(regex=re.compile(r"(?P<filename>.+\.csv)")),
    )
    batch_definitions = data_connector.get_batch_definition_list(batch_request)

    # Verify expected batch count
    assert len(batch_definitions) == expected_batch_count

    # Verify batch definitions have correct structure
    for batch_definition in batch_definitions:
        assert batch_definition.datasource_name == "my_s3_datasource"
        assert batch_definition.data_asset_name == "my_data_asset"
        assert expected_identifier_key in batch_definition.batch_identifiers

    if whole_directory_override:
        # For directory mode, verify single batch with directory path
        batch_definition = batch_definitions[0]
        assert batch_definition.batch_identifiers["path"] == whole_directory_path
    else:
        # For file mode, verify individual file batches
        file_names = [bd.batch_identifiers["filename"] for bd in batch_definitions]
        expected_files = ["file1.csv", "file2.csv", "file3.csv"]
        assert sorted(file_names) == sorted(expected_files)


@pytest.mark.unit
@mock_s3
def test_s3_data_connector_missing_file_path_template_map_fn_error(s3_bucket_name, aws_region):
    """Test S3DataConnector raises MissingFilePathTemplateMapFnError
    when missing file_path_template_map_fn."""
    s3_client, bucket = create_s3_setup(s3_bucket_name, aws_region)

    data_connector = S3DataConnector(
        datasource_name="my_s3_datasource",
        data_asset_name="my_data_asset",
        s3_client=s3_client,
        bucket=bucket,
        prefix="test/",
        file_path_template_map_fn=None,
    )

    with pytest.raises(MissingFilePathTemplateMapFnError):
        data_connector._get_full_file_path("test.csv")
