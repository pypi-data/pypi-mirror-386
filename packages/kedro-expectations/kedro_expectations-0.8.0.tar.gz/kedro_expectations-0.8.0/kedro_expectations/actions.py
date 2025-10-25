from great_expectations.checkpoint import ValidationAction
from great_expectations.checkpoint.actions import ActionContext
from great_expectations.checkpoint.checkpoint import CheckpointResult
from great_expectations.compatibility.typing_extensions import override


class NoOpAction(ValidationAction):
    type = "noop"
    name = "noop"

    @override
    def run(  # noqa: PLR0913
        self,
        checkpoint_result: CheckpointResult,
        action_context: ActionContext = None,
    ) -> None:
        print("Happily doing nothing")
