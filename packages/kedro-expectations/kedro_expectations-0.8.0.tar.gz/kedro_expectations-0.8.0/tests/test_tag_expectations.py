from kedro.framework.session import KedroSession
from kedro_expectations import KedroExpectationsHooks
from kedro_expectations.notification import DummyNotifier


def test_tags_one_of_two_suites(initialize_kedro_project, capfd):
    tags = ["T"]
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks(notify_config=DummyNotifier(), expectation_tags=tags)
        session._hook_manager.register(hooks)
        session.run(pipeline_name="data_processing")
        checkpoint_results = hooks.checkpoint_results
        out, err = capfd.readouterr()

    assert "Happily doing nothing" in out
    assert "Suite companies.second_test_suite for DataSet companies failed!" not in out
    assert len(checkpoint_results) == 1
    assert "companies.second_test_suite" == list(checkpoint_results[0].run_results.values())[0].suite_name


def test_tags_all_expectation_suites(initialize_kedro_project, capfd):
    tags = ["P", "T"]
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks(notify_config=DummyNotifier(), expectation_tags=tags)
        session._hook_manager.register(hooks)
        session.run(pipeline_name="data_processing")
        checkpoint = hooks.checkpoint_results
        out, err = capfd.readouterr()

    assert "Happily doing nothing" in out
    assert len(checkpoint) == 2


def test_tags_inexistent_tag(initialize_kedro_project, capfd):
    tags = ["X"]
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        hooks = KedroExpectationsHooks(notify_config=DummyNotifier(), expectation_tags=tags)
        session._hook_manager.register(hooks)
        session.run(pipeline_name="data_processing")
        checkpoint = hooks.checkpoint_results
        out, err = capfd.readouterr()

    assert "No expectation suite for tags ['X']." in out
    assert len(checkpoint) == 0
