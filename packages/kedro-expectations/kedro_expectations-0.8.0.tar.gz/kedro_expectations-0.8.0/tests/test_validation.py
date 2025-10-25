from unittest.mock import patch

import pytest
from great_expectations import ExpectationSuite
from kedro.pipeline.node import Node
from kedro.framework.session import KedroSession

from kedro_expectations import KedroExpectationsHooks
from kedro_expectations.exceptions import SuiteValidationFailure
from kedro_expectations.notification import DummyNotifier, EmailNotifier
from kedro_expectations.cli.create_suite import start_suite_creation
import great_expectations as ge

from tests.test_utils import get_random_string


@pytest.fixture(name="test_node")
def test_node():
    return Node(
        func=lambda x: x,
        inputs="companies_in",
        outputs="companies_out",
        name="test_node",
    )


def test_project_dir_exists(initialize_kedro_project):
    # The `initialize_kedro_project` fixture is automatically invoked,
    # and its return value is the project directory.
    project_dir = initialize_kedro_project

    # Check if the project directory contains the expected files
    assert (project_dir / "src" / "test_project").exists()
    assert (project_dir / "conf" / "base" / "catalog.yml").exists()


def test_gx_failure(initialize_kedro_project, capfd):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        assert not session._hook_manager.is_registered(KedroExpectationsHooks)
        session._hook_manager.register(KedroExpectationsHooks(on_failure="raise_fast"))
        with pytest.raises(SuiteValidationFailure):
            session.run(pipeline_name="data_processing_failing")


def test_register_hook(initialize_kedro_project):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        assert not session._hook_manager.has_plugin("kedro-expectations")
        session._hook_manager.register(KedroExpectationsHooks(), "kedro-expectations")
        assert session._hook_manager.has_plugin("kedro-expectations")


def test_register_hook_wrong_argument(initialize_kedro_project):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        with pytest.raises(Exception):
            session._hook_manager.register(
                KedroExpectationsHooks(on_failure="other failure text")
            )


def test_create_hook_parallel_invalid_mode():
    on_failure = "raise_fast"
    parallel_validation = True

    with pytest.raises(Exception):
        KedroExpectationsHooks(
            on_failure=on_failure, parallel_validation=parallel_validation
        )


@pytest.mark.parametrize("on_failure", ["raise_later", "continue"])
def test_create_hook_parallel_valid_mode(on_failure):
    parallel_validation = True

    hook = KedroExpectationsHooks(
        on_failure=on_failure, parallel_validation=parallel_validation
    )

    # should not raise an exception
    assert hook.on_failure == on_failure
    assert hook.parallel_validation == parallel_validation


def test_after_context_created_parse_params(
    initialize_kedro_project,
):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks(
            on_failure="raise_fast",
            parallel_validation=False,
            check_orphan_expectation_suites=False,
            single_datasource_check=False,
            expectation_tags=[],
            max_processes=1,
            notify_config=DummyNotifier(notify_on="all"),
        )
        session._hook_manager.register(hooks)

        notifiy_config = {
            "module": "kedro_expectations.notification",
            "class": "EmailNotifier",
            "kwargs": {
                "notify_on": "failure",
                "recipients": ["john.doe@anacision.de"],
                "smtp_address": "testserver",
                "smtp_port": 1234,
            },
        }
        hook_options = {
            "hook_options": {
                "on_failure": "raise_later",
                "parallel_validation": True,
                "check_orphan_expectation_suites": True,
                "single_datasource_check": True,
                "expectation_tags": ["tag1", "tag2"],
                "max_processes": 4,
                "notify_config": notifiy_config,
            }
        }

        context = session.load_context()
        params = context.config_loader["parameters"]
        params.update(hook_options)
        context.config_loader["parameters"] = params
        hooks.after_context_created(context)

        # check if the hook options are parsed and updated correctly
        assert hooks.on_failure == "raise_later"
        assert hooks.parallel_validation is True
        assert hooks.check_orphan_expectation_suites is True
        assert hooks.single_datasource_check is True
        assert hooks.expectation_tags == ["tag1", "tag2"]
        assert hooks.max_processes == 4
        # check if the notifier is correctly initialized
        assert isinstance(hooks._notifier, EmailNotifier)
        assert hooks._notifier._notify_on == "failure"
        assert hooks._notifier._recipients == ["john.doe@anacision.de"]


def test_after_catalog_created_orphan_suites_continue(initialize_kedro_project, capfd):
    project_dir = initialize_kedro_project
    context = ge.get_context(mode="file")

    with KedroSession.create(project_path=project_dir) as session:
        session._hook_manager.register(KedroExpectationsHooks(on_failure="continue"))
        context.suites.add(ExpectationSuite("orphan_suite"))
        session.run(pipeline_name="data_processing")

        out, err = capfd.readouterr()
        assert "Pipeline execution completed" in out

        context.suites.delete("orphan_suite")


@pytest.mark.parametrize("on_failure", ["raise_later", "raise_fast"])
def test_after_catalog_created_orphan_suites_raise(
    initialize_kedro_project, capfd, on_failure
):
    project_dir = initialize_kedro_project
    context = ge.get_context(mode="file")

    with KedroSession.create(project_path=project_dir) as session:
        session._hook_manager.register(KedroExpectationsHooks(on_failure=on_failure))
        context.suites.add(ExpectationSuite("orphan_suite"))

        with pytest.raises(SuiteValidationFailure):
            session.run(pipeline_name="data_processing")

        context.suites.delete("orphan_suite")


def test_before_node_run_success(initialize_kedro_project, test_node):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks()
        session._hook_manager.register(hooks)
        catalog = session.load_context().catalog
        dataset = catalog.load("companies")
        hooks.before_node_run(catalog, {"companies": dataset}, test_node)

        assert len(hooks.checkpoint_results) == 2
        assert all([result.success for result in hooks.checkpoint_results])


def test_before_node_run_no_expectation_suites(
    initialize_kedro_project, capfd, test_node
):
    project_dir = initialize_kedro_project

    try:
        context = ge.get_context(mode="file")
        context.suites.delete("companies.succeeding_test_suite")
        context.suites.delete("companies.second_test_suite")
        with KedroSession.create(project_path=project_dir) as session:
            hooks = KedroExpectationsHooks()
            session._hook_manager.register(hooks)
            catalog = session.load_context().catalog
            dataset = catalog.load("companies")
            hooks.before_node_run(catalog, {"companies": dataset}, test_node)

            out, err = capfd.readouterr()
            assert "No expectation suite was found" in out

    finally:
        # reste context for next tests
        ge.get_context(mode="file").suites.add(
            ExpectationSuite("companies.succeeding_test_suite")
        )
        ge.get_context(mode="file").suites.add(
            ExpectationSuite("companies.second_test_suite")
        )


def test_before_node_run_suite_validation_fail(
    initialize_kedro_project, capfd, test_node
):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks()
        session._hook_manager.register(hooks)
        catalog = session.load_context().catalog

        with pytest.raises(SuiteValidationFailure):
            hooks.before_node_run(catalog, {"companies": None}, test_node)


def test_before_node_run_partitioned_success(initialize_kedro_project, test_node):
    project_dir = initialize_kedro_project

    try:
        ge.get_context(mode="file").suites.add(
            ExpectationSuite("companies_partitioned.new_test_suite")
        )
        with KedroSession.create(project_path=project_dir) as session:
            hooks = KedroExpectationsHooks()
            session._hook_manager.register(hooks)
            catalog = session.load_context().catalog
            dataset = catalog.load("companies_partitioned")

            hooks.before_node_run(
                catalog, {"companies_partitioned": dataset}, test_node
            )

            assert len(hooks.checkpoint_results) == 3
            assert all([result.success for result in hooks.checkpoint_results])
    finally:
        ge.get_context(mode="file").suites.delete(
            "companies_partitioned.new_test_suite"
        )


def test_before_node_run_partitioned_no_expectation_suite(
    initialize_kedro_project, capfd, test_node
):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks()
        session._hook_manager.register(hooks)
        catalog = session.load_context().catalog
        dataset = catalog.load("companies_partitioned")

        hooks.before_node_run(catalog, {"companies_partitioned": dataset}, test_node)
        out, err = capfd.readouterr()
        assert 'No expectation suite was found for "companies_partitioned"' in out


def test_before_node_run_partitioned_validation_fail(
    initialize_kedro_project, capfd, test_node
):
    project_dir = initialize_kedro_project
    expectation_suite_name = "new_test_suite" + get_random_string(5)

    try:
        user_input = [2, 1, "companies_partitioned", expectation_suite_name, "0"]
        with patch("click.prompt", side_effect=user_input):
            start_suite_creation(ge.get_context(mode="file"))

        with KedroSession.create(project_path=project_dir) as session:
            hooks = KedroExpectationsHooks()
            session._hook_manager.register(hooks)
            catalog = session.load_context().catalog
            dataset = catalog.load("companies_partitioned")
            hooks.before_node_run(
                catalog, {"companies_partitioned": dataset}, test_node
            )
            # The checks simply fail because each partition is checked on its own but the profiler ran on full set
            assert len(hooks._fail_log) == 3
    finally:
        ge.get_context(mode="file").suites.delete(
            f"companies_partitioned.{expectation_suite_name}"
        )


@pytest.mark.parametrize("on_failure", ["raise_later", "continue"])
def test_before_node_run_parallel_validation(
    initialize_kedro_project, on_failure, test_node
):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks(on_failure=on_failure, parallel_validation=True)
        session._hook_manager.register(hooks)
        catalog = session.load_context().catalog
        dataset = catalog.load("companies")

        hooks.before_node_run(catalog, {"companies": dataset}, test_node)
        assert len(hooks.checkpoint_results) == 0
        assert sum(st != "finished" for st in hooks._process_status.values()) == 1
        hooks._process_pool.terminate()


@pytest.mark.parametrize("on_failure", ["raise_later", "continue"])
def test_after_pipeline_run_parallel_validation_join(
    initialize_kedro_project, on_failure, test_node
):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks(on_failure=on_failure, parallel_validation=True)
        session._hook_manager.register(hooks)
        catalog = session.load_context().catalog
        dataset = catalog.load("companies")

        hooks.before_node_run(catalog, {"companies": dataset}, test_node)
        assert len(hooks.checkpoint_results) == 0
        assert sum(st != "finished" for st in hooks._process_status.values()) == 1
        # this function waits for all validation processes to finish
        hooks.after_pipeline_run(dict(), None, None, catalog)
        assert len(hooks.checkpoint_results) == 2
        assert sum(st == "finished" for st in hooks._process_status.values()) == 1


def test_full_pipeline_run_parallel_validation_raise_later(initialize_kedro_project):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks(
            on_failure="raise_later", parallel_validation=True
        )
        session._hook_manager.register(hooks)
        with pytest.raises(SuiteValidationFailure):
            session.run(pipeline_name="data_processing_failing")
        assert len(hooks.checkpoint_results) == 1
        assert not hooks.checkpoint_results[0].success
        assert sum(st == "finished" for st in hooks._process_status.values()) == 1


def test_full_pipeline_run_parallel_validation_continue(initialize_kedro_project):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks(on_failure="continue", parallel_validation=True)
        session._hook_manager.register(hooks)
        session.run(pipeline_name="data_processing_failing")
        assert len(hooks.checkpoint_results) == 1
        assert not hooks.checkpoint_results[0].success
        assert sum(st == "finished" for st in hooks._process_status.values()) == 1


def test_after_pipeline_run_no_checkpoint_results(initialize_kedro_project):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        notifier = DummyNotifier(notify_on="all")
        hooks = KedroExpectationsHooks(notify_config=notifier)
        session._hook_manager.register(hooks)
        catalog = session.load_context().catalog

        hooks.after_pipeline_run(dict(), None, None, catalog)

        assert len(hooks.checkpoint_results) == 0
        assert list(hooks._datasource_run_counter.values()) == list()


def test_after_pipeline_run_partitioned_fail(initialize_kedro_project, test_node):
    project_dir = initialize_kedro_project

    try:
        user_input = [2, 1, "companies_partitioned", "new_test_suite", "0"]
        with patch("click.prompt", side_effect=user_input):
            start_suite_creation(ge.get_context(mode="file"))

        with KedroSession.create(project_path=project_dir) as session:
            notifier = DummyNotifier(notify_on="all")
            hooks = KedroExpectationsHooks(notify_config=notifier)
            session._hook_manager.register(hooks)
            catalog = session.load_context().catalog
            dataset = catalog.load("companies_partitioned")

            hooks.before_node_run(
                catalog, {"companies_partitioned": dataset}, test_node
            )
            hooks.after_pipeline_run(dict(), None, None, catalog)
            # The checks simply fail because each partition is checked on its own but the profiler ran on full set
            assert [result.success for result in hooks.checkpoint_results] == [
                False
            ] * 3
            assert list(hooks._datasource_run_counter.values()) == [1]

    finally:
        ge.get_context(mode="file").suites.delete(
            "companies_partitioned.new_test_suite"
        )
