import itertools
import ntpath
import os
import pickle
import random
import string
import tempfile
from pathlib import Path
from unittest.mock import patch

import great_expectations as ge
import pytest
from kedro.framework.session import KedroSession
from kedro_expectations.assistant.rules import DATASET_TYPE
from kedro_expectations.constants import _DEFAULT_PANDAS_DATASOURCE_NAME
from kedro_expectations.utils import (
    base_ge_folder_exists,
    delete_checkpoints,
    get_all_expectations,
    get_or_add_dataframe_asset,
    get_or_add_pandas_datasource,
    get_suite_name,
    is_dataset_in_catalog,
    load_checkpoints,
    location_is_kedro_root_folder,
    populate_new_suite,
    store_checkpoints,
)
from moto.server import ThreadedMotoServer

# Tests


def get_random_string(length):
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))


def test_base_ge_folder_exists():
    assert base_ge_folder_exists()


def test_base_ge_folder_exists_fail(initialize_kedro_project, capfd):
    project_path = initialize_kedro_project
    random_string = get_random_string(10)
    not_root = project_path / random_string
    try:
        not_root.mkdir()
        os.chdir(not_root)
        assert not base_ge_folder_exists()
        out, err = capfd.readouterr()
        assert "This command has NOT been run" in out
    finally:
        os.chdir(project_path)
        os.rmdir(not_root)


def test_location_is_kedro_root_folder():
    assert location_is_kedro_root_folder()


def test_is_dataset_in_catalog(initialize_kedro_project):
    dataset_name = "companies"
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        catalog = session.load_context().catalog
        result = is_dataset_in_catalog(dataset_name, catalog)

    assert result


def test_is_dataset_in_catalog_false():
    with KedroSession.create(project_path=None) as session:
        dataset_name = get_random_string(10)
        catalog = session.load_context().catalog
        result = is_dataset_in_catalog(dataset_name, catalog)

    assert not result


def test_is_dataset_in_catalog_fail():
    dataset_name = get_random_string(10)
    with pytest.raises(Exception):
        is_dataset_in_catalog(dataset_name, None)


def test_get_pandas_datasource_add_new():
    context = ge.get_context(mode="file")
    datasource_name = get_random_string(10)
    result = get_or_add_pandas_datasource(context, datasource_name)
    assert result == context.get_datasource(datasource_name)
    # reset context so it stays the same for the next test
    context.delete_datasource(datasource_name)


def test_get_pandas_datasource():
    context = ge.get_context(mode="file")
    result = get_or_add_pandas_datasource(context)
    assert result == context.get_datasource(_DEFAULT_PANDAS_DATASOURCE_NAME)


def test_get_pandas_datasource_input_fail():
    context = ge.get_context(mode="file")
    with pytest.raises(TypeError):
        get_or_add_pandas_datasource(context, 2)


def test_get_dataframe_asset_add_new():
    # Necessary to reload datasource at each step as it does not self-update :-(
    datasource = lambda: ge.get_context(mode="file").get_datasource(
        _DEFAULT_PANDAS_DATASOURCE_NAME
    )
    asset_name = get_random_string(10)
    try:
        # add asset, then check if found in datasource
        asset = get_or_add_dataframe_asset(ge.get_context(mode="file"), asset_name)
        assert asset == datasource().get_asset(asset_name)
    finally:
        datasource().delete_asset(asset_name)


def test_get_dataframe_asset():
    datasource = ge.get_context(mode="file").get_datasource(
        _DEFAULT_PANDAS_DATASOURCE_NAME
    )
    asset = datasource.get_asset("companies")
    assert asset == get_or_add_dataframe_asset(ge.get_context(mode="file"), "companies")


def test_get_all_expectations():
    context = ge.get_context(mode="file")
    out_succeeding = get_all_expectations(context, "companies")
    out_unexpected = get_all_expectations(context, "companies_unexpected")

    assert len(out_succeeding) == 2
    assert len(out_unexpected) == 1
    head, tail = ntpath.split(out_unexpected[0])
    assert tail == "failing_test_suite.json"


def test_get_all_expectations_empty():
    context = ge.get_context(mode="file")
    out = get_all_expectations(context, get_random_string(10))
    assert out == list()


def test_get_suite_name_linux_path():
    exp_suites_pattern = "/home/user/gx/expectations/suite_name.json"
    out = get_suite_name(exp_suites_pattern, "key_1")
    assert out == "key_1.suite_name"


def test_get_suite_name_windows_path():
    exp_suites_pattern = "C:\\user\\gx\\expectations\\suite_name.json"
    out = get_suite_name(exp_suites_pattern, "key_2")
    assert out == "key_2.suite_name"


def test_get_suite_name_new_values():
    expectation_file = "path_to_file.json"
    out = get_suite_name(expectation_file, "key_3")
    assert out == "key_3.path_to_file"


def test_populate_new_suite_no_columns(initialize_kedro_project, capfd):
    project_dir = initialize_kedro_project
    expectation_suite_name = "companies.succeeding_test_suite"
    with KedroSession.create(project_path=project_dir) as session:
        input_data = session.load_context().catalog.load("companies")

    user_input = [
        "id",
        "company_rating",
        "company_location",
        "total_fleet_count",
        "iata_approved",
        "0",
    ]
    with patch("click.prompt", side_effect=user_input):
        populate_new_suite(
            input_data, expectation_suite_name, dataset_type=DATASET_TYPE.FULL
        )

    out, err = capfd.readouterr()
    assert "All the columns were marked to be excluded! Impossible to validate!" in out


@pytest.mark.parametrize(
    "user_input", [["company_rating", "0"], ["company_rating", "id", "0"]]
)
def test_populate_new_suite(initialize_kedro_project, capfd, user_input):
    project_dir = initialize_kedro_project
    expectation_suite_name = "companies.succeeding_test_suite"
    with KedroSession.create(project_path=project_dir) as session:
        input_data = session.load_context().catalog.load("companies")

    with patch("click.prompt", side_effect=user_input):
        populate_new_suite(
            input_data, expectation_suite_name, dataset_type=DATASET_TYPE.FULL
        )

    out, err = capfd.readouterr()
    assert (
        f"The following columns are not going to be validated:\n{user_input[:-1]}"
        in out
    )


@pytest.mark.parametrize("user_input", [["0"], ["inexistent", "0"]])
def test_populate_new_suite_validate_all(initialize_kedro_project, capfd, user_input):
    project_dir = initialize_kedro_project
    expectation_suite_name = "companies.succeeding_test_suite"
    with KedroSession.create(project_path=project_dir) as session:
        input_data = session.load_context().catalog.load("companies")

    with patch("click.prompt", side_effect=user_input):
        populate_new_suite(
            input_data, expectation_suite_name, dataset_type=DATASET_TYPE.FULL
        )

    out, err = capfd.readouterr()
    assert "You chose for all columns to be validated!" in out


def test_populate_new_suite_validate_fail(initialize_kedro_project):
    project_dir = initialize_kedro_project
    expectation_suite_name = "companies.inexistent_suite"
    with KedroSession.create(project_path=project_dir) as session:
        input_data = session.load_context().catalog.load("companies")

    with pytest.raises(Exception):
        populate_new_suite(
            input_data, expectation_suite_name, dataset_type=DATASET_TYPE.FULL
        )


def test_store_checkpoints():
    with tempfile.TemporaryDirectory() as temp_dir:
        checkpoint_data = {"key": "value"}
        store_checkpoints(temp_dir, checkpoint_data)

        files = list(Path(temp_dir).glob("*.pkl"))
        assert len(files) == 1

        with open(files[0], "rb") as f:
            loaded_data = pickle.load(f)
        assert loaded_data == checkpoint_data


def test_load_checkpoints():
    with tempfile.TemporaryDirectory() as temp_dir:
        checkpoint_data = [
            [{"key1": "value1"}],
            [{"key2": "value2"}, {"key3": "value3"}],
            [],
        ]
        for i, data in enumerate(checkpoint_data):
            with open(os.path.join(temp_dir, f"checkpoint_{i}.pkl"), "wb") as f:
                pickle.dump(data, f)

        loaded_data = load_checkpoints(temp_dir)
        assert len(loaded_data) == len(checkpoint_data)
        target = [x for y in checkpoint_data for x in y]

        assert target == loaded_data


@pytest.fixture
def moto_server():
    server = ThreadedMotoServer()
    server.start()
    yield server
    server.stop()  # Ensure cleanup after each test


def test_delete_checkpoints():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create dummy checkpoint files
        for i in range(3):
            with open(os.path.join(temp_dir, f"checkpoint_{i}.pkl"), "wb") as f:
                pickle.dump({"test": i}, f)

        delete_checkpoints(temp_dir)
        assert len(list(Path(temp_dir).glob("*.pkl"))) == 0


@pytest.mark.parametrize("mock_glob", [patch("pathlib.Path.glob", return_value=[])])
def test_load_checkpoints_no_files(mock_glob):
    with tempfile.TemporaryDirectory() as temp_dir:
        assert load_checkpoints(temp_dir) == []


@pytest.mark.parametrize(
    "mock_iterdir", [patch("pathlib.Path.iterdir", return_value=[])]
)
def test_delete_checkpoints_empty_folder(mock_iterdir):
    with tempfile.TemporaryDirectory() as temp_dir:
        delete_checkpoints(temp_dir)  # Should not raise any errors


# TODO Add s3 tests! Mockup with moto_server fixture
