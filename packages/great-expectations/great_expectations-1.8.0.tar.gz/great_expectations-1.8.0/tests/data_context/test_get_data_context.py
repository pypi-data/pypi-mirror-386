import pathlib
import shutil
import uuid
from typing import Any
from unittest import mock

import pytest

import great_expectations as gx
from great_expectations.data_context import CloudDataContext, EphemeralDataContext
from great_expectations.data_context.cloud_constants import GXCloudEnvironmentVariable
from great_expectations.data_context.data_context.cloud_data_context import (
    CloudUserInfo,
    Workspace,
)
from great_expectations.data_context.data_context.file_data_context import (
    FileDataContext,
)
from great_expectations.data_context.types.base import (
    DataContextConfig,
    InMemoryStoreBackendDefaults,
)
from great_expectations.exceptions.exceptions import (
    GitIgnoreScaffoldingError,
    GXCloudConfigurationError,
)
from tests.test_utils import working_directory

GX_CLOUD_PARAMS_ALL = {
    "cloud_base_url": "localhost:7000",
    "cloud_organization_id": "bd20fead-2c31-4392-bcd1-f1e87ad5a79c",
    "cloud_workspace_id": "fffff6781234567812345678123fffff",
    "cloud_access_token": "i_am_a_token",
}
GX_CLOUD_PARAMS_REQUIRED = {
    "cloud_organization_id": "bd20fead-2c31-4392-bcd1-f1e87ad5a79c",
    "cloud_access_token": "i_am_a_token",
}


@pytest.fixture()
def set_up_cloud_envs(monkeypatch):
    monkeypatch.setenv("GX_CLOUD_BASE_URL", "localhost:7000")
    monkeypatch.setenv("GX_CLOUD_ORGANIZATION_ID", "bd20fead-2c31-4392-bcd1-f1e87ad5a79c")
    monkeypatch.setenv("GX_CLOUD_ACCESS_TOKEN", "i_am_a_token")
    monkeypatch.setenv("GX_CLOUD_WORKSPACE_ID", "fffff6781234567812345678123fffff")


@pytest.fixture
def clear_env_vars(monkeypatch):
    # Delete local env vars (if present)
    for env_var in GXCloudEnvironmentVariable:
        monkeypatch.delenv(env_var, raising=False)


@pytest.mark.unit
def test_base_context(clear_env_vars):
    config: DataContextConfig = DataContextConfig(
        config_version=3.0,
        plugins_directory=None,
        expectations_store_name="expectations_store",
        checkpoint_store_name="checkpoint_store",
        stores={
            "expectations_store": {"class_name": "ExpectationsStore"},
            "checkpoint_store": {"class_name": "CheckpointStore"},
            "validation_result_store": {"class_name": "ValidationResultsStore"},
            "validation_definition_store": {"class_name": "ValidationDefinitionStore"},
        },
        validation_results_store_name="validation_result_store",
        data_docs_sites={},
    )
    assert isinstance(gx.get_context(project_config=config), EphemeralDataContext)


@pytest.mark.unit
def test_base_context__with_overridden_yml(tmp_path: pathlib.Path, clear_env_vars):
    project_path = tmp_path / "empty_data_context"
    project_path.mkdir()
    context_path = project_path / FileDataContext.GX_DIR
    context = gx.get_context(context_root_dir=context_path)
    assert isinstance(context, FileDataContext)
    assert context.expectations_store_name == "expectations_store"

    config: DataContextConfig = DataContextConfig(
        config_version=3.0,
        plugins_directory=None,
        expectations_store_name="new_expectations_store",
        checkpoint_store_name="new_checkpoint_store",
        stores={
            "new_expectations_store": {"class_name": "ExpectationsStore"},
            "new_checkpoint_store": {"class_name": "CheckpointStore"},
            "new_validation_result_store": {"class_name": "ValidationResultsStore"},
        },
        validation_results_store_name="new_validation_result_store",
        data_docs_sites={},
    )
    context = gx.get_context(project_config=config, context_root_dir=context_path)
    assert isinstance(context, FileDataContext)
    assert context.expectations_store_name == "new_expectations_store"


@pytest.mark.unit
def test_data_context_root_dir_returns_data_context(
    tmp_path: pathlib.Path,
    clear_env_vars,
):
    project_path = tmp_path / "empty_data_context"
    project_path.mkdir()
    context_path = project_path / FileDataContext.GX_DIR
    assert isinstance(gx.get_context(context_root_dir=str(context_path)), FileDataContext)


@pytest.mark.unit
def test_base_context_invalid_root_dir(clear_env_vars, tmp_path):
    config: DataContextConfig = DataContextConfig(
        config_version=3.0,
        plugins_directory=None,
        expectations_store_name="expectations_store",
        checkpoint_store_name="checkpoint_store",
        stores={
            "expectations_store": {"class_name": "ExpectationsStore"},
            "checkpoint_store": {"class_name": "CheckpointStore"},
            "validation_result_store": {"class_name": "ValidationResultsStore"},
        },
        validation_results_store_name="validation_result_store",
        data_docs_sites={},
    )

    context_root_dir = tmp_path / "root"
    context_root_dir.mkdir()
    assert isinstance(
        gx.get_context(project_config=config, context_root_dir=context_root_dir),
        FileDataContext,
    )


@pytest.mark.parametrize("ge_cloud_mode", [True, None])
@pytest.mark.cloud
def test_cloud_context_env(set_up_cloud_envs, empty_ge_cloud_data_context_config, ge_cloud_mode):
    with mock.patch.object(
        CloudDataContext,
        "retrieve_data_context_config_from_cloud",
        return_value=empty_ge_cloud_data_context_config,
    ):
        assert isinstance(
            gx.get_context(cloud_mode=ge_cloud_mode),
            CloudDataContext,
        )


@pytest.mark.cloud
def test_cloud_missing_env_throws_exception(clear_env_vars, empty_ge_cloud_data_context_config):
    with pytest.raises(GXCloudConfigurationError):
        gx.get_context(cloud_mode=True)


@pytest.mark.parametrize("params", [GX_CLOUD_PARAMS_REQUIRED, GX_CLOUD_PARAMS_ALL])
@pytest.mark.cloud
@pytest.mark.filterwarnings("ignore:Workspace id is not set when instantiating a CloudDataContext")
def test_cloud_context_params(
    unset_gx_env_variables: None,
    monkeypatch: pytest.MonkeyPatch,
    empty_ge_cloud_data_context_config: DataContextConfig,
    # params is annotated with Any since mypy will fail with str values when checking
    # gx.get_context(**params) because there are no str only value variants.
    params: dict[str, Any],
):
    with (
        mock.patch.object(
            CloudDataContext,
            "retrieve_data_context_config_from_cloud",
            return_value=empty_ge_cloud_data_context_config,
        ),
        mock.patch.object(
            CloudDataContext,
            "cloud_user_info",
            return_value=CloudUserInfo(
                user_id=uuid.UUID("12345678-1234-1234-1234-123456789012"),
                workspaces=[Workspace(id="fffff6781234567812345678123fffff", role="editor")],
            ),
        ),
    ):
        assert isinstance(
            gx.get_context(**params),
            CloudDataContext,
        )


@pytest.mark.cloud
@pytest.mark.filterwarnings("ignore:Workspace id is not set when instantiating a CloudDataContext")
def test_cloud_context_with_in_memory_config_overrides(
    unset_gx_env_variables: None,
    monkeypatch: pytest.MonkeyPatch,
    empty_ge_cloud_data_context_config: DataContextConfig,
):
    with (
        mock.patch.object(
            CloudDataContext,
            "retrieve_data_context_config_from_cloud",
            return_value=empty_ge_cloud_data_context_config,
        ),
        mock.patch.object(
            CloudDataContext,
            "cloud_user_info",
            return_value=CloudUserInfo(
                user_id=uuid.UUID("12345678-1234-1234-1234-123456789012"),
                workspaces=[Workspace(id="fffff6781234567812345678123fffff", role="editor")],
            ),
        ),
    ):
        context = gx.get_context(
            cloud_base_url="localhost:7000",
            cloud_organization_id="bd20fead-2c31-4392-bcd1-f1e87ad5a79c",
            cloud_access_token="i_am_a_token",
        )
        assert isinstance(context, CloudDataContext)
        assert context.expectations_store_name == "default_expectations_store"

        config: DataContextConfig = DataContextConfig(
            config_version=3.0,
            plugins_directory=None,
            expectations_store_name="new_expectations_store",
            checkpoint_store_name="new_checkpoint_store",
            stores={
                "new_expectations_store": {"class_name": "ExpectationsStore"},
                "new_checkpoint_store": {"class_name": "CheckpointStore"},
                "new_validation_result_store": {"class_name": "ValidationResultsStore"},
            },
            validation_results_store_name="new_validation_result_store",
            data_docs_sites={},
        )
        context = gx.get_context(
            project_config=config,
            cloud_base_url="localhost:7000",
            cloud_organization_id="bd20fead-2c31-4392-bcd1-f1e87ad5a79c",
            cloud_access_token="i_am_a_token",
        )
        assert isinstance(context, CloudDataContext)
        assert context.expectations_store_name == "new_expectations_store"


@pytest.mark.unit
def test_get_context_with_no_arguments_returns_ephemeral_with_sensible_defaults():
    context = gx.get_context()
    assert isinstance(context, EphemeralDataContext)

    defaults = InMemoryStoreBackendDefaults(init_temp_docs_sites=True)
    assert context.config.stores == defaults.stores


@pytest.mark.unit
def test_get_context_with_mode_equals_ephemeral_returns_ephemeral_data_context():
    context = gx.get_context(mode="ephemeral")
    assert isinstance(context, EphemeralDataContext)


@pytest.mark.unit
def test_get_context_with_mode_equals_file_returns_file_data_context(
    tmp_path: pathlib.Path,
):
    with working_directory(tmp_path):
        context = gx.get_context(mode="file")
    assert isinstance(context, FileDataContext)


@pytest.mark.cloud
def test_get_context_with_mode_equals_cloud_returns_cloud_data_context(
    empty_ge_cloud_data_context_config: DataContextConfig, set_up_cloud_envs
):
    with mock.patch.object(
        CloudDataContext,
        "retrieve_data_context_config_from_cloud",
        return_value=empty_ge_cloud_data_context_config,
    ) as mock_retrieve_config:
        context = gx.get_context(mode="cloud")

    mock_retrieve_config.assert_called_once()
    assert isinstance(context, CloudDataContext)


@pytest.mark.filesystem
def test_get_context_with_context_root_dir_scaffolds_filesystem(tmp_path: pathlib.Path):
    root = tmp_path / "root"
    context_root_dir = root.joinpath(FileDataContext.GX_DIR)
    assert not context_root_dir.exists()

    context = gx.get_context(context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert context_root_dir.exists()
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "\nuncommitted/"


@pytest.mark.filesystem
def test_get_context_with_custom_context_root_dir_scaffolds_filesystem(tmp_path: pathlib.Path):
    root = tmp_path / "root"
    context_root_dir = root.joinpath("hello_world")
    assert not context_root_dir.exists()

    context = gx.get_context(context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert context_root_dir.exists()
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "\nuncommitted/"


@pytest.mark.filesystem
def test_get_context_with_mode_and_custom_context_root_dir_scaffolds_filesystem(
    tmp_path: pathlib.Path,
):
    root = tmp_path / "root"
    context_root_dir = root.joinpath("hello_world")
    assert not context_root_dir.exists()

    context = gx.get_context(mode="file", context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert context_root_dir.exists()
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "\nuncommitted/"


@pytest.mark.filesystem
def test_errors_if_context_root_dir_and_project_root_dir_are_both_provided_for_file_context(
    tmp_path: pathlib.Path,
):
    root = tmp_path / "root"
    context_root_dir = root.joinpath("hello_world")
    assert not context_root_dir.exists()

    with pytest.raises(
        TypeError,
        match="'project_root_dir' and 'context_root_dir' are conflicting args; please only provide one",  # noqa: E501
    ):
        gx.get_context(  # type: ignore[call-overload]
            mode="file",
            context_root_dir=context_root_dir,
            project_root_dir=context_root_dir.parent,
        )


@pytest.mark.filesystem
def test_get_context_with_context_root_dir_scaffolds_existing_gitignore(clear_env_vars, tmp_path):
    context_root_dir = tmp_path / FileDataContext.GX_DIR
    context_root_dir.mkdir()
    with open(context_root_dir / FileDataContext.GITIGNORE, "w") as f:
        f.write("asdf")

    context = gx.get_context(context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "asdf\nuncommitted/"


@pytest.mark.filesystem
def test_get_context_with_context_root_dir_scaffolds_new_gitignore(clear_env_vars, tmp_path):
    context_root_dir = tmp_path / FileDataContext.GX_DIR
    context_root_dir.mkdir()

    context = gx.get_context(context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "\nuncommitted/"


@pytest.mark.filesystem
def test_get_context_with_context_root_dir_gitignore_error(clear_env_vars, tmp_path):
    context_root_dir = tmp_path / FileDataContext.GX_DIR
    context_root_dir.mkdir()

    with mock.patch(
        "great_expectations.data_context.data_context.serializable_data_context.SerializableDataContext._scaffold_gitignore",
        side_effect=OSError("Error"),
    ):
        with pytest.raises(GitIgnoreScaffoldingError):
            gx.get_context(context_root_dir=context_root_dir)


@pytest.mark.filesystem
def test_get_context_scaffolds_gx_dir(tmp_path: pathlib.Path):
    with working_directory(tmp_path):
        context = gx.get_context(mode="file")
    assert isinstance(context, FileDataContext)

    project_root_dir = pathlib.Path(context.root_directory)
    assert project_root_dir.stem == FileDataContext.GX_DIR


@pytest.mark.filesystem
def test_get_context_finds_legacy_great_expectations_dir(
    tmp_path: pathlib.Path,
):
    working_dir = tmp_path / "a" / "b" / "c" / "d" / "working_dir"

    # Scaffold great_expectations
    context_root_dir = working_dir / FileDataContext._LEGACY_GX_DIR
    context_root_dir.mkdir(parents=True)

    # Scaffold great_expectations.yml
    gx_yml = context_root_dir / FileDataContext.GX_YML
    yml_fixture = (
        pathlib.Path(__file__)
        .joinpath("../../test_fixtures/great_expectations_basic.yml")
        .resolve()
    )
    assert yml_fixture.exists()
    shutil.copy(yml_fixture, gx_yml)

    with working_directory(working_dir):
        context = gx.get_context()
    assert isinstance(context, FileDataContext)

    project_root_dir = pathlib.Path(context.root_directory)
    assert project_root_dir.stem == FileDataContext._LEGACY_GX_DIR
