import textwrap

from pydantic_ai_kernel import PydanticAIBaseKernel
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequestPart,
    SystemPromptPart,
    UserPromptPart,
    ToolReturnPart,
    RetryPromptPart,
    ModelResponsePart,
    TextPart,
    ToolCallPart,
    BuiltinToolCallPart,
    ModelMessagesTypeAdapter,
    ThinkingPart,
    FilePart,
)
from metakernel import Magic, option


class AgentHistoryMagic(Magic):

    @option(
        "-l",
        "--light",
        action="store_true",
        default=False,
        help="Display raw text, no color",
    )
    @option(
        "-r",
        "--raw",
        action="store_true",
        default=False,
        help="Return raw json of agent history",
    )
    def line_agent_history(self, light: bool = False, raw: bool = False) -> None:
        """
        %agent_history - display the agent history

        Examples :
        ---
            - `%agent_history -l` : display the cells nicely, without ANSI colors
            - `%agent_history -r` : display the raw json history of agent from pydantic-ai

        """

        self.kernel: PydanticAIBaseKernel
        self.evaluate = False

        history: list[ModelMessage] = self.kernel.agent_history

        if raw:
            self.kernel.Print(
                ModelMessagesTypeAdapter.dump_json(history, indent=4).decode("utf-8")
            )
            return
        for each_model_message in history:
            self.kernel.Print(nice_model_message_display(each_model_message, not light))


def put_text_in_box(text: str, indent: int) -> str:
    """
    Creates a string where the text is in a box,
    with an indentation of indent. Deals with
    multi-line text.

    Example : (text = 'Hey !', indent=4)
    ---
            │   Hey !
            ╰───────────────────────────────

    Parameters :
    ---
        - text (str) : the text inside the box
        - indent (int) : the indent of the box

    Returns :
    ---
        A string that represents the string, in a
        pretty box.
    """
    out = ""
    preshift = " " * indent + "│" + " " * 3

    out += f"{textwrap.indent(text, preshift, predicate=lambda line: True)}\n"
    out += " " * indent + "╰─" + "─" * 30 + "\n"
    return out


def nice_display_model_message_part(
    part: ModelRequestPart | ModelResponsePart, indent: int, prettier: bool = False
) -> str:
    """
    Transform the model message part in a string that is more human-readable.

    Parameters :
    ---
        - part (ModelRequestPart | ModelResponsePart) : the pydantic-ai object
            containing the information
        - indent (int) : the number of empty spaces before the text is displayed
        - prettier (bool = False) : if True, the type of the part is displayed
            in color, with ANSI escape color codes.

    Returns :
    ---
        - a string, which should be printed.
    """
    title = ""
    content = ""
    if isinstance(part, SystemPromptPart):
        title = "System Prompt"
        content = part.content
    elif isinstance(part, UserPromptPart):
        title = "User Prompt"
        content = str(part.content)
    elif isinstance(part, ToolReturnPart):
        title = "Tool Return"
        content = f"{part.tool_name} : {part.content}"
    elif isinstance(part, RetryPromptPart):
        title = "Retry"
        content = str(part.content)
    elif isinstance(part, TextPart):
        title = "Text"
        content = part.content
    elif isinstance(part, ToolCallPart) or isinstance(part, BuiltinToolCallPart):
        title = "Tool Calling"
        content = f"Name :{part.tool_name}\nArgs :{part.args}"
    elif isinstance(part, ThinkingPart):
        title = "Thinking"
        content = part.content
    elif isinstance(part, FilePart):
        title = "File"

    if prettier:
        title = f"\033[0;32m{title}\033[0m"

    out = " " * 2 + title + " :\n"
    out += put_text_in_box(content, indent)
    return out


def nice_model_message_display(message: ModelMessage, prettier: bool = False) -> str:
    """
    Display all the parts of the message, in a box with the part type as a box title.

    Parameters:
    ---
        - message (ModelMessage) : a pydantic-ai ModelMessage, containing text / tool call
            informations
        - prettier (bool = False) : whether to display the title in color or not (ANSI color
            codes)/

    Returns :
    ---
        A string which should be printed, containing the message history.
    """
    indent = 4
    out = ""
    for each_part in message.parts:
        out += nice_display_model_message_part(each_part, indent, prettier)
    return out


def register_magics(kernel) -> None:
    kernel.register_magics(AgentHistoryMagic)
