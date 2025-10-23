from typing import List

import fastworkflow
from pydantic import BaseModel, Field, ConfigDict
from fastworkflow.workflow import Workflow
from fastworkflow import CommandOutput, CommandResponse

# Domain helpers
from ..retail_data import load_data
from ..tools.find_user_id_by_email import FindUserIdByEmail


class Signature:
    """
    Find user id by email. 
    If email is not available, use `find_user_id_by_name_zip` instead.
    As a last resort transfer to a human agent
    """
    class Input(BaseModel):
        """Parameters taken from user utterance."""

        email: str = Field(
            default="NOT_FOUND",
            description="The email address to search for",
            pattern=r"^(NOT_FOUND|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$",
            examples=["user@example.com"],
        )

        model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    class Output(BaseModel):
        user_id: str = Field(
            description="User identifier returned by lookup.",
            json_schema_extra={
                "used_by": ["get_user_details"]
            }
        )

    plain_utterances: List[str] = [
        "Can you tell me the ID linked to john.doe@example.com?",
        "I only have the email address — how do I find the user ID?",
        "What's the account ID for someone with the email jane_smith@domain.com?",
        "I need the unique user ID associated with this email: support@acme.io",
        "Do we have an ID on file for mark.brown@company.org?",
    ]

    template_utterances: List[str] = []

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> List[str]:
        utterance_definition = fastworkflow.RoutingRegistry.get_definition(workflow.folderpath)
        utterances_obj = utterance_definition.get_command_utterances(command_name)

        from fastworkflow.train.generate_synthetic import generate_diverse_utterances

        return generate_diverse_utterances(utterances_obj.plain_utterances, command_name)


class ResponseGenerator:
    def __call__(
        self,
        workflow: Workflow,
        command: str,
        command_parameters: Signature.Input,
    ) -> CommandOutput:
        output = self._process_command(workflow, command_parameters)
        return CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                CommandResponse(response=f"The user id is: {output.user_id}")
            ],
        )

    def _process_command(self, workflow: Workflow, input: Signature.Input) -> Signature.Output:
        data = load_data()
        user_id = FindUserIdByEmail.invoke(data=data, email=input.email)
        return Signature.Output(user_id=user_id) 