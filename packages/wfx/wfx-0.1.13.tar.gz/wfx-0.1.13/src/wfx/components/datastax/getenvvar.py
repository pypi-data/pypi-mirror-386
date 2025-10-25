import os

from wfx.custom.custom_component.component import Component
from wfx.inputs.inputs import StrInput
from wfx.schema.message import Message
from wfx.template.field.base import Output


class GetEnvVar(Component):
    display_name = "Get Environment Variable"
    description = "Gets the value of an environment variable from the system."
    icon = "AstraDB"

    inputs = [
        StrInput(
            name="env_var_name",
            display_name="Environment Variable Name",
            info="Name of the environment variable to get",
        )
    ]

    outputs = [
        Output(display_name="Environment Variable Value", name="env_var_value", method="process_inputs"),
    ]

    def process_inputs(self) -> Message:
        if self.env_var_name not in os.environ:
            msg = f"Environment variable {self.env_var_name} not set"
            raise ValueError(msg)
        return Message(text=os.environ[self.env_var_name])
