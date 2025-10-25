from wfx.base.io.text import TextComponent
from wfx.io import MultilineInput, Output
from wfx.schema.message import Message


class TextOutputComponent(TextComponent):
    display_name = "Text Output"
    description = "Sends text output via API."
    documentation: str = "https://aiexec-docs.khulnasoft.com/components-io#text-output"
    icon = "type"
    name = "TextOutput"

    inputs = [
        MultilineInput(
            name="input_value",
            display_name="Inputs",
            info="Text to be passed as output.",
        ),
    ]
    outputs = [
        Output(display_name="Output Text", name="text", method="text_response"),
    ]

    def text_response(self) -> Message:
        message = Message(
            text=self.input_value,
        )
        self.status = self.input_value
        return message
