import pytest
from kedro.framework.session import KedroSession
from kedro_expectations.exceptions import SuiteValidationFailure
from kedro_expectations import KedroExpectationsHooks
from kedro_expectations.notification import (
    DummyNotifier,
    EmailNotifier,
    _DEFAULT_SUBJECT,
    _DEFAULT_SENDER_ALIAS,
)
from unittest.mock import patch
from great_expectations.checkpoint.actions import EmailAction


@pytest.mark.parametrize("notify_on", ["all", "success"])
def test_gx_success_notification(initialize_kedro_project, capfd, notify_on):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        assert not session._hook_manager.is_registered(KedroExpectationsHooks)
        session._hook_manager.register(
            KedroExpectationsHooks(
                on_failure="raise_fast",
                notify_config=DummyNotifier(notify_on=notify_on),
            )
        )

        session.run(pipeline_name="data_processing")
        # Check if the DummyNotifier (which runs the gx NoOpAction) got called
        out, err = capfd.readouterr()
        assert "Happily doing nothing" in out


def test_gx_failure_notification_no_failure(initialize_kedro_project, capfd):
    project_dir = initialize_kedro_project

    with KedroSession.create(project_path=project_dir) as session:
        assert not session._hook_manager.is_registered(KedroExpectationsHooks)
        session._hook_manager.register(
            KedroExpectationsHooks(
                on_failure="raise_fast",
                notify_config=DummyNotifier(notify_on="failure"),
            )
        )

        session.run(pipeline_name="data_processing")
        # Check if the DummyNotifier (which runs the gx NoOpAction) got NOT called
        out, err = capfd.readouterr()
        assert "Happily doing nothing" not in out


def test_email_notification_success(initialize_kedro_project):
    # Initialize the project directory
    project_dir = initialize_kedro_project

    # Mock the send_email function
    with patch.object(EmailAction, "_send_email") as mock_send_email:
        # Set up the Kedro session
        with KedroSession.create(project_path=project_dir) as session:
            assert not session._hook_manager.is_registered(KedroExpectationsHooks)
            session._hook_manager.register(
                KedroExpectationsHooks(
                    on_failure="raise_fast",
                    notify_config=EmailNotifier(
                        notify_on="success",
                        recipients=["john.doe@anacision.de"],
                        smtp_address="testserver",
                        smtp_port="1234",
                    ),
                )
            )

            session.run(pipeline_name="data_processing")

            # Ensure send_email was called once
            mock_send_email.assert_called_once()

            # Retrieve the actual call arguments
            called_args, called_kwargs = mock_send_email.call_args

            # Perform 1:1 checks for other arguments
            assert called_kwargs["title"] == _DEFAULT_SUBJECT + ": True"
            assert called_kwargs["receiver_emails_list"] == ["john.doe@anacision.de"]

            # Check if specific words are in the html content
            html_content = called_kwargs["html"]
            assert (
                html_content.count(
                    "<p><strong>Summary</strong>: <strong>2</strong> of <strong>2</strong> expectations were met</p>"
                )
                == 1
            )
            assert (
                html_content.count(
                    "<p><strong><h3><u>Summary_Expectation_Suite</u></h3></strong></p>"
                )
                == 1
            )


def test_email_notification_failure(initialize_kedro_project):
    # Initialize the project directory
    project_dir = initialize_kedro_project

    # Mock the send_email function
    with patch.object(EmailAction, "_send_email") as mock_send_email:
        # Set up the Kedro session
        with KedroSession.create(project_path=project_dir) as session:
            assert not session._hook_manager.is_registered(KedroExpectationsHooks)
            session._hook_manager.register(
                KedroExpectationsHooks(
                    on_failure="raise_fast",
                    notify_config=EmailNotifier(
                        notify_on="failure",
                        recipients=["john.doe@anacision.de"],
                        smtp_address="testserver",
                        smtp_port="1234",
                    ),
                )
            )

            # Expecting a SuiteValidationFailure to be raised
            with pytest.raises(SuiteValidationFailure):
                session.run(pipeline_name="data_processing_failing")

            # Ensure send_email was called once
            mock_send_email.assert_called_once()

            # Retrieve the actual call arguments
            called_args, called_kwargs = mock_send_email.call_args

            # Perform 1:1 checks for other arguments
            assert called_kwargs["title"] == _DEFAULT_SUBJECT + ": False"
            assert called_kwargs["receiver_emails_list"] == ["john.doe@anacision.de"]

            # Check if specific words are in the html content
            html_content = called_kwargs["html"]
            assert (
                html_content.count(
                    "<p><strong>Summary</strong>: <strong>0</strong> of <strong>1</strong> expectations were met</p>"
                )
                == 2
            )
            assert (
                html_content.count(
                    "<p><strong><h3><u>Summary_Expectation_Suite</u></h3></strong></p>"
                )
                == 1
            )
            assert (
                html_content.count(
                    "<p><strong>Expectation Suite Name</strong>: companies_unexpected.failing_test_suite</p>"
                )
                == 1
            )
