from abc import ABC, abstractmethod
from typing import List, Literal

from great_expectations.checkpoint import EmailAction, ValidationAction
from great_expectations.checkpoint.actions import ActionContext, should_notify
from great_expectations.checkpoint.checkpoint import CheckpointResult
from pydantic import Field

from .actions import NoOpAction

_DEFAULT_SUBJECT = "Summary Run Validation"
_DEFAULT_SENDER_ALIAS = "validation_notifier@kedro-expectations.io"


class BaseNotifier(ABC):
    def __init__(
        self,
        sender_alias: str,
        recipients: List[str],
        notify_on: str = "all",
        subject: str = _DEFAULT_SUBJECT,
    ):
        """
        :param sender_alias: Alias of the sender
        :param recipients: List of recipients as str. Format is dependent on the specific notifier.
        :param notify_on: Specifies validation status that triggers notification. One of "all", "failure", "success".
        :param subject: General subject of the notification.
        """

        self._sender_alias = sender_alias
        self._recipients = recipients
        self._notify_on = notify_on
        self.subject = subject

    @property
    @abstractmethod
    def _action(self) -> ValidationAction:
        pass

    def will_notify(self, success: bool) -> bool:
        return (
            (self._notify_on == "all")
            | (self._notify_on == "success" and success)
            | (self._notify_on == "failure" and not success)
        )

    def run(
        self,
        checkpoint_result: CheckpointResult,
        action_context: ActionContext = None,
    ):

        success = checkpoint_result.success
        if self.will_notify(success):
            self._action.run(
                checkpoint_result=checkpoint_result, action_context=action_context
            )


class EmailNotifier(BaseNotifier):
    _action = None

    def __init__(
        self,
        recipients: List[str],
        smtp_address: str,
        smtp_port: str,
        sender_alias: str = _DEFAULT_SENDER_ALIAS,
        sender_login: str = None,
        sender_password: str = None,
        security_protocol: str = "SSL",
        notify_on: str = "all",
        subject: str = _DEFAULT_SUBJECT,
    ):
        super().__init__(
            sender_alias=sender_alias,
            recipients=recipients,
            notify_on=notify_on,
            subject=subject,
        )
        self._action = EmailAction(
            name="kedro_expectation_email_action",
            renderer={
                "module_name": "great_expectations.render.renderer.email_renderer",
                "class_name": "EmailRenderer",
            },
            smtp_address=smtp_address,
            smtp_port=smtp_port,
            sender_login=sender_login,
            sender_password=sender_password,
            receiver_emails=",".join(recipients),
            sender_alias=sender_alias,
            use_ssl=security_protocol.lower() == "ssl",
            use_tls=security_protocol.lower() == "tls",
            notify_on=self._notify_on,
            notify_with=None,
        )


class FileStoreAction(EmailAction):
    """
    Action that writes the notification to a file ./email.txt
    Used by the FileNotifier.

    Convenient for local debugging.
    """

    type: Literal["file_store_email"] = "file_store_email"

    # @override
    def run(
        self,
        checkpoint_result: CheckpointResult,
        action_context: ActionContext | None = None,
    ) -> dict:
        success = checkpoint_result.success or False
        if not should_notify(success=success, notify_on=self.notify_on):
            return {"email_result": ""}

        title, html = self.renderer.render(checkpoint_result=checkpoint_result)

        email_text = f"{title}\n{html}"

        with open(
            "./email.txt",
            "w",
            encoding="utf-8",
        ) as file:
            file.write(email_text)

        return {"email_result": "success"}


class FileNotifier(BaseNotifier):
    """
    Notifier that writes the notification to a file ./email.txt

    Convenient for local debugging.
    """

    _action = None

    def __init__(
        self,
        recipients: List[str],
        smtp_address: str,
        smtp_port: str,
        sender_alias: str = _DEFAULT_SENDER_ALIAS,
        sender_login: str = None,
        sender_password: str = None,
        security_protocol: str = "SSL",
        notify_on: str = "all",
        subject: str = _DEFAULT_SUBJECT,
    ):
        super().__init__(
            sender_alias=sender_alias,
            recipients=recipients,
            notify_on=notify_on,
            subject=subject,
        )
        self._action = FileStoreAction(
            name="kedro_expectation_file_action",
            renderer={
                "module_name": "great_expectations.render.renderer.email_renderer",
                "class_name": "EmailRenderer",
            },
            smtp_address=smtp_address,
            smtp_port=smtp_port,
            sender_login=sender_login,
            sender_password=sender_password,
            receiver_emails=",".join(recipients),
            sender_alias=sender_alias,
            use_ssl=security_protocol.lower() == "ssl",
            use_tls=security_protocol.lower() == "tls",
            notify_on=self._notify_on,
            notify_with=None,
        )


class DummyNotifier(BaseNotifier):
    """
    Dummy class used for test purposes
    """

    _action = NoOpAction()

    def __init__(
        self,
        notify_on: str = "all",
    ):
        super().__init__(
            sender_alias="", recipients=[], notify_on=notify_on, subject=""
        )
