from typing import List

import fastworkflow
from pydantic import BaseModel, Field, ConfigDict
from fastworkflow.workflow import Workflow
from fastworkflow import CommandOutput, CommandResponse
from fastworkflow.train.generate_synthetic import generate_diverse_utterances

from ..retail_data import load_data
from ..tools.calculate import Calculate


class Signature:
    """Calculate a mathematical expression"""

    class Input(BaseModel):
        expression: str = Field(
            default="NOT_FOUND",
            description=(
                "The mathematical expression to calculate. Allowed characters: digits, "
                "+, -, *, /, parentheses, spaces."
            ),
            pattern=r"^(NOT_FOUND|[0-9+\-*/().\s]+)$",
            examples=["(2 + 3) * 4", "10 / 2 + 3", "(8-3)/5"],
        )

        model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    class Output(BaseModel):
        result: str = Field(
            description=(
                "Calculated result as a string. Returns an error message for invalid input."
            )
        )

    plain_utterances: List[str] = [
        "What is 2 + 2?",
        "Calculate (2 + 3) * 4",
        "Can you compute 10 / 2 + 3?",
        "Evaluate (8-3)/5",
        "Please calculate 7 * (6 - 2)",
    ]

    template_utterances: List[str] = []

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> List[str]:
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:
    def __call__(self, workflow: Workflow, command: str, command_parameters: Signature.Input) -> CommandOutput:
        output = self._process_command(workflow, command_parameters)
        response = f"Result: {output.result}"
        return CommandOutput(
            workflow_id=workflow.id,
            command_responses=[CommandResponse(response=response)],
        )

    def _process_command(self, workflow: Workflow, input: Signature.Input) -> Signature.Output:
        data = load_data()
        result = Calculate.invoke(data=data, expression=input.expression)
        return Signature.Output(result=result)


