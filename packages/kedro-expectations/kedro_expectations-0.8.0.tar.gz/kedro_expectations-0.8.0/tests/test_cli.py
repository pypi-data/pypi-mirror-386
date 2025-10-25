from unittest.mock import patch

import great_expectations as ge
import pytest

from kedro_expectations.cli.create_suite import start_suite_creation
from kedro_expectations.constants import _DEFAULT_PANDAS_DATASOURCE_NAME
from tests.test_utils import get_random_string


def test_start_suite_creation_generic(initialize_kedro_project):
    context = ge.get_context(mode="file")
    expectation_suite_name = "new_test_suite" + get_random_string(5)
    try:
        user_input = [1, "companies", expectation_suite_name, "0"]

        with patch("click.prompt", side_effect=user_input):
            start_suite_creation(context)
        assert (
            "companies"
            in ge.get_context(mode="file").get_available_data_asset_names()[
                _DEFAULT_PANDAS_DATASOURCE_NAME
            ]
        )
        assert f"companies.{expectation_suite_name}" in [
            suite["name"] for suite in ge.get_context(mode="file").suites.all()
        ]
    finally:
        ge.get_context(mode="file").suites.delete(f"companies.{expectation_suite_name}")


def test_start_suite_creation_generic_fail_suite_name(initialize_kedro_project):
    context = ge.get_context(mode="file")
    user_input = [1, "companies", "succeeding_test_suite", "0"]
    with patch("click.prompt", side_effect=user_input):
        with pytest.raises(Exception):
            start_suite_creation(context)


def test_start_suite_creation_wrong_input(initialize_kedro_project, capfd):
    context = ge.get_context(mode="file")
    user_input = [5]
    with patch("click.prompt", side_effect=user_input):
        start_suite_creation(context)
    out, err = capfd.readouterr()
    assert "The number typed is invalid. Aborting!" in out


def test_start_suite_creation_dataset_not_in_catalog(initialize_kedro_project, capfd):
    context = ge.get_context(mode="file")
    dataset_name = get_random_string(10)
    user_input = [1, dataset_name, "new_test_suite", "0"]

    with patch("click.prompt", side_effect=user_input):
        start_suite_creation(context)

    assert (
        dataset_name
        not in ge.get_context(mode="file").get_available_data_asset_names()[
            _DEFAULT_PANDAS_DATASOURCE_NAME
        ]
    )
    out, err = capfd.readouterr()
    assert f"The input {dataset_name} was not found at the DataCatalog." in out


def test_start_suite_creation_partitioned(initialize_kedro_project):
    context = ge.get_context(mode="file")
    expectation_suite_name = "new_test_suite" + get_random_string(5)
    try:
        user_input = [2, 1, "companies_partitioned", expectation_suite_name, "0"]
        with patch("click.prompt", side_effect=user_input):
            start_suite_creation(context)

        assert (
            "companies_partitioned"
            in ge.get_context(mode="file").get_available_data_asset_names()[
                _DEFAULT_PANDAS_DATASOURCE_NAME
            ]
        )
        assert f"companies_partitioned.{expectation_suite_name}" in [
            suite["name"] for suite in ge.get_context(mode="file").suites.all()
        ]

    finally:
        ge.get_context(mode="file").suites.delete(
            f"companies_partitioned.{expectation_suite_name}"
        )


def test_start_suite_creation_partitioned_no_partition(initialize_kedro_project, capfd):
    context = ge.get_context(mode="file")
    user_input = [2, 1, "reviews"]
    with patch("click.prompt", side_effect=user_input):
        with pytest.raises(Exception):
            start_suite_creation(context)
        out, err = capfd.readouterr()
        assert "The dataset reviews is not partitioned!" in out


def test_start_suite_creation_partitioned_inexistent(initialize_kedro_project):
    context = ge.get_context(mode="file")
    user_input = [2, 1, "inexistent_dataset"]
    with patch("click.prompt", side_effect=user_input):
        with pytest.raises(AttributeError):
            start_suite_creation(context)


def test_start_suite_creation_partitioned_specific(initialize_kedro_project):
    context = ge.get_context(mode="file")
    expectation_suite_name = "new_test_suite" + get_random_string(5)
    try:
        user_input = [
            2,
            2,
            "companies_partitioned",
            "companies_1",
            expectation_suite_name,
            "0",
        ]
        with patch("click.prompt", side_effect=user_input):
            start_suite_creation(context)

        assert (
            "companies_partitioned"
            in ge.get_context(mode="file").get_available_data_asset_names()[
                _DEFAULT_PANDAS_DATASOURCE_NAME
            ]
        )
        assert f"companies_partitioned.companies_1.{expectation_suite_name}" in [
            suite["name"] for suite in ge.get_context(mode="file").suites.all()
        ]

    finally:
        ge.get_context(mode="file").suites.delete(
            f"companies_partitioned.companies_1.{expectation_suite_name}"
        )


def test_start_suite_creation_partitioned_specific_inexistent(
    initialize_kedro_project, capfd
):
    context = ge.get_context(mode="file")
    user_input = [
        2,
        2,
        "companies_partitioned",
        "inexistent_partition",
        "new_test_suite",
        "0",
    ]
    with patch("click.prompt", side_effect=user_input):
        start_suite_creation(context)

    out, err = capfd.readouterr()
    assert "The partition inexistent_partition does not exit!" in out
